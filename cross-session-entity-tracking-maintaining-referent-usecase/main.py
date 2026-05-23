#!/usr/bin/env python3
"""
Cross-Session Entity Tracking Demo

Demonstrates RushDB's capabilities for maintaining referential integrity
across multi-turn AI conversations.

The scenario: A customer support chatbot that tracks products across
multiple chat sessions, using both graph relationships and vector
similarity for entity resolution.
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

API_TOKEN = os.getenv("RUSHDB_API_TOKEN")
if not API_TOKEN:
    print("ERROR: RUSHDB_API_TOKEN not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

# ============================================================================
# Entity Resolution Engine
# ============================================================================

class EntityResolver:
    """
    Resolves ambiguous entity references using a multi-strategy approach:
    1. Exact match (by ID or unique identifier)
    2. Recent context (check recent session history)
    3. Semantic search (vector similarity as fallback)
    """
    
    def __init__(self, db):
        self.db = db
        
    def resolve(self, user_utterance: str, session_id: str = None) -> dict:
        """
        Resolve an entity reference from user input.
        
        Returns a dict with:
        - entity: the resolved Product record (or None)
        - strategy: how resolution happened
        - confidence: 0.0 to 1.0
        """
        # Strategy 1: Check recent session history
        if session_id:
            resolved = self._resolve_via_history(session_id)
            if resolved:
                return resolved
        
        # Strategy 2: Semantic search fallback
        resolved = self._resolve_via_semantics(user_utterance)
        return resolved
    
    def _resolve_via_history(self, session_id: str):
        """Check if this session continues a previous one."""
        # Find the current session
        sessions = self.db.records.find({
            "labels": ["SESSION"],
            "where": {"__id": session_id}
        })
        
        if not sessions:
            return None
        
        session = sessions[0]
        
        # Find sessions this one continues
        prev_sessions = self.db.records.find({
            "labels": ["SESSION"],
            "where": {
                "SESSION": {
                    "$relation": {"type": "CONTINUES", "direction": "in"},
                    "__id": session_id
                }
            }
        })
        
        if not prev_sessions:
            prev_sessions = self.db.records.find({
                "labels": ["SESSION"],
                "where": {
                    "user_id": session.get("user_id")
                },
                "orderBy": {"started_at": "desc"},
                "limit": 1
            })
        
        if not prev_sessions:
            return None
        
        # Find messages in the previous session that refer to products
        messages = self.db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "SESSION": {"$id": prev_sessions[0].id},
                "PRODUCT": {"$exists": True}
            },
            "limit": 5
        })
        
        for msg in messages:
            # Check if message has a direct product reference
            refs = self.db.records.find({
                "labels": ["ENTITY_REFERENCE"],
                "where": {
                    "MESSAGE": {"$id": msg.id},
                    "RESOLVED_TO": {"$exists": True}
                }
            })
            
            for ref in refs:
                resolved = self.db.records.find({
                    "labels": ["PRODUCT"],
                    "where": {
                        "ENTITY_REFERENCE": {"$id": ref.id}
                    }
                })
                
                if resolved:
                    return {
                        "entity": resolved[0],
                        "strategy": "session_history",
                        "confidence": 0.95,
                        "note": f"Found reference from {prev_sessions[0].data.get('started_at', 'earlier session')}"
                    }
        
        return None
    
    def _resolve_via_semantics(self, query: str):
        """Use vector similarity to find matching products."""
        results = self.db.ai.search({
            "propertyName": "description",
            "query": query,
            "labels": ["PRODUCT"],
            "limit": 3
        })
        
        if results and len(results) > 0:
            top = results[0]
            return {
                "entity": top,
                "strategy": "semantic_search",
                "confidence": top.score or 0.8,
                "note": f"Matched via description similarity"
            }
        
        return {
            "entity": None,
            "strategy": "none",
            "confidence": 0.0,
            "note": "No matching product found"
        }


# ============================================================================
# Context Injector
# ============================================================================

class ContextInjector:
    """
    Retrieves full entity subgraph for context-aware response generation.
    Gathers product details, related messages, and session history.
    """
    
    def __init__(self, db):
        self.db = db
    
    def get_product_context(self, product, session=None) -> dict:
        """
        Build a comprehensive context object for a product.
        Includes all relevant data for generating informed responses.
        """
        context = {
            "product": product.data,
            "related_messages": [],
            "session_history": [],
            "entity_state": {}
        }
        
        # Find all messages about this product
        messages = self.db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "PRODUCT": {"$id": product.id}
            },
            "orderBy": {"timestamp": "desc"},
            "limit": 5
        })
        context["related_messages"] = [m.data for m in messages]
        
        # Find all sessions that discussed this product
        sessions = self.db.records.find({
            "labels": ["SESSION"],
            "where": {
                "MESSAGE": {
                    "PRODUCT": {"$id": product.id}
                }
            },
            "limit": 10
        })
        context["session_history"] = [s.data for s in sessions]
        
        # Get current stock state
        context["entity_state"] = {
            "in_stock": product.get("stock", 0) > 0,
            "stock_count": product.get("stock", 0),
            "warranty_months": product.get("warranty_months", 0),
            "last_updated": datetime.now().isoformat()
        }
        
        return context
    
    def format_context_for_prompt(self, context: dict) -> str:
        """Format context as a readable string for prompt injection."""
        lines = ["\n[Context]"]
        
        p = context["product"]
        lines.append(f"Product: {p.get('name')} by {p.get('brand')}")
        lines.append(f"Price: ${p.get('price', 0):.2f}")
        lines.append(f"SKU: {p.get('sku')}")
        lines.append(f"Stock: {context['entity_state']['stock_count']} units")
        lines.append(f"Warranty: {p.get('warranty_months')} months")
        
        if p.get("specs"):
            lines.append("Specifications:")
            for key, val in p["specs"].items():
                lines.append(f"  - {key}: {val}")
        
        if context["related_messages"]:
            lines.append(f"\nPrevious mentions: {len(context['related_messages'])} message(s)")
        
        lines.append("[/Context]")
        return "\n".join(lines)


# ============================================================================
# Session Bridge Manager
# ============================================================================

class SessionBridge:
    """
    Manages connections between conversation turns and established entity graphs.
    Handles session continuity and entity state updates.
    """
    
    def __init__(self, db):
        self.db = db
    
    def start_session(self, user_id: str, channel: str = "api") -> dict:
        """Start a new conversation session."""
        session = self.db.records.create(
            label="SESSION",
            data={
                "user_id": user_id,
                "started_at": datetime.now().isoformat() + "Z",
                "channel": channel,
                "status": "active"
            }
        )
        
        # Find and link to most recent session for same user
        previous = self.db.records.find({
            "labels": ["SESSION"],
            "where": {
                "user_id": user_id,
                "status": "closed"
            },
            "orderBy": {"started_at": "desc"},
            "limit": 1
        })
        
        if previous:
            self.db.records.attach(
                source=session,
                target=previous[0],
                options={"type": "CONTINUES"}
            )
            session.data["_linked_to_previous"] = previous[0].id
        
        return session
    
    def add_message(self, session, role: str, content: str) -> dict:
        """Add a message to the session with timestamp."""
        message = self.db.records.create(
            label="MESSAGE",
            data={
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        )
        
        self.db.records.attach(
            source=message,
            target=session,
            options={"type": "BELONGS_TO"}
        )
        
        return message
    
    def link_entity_reference(self, message, entity, raw_text: str, 
                              strategy: str, confidence: float):
        """Create a formal entity reference linking message to entity."""
        reference = self.db.records.create(
            label="ENTITY_REFERENCE",
            data={
                "raw_text": raw_text,
                "resolution_strategy": strategy,
                "confidence": confidence,
                "created_at": datetime.now().isoformat() + "Z"
            }
        )
        
        self.db.records.attach(
            source=reference,
            target=message,
            options={"type": "TRACKS"}
        )
        
        self.db.records.attach(
            source=message,
            target=entity,
            options={"type": "REFERS_TO"}
        )
        
        self.db.records.attach(
            source=reference,
            target=entity,
            options={"type": "RESOLVED_TO"}
        )
        
        # Update session to mention this entity
        session = self.db.records.find({
            "labels": ["SESSION"],
            "where": {
                "MESSAGE": {"$id": message.id}
            }
        })[0]
        
        self.db.records.attach(
            source=session,
            target=entity,
            options={"type": "MENTIONS"}
        )
        
        return reference
    
    def close_session(self, session):
        """Mark session as closed."""
        session.update({"status": "closed", "ended_at": datetime.now().isoformat() + "Z"})


# ============================================================================
# Demo Scenarios
# ============================================================================

def run_demo():
    """Execute the full entity tracking demonstration."""
    
    print("\n" + "=" * 70)
    print("CROSS-SESSION ENTITY TRACKING DEMO")
    print("=" * 70)
    
    # Initialize components
    db = RushDB(API_TOKEN)
    resolver = EntityResolver(db)
    injector = ContextInjector(db)
    bridge = SessionBridge(db)
    
    print("\n✓ All components initialized")
    
    # -------------------------------------------------------------------
    # Demo 1: Fresh semantic search
    # -------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("SCENARIO 1: User mentions product category, system resolves to specific item")
    print("-" * 70)
    
    print("\nUser: 'I need a laptop for video editing'")
    
    result = resolver.resolve("laptop for video editing")
    
    print(f"\n  Resolution strategy: {result['strategy']}")
    print(f"  Confidence: {result['confidence']:.2%}")
    print(f"  {result['note']}")
    
    if result['entity']:
        entity = result['entity']
        print(f"\n  → Resolved to: {entity['name']} (${entity['price']:.2f})")
        print(f"    SKU: {entity['sku']}")
        
        # Show context injection
        context = injector.get_product_context(entity)
        prompt_context = injector.format_context_for_prompt(context)
        print(f"\n  Context for response generation:{prompt_context}")
    
    # -------------------------------------------------------------------
    # Demo 2: Session history resolution
    # -------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("SCENARIO 2: Ambiguous reference resolved via session history")
    print("-" * 70)
    
    # Get the first session
    sessions = db.records.find({
        "labels": ["SESSION"],
        "orderBy": {"started_at": "asc"},
        "limit": 1
    })
    
    if sessions:
        session1 = sessions[0]
        print(f"\nUser: 'Is the laptop I looked at still available?'")
        print(f"  (in session continuing from {session1.data.get('started_at', 'earlier')})")
        
        result = resolver.resolve("the laptop I looked at", session_id=session1.id)
        
        print(f"\n  Resolution strategy: {result['strategy']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  {result['note']}")
        
        if result['entity']:
            entity = result['entity']
            print(f"\n  → Resolved to: {entity['name']}")
            print(f"    Stock: {entity.get('stock', 0)} units")
    
    # -------------------------------------------------------------------
    # Demo 3: Full conversation flow
    # -------------------------------------------------------------------
    print("\n" + "-" * 70)
    print("SCENARIO 3: Complete multi-turn conversation with entity tracking")
    print("-" * 70)
    
    # Start new session
    new_session = bridge.start_session("demo_user", channel="demo")
    print(f"\n[SESSION STARTED: {new_session.id[:16]}...]")
    
    # Turn 1
    msg1 = bridge.add_message(new_session, "user", "Show me your best laptop for development work")
    result1 = resolver.resolve("best laptop for development work")
    
    print(f"\nUser: {msg1.data['content']}")
    if result1['entity']:
        ref1 = bridge.link_entity_reference(
            msg1, result1['entity'], "laptop for development work",
            result1['strategy'], result1['confidence']
        )
        print(f"Assistant: The {result1['entity']['name']} would be great for development!")
        print(f"  (Entity tracked via {result1['strategy']}, confidence: {result1['confidence']:.2%})")
    
    # Turn 2
    msg2 = bridge.add_message(new_session, "user", "What's the warranty on that?")
    result2 = resolver.resolve("that", session_id=new_session.id)
    
    print(f"\nUser: {msg2.data['content']}")
    if result2['entity']:
        ref2 = bridge.link_entity_reference(
            msg2, result2['entity'], "that",
            result2['strategy'], result2['confidence']
        )
        entity = result2['entity']
        print(f"Assistant: The {entity['name']} comes with a {entity.get('warranty_months', 12)}-month warranty.")
        print(f"  (Entity tracked via {result2['strategy']})")
    
    # Turn 3
    msg3 = bridge.add_message(new_session, "user", "And the RAM can be upgraded?")
    result3 = resolver.resolve("that RAM", session_id=new_session.id)
    
    print(f"\nUser: {msg3.data['content']}")
    if result3['entity']:
        print(f"Assistant: The {result3['entity']['name']} has {result3['entity'].get('specs', {}).get('ram', 'N/A')} RAM.")
        print(f"  (Continuing context from same session)")
    
    # Close session
    bridge.close_session(new_session)
    print(f"\n[SESSION CLOSED]")
    
    # -------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("ENTITY TRACKING SUMMARY")
    print("=" * 70)
    
    # Count entities tracked
    all_refs = db.records.find({"labels": ["ENTITY_REFERENCE"], "limit": 100})
    all_products = db.records.find({"labels": ["PRODUCT"]})
    all_sessions = db.records.find({"labels": ["SESSION"]})
    all_messages = db.records.find({"labels": ["MESSAGE"]})
    
    print(f"""
  Records created:
    - Sessions: {len(all_sessions)}
    - Messages: {len(all_messages)}
    - Products: {len(all_products)}
    - Entity References: {len(all_refs)}
  
  Graph structure:
    - Messages linked to Sessions (BELONGS_TO)
    - Messages linked to Products (REFERS_TO)
    - Sessions linked to Sessions (CONTINUES)
    - Entity references track resolution strategy & confidence
  
  Entity resolution strategies demonstrated:
    - Semantic search (vector similarity)
    - Session history (previous mentions)
    - Context continuity (same session)
""")
    
    return {
        "sessions": len(all_sessions),
        "messages": len(all_messages),
        "products": len(all_products),
        "references": len(all_refs)
    }


# ============================================================================
# Main
# ============================================================================

def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("RushDB Cross-Session Entity Tracking Demo")
    print("=" * 70)
    print("\nThis demo shows how RushDB maintains referential integrity")
    print("across multi-turn conversations using graph + vector capabilities.")
    
    # Check that we have data
    db = RushDB(API_TOKEN)
    products = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    
    if not products:
        print("\n⚠ No products found in database.")
        print("Run 'python seed.py' first to set up the demo data.")
        sys.exit(1)
    
    # Run the demo
    try:
        stats = run_demo()
        print("\n" + "=" * 70)
        print("✓ Demo completed successfully!")
        print("=" * 70)
    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
