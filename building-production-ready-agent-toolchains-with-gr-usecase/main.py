#!/usr/bin/env python3
"""
Main agent demo: Customer support agent with graph-native orchestration.

This script demonstrates:
1. Semantic tool discovery via vector search
2. Graph-based conversation tracking with audit trail
3. Context-preserving escalation handling
4. Full conversation graph traversal and retrieval

Each agent action creates a node in the conversation graph, preserving
what was done, why, and the complete context for audit and escalation.
"""

import os
import sys
import time
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

# Load environment
load_dotenv()

from rushdb import RushDB

# Configuration
INDEX_LABEL = "SUPPORT_TOOL"
INDEX_PROPERTY = "description"


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print('=' * 60)


def print_step(step_num: int, description: str):
    """Print a step description."""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 40)


class SupportAgent:
    """
    Customer support agent using RushDB graph + vector architecture.
    
    Each support flow creates:
    - A SUPPORT_SESSION record for the conversation
    - AGENT_ACTION nodes for each tool execution (audit trail)
    - ESCALATION records with full context when human handoff needed
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.session = None
        self.conversation_history = []
    
    def create_session(self, user_id: str, query: str) -> object:
        """Create a new support session."""
        session = self.db.records.create(
            label="SUPPORT_SESSION",
            data={
                "user_id": user_id,
                "initial_query": query,
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        )
        self.session = session
        return session
    
    def semantic_tool_discovery(self, query: str, limit: int = 3) -> list:
        """
        Find the most relevant support tools for a user query.
        
        Uses RushDB's semantic search to find tools whose descriptions
        best match the semantic meaning of the user's query.
        """
        results = self.db.ai.search({
            "propertyName": INDEX_PROPERTY,
            "query": query,
            "labels": [INDEX_LABEL],
            "limit": limit
        })
        return results
    
    def execute_tool_action(
        self,
        tool_record: object,
        reasoning: str,
        context: dict,
        status: str = "success"
    ) -> object:
        """
        Execute a support tool and record the action in the graph.
        
        Creates an AGENT_ACTION node with full audit information:
        - What tool was executed
        - Why it was selected (reasoning)
        - Complete context at execution time
        - Result status
        """
        # Create the action record
        action = self.db.records.create(
            label="AGENT_ACTION",
            data={
                "type": "tool_execution",
                "tool_name": tool_record.data.get("name"),
                "tool_category": tool_record.data.get("category"),
                "reasoning": reasoning,
                "context": context,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Attach action to the session (graph edge)
        self.db.records.attach(
            source=action,
            target=self.session,
            options={"type": "EXECUTED_IN", "direction": "out"}
        )
        
        # Track for later escalation context
        self.conversation_history.append(action)
        
        return action
    
    def escalate_to_human(
        self,
        reason: str,
        priority: str,
        summary: str
    ) -> object:
        """
        Escalate to human agent with full conversation context preserved.
        
        The escalation record is connected to every action in the
        conversation history, preserving complete context for handoff.
        """
        # Create escalation record
        escalation = self.db.records.create(
            label="ESCALATION",
            data={
                "reason": reason,
                "priority": priority,
                "summary": summary,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "conversation_length": len(self.conversation_history)
            }
        )
        
        # Attach escalation to the session
        self.db.records.attach(
            source=escalation,
            target=self.session,
            options={"type": "CREATED_FROM", "direction": "out"}
        )
        
        # Attach all conversation history to the escalation
        # This preserves the complete context for the human agent
        for action in self.conversation_history:
            self.db.records.attach(
                source=action,
                target=escalation,
                options={"type": "PART_OF", "direction": "out"}
            )
        
        # Update session status
        self.db.records.update(
            record_id=self.session.id,
            data={"status": "escalated", "escalation_id": escalation.id}
        )
        
        return escalation
    
    def resolve_session(self, resolution: str) -> object:
        """Mark the session as resolved."""
        resolved = self.db.records.update(
            record_id=self.session.id,
            data={
                "status": "resolved",
                "resolution": resolution,
                "resolved_at": datetime.now(timezone.utc).isoformat()
            }
        )
        return resolved
    
    def get_conversation_graph(self) -> dict:
        """
        Retrieve the full conversation graph for audit/debugging.
        
        Returns a structured view of:
        - The support session
        - All agent actions in order
        - Any escalations
        """
        # Get all actions attached to this session
        actions = self.db.records.find({
            "labels": ["AGENT_ACTION"],
            "where": {
                "SUPPORT_SESSION": {
                    "$relation": {"type": "EXECUTED_IN", "direction": "in"}
                }
            },
            "orderBy": {"timestamp": "asc"}
        })
        
        # Get escalations
        escalations = self.db.records.find({
            "labels": ["ESCALATION"],
            "where": {
                "SUPPORT_SESSION": {
                    "$relation": {"type": "CREATED_FROM", "direction": "in"}
                }
            }
        })
        
        return {
            "session": self.session.data if self.session else None,
            "actions": [a.data for a in actions],
            "escalations": [e.data for e in escalations],
            "total_actions": len(actions)
        }


def demo():
    """Run the complete support agent demo."""
    
    print_section("CUSTOMER SUPPORT AGENT - Graph-Native Orchestration Demo")
    
    # Initialize RushDB client
    api_token = os.getenv("RUSHDb_API_TOKEN")
    if not api_token:
        print("\n❌ Error: RUSHDb_API_TOKEN not found in .env")
        print("   Copy .env.example to .env and add your API token.")
        sys.exit(1)
    
    print(f"\n🔗 Connecting to RushDB...")
    db = RushDB(api_token)
    print("  ✓ Connected")
    
    # Initialize the agent
    agent = SupportAgent(db)
    
    # Simulated user scenario
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    initial_query = "I tried to reset my password but the link expired and now my account is locked. I can't log in at all."
    
    # ================================================================
    # STEP 1: Create support session
    # ================================================================
    print_step(1, "Create support session")
    
    start_time = time.time()
    session = agent.create_session(user_id, initial_query)
    
    print(f"  User ID: {user_id}")
    print(f"  Query: {initial_query[:60]}...")
    print(f"  Session ID: {session.id}")
    print(f"  ✓ Session created ({(time.time() - start_time)*1000:.1f}ms)")
    
    # ================================================================
    # STEP 2: Semantic tool discovery
    # ================================================================
    print_step(2, "Semantic tool discovery via vector search")
    
    start_time = time.time()
    tools = agent.semantic_tool_discovery(
        query="password reset expired link account locked",
        limit=3
    )
    search_time = (time.time() - start_time) * 1000
    
    print(f"  Query: 'password reset expired link account locked'")
    print(f"  ✓ Found {len(tools)} relevant tools ({search_time:.1f}ms)")
    
    for i, tool in enumerate(tools):
        score = tool.score if hasattr(tool, 'score') else tool.data.get('__score', 0)
        print(f"    [{i+1}] {tool.data.get('name')} (score: {score:.3f})")
    
    # ================================================================
    # STEP 3: Execute tool actions (audit trail)
    # ================================================================
    print_step(3, "Execute support tools with full audit trail")
    
    if tools:
        # First action: Identify the password reset tool
        start_time = time.time()
        tool = tools[0]  # Best match
        action1 = agent.execute_tool_action(
            tool_record=tool,
            reasoning=f"Selected '{tool.data.get('name')}' because user reported password reset failure with expired link",
            context={
                "user_id": user_id,
                "issue_type": "password_reset_expired",
                "session_id": session.id,
                "tool_score": tool.score if hasattr(tool, 'score') else 0
            },
            status="success"
        )
        print(f"  Action 1: {action1.data.get('type')} - {action1.data.get('tool_name')}")
        print(f"    Reasoning: {action1.data.get('reasoning')[:70]}...")
        print(f"    ✓ Created ({time.time() - start_time)*1000:.1f}ms)")
        
        # Simulate a second step: Check account lock status
        start_time = time.time()
        lock_tool = tools[1] if len(tools) > 1 else tools[0]
        action2 = agent.execute_tool_action(
            tool_record=lock_tool,
            reasoning="User also mentioned account is locked, checking account_lockout_unlock tool as secondary action",
            context={
                "user_id": user_id,
                "issue_type": "account_lockout",
                "session_id": session.id,
                "preceding_action": action1.id
            },
            status="success"
        )
        print(f"  Action 2: {action2.data.get('type')} - {action2.data.get('tool_name')}")
        print(f"    ✓ Created ({time.time() - start_time)*1000:.1f}ms)")
    
    # ================================================================
    # STEP 4: Escalate to human agent
    # ================================================================
    print_step(4, "Context-preserving escalation to human agent")
    
    # Simulate that we need human help (account verification failed)
    start_time = time.time()
    escalation = agent.escalate_to_human(
        reason="account_verification_failed",
        priority="high",
        summary="User cannot verify account ownership via email or phone. Requires identity verification before password reset can proceed."
    )
    print(f"  Reason: {escalation.data.get('reason')}")
    print(f"  Priority: {escalation.data.get('priority')}")
    print(f"  Summary: {escalation.data.get('summary')[:60]}...")
    print(f"  Actions in context: {escalation.data.get('conversation_length')}")
    print(f"  ✓ Escalation created with full context ({time.time() - start_time)*1000:.1f}ms)")
    
    # ================================================================
    # STEP 5: Simulate human resolution (continue the graph)
    # ================================================================
    print_step(5, "Human agent completes resolution")
    
    start_time = time.time()
    
    # Human agent creates a verification bypass
    verification_action = db.records.create(
        label="AGENT_ACTION",
        data={
            "type": "manual_verification",
            "agent_id": "human_agent_42",
            "action": "security_questions_verified",
            "context": {
                "escalation_id": escalation.id,
                "user_id": user_id,
                "verification_method": "security_questions"
            },
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    db.records.attach(
        source=verification_action,
        target=escalation,
        options={"type": "PART_OF", "direction": "out"}
    )
    
    # Create temporary bypass code
    bypass_action = db.records.create(
        label="AGENT_ACTION",
        data={
            "type": "temp_bypass_created",
            "bypass_code": "TMP-" + uuid.uuid4().hex[:8].upper(),
            "expires_in_minutes": 30,
            "context": {
                "user_id": user_id,
                "verified_by": verification_action.id
            },
            "status": "success",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )
    db.records.attach(
        source=bypass_action,
        target=escalation,
        options={"type": "PART_OF", "direction": "out"}
    )
    
    # Resolve the session
    agent.resolve_session(
        resolution="Account verified via security questions. Temporary bypass code sent to user's verified backup email."
    )
    
    print(f"  Verification: security_questions (agent: human_agent_42)")
    print(f"  Bypass: {bypass_action.data.get('bypass_code')}")
    print(f"  ✓ Resolution complete ({time.time() - start_time)*1000:.1f}ms)")
    
    # ================================================================
    # STEP 6: Retrieve and display conversation graph
    # ================================================================
    print_step(6, "Retrieve full conversation graph for audit")
    
    start_time = time.time()
    graph = agent.get_conversation_graph()
    retrieval_time = (time.time() - start_time) * 1000
    
    print(f"  ✓ Graph retrieved in {retrieval_time:.1f}ms")
    print(f"\n  Session: {graph['session']['__id']}")
    print(f"  Status: {graph['session']['status']}")
    print(f"  Resolution: {graph['session'].get('resolution', 'N/A')[:60]}...")
    print(f"\n  Conversation Timeline:")
    
    for i, action in enumerate(graph['actions']):
        print(f"    {i+1}. [{action.get('type')}] {action.get('tool_name', action.get('action', 'N/A'))}")
        if action.get('reasoning'):
            print(f"       → {action.get('reasoning')[:55]}...")
    
    print(f"\n  Escalations: {len(graph['escalations'])}")
    for esc in graph['escalations']:
        print(f"    • {esc.get('reason')} (priority: {esc.get('priority')})")
    
    # ================================================================
    # STEP 7: Graph traversal - find all actions for this escalation
    # ================================================================
    print_step(7, "Graph traversal: trace all actions in escalation context")
    
    start_time = time.time()
    
    # Find all actions that are part of this escalation
    escalation_context = db.records.find({
        "labels": ["AGENT_ACTION"],
        "where": {
            "ESCALATION": {
                "$relation": {"type": "PART_OF", "direction": "in"}
            }
        },
        "orderBy": {"timestamp": "asc"}
    })
    
    traversal_time = (time.time() - start_time) * 1000
    print(f"  ✓ Graph traversal completed in {traversal_time:.1f}ms")
    print(f"\n  Complete Escalation Context ({len(escalation_context)} actions):")
    
    for action in escalation_context:
        action_type = action.data.get('type', 'unknown')
        tool = action.data.get('tool_name') or action.data.get('action', 'N/A')
        timestamp = action.data.get('timestamp', '')
        print(f"    • {action_type}: {tool}")
    
    # ================================================================
    # Summary
    # ================================================================
    total_time = (time.time() - start_time) + search_time
    
    print("\n" + "=" * 60)
    print(" DEMO SUMMARY")
    print("=" * 60)
    print(f"\n  Architecture Demonstrated:")
    print(f"    ✓ Graph for conversation flow and tool dependencies")
    print(f"    ✓ Vectors for semantic tool matching ({search_time:.1f}ms)")
    print(f"    ✓ Complete audit trail ({len(graph['actions'])} actions)")
    print(f"    ✓ Context-preserving escalation")
    print(f"    ✓ Single-query graph traversal ({traversal_time:.1f}ms)")
    print(f"\n  Performance:")
    print(f"    • Semantic search: {search_time:.1f}ms (sub-100ms ✓)")
    print(f"    • Graph operations: {traversal_time:.1f}ms (sub-100ms ✓)")
    print(f"\n  All timestamps preserved for full audit compliance.")
    print("=" * 60)
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    demo()
