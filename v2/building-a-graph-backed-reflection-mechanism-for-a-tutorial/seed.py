"""
Seed script for the reflection mechanism example.

Creates a set of realistic experiences, actions, reflections, and insights
that demonstrate the self-improvement loop in a hypothetical customer support
agent.

This script is idempotent - safe to run multiple times.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    raise ValueError(
        "RUSHDB_API_KEY not found. "
        "Copy .env.example to .env and add your API key."
    )

db = RushDB(api_key)


def clear_existing_data():
    """Remove all seeded data to ensure clean state."""
    labels_to_clear = ["INSIGHT", "REFLECTION", "ACTION", "EXPERIENCE"]
    for label in labels_to_clear:
        try:
            db.records.delete_many({"labels": [label], "where": {}})
        except Exception:
            pass
    print("✓ Cleared existing data\n")


def create_experiences():
    """Create sample experiences for a customer support agent."""
    experiences = []
    
    # Experience 1: Customer frustrated about billing
    exp1 = db.records.create(
        label="EXPERIENCE",
        data={
            "session_id": "support_001",
            "type": "customer_support",
            "outcome": "resolved",
            "customer_sentiment": "frustrated",
            "topic": "billing_inquiry",
            "duration_minutes": 15
        }
    )
    experiences.append(exp1)
    
    # Actions within experience 1
    actions_exp1 = [
        {"type": "greeting", "tone": "warm", "effective": True},
        {"type": "question", "topic": "billing_details", "effective": True},
        {"type": "explanation", "topic": "invoice_breakdown", "effective": True},
        {"type": "apology", "trigger": "customer_frustration", "effective": True}
    ]
    for action_data in actions_exp1:
        action = db.records.create(label="ACTION", data=action_data)
        db.records.attach(source=exp1, target=action, options={"type": "CONTAINS"})
    
    # Experience 2: Technical issue - password reset
    exp2 = db.records.create(
        label="EXPERIENCE",
        data={
            "session_id": "support_002",
            "type": "customer_support",
            "outcome": "resolved",
            "customer_sentiment": "confused",
            "topic": "password_reset",
            "duration_minutes": 8
        }
    )
    experiences.append(exp2)
    
    actions_exp2 = [
        {"type": "greeting", "tone": "patient", "effective": True},
        {"type": "step_by_step_guide", "topic": "password_reset", "effective": True},
        {"type": "confirmation", "topic": "new_password_works", "effective": True}
    ]
    for action_data in actions_exp2:
        action = db.records.create(label="ACTION", data=action_data)
        db.records.attach(source=exp2, target=action, options={"type": "CONTAINS"})
    
    # Experience 3: Feature request handling
    exp3 = db.records.create(
        label="EXPERIENCE",
        data={
            "session_id": "support_003",
            "type": "feature_request",
            "outcome": "logged",
            "customer_sentiment": "neutral",
            "topic": "export_functionality",
            "duration_minutes": 5
        }
    )
    experiences.append(exp3)
    
    actions_exp3 = [
        {"type": "acknowledgment", "topic": "feature_request", "effective": True},
        {"type": "prioritization_discussion", "effective": True},
        {"type": "follow_up_promise", "effective": True}
    ]
    for action_data in actions_exp3:
        action = db.records.create(label="ACTION", data=action_data)
        db.records.attach(source=exp3, target=action, options={"type": "CONTAINS"})
    
    return experiences


def create_reflections(experiences):
    """Create reflections analyzing each experience."""
    reflections = []
    
    reflection_data = [
        {
            "experience_id": experiences[0].id,
            "analysis": "Customer was frustrated due to unclear invoice. "
                        "Apologizing early and providing detailed breakdown resolved tension.",
            "key_learnings": [
                "Empathy first, then solution",
                "Detailed explanations reduce frustration",
                "Acknowledge mistakes promptly"
            ],
            "confidence": 0.92
        },
        {
            "experience_id": experiences[1].id,
            "analysis": "Customer was confused about the reset process. "
                        "Breaking it into clear steps with confirmation worked well.",
            "key_learnings": [
                "Step-by-step guidance reduces confusion",
                "Confirm understanding at each step",
                "Patience is essential for confused users"
            ],
            "confidence": 0.88
        },
        {
            "experience_id": experiences[2].id,
            "analysis": "Feature request was handled by acknowledging importance "
                        "and promising follow-up. Customer appreciated being heard.",
            "key_learnings": [
                "Customers value acknowledgment",
                "Promising follow-up builds trust",
                "Log requests for product team"
            ],
            "confidence": 0.85
        }
    ]
    
    for refl_data in reflection_data:
        reflection = db.records.create(
            label="REFLECTION",
            data={
                "analysis": refl_data["analysis"],
                "key_learnings": refl_data["key_learnings"],
                "confidence": refl_data["confidence"],
                "timestamp": "2025-01-15T10:30:00Z"
            }
        )
        
        # Link reflection to its experience
        experience = db.records.find_by_id(refl_data["experience_id"])
        db.records.attach(source=experience, target=reflection, options={"type": "PRODUCES"})
        
        reflections.append(reflection)
    
    return reflections


def create_insights(reflections):
    """Generate insights from reflection patterns."""
    insights = []
    
    insight_definitions = [
        {
            "name": "empathy_first_resolution",
            "description": "Start with empathy before jumping to solutions. "
                          "Acknowledge the customer's emotional state.",
            "applies_to": ["frustrated_customer", "angry_customer", "confused_customer"],
            "effectiveness_score": 0.95
        },
        {
            "name": "stepwise_guidance",
            "description": "Break complex tasks into clear, numbered steps. "
                          "Confirm understanding at each stage.",
            "applies_to": ["technical_task", "reset_process", "configuration"],
            "effectiveness_score": 0.91
        },
        {
            "name": "acknowledgment_matters",
            "description": "Customers feel valued when their concerns are acknowledged "
                          "before any solution is provided.",
            "applies_to": ["feature_request", "complaint", "question"],
            "effectiveness_score": 0.89
        },
        {
            "name": "detailed_explanations",
            "description": "Providing detailed explanations reduces follow-up questions "
                          "and increases customer satisfaction.",
            "applies_to": ["billing_explanation", "technical_explanation", "policy_explanation"],
            "effectiveness_score": 0.87
        },
        {
            "name": "follow_through_promise",
            "description": "Always follow through on promised actions. "
                          "If you say you'll do something, do it.",
            "applies_to": ["follow_up", "feature_request", "escalation"],
            "effectiveness_score": 0.93
        }
    ]
    
    for insight_def in insight_definitions:
        insight = db.records.create(
            label="INSIGHT",
            data={
                "name": insight_def["name"],
                "description": insight_def["description"],
                "applies_to": insight_def["applies_to"],
                "effectiveness_score": insight_def["effectiveness_score"],
                "usage_count": random.randint(5, 20),
                "created_at": "2025-01-15T10:30:00Z"
            }
        )
        
        # Link insight to the reflection that generated it
        for reflection in reflections[:3]:
            db.records.attach(source=reflection, target=insight, options={"type": "GENERATES"})
        
        insights.append(insight)
    
    return insights


def print_progress(message):
    """Print formatted progress message."""
    print(f"  {message}")


def main():
    print("\n=== Seeding Reflection Mechanism Data ===\n")
    
    print("[1] Clearing existing data...")
    clear_existing_data()
    
    print("[2] Creating experiences...")
    experiences = create_experiences()
    for exp in experiences:
        print_progress(f"✓ Created experience: '{exp.data.get('session_id')}'")
    print()
    
    print("[3] Creating reflections...")
    reflections = create_reflections(experiences)
    for refl in reflections:
        print_progress(f"✓ Created reflection analyzing: '{refl.data.get('analysis')[:50]}...'")
    print()
    
    print("[4] Generating insights...")
    insights = create_insights(reflections)
    for insight in insights:
        print_progress(f"✓ Generated insight: '{insight.data.get('name')}'")
    print()
    
    print("[5] Verifying graph structure...")
    
    # Verify relationships
    for exp in experiences[:1]:
        contained_actions = db.records.find({
            "labels": ["ACTION"],
            "where": {
                "EXPERIENCE": {"$relation": {"type": "CONTAINS", "direction": "in"}}
            }
        })
        print_progress(f"  Experience '{exp.data.get('session_id')}' has {len(contained_actions.data)} actions")
    
    # Verify label counts
    labels = db.labels.find({})
    print_progress(f"  Total labels in graph: {len(labels)}")
    print()
    
    print("=== Seeding Complete ===\n")
    print("Run 'python main.py' to see the reflection system in action.\n")


if __name__ == "__main__":
    main()
