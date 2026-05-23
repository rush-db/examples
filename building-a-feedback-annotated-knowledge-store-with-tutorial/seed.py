"""
Seed script for the Feedback-Annotated Knowledge Store.

This script creates a realistic dataset of knowledge entries and feedback corrections
to demonstrate the human-in-the-loop workflow.

The script is idempotent - running it multiple times is safe and will skip
records that already exist.
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Check for API token
api_token = os.getenv("RUSHDB_API_TOKEN")
if not api_token:
    print("ERROR: RUSHDB_API_TOKEN not found in environment")
    print("Please copy .env.example to .env and add your token")
    exit(1)

db = RushDB(api_token)

# Sample knowledge entries covering various topics
KNOWLEDGE_ENTRIES = [
    {
        "topic": "machine_learning",
        "title": "Gradient Descent Optimization",
        "content": "Gradient descent is an iterative optimization algorithm used to find the minimum of a function. In ML, it adjusts model parameters in the direction that reduces the loss function most rapidly.",
        "source": "ML Handbook 3rd Edition",
        "confidence": 0.95
    },
    {
        "topic": "machine_learning",
        "title": "Backpropagation Algorithm",
        "content": "Backpropagation is the algorithm used to compute gradients in neural networks. It works by propagating the error from the output layer backwards through hidden layers.",
        "source": "Deep Learning Course",
        "confidence": 0.92
    },
    {
        "topic": "databases",
        "title": "ACID Properties",
        "content": "ACID stands for Atomicity, Consistency, Isolation, and Durability. These are the four key properties that guarantee reliable transaction processing in database systems.",
        "source": "Database Systems Guide",
        "confidence": 0.98
    },
    {
        "topic": "databases",
        "title": "CAP Theorem",
        "content": "The CAP theorem states that a distributed system can only provide two of three guarantees: Consistency, Availability, and Partition tolerance. You must choose between CA, CP, or AP.",
        "source": "Distributed Systems Primer",
        "confidence": 0.88
    },
    {
        "topic": "programming",
        "title": "Garbage Collection",
        "content": "Garbage collection is an automatic memory management feature that reclaims memory occupied by objects that are no longer in use by the program.",
        "source": "Programming Languages Handbook",
        "confidence": 0.97
    },
    {
        "topic": "programming",
        "title": "Observer Pattern",
        "content": "The Observer pattern is a behavioral design pattern where an object maintains a list of dependents and notifies them automatically of any state changes.",
        "source": "Design Patterns Book",
        "confidence": 0.94
    },
    {
        "topic": "networking",
        "title": "TCP Three-Way Handshake",
        "content": "TCP establishes a connection using a three-way handshake: SYN, SYN-ACK, and ACK. This ensures both endpoints are ready for communication.",
        "source": "Networking Fundamentals",
        "confidence": 0.96
    },
    {
        "topic": "networking",
        "title": "DNS Resolution Process",
        "content": "DNS resolution converts human-readable domain names into IP addresses. It involves recursive queries to DNS servers until the authoritative answer is found.",
        "source": "Internet Protocols Guide",
        "confidence": 0.91
    },
    {
        "topic": "security",
        "title": "SQL Injection Prevention",
        "content": "SQL injection attacks occur when untrusted data is sent to an interpreter as part of a command. Prevention includes using parameterized queries and input validation.",
        "source": "Security Best Practices",
        "confidence": 0.93
    },
    {
        "topic": "security",
        "title": "OAuth 2.0 Flow",
        "content": "OAuth 2.0 is an authorization framework that enables applications to obtain limited access to user accounts on third-party services by delegating user authentication.",
        "source": "Auth Standards Documentation",
        "confidence": 0.89
    },
    {
        "topic": "cloud_computing",
        "title": "Auto-scaling Groups",
        "content": "Auto-scaling groups automatically adjust the number of compute instances based on demand metrics. They maintain desired capacity and replace failed instances.",
        "source": "Cloud Architecture Guide",
        "confidence": 0.90
    },
    {
        "topic": "cloud_computing",
        "title": "Container Orchestration",
        "content": "Container orchestration automates the deployment, management, and scaling of containerized applications. Kubernetes is the most popular orchestration platform.",
        "source": "DevOps Handbook",
        "confidence": 0.94
    },
    {
        "topic": "data_science",
        "title": "Cross-Validation Technique",
        "content": "Cross-validation is a technique to evaluate predictive models by partitioning data into complementary subsets, training on one subset and validating on another.",
        "source": "Data Science Methods",
        "confidence": 0.92
    },
    {
        "topic": "data_science",
        "title": "Feature Engineering",
        "content": "Feature engineering is the process of using domain knowledge to create features that make machine learning algorithms work better. It involves transformation and selection of input variables.",
        "source": "Analytics Handbook",
        "confidence": 0.87
    },
    {
        "topic": "devops",
        "title": "CI/CD Pipeline",
        "content": "CI/CD pipelines automate the process of integrating code changes, running tests, and deploying applications. CI focuses on integration, CD on delivery and deployment.",
        "source": "DevOps Practices",
        "confidence": 0.95
    }
]

# Sample feedback corrections
FEEDBACK_TEMPLATES = [
    {
        "feedback_type": "correction",
        "description": "The mathematical formula shown is incorrect. The correct version should use a squared error term.",
        "severity": "high",
        "reviewer": "Dr. Sarah Chen"
    },
    {
        "feedback_type": "clarification",
        "description": "The term 'iterative' could be confusing. Please specify what is being iterated over.",
        "severity": "medium",
        "reviewer": "Prof. James Miller"
    },
    {
        "feedback_type": "addition",
        "description": "Should mention that this only applies to convex optimization problems.",
        "severity": "medium",
        "reviewer": "Lisa Wang"
    },
    {
        "feedback_type": "outdated",
        "description": "This information was updated in the latest version. The new approach uses distributed computing.",
        "severity": "low",
        "reviewer": "Michael Brown"
    },
    {
        "feedback_type": "correction",
        "description": "The example code has a bug in line 42. The array index should start at 1, not 0.",
        "severity": "high",
        "reviewer": "Dr. Sarah Chen"
    },
    {
        "feedback_type": "clarification",
        "description": "What are the performance implications of this approach? Please add benchmarks.",
        "severity": "low",
        "reviewer": "Alex Turner"
    },
    {
        "feedback_type": "addition",
        "description": "Consider adding a comparison with similar approaches to help readers understand trade-offs.",
        "severity": "medium",
        "reviewer": "Prof. James Miller"
    },
    {
        "feedback_type": "correction",
        "description": "The acronym should be expanded before first use. Write out 'Consistency, Availability, Partition tolerance'.",
        "severity": "low",
        "reviewer": "Rachel Green"
    },
    {
        "feedback_type": "outdated",
        "description": "This approach has been deprecated. Please update to the current recommendation.",
        "severity": "high",
        "reviewer": "Michael Brown"
    },
    {
        "feedback_type": "addition",
        "description": "Adding a diagram would significantly improve understanding of this process.",
        "severity": "low",
        "reviewer": "Lisa Wang"
    }
]

# Status options for feedback workflow
FEEDBACK_STATUSES = ["pending", "reviewed", "applied", "rejected"]


def check_if_seeded():
    """Check if data already exists by looking for a known entry."""
    result = db.records.find({
        "labels": ["KNOWLEDGE_ENTRY"],
        "where": {"title": "Gradient Descent Optimization"},
        "limit": 1
    })
    return len(result.data) > 0


def create_knowledge_entries():
    """Create all knowledge entries."""
    print("\n📚 Creating knowledge entries...")
    entries = []
    
    for i, entry_data in enumerate(KNOWLEDGE_ENTRIES, 1):
        # Check if this entry already exists
        existing = db.records.find({
            "labels": ["KNOWLEDGE_ENTRY"],
            "where": {"title": entry_data["title"]},
            "limit": 1
        })
        
        if existing.data:
            print(f"  [{i}/{len(KNOWLEDGE_ENTRIES)}] Skipping existing: {entry_data['title']}")
            entries.append(existing.data[0])
            continue
        
        # Create the entry with metadata
        entry = db.records.create(
            label="KNOWLEDGE_ENTRY",
            data={
                **entry_data,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": 1
            }
        )
        entries.append(entry)
        print(f"  [{i}/{len(KNOWLEDGE_ENTRIES)}] Created: {entry_data['title']}")
        
        # Progress indicator every 5 entries
        if i % 5 == 0:
            print(f"  ... {i}/{len(KNOWLEDGE_ENTRIES)} entries processed")
    
    print(f"\n✅ Created {len(entries)} knowledge entries")
    return entries


def create_feedback_records(entries):
    """Create feedback records and attach them to knowledge entries."""
    print("\n📝 Creating feedback corrections...")
    
    feedback_count = 0
    
    # Generate feedback for random subset of entries
    selected_entries = random.sample(entries, min(len(entries), 12))
    
    for i, entry in enumerate(selected_entries, 1):
        # Determine number of feedback items for this entry (1-3)
        num_feedback = random.randint(1, 3)
        
        # Create feedback items
        for j in range(num_feedback):
            template = random.choice(FEEDBACK_TEMPLATES)
            status = random.choice(FEEDBACK_STATUSES)
            
            # Calculate submission time (within last 30 days)
            days_ago = random.randint(1, 30)
            submitted_at = datetime.now() - timedelta(days=days_ago)
            
            feedback = db.records.create(
                label="FEEDBACK",
                data={
                    "type": template["feedback_type"],
                    "description": template["description"],
                    "severity": template["severity"],
                    "status": status,
                    "reviewer": template["reviewer"],
                    "submitted_at": submitted_at.isoformat(),
                    "reviewed_at": (submitted_at + timedelta(hours=random.randint(2, 72))).isoformat() if status != "pending" else None
                }
            )
            
            # Attach feedback to the knowledge entry
            db.records.attach(
                source=entry,
                target=feedback,
                options={"type": "HAS_FEEDBACK"}
            )
            
            feedback_count += 1
        
        print(f"  [{i}/{len(selected_entries)}] Added feedback to: {entry.data.get('title', 'Unknown')}")
    
    print(f"\n✅ Created {feedback_count} feedback records")


def create_annotators():
    """Create annotator profiles who provide feedback."""
    print("\n👤 Creating annotator profiles...")
    
    annotators = [
        {"name": "Dr. Sarah Chen", "expertise": "machine_learning", "total_reviews": 0},
        {"name": "Prof. James Miller", "expertise": "databases", "total_reviews": 0},
        {"name": "Lisa Wang", "expertise": "programming", "total_reviews": 0},
        {"name": "Michael Brown", "expertise": "networking", "total_reviews": 0},
        {"name": "Alex Turner", "expertise": "cloud_computing", "total_reviews": 0},
        {"name": "Rachel Green", "expertise": "security", "total_reviews": 0}
    ]
    
    created_count = 0
    for annotator_data in annotators:
        # Check if annotator exists
        existing = db.records.find({
            "labels": ["ANNOTATOR"],
            "where": {"name": annotator_data["name"]},
            "limit": 1
        })
        
        if existing.data:
            print(f"  Skipping existing: {annotator_data['name']}")
            continue
        
        db.records.create(
            label="ANNOTATOR",
            data={
                **annotator_data,
                "created_at": datetime.now().isoformat()
            }
        )
        created_count += 1
        print(f"  Created: {annotator_data['name']}")
    
    print(f"\n✅ Created {created_count} new annotator profiles")


def print_summary():
    """Print summary of seeded data."""
    print("\n" + "=" * 60)
    print("📊 DATABASE SUMMARY")
    print("=" * 60)
    
    # Count knowledge entries
    entries = db.records.find({"labels": ["KNOWLEDGE_ENTRY"]})
    print(f"  Knowledge Entries: {len(entries.data)}")
    
    # Count feedback
    feedback = db.records.find({"labels": ["FEEDBACK"]})
    print(f"  Feedback Records: {len(feedback.data)}")
    
    # Count annotators
    annotators = db.records.find({"labels": ["ANNOTATOR"]})
    print(f"  Annotators: {len(annotators.data)}")
    
    # Count by feedback status
    pending = db.records.find({
        "labels": ["FEEDBACK"],
        "where": {"status": "pending"}
    })
    applied = db.records.find({
        "labels": ["FEEDBACK"],
        "where": {"status": "applied"}
    })
    print(f"\n  Feedback by status:")
    print(f"    - Pending: {len(pending.data)}")
    print(f"    - Applied: {len(applied.data)}")
    
    print("\n" + "=" * 60)


def main():
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("🚀 FEEDBACK-ANNOTATED KNOWLEDGE STORE - SEEDING")
    print("=" * 60)
    
    # Check if already seeded
    if check_if_seeded():
        print("\n⚠️  Database appears to already contain seeded data.")
        response = input("Skip seeding and show summary? (y/n): ")
        if response.lower() == 'y':
            print_summary()
            return
        print("Proceeding with seeding anyway...")
    
    # Create data
    entries = create_knowledge_entries()
    create_feedback_records(entries)
    create_annotators()
    print_summary()
    
    print("\n✅ Seeding complete! Run `python main.py` to see the demo.")


if __name__ == "__main__":
    main()
