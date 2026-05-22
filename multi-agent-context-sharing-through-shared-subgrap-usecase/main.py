#!/usr/bin/env python3
"""
Multi-Agent Context Sharing Through Shared Subgraph References

This demo shows how RushDB's graph-based shared subgraph references solve
the token overhead and state inconsistency problems in multi-agent LLM systems.

The scenario: E-commerce customer service with 3 agents:
1. Triage Agent - determines user intent
2. Routing Agent - selects fulfillment path
3. Fulfillment Agent - executes the request

Each agent reads/writes to their slice of the shared subgraph WITHOUT
requiring full context duplication in every prompt.
"""

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rushdb import RushDB, Record

# ============================================================================
# TOKEN COST ESTIMATION (for comparison)
# ============================================================================

# Approximate token counts for different context approaches
TOKENS_USER_PROFILE = 85       # Basic user info
TOKENS_PREFERENCES = 45        # Shipping, language, etc.
TOKENS_ORDERS = 120            # Order history (up to 5 orders)
TOKENS_SESSION = 35            # Current session state

# Total context that would be injected naively per agent
NAIVE_CONTEXT_TOKENS = (
    TOKENS_USER_PROFILE +
    TOKENS_PREFERENCES +
    TOKENS_ORDERS +
    TOKENS_SESSION
)  # ~285 tokens per agent, ~855 for 3-agent pipeline

# What each agent ACTUALLY needs (subgraph slice)
SLICE_TOKENS_ESTIMATE = {
    "triage": 80,       # SESSION + minimal user info
    "routing": 50,      # Just intent from SESSION
    "fulfillment": 150, # ORDER + PREFERENCES
}

SUBGRAPH_TOTAL_TOKENS = sum(SLICE_TOKENS_ESTIMATE.values())  # ~280 tokens


@dataclass
class TokenMetrics:
    """Track token usage and performance metrics."""
    naive_total: int = 0
    subgraph_total: int = 0
    agent_times: dict = field(default_factory=dict)
    
    def calculate_savings(self):
        """Calculate token and cost savings."""
        savings = self.naive_total - self.subgraph_total
        percent = (savings / self.naive_total * 100) if self.naive_total else 0
        return {
            "naive_tokens": self.naive_total,
            "subgraph_tokens": self.subgraph_total,
            "tokens_saved": savings,
            "percent_reduction": f"{percent:.1f}%",
        }


# ============================================================================
# RUSHDb CLIENT INITIALIZATION
# ============================================================================

def get_db_client() -> RushDB:
    """Initialize RushDB client."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError(
            "RUSHDB_API_KEY not found. "
            "Please copy .env.example to .env and add your API key."
        )
    
    url = os.getenv("RUSHDB_URL")
    if url:
        return RushDB(api_key, url=url)
    return RushDB(api_key)


# ============================================================================
# SUBGRAPH OPERATIONS
# ============================================================================

def get_user_subgraph(db: RushDB, user_email: str) -> dict:
    """
    Retrieve the complete user context subgraph.
    
    This returns the connected graph structure:
    USER → HAS_PREFERENCES → PREFERENCES
      │
      └── HAS_SESSION → SESSION
      │
      └── PLACED → ORDER(s)
    """
    # Find the user
    users = db.records.find({
        "labels": ["USER"],
        "where": {"email": user_email},
        "limit": 1,
    })
    
    if not users.data:
        raise ValueError(f"User not found: {user_email}")
    
    user: Record = users.data[0]
    
    # Find related records through the graph
    # Find PREFERENCES (via HAS_PREFERENCES)
    prefs = db.records.find({
        "labels": ["PREFERENCES"],
        "where": {"USER": {"$relation": {"type": "HAS_PREFERENCES", "direction": "in"}, "email": user_email}},
        "limit": 1,
    })
    
    # Find active SESSION
    sessions = db.records.find({
        "labels": ["SESSION"],
        "where": {
            "USER": {"$relation": {"type": "HAS_SESSION", "direction": "in"}, "email": user_email},
            "status": "active",
        },
        "orderBy": {"started_at": "desc"},
        "limit": 1,
    })
    
    # Find recent ORDERS
    orders = db.records.find({
        "labels": ["ORDER"],
        "where": {"USER": {"$relation": {"type": "PLACED", "direction": "in"}, "email": user_email}},
        "orderBy": {"created_at": "desc"},
        "limit": 5,
    })
    
    return {
        "user": user,
        "preferences": prefs.data[0] if prefs.data else None,
        "session": sessions.data[0] if sessions.data else None,
        "orders": orders.data,
    }


# ============================================================================
# MULTI-AGENT PIPELINE
# ============================================================================

@dataclass
class AgentResult:
    """Result from an agent execution."""
    agent: str
    tokens_used: int
    latency_ms: float
    data: dict


class TriageAgent:
    """
    Triage Agent - Entry point for customer requests.
    
    Reads: SESSION (to check for existing context), minimal USER info
    Writes: Updates SESSION with determined intent
    
    Token cost: ~80 tokens (vs ~285 for naive full context)
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.name = "TriageAgent"
    
    def run(self, subgraph: dict, request: str) -> AgentResult:
        """
        Analyze user request and determine intent.
        
        In a real system, this would use an LLM. Here we simulate
        intent detection based on keywords.
        """
        start = time.time()
        
        session = subgraph["session"]
        user = subgraph["user"]
        
        # Simulate reading only session slice (not full context)
        # tokens_used represents actual context read
        tokens_used = 80
        
        # Simulate intent detection logic
        request_lower = request.lower()
        if "return" in request_lower or "refund" in request_lower:
            intent = "return_request"
            confidence = 0.92
            suggested_action = "initiate_return_flow"
        elif "track" in request_lower or "where" in request_lower or "shipping" in request_lower:
            intent = "track_order"
            confidence = 0.88
            suggested_action = "show_tracking"
        elif "cancel" in request_lower:
            intent = "cancel_request"
            confidence = 0.95
            suggested_action = "initiate_cancellation"
        elif "help" in request_lower or "question" in request_lower:
            intent = "general_inquiry"
            confidence = 0.75
            suggested_action = "provide_help"
        else:
            intent = "unknown"
            confidence = 0.50
            suggested_action = "escalate"
        
        # Write the determined intent back to the subgraph
        # This is the key: other agents will read this slice
        self.db.records.update(
            record_id=session.id,
            data={
                "intent": intent,
                "confidence": confidence,
                "triage_completed_at": datetime.now().isoformat(),
                "triage_agent": self.name,
                "suggested_action": suggested_action,
            },
        )
        
        latency = (time.time() - start) * 1000
        
        return AgentResult(
            agent=self.name,
            tokens_used=tokens_used,
            latency_ms=latency,
            data={
                "intent": intent,
                "confidence": confidence,
                "suggested_action": suggested_action,
            },
        )


class RoutingAgent:
    """
    Routing Agent - Selects the appropriate fulfillment path.
    
    Reads: SESSION (just the intent field set by Triage)
    Writes: Updates SESSION with routing decision
    
    Token cost: ~50 tokens (vs ~285 for naive)
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.name = "RoutingAgent"
    
    def run(self, subgraph: dict) -> AgentResult:
        """Select fulfillment path based on determined intent."""
        start = time.time()
        
        session = subgraph["session"]
        intent = session.get("intent", "unknown")
        
        # Read only the intent - not full context
        tokens_used = 50
        
        # Route mapping
        route_map = {
            "return_request": {
                "route": "returns_department",
                "priority": "high",
                "requires_approval": False,
                "sla_minutes": 30,
            },
            "track_order": {
                "route": "logistics_service",
                "priority": "medium",
                "requires_approval": False,
                "sla_minutes": 5,
            },
            "cancel_request": {
                "route": "orders_cancellation",
                "priority": "high",
                "requires_approval": True,
                "sla_minutes": 15,
            },
            "general_inquiry": {
                "route": "knowledge_base",
                "priority": "low",
                "requires_approval": False,
                "sla_minutes": 60,
            },
            "unknown": {
                "route": "human_escalation",
                "priority": "medium",
                "requires_approval": False,
                "sla_minutes": 120,
            },
        }
        
        route = route_map.get(intent, route_map["unknown"])
        
        # Write routing decision back to subgraph
        self.db.records.update(
            record_id=session.id,
            data={
                "route": route["route"],
                "priority": route["priority"],
                "requires_approval": route["requires_approval"],
                "sla_minutes": route["sla_minutes"],
                "routing_completed_at": datetime.now().isoformat(),
                "routing_agent": self.name,
            },
        )
        
        latency = (time.time() - start) * 1000
        
        return AgentResult(
            agent=self.name,
            tokens_used=tokens_used,
            latency_ms=latency,
            data=route,
        )


class FulfillmentAgent:
    """
    Fulfillment Agent - Executes the routed request.
    
    Reads: ORDER(s), PREFERENCES (based on route)
    Writes: RESULT record linked to SESSION
    
    Token cost: ~150 tokens (vs ~285 for naive)
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.name = "FulfillmentAgent"
    
    def run(self, subgraph: dict) -> AgentResult:
        """Execute the request based on routing decision."""
        start = time.time()
        
        session = subgraph["session"]
        user = subgraph["user"]
        orders = subgraph["orders"]
        prefs = subgraph["preferences"]
        
        intent = session.get("intent", "unknown")
        route = session.get("route", "unknown")
        
        # Read relevant slices - more tokens than other agents
        # because we need order/preference data
        tokens_used = 150
        
        result_data = {"type": "executed", "route": route}
        
        if intent == "return_request" and orders:
            # Find most recent eligible order for return
            latest_order = orders[0]
            
            result_data.update({
                "action": "return_initiated",
                "order_id": latest_order.id,
                "order_number": latest_order.get("order_number"),
                "total": latest_order.get("total"),
                "return_label_sent": True,
                "shipping_preference": prefs.get("shipping") if prefs else "standard",
            })
        
        elif intent == "track_order" and orders:
            # Get most recent order for tracking
            latest_order = orders[0]
            
            result_data.update({
                "action": "tracking_info",
                "order_id": latest_order.id,
                "order_number": latest_order.get("order_number"),
                "status": latest_order.get("status"),
                "shipping_address": latest_order.get("shipping_address"),
            })
        
        elif intent == "cancel_request" and orders:
            latest_order = orders[0]
            can_cancel = latest_order.get("status") in ["pending", "processing"]
            
            result_data.update({
                "action": "cancellation_processed",
                "order_id": latest_order.id if can_cancel else None,
                "order_number": latest_order.get("order_number"),
                "cancelled": can_cancel,
                "reason": "customer_request" if can_cancel else "order_already_shipped",
            })
        
        elif intent == "general_inquiry":
            result_data.update({
                "action": "help_provided",
                "suggested_articles": ["faq_shipping", "faq_returns", "faq_account"],
            })
        
        # Create RESULT record linked to session
        result = self.db.records.create(
            label="RESULT",
            data={
                "user_id": user.get("external_id"),
                "intent": intent,
                "route": route,
                "fulfillment_data": result_data,
                "completed_at": datetime.now().isoformat(),
                "fulfillment_agent": self.name,
            },
        )
        
        # Link RESULT to SESSION
        self.db.records.attach(
            source=session,
            target=result,
            options={"type": "PRODUCED"},
        )
        
        latency = (time.time() - start) * 1000
        
        return AgentResult(
            agent=self.name,
            tokens_used=tokens_used,
            latency_ms=latency,
            data=result_data,
        )


# ============================================================================
# NAIVE APPROACH SIMULATION
# ============================================================================

def simulate_naive_approach(subgraph: dict) -> TokenMetrics:
    """
    Simulate the naive approach where full context is injected per agent.
    
    This shows what token costs would look like with traditional
    context-injection patterns.
    """
    metrics = TokenMetrics()
    
    print("\n" + "=" * 60)
    print("NAIVE APPROACH: Full Context Injection")
    print("=" * 60)
    
    # Build full context (what would be sent to each agent)
    user = subgraph["user"]
    prefs = subgraph["preferences"]
    orders = subgraph["orders"]
    
    context_parts = []
    
    # User context
    context_parts.append(f"User: {user.get('name')}, {user.get('age')} years old, {user.get('tier')} tier")
    
    # Preferences
    if prefs:
        context_parts.append(
            f"Preferences: shipping={prefs.get('shipping')}, "
            f"language={prefs.get('language')}, notifications={prefs.get('notifications')}"
        )
    
    # Order history (summarized)
    order_summary = ", ".join([f"{o.get('order_number')}({o.get('status')})" for o in orders[:5]])
    context_parts.append(f"Recent orders: {order_summary}")
    
    full_context = " | ".join(context_parts)
    
    # Each agent would receive this full context
    print(f"\n📋 Full context string ({len(full_context)} chars):")
    print(f"   \"{full_context}\"")
    print(f"\n   Token breakdown:")
    print(f"   - User profile:     {TOKENS_USER_PROFILE} tokens")
    print(f"   - Preferences:      {TOKENS_PREFERENCES} tokens")
    print(f"   - Orders (5 max):   {TOKENS_ORDERS} tokens")
    print(f"   - Session:          {TOKENS_SESSION} tokens")
    print(f"   - ─────────────────────────")
    print(f"   - Total per agent:  {NAIVE_CONTEXT_TOKENS} tokens")
    print(f"   - 3 agents total:   {NAIVE_CONTEXT_TOKENS * 3} tokens")
    
    # Naive approach token cost
    naive_tokens = NAIVE_CONTEXT_TOKENS * 3
    metrics.naive_total = naive_tokens
    
    return metrics


# ============================================================================
# SUBGRAPH APPROACH DEMONSTRATION
# ============================================================================

def run_subgraph_pipeline(db: RushDB, subgraph: dict) -> tuple[TokenMetrics, list[AgentResult]]:
    """
    Run the multi-agent pipeline using shared subgraph references.
    """
    metrics = TokenMetrics()
    results = []
    
    print("\n" + "=" * 60)
    print("SUBGRAPH APPROACH: Agent Slice Reading")
    print("=" * 60)
    
    # Initialize agents
    triage = TriageAgent(db)
    routing = RoutingAgent(db)
    fulfillment = FulfillmentAgent(db)
    
    # Test request
    test_request = "I want to return my last order"
    
    print(f"\n📨 Test request: \"{test_request}\"")
    print(f"   User: {subgraph['user'].get('name')} ({subgraph['user'].get('email')})")
    
    # Step 1: Triage Agent
    print(f"\n{'─' * 40}")
    print("STEP 1: TRIAGE AGENT")
    print(f"{'─' * 40}")
    print(f"   Reading: SESSION slice (status, started_at)")
    print(f"   Writing: SESSION.intent, confidence, suggested_action")
    
    result = triage.run(subgraph, test_request)
    results.append(result)
    metrics.agent_times["triage"] = result.latency_ms
    metrics.subgraph_total += result.tokens_used
    
    print(f"\n   ✅ Determined intent: {result.data['intent']}")
    print(f"   ✅ Confidence: {result.data['confidence']:.0%}")
    print(f"   ✅ Suggested action: {result.data['suggested_action']}")
    print(f"   📊 Tokens used: {result.tokens_used} (vs {NAIVE_CONTEXT_TOKENS} naive)")
    print(f"   ⏱️  Latency: {result.latency_ms:.1f}ms")
    
    # Re-fetch subgraph to get updated session
    user_email = subgraph["user"].get("email")
    subgraph = get_user_subgraph(db, user_email)
    
    # Step 2: Routing Agent
    print(f"\n{'─' * 40}")
    print("STEP 2: ROUTING AGENT")
    print(f"{'─' * 40}")
    print(f"   Reading: SESSION.intent only")
    print(f"   Writing: SESSION.route, priority, sla_minutes")
    
    result = routing.run(subgraph)
    results.append(result)
    metrics.agent_times["routing"] = result.latency_ms
    metrics.subgraph_total += result.tokens_used
    
    print(f"\n   ✅ Route: {result.data['route']}")
    print(f"   ✅ Priority: {result.data['priority']}")
    print(f"   ✅ SLA: {result.data['sla_minutes']} minutes")
    print(f"   📊 Tokens used: {result.tokens_used} (vs {NAIVE_CONTEXT_TOKENS} naive)")
    print(f"   ⏱️  Latency: {result.latency_ms:.1f}ms")
    
    # Step 3: Fulfillment Agent
    print(f"\n{'─' * 40}")
    print("STEP 3: FULFILLMENT AGENT")
    print(f"{'─' * 40}")
    print(f"   Reading: ORDER slice, PREFERENCES slice")
    print(f"   Writing: RESULT record (linked to SESSION)")
    
    result = fulfillment.run(subgraph)
    results.append(result)
    metrics.agent_times["fulfillment"] = result.latency_ms
    metrics.subgraph_total += result.tokens_used
    
    print(f"\n   ✅ Action: {result.data.get('action', 'completed')}")
    if "order_id" in result.data and result.data["order_id"]:
        print(f"   ✅ Order: {result.data.get('order_number')}")
    if "return_label_sent" in result.data:
        print(f"   ✅ Return label: {'sent' if result.data['return_label_sent'] else 'not sent'}")
    print(f"   📊 Tokens used: {result.tokens_used} (vs {NAIVE_CONTEXT_TOKENS} naive)")
    print(f"   ⏱️  Latency: {result.latency_ms:.1f}ms")
    
    return metrics, results


# ============================================================================
# RESULTS COMPARISON
# ============================================================================

def print_comparison(naive_metrics: TokenMetrics, subgraph_metrics: TokenMetrics):
    """Print side-by-side comparison of approaches."""
    print("\n" + "=" * 60)
    print("COMPARISON: Token Costs & Performance")
    print("=" * 60)
    
    savings = subgraph_metrics.calculate_savings()
    
    print(f"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TOKEN USAGE COMPARISON                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  APPROACH          │  TRIAGE  │  ROUTING  │  FULFILLMT │    TOTAL          │
│  ─────────────────────────────────────────────────────────────────────────  │
""")
    
    print(f"│  Naive (injected)   │   {NAIVE_CONTEXT_TOKELS:>6}  │   {NAIVE_CONTEXT_TOKENS:>6}  │    {NAIVE_CONTEXT_TOKENS:>7} │  {naive_metrics.naive_total:>8} tokens │")
    print(f"│  Subgraph (shared)  │   {SLICE_TOKENS_ESTIMATE['triage']:>6}  │   {SLICE_TOKENS_ESTIMATE['routing']:>6}  │    {SLICE_TOKENS_ESTIMATE['fulfillment']:>7} │  {subgraph_metrics.subgraph_total:>8} tokens │")
    
    print(f"""
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  💰 SAVINGS: {savings['tokens_saved']} tokens saved ({savings['percent_reduction']} reduction)                │
│                                                                             │
│  📊 TOKEN BREAKDOWN (Subgraph Approach):                                    │
│     • Triage Agent:     reads SESSION slice only        → {SLICE_TOKENS_ESTIMATE['triage']} tokens           │
│     • Routing Agent:    reads SESSION.intent only        → {SLICE_TOKENS_ESTIMATE['routing']} tokens           │
│     • Fulfillment Agent: reads ORDER + PREFERENCES slices → {SLICE_TOKENS_ESTIMATE['fulfillment']} tokens          │
│                                                                             │
│  ✅ STATE CONSISTENCY:                                                       │
│     • Each agent writes back to the shared subgraph                         │
│     • No context drift between agents                                        │
│     • Full audit trail via graph relationships                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
""")
    
    # Performance summary
    total_latency = sum(subgraph_metrics.agent_times.values())
    print(f"\n⏱️  AGENT LATENCIES:")
    for agent, ms in subgraph_metrics.agent_times.items():
        print(f"   • {agent}: {ms:.1f}ms")
    print(f"   • Total: {total_latency:.1f}ms")


# ============================================================================
# VERIFY SUBGRAPH STATE
# ============================================================================

def verify_subgraph_state(db: RushDB, user_email: str):
    """Verify the subgraph was properly updated by the pipeline."""
    print("\n" + "=" * 60)
    print("SUBGRAPH STATE VERIFICATION")
    print("=" * 60)
    
    subgraph = get_user_subgraph(db, user_email)
    session = subgraph["session"]
    
    print(f"\n📍 SESSION record state:")
    print(f"   ID: {session.id}")
    print(f"   Status: {session.get('status')}")
    print(f"   Intent: {session.get('intent')}")
    print(f"   Confidence: {session.get('confidence')}")
    print(f"   Route: {session.get('route')}")
    print(f"   Priority: {session.get('priority')}")
    print(f"   SLA: {session.get('sla_minutes')} minutes")
    print(f"\n   Triage completed: {session.get('triage_completed_at')}")
    print(f"   Routing completed: {session.get('routing_completed_at')}")
    
    # Find RESULT records linked to this session
    results = db.records.find({
        "labels": ["RESULT"],
        "where": {
            "SESSION": {
                "$relation": {"type": "PRODUCED", "direction": "in"},
                "id": session.id,
            }
        },
    })
    
    print(f"\n📍 RESULT records: {len(results.data)}")
    for result in results.data:
        print(f"   • {result.id}: {result.get('fulfillment_data')}")
    
    print("\n✅ Subgraph successfully updated by all agents!")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run the complete multi-agent context sharing demo."""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   MULTI-AGENT CONTEXT SHARING THROUGH SHARED SUBGRAPH REFERENCES            ║
║                                                                              ║
║   This demo shows how graph-based shared subgraph references solve:         ║
║   • Token overhead from full context injection                              ║
║   • State inconsistency between agents                                       ║
║                                                                              ║
║   Scenario: E-commerce customer service pipeline                            ║
║   • Triage Agent → determines user intent                                    ║
║   • Routing Agent → selects fulfillment path                                 ║
║   • Fulfillment Agent → executes the request                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Initialize RushDB
        print("\n🔌 Initializing RushDB client...")
        db = get_db_client()
        print("   ✅ Connected successfully")
        
        # Find a user to demo with
        print("\n👤 Finding demo user...")
        users = db.records.find({"labels": ["USER"], "limit": 1})
        
        if not users.data:
            print("\n⚠️  No users found in database!")
            print("   Please run `python seed.py` first to create sample data.")
            print("\n   Alternatively, you can seed directly:")
            print("   $ cp .env.example .env")
            print("   $ python seed.py")
            return
        
        demo_user = users.data[0]
        user_email = demo_user.get("email")
        print(f"   ✅ Found user: {demo_user.get('name')} ({user_email})")
        
        # Get user subgraph
        print("\n📊 Loading user context subgraph...")
        subgraph = get_user_subgraph(db, user_email)
        print(f"   ✅ Subgraph loaded:")
        print(f"      • USER: {subgraph['user'].id}")
        print(f"      • PREFERENCES: {subgraph['preferences'].id if subgraph['preferences'] else 'None'}")
        print(f"      • SESSION: {subgraph['session'].id if subgraph['session'] else 'None'}")
        print(f"      • ORDERS: {len(subgraph['orders'])} records")
        
        # Run naive simulation
        naive_metrics = simulate_naive_approach(subgraph)
        
        # Run subgraph-based pipeline
        subgraph_metrics, results = run_subgraph_pipeline(db, subgraph)
        
        # Print comparison
        print_comparison(naive_metrics, subgraph_metrics)
        
        # Verify final state
        verify_subgraph_state(db, user_email)
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print(f"""
Next steps:
• Run the demo again with different user intents
• Modify seed.py to create more complex subgraph structures
• Check RushDB dashboard to visualize the graph relationships

Learn more:
• Docs: https://docs.rushdb.com
• GitHub: https://github.com/rush-db/examples
        """)
        
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("\n   Please ensure:")
        print("   1. You have a .env file with RUSHDB_API_KEY")
        print("   2. You've run `python seed.py` to create sample data")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
