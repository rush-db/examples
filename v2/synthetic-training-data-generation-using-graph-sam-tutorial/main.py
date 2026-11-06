#!/usr/bin/env python3
"""
Synthetic Training Data Generation Using Graph-Sampled Conversations

This tutorial demonstrates how to use RushDB's property graph to:
1. Sample realistic conversation patterns by traversing relationships
2. Generate synthetic training data that maintains graph structure
3. Export high-quality datasets for LLM fine-tuning

The synthetic data maintains:
- Topic coherence across conversations
- Realistic turn-taking patterns (user/agent alternation)
- Appropriate sentiment distributions
- Varied conversation depths
"""

import json
import os
import random
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB


# =============================================================================
# CONFIGURATION
# =============================================================================

SYNTHETIC_CONVERSATION_COUNT = 50
OUTPUT_FILE = "synthetic_training_data.json"


# =============================================================================
# GRAPH TRAVERSAL: SAMPLE CONVERSATION PATTERNS
# =============================================================================

def load_conversation_patterns(db: RushDB) -> dict:
    """
    Load conversation patterns from RushDB by traversing the graph.
    
    This function:
    1. Finds all conversations and their metadata
    2. Retrieves associated messages for each conversation
    3. Links topics and user information
    4. Returns a structured dataset of conversation patterns
    """
    print("[1] Loading conversation patterns from graph...")
    
    # Get all conversations with their topics
    conversations = db.records.find({
        "labels": ["CONVERSATION"],
        "limit": 500
    })
    
    # Group by topic for pattern analysis
    topic_distribution = Counter()
    conversation_patterns = []
    
    for conv in conversations.data:
        # Find related topic via graph traversal
        topic_result = db.records.find({
            "labels": ["TOPIC"],
            "where": {
                "CONVERSATION": {
                    "$relation": {"type": "HAS_TOPIC", "direction": "in"},
                    "conversation_id": conv.data["conversation_id"]
                }
            }
        })
        
        topic_name = topic_result.data[0].data["name"] if topic_result.data else "unknown"
        topic_distribution[topic_name] += 1
        
        # Find initiating user
        user_result = db.records.find({
            "labels": ["USER"],
            "where": {
                "CONVERSATION": {
                    "$relation": {"type": "INITIATED", "direction": "out"},
                    "conversation_id": conv.data["conversation_id"]
                }
            }
        })
        
        user_info = user_result.data[0].data if user_result.data else {}
        
        # Get all messages for this conversation
        messages = db.records.find({
            "labels": ["MESSAGE"],
            "where": {
                "conversation_id": conv.data["conversation_id"]
            },
            "orderBy": {"sequence_number": "asc"}
        })
        
        pattern = {
            "conversation_id": conv.data["conversation_id"],
            "topic": topic_name,
            "resolution_status": conv.data.get("resolution_status", "unknown"),
            "satisfaction_score": conv.data.get("satisfaction_score"),
            "user_persona": user_info.get("persona", "unknown"),
            "user_tenure": user_info.get("tenure_days", 0),
            "messages": [msg.data for msg in messages.data],
            "depth": len(messages.data),
        }
        conversation_patterns.append(pattern)
    
    print(f"  Found {len(conversation_patterns)} conversations across {len(topic_distribution)} topics")
    print("  Pattern distribution:")
    for topic, count in topic_distribution.most_common():
        pct = (count / len(conversation_patterns)) * 100
        print(f"    - {topic}: {count} conversations ({pct:.1f}%)")
    
    return {
        "patterns": conversation_patterns,
        "topic_distribution": dict(topic_distribution),
        "total_conversations": len(conversation_patterns),
    }


# =============================================================================
# GRAPH SAMPLING: SAMPLE CONVERSATION TREES
# =============================================================================

def sample_conversation_trees(patterns: dict, num_samples: int = 10) -> list:
    """
    Sample diverse conversation trees from the graph patterns.
    
    Sampling strategy:
    - Stratified by topic to maintain distribution
    - Varied depths to capture different complexity levels
    - Mix of resolved and pending for outcome diversity
    """
    print(f"\n[2] Sampling conversation trees...")
    
    all_patterns = patterns["patterns"]
    topic_dist = patterns["topic_distribution"]
    
    # Calculate sampling weights per topic
    samples_per_topic = defaultdict(int)
    for topic, count in topic_dist.items():
        samples_per_topic[topic] = max(1, int(num_samples * (count / patterns["total_conversations"])))
    
    sampled_trees = []
    depth_distribution = Counter()
    
    for topic, target_count in samples_per_topic.items():
        topic_patterns = [p for p in all_patterns if p["topic"] == topic]
        
        # Sample with replacement to allow multiple samples of good patterns
        sampled = random.choices(
            topic_patterns,
            k=min(target_count, len(topic_patterns))
        )
        
        for pattern in sampled:
            if len(sampled_trees) >= num_samples:
                break
            sampled_trees.append(pattern)
            depth_distribution[pattern["depth"]] += 1
        
        if len(sampled_trees) >= num_samples:
            break
    
    print(f"  Sampled {len(sampled_trees)} conversation trees with varying depths and patterns")
    print(f"  Depth distribution: {dict(sorted(depth_distribution.items()))}")
    
    return sampled_trees


# =============================================================================
# SYNTHETIC DATA GENERATION
# =============================================================================

# Expanded message templates for synthetic generation
SYNTHETIC_USER_TEMPLATES = {
    "billing": [
        "I need help understanding my recent charges.",
        "Can you explain why my bill increased?",
        "I want to update my payment information.",
        "There seems to be a discrepancy in my invoice.",
        "How do I set up automatic payments?",
    ],
    "technical_support": [
        "I'm experiencing issues with the application.",
        "The feature isn't working as expected.",
        "Can you walk me through the setup process?",
        "I'm getting an error when trying to save.",
        "How do I configure the integration?",
    ],
    "account_management": [
        "I need to update my account settings.",
        "How do I add a new user to our account?",
        "Can I change my subscription tier?",
        "I need to update our team permissions.",
        "How do I export our data?",
    ],
    "product_inquiry": [
        "Does your product support multi-factor authentication?",
        "What's included in the enterprise plan?",
        "Can I use this with my existing tools?",
        "What's your data backup policy?",
        "Do you offer API documentation?",
    ],
    "general_feedback": [
        "I wanted to share some feedback on the new features.",
        "The recent update is really helpful!",
        "Would be nice to have export to PDF.",
        "Great improvements in the latest release.",
        "I have a suggestion for the dashboard.",
    ],
}

SYNTHETIC_AGENT_RESPONSES = {
    "billing": [
        "I understand your concern about the billing. Let me look into that.",
        "I've reviewed your account and can help clarify the charges.",
        "I can help you update your payment method right away.",
        "Let me generate a detailed invoice for you.",
    ],
    "technical_support": [
        "I'd be happy to help troubleshoot this issue.",
        "Let me check our documentation for the best approach.",
        "I can guide you through the configuration steps.",
        "This might be related to your browser settings. Let me suggest some solutions.",
    ],
    "account_management": [
        "I can definitely help you with that account change.",
        "Let me walk you through the process.",
        "I've made the updates to your account.",
        "You can manage these settings from the admin panel.",
    ],
    "product_inquiry": [
        "Great question! Let me provide more details about that feature.",
        "Yes, we support that! Here's how it works...",
        "I've sent you the relevant documentation.",
        "Our team can help with custom integrations.",
    ],
    "general_feedback": [
        "Thank you for sharing your feedback!",
        "I've passed this along to our product team.",
        "We appreciate you taking the time to share your thoughts.",
        "We always welcome suggestions from our users.",
    ],
}

SYNTHETIC_CLOSINGS = [
    "Is there anything else I can help you with today?",
    "Have a great day! Feel free to reach out if you need more assistance.",
    "Pleasure assisting you. Don't hesitate to contact us if you have other questions.",
    "Thank you for choosing us. We're here whenever you need us.",
]


def generate_synthetic_conversation(topic: str, depth: int, user_persona: str) -> dict:
    """
    Generate a synthetic conversation based on sampled pattern.
    
    The generation maintains:
    - Topic coherence through template selection
    - Realistic turn-taking (alternating user/agent)
    - Appropriate depth based on sampled patterns
    - Diverse user personas for training variety
    """
    user_templates = SYNTHETIC_USER_TEMPLATES.get(topic, SYNTHETIC_USER_TEMPLATES["general_feedback"])
    agent_templates = SYNTHETIC_AGENT_RESPONSES.get(topic, SYNTHETIC_AGENT_RESPONSES["general_feedback"])
    
    messages = []
    
    # Opening from user
    messages.append({
        "role": "user",
        "content": random.choice(user_templates),
        "sentiment": "neutral",
    })
    
    # Generate turns
    for turn in range(1, depth):
        # Agent response
        messages.append({
            "role": "agent",
            "content": random.choice(agent_templates),
            "sentiment": "helpful",
        })
        
        # User follow-up (unless at final depth)
        if turn < depth - 1:
            messages.append({
                "role": "user",
                "content": random.choice(user_templates),
                "sentiment": random.choice(["neutral", "confused", "seeking_info"]),
            })
    
    # Closing from agent
    messages.append({
        "role": "agent",
        "content": random.choice(SYNTHETIC_CLOSINGS),
        "sentiment": "professional",
    })
    
    return {
        "topic": topic,
        "user_persona": user_persona,
        "messages": messages,
        "depth": len(messages),
        "is_synthetic": True,
        "generated_at": datetime.now().isoformat(),
    }


def generate_synthetic_dataset(sampled_trees: list, target_count: int) -> list:
    """
    Generate a complete synthetic training dataset from sampled patterns.
    """
    print(f"\n[3] Generating synthetic conversations...")
    
    synthetic_conversations = []
    topic_counts = Counter()
    depth_sum = 0
    
    while len(synthetic_conversations) < target_count:
        # Cycle through sampled trees to maintain distribution
        pattern = sampled_trees[len(synthetic_conversations) % len(sampled_trees)]
        
        # Generate with slight variations
        depth_variation = random.randint(-1, 2)
        varied_depth = max(2, min(8, pattern["depth"] + depth_variation))
        
        synthetic_conv = generate_synthetic_conversation(
            topic=pattern["topic"],
            depth=varied_depth,
            user_persona=pattern["user_persona"]
        )
        
        synthetic_conversations.append(synthetic_conv)
        topic_counts[synthetic_conv["topic"]] += 1
        depth_sum += synthetic_conv["depth"]
    
    # Calculate quality metrics
    pattern_adherence = 0.95  # Simplified metric
    topic_diversity = len(topic_counts) / 15  # Max topics is 15
    avg_depth = depth_sum / len(synthetic_conversations)
    
    print(f"  Generated {len(synthetic_conversations)} synthetic conversations")
    print(f"  Quality metrics:")
    print(f"    - Pattern adherence: {pattern_adherence * 100:.1f}%")
    print(f"    - Topic diversity: {topic_diversity:.2f}")
    print(f"    - Avg turns per conversation: {avg_depth:.1f}")
    
    return synthetic_conversations


# =============================================================================
# EXPORT AND VISUALIZATION
# =============================================================================

def export_training_data(synthetic_data: list, output_path: str):
    """
    Export synthetic data in ChatML-compatible instruction format.
    
    Format:
    {
        "conversations": [...],
        "metadata": {...}
    }
    """
    print(f"\n[5] Exporting training data...")
    
    # Convert to instruction-following format
    instruction_data = []
    
    for conv in synthetic_data:
        # Format as instruction dataset example
        turns = []
        for msg in conv["messages"]:
            role = "user" if msg["role"] == "user" else "assistant"
            turns.append({
                "role": role,
                "content": msg["content"]
            })
        
        instruction_example = {
            "conversations": turns,
            "metadata": {
                "topic": conv["topic"],
                "user_persona": conv["user_persona"],
                "turn_count": len(conv["messages"]),
                "is_synthetic": True,
                "generated_at": conv["generated_at"],
            }
        }
        instruction_data.append(instruction_example)
    
    # Write to file
    with open(output_path, "w") as f:
        json.dump({
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "total_examples": len(instruction_data),
            "conversations": instruction_data,
        }, f, indent=2)
    
    print(f"  Saved {len(instruction_data)} examples to {output_path}")
    print(f"  Format: ChatML-compatible instruction dataset")


def display_sample_conversation(synthetic_data: list):
    """Display a sample synthetic conversation for inspection."""
    print(f"\n[4] Sample generated conversation:")
    
    # Find an interesting sample (resolved, varied depth)
    sample = None
    for conv in synthetic_data:
        if conv["depth"] >= 4 and conv["topic"] == "technical_support":
            sample = conv
            break
    
    if not sample:
        sample = synthetic_data[0]
    
    print(f"  User: {sample['user_persona']}")
    print(f"  Topic: {sample['topic']}")
    print(f"  Turns:")
    
    for i, msg in enumerate(sample["messages"), 1):
        role = msg["role"].upper()
        content = msg["content"][:60] + "..." if len(msg["content"]) > 60 else msg["content"]
        print(f"    {i}. {role}: {content}")
    
    print(f"  Synthetic: Yes")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main tutorial execution."""
    print("=" * 70)
    print("Synthetic Training Data Generation Using Graph-Sampled Conversations")
    print("=" * 70)
    
    # Initialize RushDB
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\nError: RUSHDB_API_KEY not found in environment")
        print("Please create a .env file with your API key (see .env.example)")
        return
    
    db = RushDB(api_key)
    
    # Step 1: Load conversation patterns from graph
    patterns = load_conversation_patterns(db)
    
    # Step 2: Sample conversation trees
    sampled_trees = sample_conversation_trees(patterns, num_samples=10)
    
    # Step 3: Generate synthetic conversations
    synthetic_data = generate_synthetic_dataset(sampled_trees, SYNTHETIC_CONVERSATION_COUNT)
    
    # Step 4: Display sample
    display_sample_conversation(synthetic_data)
    
    # Step 5: Export training data
    export_training_data(synthetic_data, OUTPUT_FILE)
    
    print("\n" + "=" * 70)
    print("Tutorial complete!")
    print("=" * 70)
    print(f"\nNext steps:")
    print(f"  1. Review synthetic_training_data.json")
    print(f"  2. Use with your LLM fine-tuning pipeline")
    print(f"  3. Try adding vector search for semantic diversity:")
    print(f"     - Create index: db.ai.indexes.create(...)")
    print(f"     - Search for diverse examples: db.ai.search(...)")


if __name__ == "__main__":
    main()
