#!/usr/bin/env python3
"""
Seed script for Dynamic Personality Injection demo.
Creates agents, personality traits, and contexts with their relationships.

Run this once before main.py to populate the database with demo data.
This script is idempotent — safe to run multiple times.
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
# DATA DEFINITIONS
# ============================================================================

# Base personality traits (first-class records)
TRAITS = [
    {"name": "empathetic", "description": "Understands and shares the feelings of others", "weight_range": [0.5, 1.0]},
    {"name": "analytical", "description": "Breaks down complex problems systematically", "weight_range": [0.6, 1.0]},
    {"name": "playful", "description": "Uses humor and light-heartedness appropriately", "weight_range": [0.3, 0.9]},
    {"name": "formal", "description": "Maintains professional tone and structure", "weight_range": [0.4, 0.8]},
    {"name": "creative", "description": "Generates novel and imaginative solutions", "weight_range": [0.5, 1.0]},
    {"name": "patient", "description": "Takes time to ensure understanding", "weight_range": [0.6, 1.0]},
    {"name": "witty", "description": "Responds with clever, appropriate humor", "weight_range": [0.2, 0.8]},
    {"name": "diplomatic", "description": "Navigates sensitive situations gracefully", "weight_range": [0.5, 1.0]},
]

# Contexts (situations that modify behavior)
CONTEXTS = [
    {"name": "customer_support", "domain": "support", "stakes_level": "high"},
    {"name": "technical_debugging", "domain": "engineering", "stakes_level": "medium"},
    {"name": "creative_writing", "domain": "content", "stakes_level": "low"},
    {"name": "onboarding", "domain": "education", "stakes_level": "medium"},
    {"name": "conflict_resolution", "domain": "support", "stakes_level": "critical"},
]

# Agents (AI characters)
AGENTS = [
    {
        "name": "SupportBot",
        "description": "A helpful support assistant focused on customer satisfaction",
        "base_traits": ["empathetic", "patient", "diplomatic"],
    },
    {
        "name": "CodeAssistant",
        "description": "An expert coding assistant that helps debug and architect solutions",
        "base_traits": ["analytical", "patient", "creative"],
    },
    {
        "name": "CreativeMuse",
        "description": "An imaginative assistant that helps with creative writing and brainstorming",
        "base_traits": ["creative", "playful", "empathetic"],
    },
]

# Context-Trait relationships (what traits matter in each context)
CONTEXT_TRAITS = {
    "customer_support": {"requires": ["empathetic", "patient", "diplomatic"], "boosts": {"empathetic": 1.06, "diplomatic": 1.2, "patient": 1.12}},
    "technical_debugging": {"requires": ["analytical", "patient", "witty"], "boosts": {"analytical": 1.15, "patient": 1.05}},
    "creative_writing": {"requires": ["creative", "playful", "empathetic"], "boosts": {"creative": 1.2, "playful": 1.1}},
    "onboarding": {"requires": ["empathetic", "patient", "diplomatic", "playful"], "boosts": {"empathetic": 1.1, "patient": 1.05}},
    "conflict_resolution": {"requires": ["diplomatic", "empathetic", "patient"], "boosts": {"diplomatic": 1.35, "empathetic": 1.1, "patient": 0.85}},
}


def cleanup_existing_data():
    """Remove existing records to ensure clean state."""
    print("Cleaning up existing data...")
    labels_to_clean = ["AGENT", "PERSONALITY_TRAIT", "CONTEXT"]
    for label in labels_to_clean:
        db.records.delete({"labels": [label], "where": {}})
    print("  ✓ Cleaned existing records\n")


def seed_traits():
    """Create personality trait records."""
    print("Creating personality traits...")
    trait_records = []
    for i, trait in enumerate(TRAITS):
        record = db.records.create(
            label="PERSONALITY_TRAIT",
            data={
                "name": trait["name"],
                "description": trait["description"],
                "weight_min": trait["weight_range"][0],
                "weight_max": trait["weight_range"][1],
            }
        )
        trait_records.append(record)
        if (i + 1) % 4 == 0:
            print(f"  ✓ Created {i + 1}/{len(TRAITS)} traits")
    print(f"  ✓ Created {len(TRAITS)} personality traits\n")
    return {t.data["name"]: t for t in trait_records}


def seed_contexts():
    """Create context records."""
    print("Creating contexts...")
    context_records = []
    for context in CONTEXTS:
        record = db.records.create(
            label="CONTEXT",
            data={
                "name": context["name"],
                "domain": context["domain"],
                "stakes_level": context["stakes_level"],
            }
        )
        context_records.append(record)
    print(f"  ✓ Created {len(CONTEXTS)} contexts\n")
    return {c.data["name"]: c for c in context_records}


def seed_agents(trait_map, context_map):
    """Create agent records and attach base traits."""
    print("Creating agents and their trait relationships...")
    agent_records = []
    
    for agent_def in AGENTS:
        # Create agent record
        agent = db.records.create(
            label="AGENT",
            data={
                "name": agent_def["name"],
                "description": agent_def["description"],
            }
        )
        agent_records.append(agent)
        print(f"  ✓ Created agent: {agent.data['name']}")
        
        # Attach base traits with weights
        for i, trait_name in enumerate(agent_def["base_traits"]):
            trait = trait_map[trait_name]
            base_weight = (trait.data["weight_min"] + trait.data["weight_max"]) / 2
            
            db.records.attach(
                source=agent,
                target=trait,
                options={"type": "HAS_TRAIT", "direction": "out"}
            )
            # Store the weight as a property on the relationship
            # We do this by creating a relationship metadata record
            rel_meta = db.records.create(
                label="TRAIT_WEIGHT",
                data={
                    "weight": round(base_weight, 2),
                    "agent_id": agent.id,
                    "trait_name": trait_name,
                    "context": "base",
                }
            )
            db.records.attach(source=agent, target=rel_meta, options={"type": "TRAIT_LINK", "direction": "out"})
        
        # Attach relevant contexts
        agent_contexts = ["customer_support", "technical_debugging", "creative_writing", "onboarding", "conflict_resolution"]
        if agent_def["name"] == "SupportBot":
            agent_contexts = ["customer_support", "onboarding", "conflict_resolution"]
        elif agent_def["name"] == "CodeAssistant":
            agent_contexts = ["technical_debugging", "onboarding"]
        elif agent_def["name"] == "CreativeMuse":
            agent_contexts = ["creative_writing", "onboarding", "customer_support"]
        
        for ctx_name in agent_contexts:
            if ctx_name in context_map:
                db.records.attach(
                    source=agent,
                    target=context_map[ctx_name],
                    options={"type": "ACTS_IN", "direction": "out"}
                )
    
    print(f"  ✓ Created {len(AGENTS)} agents with trait relationships\n")
    return agent_records


def seed_context_trait_relationships(trait_map, context_map):
    """Create context-trait relationships with boost factors."""
    print("Creating context-trait relationships...")
    
    for ctx_name, ctx_config in CONTEXT_TRAITS.items():
        context = context_map[ctx_name]
        
        # Attach required traits
        for trait_name in ctx_config["requires"]:
            if trait_name in trait_map:
                trait = trait_map[trait_name]
                
                # Create relationship metadata
                boost_factor = ctx_config["boosts"].get(trait_name, 1.0)
                
                db.records.attach(
                    source=context,
                    target=trait,
                    options={"type": "REQUIRES", "direction": "out"}
                )
                
                # Store boost factor as relationship property
                boost_record = db.records.create(
                    label="CONTEXT_BOOST",
                    data={
                        "boost_factor": boost_factor,
                        "context_name": ctx_name,
                        "trait_name": trait_name,
                    }
                )
                db.records.attach(source=context, target=boost_record, options={"type": "BOOSTS", "direction": "out"})
        
        print(f"  ✓ Context '{ctx_name}': {len(ctx_config['requires'])} required traits")
    
    print("")


def main():
    """Run the seeding process."""
    print("=" * 60)
    print("Dynamic Personality Injection - Data Seeding")
    print("=" * 60 + "\n")
    
    # Clean slate
    cleanup_existing_data()
    
    # Seed data
    trait_map = seed_traits()
    context_map = seed_contexts()
    agents = seed_agents(trait_map, context_map)
    seed_context_trait_relationships(trait_map, context_map)
    
    print("=" * 60)
    print("Seeding complete!")
    print("=" * 60)
    print("\nRun 'python main.py' to see the personality injection demo.\n")


if __name__ == "__main__":
    main()
