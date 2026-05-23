#!/usr/bin/env python3
"""
Dynamic Personality Injection via Graph-Edge Personality Traits

This tutorial demonstrates how to use RushDB's property graph model
to implement dynamic, context-aware personality injection for AI agents.

Key concepts:
1. Agents, Traits, and Contexts as first-class records
2. Relationships as personality carriers (HAS_TRAIT, REQUIRES, BOOSTS)
3. Graph traversal for personality queries
4. Contextual trait weight adjustment
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

API_TOKEN = os.getenv("RUSHDB_API_TOKEN")
if not API_TOKEN:
    raise ValueError("RUSHDB_API_TOKEN not found in environment. Copy .env.example to .env and add your token.")

db = RushDB(API_TOKEN)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_agent_by_name(name: str):
    """Find an agent record by name."""
    results = db.records.find({
        "labels": ["AGENT"],
        "where": {"name": name}
    })
    return results[0] if results else None


def get_context_by_name(name: str):
    """Find a context record by name."""
    results = db.records.find({
        "labels": ["CONTEXT"],
        "where": {"name": name}
    })
    return results[0] if results else None


def get_trait_by_name(name: str):
    """Find a personality trait record by name."""
    results = db.records.find({
        "labels": ["PERSONALITY_TRAIT"],
        "where": {"name": name}
    })
    return results[0] if results else None


def get_agent_base_traits(agent_id: str):
    """
    Get an agent's base personality traits via graph traversal.
    
    This queries the graph to find all PERSONALITY_TRAIT records
    connected to the agent via a HAS_TRAIT relationship.
    """
    # Find trait weight records linked to this agent
    weight_records = db.records.find({
        "labels": ["TRAIT_WEIGHT"],
        "where": {
            "AGENT": {"$id": {"$in": [agent_id]}, "$relation": {"type": "TRAIT_LINK", "direction": "in"}},
            "context": "base"
        }
    })
    
    traits = []
    for wr in weight_records:
        trait_name = wr.data["trait_name"]
        trait_record = get_trait_by_name(trait_name)
        if trait_record:
            traits.append({
                "name": trait_name,
                "description": trait_record.data["description"],
                "weight": wr.data["weight"],
                "source": "base"
            })
    
    return sorted(traits, key=lambda x: x["weight"], reverse=True)


def get_context_required_traits(context_name: str):
    """
    Get traits required by a context, including boost factors.
    
    Traverses CONTEXT --[REQUIRES]--> PERSONALITY_TRAIT
    and CONTEXT --[BOOSTS]--> CONTEXT_BOOST
    """
    context = get_context_by_name(context_name)
    if not context:
        return []
    
    # Find required traits via REQUIRES relationships
    trait_weights = db.records.find({
        "labels": ["CONTEXT_BOOST"],
        "where": {
            "context_name": context_name
        }
    })
    
    traits = []
    for tw in trait_weights:
        trait_record = get_trait_by_name(tw.data["trait_name"])
        if trait_record:
            traits.append({
                "name": tw.data["trait_name"],
                "description": trait_record.data["description"],
                "boost_factor": tw.data["boost_factor"],
                "source": "context_boost"
            })
    
    return traits


def get_context_personality(agent, context_name: str):
    """
    Calculate an agent's effective personality in a given context.
    
    This is the core "personality injection" logic:
    1. Get agent's base traits
    2. Get context's required/boosted traits
    3. Merge and adjust weights based on context boosts
    """
    base_traits = get_agent_base_traits(agent.id)
    context_boosts = get_context_required_traits(context_name)
    
    # Build personality profile
    personality = {}
    
    # Apply base traits
    for trait in base_traits:
        personality[trait["name"]] = {
            "description": trait["description"],
            "weight": trait["weight"],
            "source": "base",
            "boosted": False
        }
    
    # Apply context boosts
    for boost in context_boosts:
        trait_name = boost["name"]
        boost_factor = boost["boost_factor"]
        
        if trait_name in personality:
            # Boost existing trait
            old_weight = personality[trait_name]["weight"]
            new_weight = round(old_weight * boost_factor, 2)
            personality[trait_name]["weight"] = new_weight
            personality[trait_name]["boosted"] = True
            personality[trait_name]["boost_factor"] = boost_factor
        else:
            # Add new trait from context
            base_weight = 0.5
            personality[trait_name] = {
                "description": boost["description"],
                "weight": round(base_weight * boost_factor, 2),
                "source": "context",
                "boosted": True,
                "boost_factor": boost_factor
            }
    
    return personality


def format_personality_display(personality: dict):
    """Format personality dictionary for display."""
    lines = []
    for name, data in sorted(personality.items(), key=lambda x: x[1]["weight"], reverse=True):
        weight = data["weight"]
        boosted = "" if not data["boosted"] else f" (boosted: {data['boost_factor']:.2f})"
        lines.append(f"  • {name}: {weight}{boosted}")
    return "\n".join(lines) if lines else "  (no traits)"


def build_system_prompt(agent, context_name: str, personality: dict):
    """
    Build a system prompt by injecting personality traits.
    
    This demonstrates how the graph traversal results
    can be used to construct a dynamic system prompt.
    """
    # Sort traits by weight
    sorted_traits = sorted(personality.items(), key=lambda x: x[1]["weight"], reverse=True)
    
    trait_lines = []
    for name, data in sorted_traits:
        trait_lines.append(f"    - {name}: {data['description']} (weight: {data['weight']})")
    
    prompt = f"""You are {agent.data['name']}. {agent.data['description']}

Your current personality traits (for {context_name} context):
{chr(10).join(trait_lines)}

Use these traits to guide your responses. Higher weight traits should influence your communication style more strongly."""
    
    return prompt


# ============================================================================
# DEMONSTRATION FUNCTIONS
# ============================================================================

def demo_base_personality():
    """Show an agent's base personality traits."""
    print("\n[1] Base personality for SupportBot:")
    
    agent = get_agent_by_name("SupportBot")
    if not agent:
        print("  (Agent not found - run seed.py first)")
        return
    
    base_traits = get_agent_base_traits(agent.id)
    
    for trait in base_traits:
        print(f"  • {trait['name']}: {trait['weight']}")


def demo_context_aware_personality():
    """Show how context modifies personality."""
    print("\n[2] Context-aware personality injection:")
    
    agent = get_agent_by_name("SupportBot")
    if not agent:
        print("  (Agent not found - run seed.py first)")
        return
    
    contexts_to_show = ["customer_support", "technical_debugging"]
    
    for ctx_name in contexts_to_show:
        personality = get_context_personality(agent, ctx_name)
        print(f"\n  Context: {ctx_name}")
        print(f"  Active traits:")
        print(format_personality_display(personality))


def demo_graph_traversal_query():
    """Demonstrate direct graph traversal for personality queries."""
    print("\n[3] Traversal query - All traits for SupportBot in customer_support:")
    
    agent = get_agent_by_name("SupportBot")
    context = get_context_by_name("customer_support")
    
    if not agent or not context:
        print("  (Records not found - run seed.py first)")
        return
    
    # Direct graph traversal: find traits via agent's context relationships
    # First, find all traits connected to the agent via HAS_TRAIT
    all_traits = db.records.find({
        "labels": ["PERSONALITY_TRAIT"],
        "where": {
            "AGENT": {"$id": {"$in": [agent.id]}, "$relation": {"type": "HAS_TRAIT", "direction": "in"}}
        }
    })
    
    # Filter to only those required by the context
    context_boosts = db.records.find({
        "labels": ["CONTEXT_BOOST"],
        "where": {"context_name": context.data["name"]}
    })
    required_trait_names = {cb.data["trait_name"] for cb in context_boosts}
    
    matched_traits = [t for t in all_traits if t.data["name"] in required_trait_names]
    
    print(f"  Found {len(matched_traits)} traits via graph traversal")
    for trait in matched_traits[:5]:
        print(f"  - {trait.data['name']} ({trait.data['description'][:40]}...)")


def demo_dynamic_trait_switching():
    """Show how personality changes when switching contexts."""
    print("\n[4] Dynamic trait switching:")
    
    agent = get_agent_by_name("SupportBot")
    if not agent:
        print("  (Agent not found - run seed.py first)")
        return
    
    print("  Switching SupportBot from customer_support to conflict_resolution...")
    
    old_context = "customer_support"
    new_context = "conflict_resolution"
    
    old_personality = get_context_personality(agent, old_context)
    new_personality = get_context_personality(agent, new_context)
    
    print(f"\n  Previous context ({old_context}) traits:")
    print(format_personality_display(old_personality))
    
    print(f"\n  New context ({new_context}) traits:")
    print(format_personality_display(new_personality))
    
    # Show key differences
    print("\n  Key changes:")
    for trait_name in new_personality:
        if trait_name in old_personality:
            old_w = old_personality[trait_name]["weight"]
            new_w = new_personality[trait_name]["weight"]
            change = ((new_w - old_w) / old_w) * 100
            direction = "↑" if change > 0 else "↓" if change < 0 else "→"
            print(f"    {trait_name}: {old_w} → {new_w} ({direction}{abs(change):.1f}%)")


def demo_cross_context_comparison():
    """Compare an agent's personality across different contexts."""
    print("\n[5] Cross-context trait comparison:")
    
    agent = get_agent_by_name("CreativeMuse")
    if not agent:
        print("  (Agent not found - run seed.py first)")
        return
    
    contexts = ["creative_writing", "onboarding", "technical_debugging"]
    
    print(f"\n  CreativeMuse comparison across contexts:")
    print("  " + "-" * 60)
    
    for ctx_name in contexts:
        personality = get_context_personality(agent, ctx_name)
        trait_names = sorted(personality.keys(), key=lambda x: personality[x]["weight"], reverse=True)
        print(f"  │ {ctx_name:<20} │ {', '.join(trait_names[:4]):<40} │")
    
    print("  " + "-" * 60)


def demo_system_prompt_generation():
    """Show how personality injection builds a system prompt."""
    print("\n[6] System prompt generation from personality injection:")
    
    agent = get_agent_by_name("SupportBot")
    if not agent:
        print("  (Agent not found - run seed.py first)")
        return
    
    context_name = "conflict_resolution"
    personality = get_context_personality(agent, context_name)
    
    prompt = build_system_prompt(agent, context_name, personality)
    
    print(f"\n  Generated system prompt for '{context_name}' context:")
    print("  " + "-" * 60)
    # Pretty print with indentation
    for line in prompt.split('\n'):
        print(f"  {line}")
    print("  " + "-" * 60)


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("Dynamic Personality Injection via Graph-Edge Personality Traits")
    print("=" * 60)
    
    # Check if data exists
    agents = db.records.find({"labels": ["AGENT"], "where": {}})
    if not agents:
        print("\n⚠ No data found. Please run 'python seed.py' first to populate the database.\n")
        return
    
    print(f"\n✓ Found {len(agents)} agents in the database.")
    
    # Run demonstrations
    demo_base_personality()
    demo_context_aware_personality()
    demo_graph_traversal_query()
    demo_dynamic_trait_switching()
    demo_cross_context_comparison()
    demo_system_prompt_generation()
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
    print("""
Key takeaways:

1. **Records as first-class entities**: Agents, traits, and contexts are 
   all RushDB records with unique IDs and properties.

2. **Relationships carry personality**: The HAS_TRAIT, REQUIRES, and BOOSTS
   relationships encode how traits attach to agents and how contexts modify them.

3. **Graph traversal enables dynamic queries**: By traversing the graph,
   we can build context-aware personality profiles without hardcoding rules.

4. **Contextual weight adjustment**: The same agent has different effective
   personalities depending on which context they're operating in.

5. **System prompt injection**: Personality profiles can be converted into
   structured system prompts for AI models.
""")


if __name__ == "__main__":
    main()
