"""
Seed script for the Weighted Priority Queue Scheduler.

Creates realistic task data with dependencies to demonstrate graph-based scheduling.
This script is idempotent — safe to run multiple times.
"""

import os
from datetime import datetime, timedelta
from random import choice, randint, seed as random_seed

from dotenv import load_dotenv
from faker import Faker

from rushdb import RushDB

fake = Faker()
Faker.seed(42)
random_seed(42)

# Task templates for realistic mock data
TASK_TEMPLATES = [
    {
        "name": "Design REST API endpoint structure",
        "base_priority": 7,
        "estimated_hours": 2,
        "category": "architecture"
    },
    {
        "name": "Implement database schema migrations",
        "base_priority": 8,
        "estimated_hours": 4,
        "category": "backend"
    },
    {
        "name": "Write authentication and authorization module",
        "base_priority": 9,
        "estimated_hours": 8,
        "category": "security"
    },
    {
        "name": "Create React component library",
        "base_priority": 6,
        "estimated_hours": 6,
        "category": "frontend"
    },
    {
        "name": "Write integration test suite",
        "base_priority": 5,
        "estimated_hours": 5,
        "category": "testing"
    },
    {
        "name": "Set up CI/CD pipeline",
        "base_priority": 6,
        "estimated_hours": 3,
        "category": "devops"
    },
    {
        "name": "Optimize database queries",
        "base_priority": 7,
        "estimated_hours": 4,
        "category": "performance"
    },
    {
        "name": "Implement caching layer",
        "base_priority": 6,
        "estimated_hours": 3,
        "category": "performance"
    },
    {
        "name": "Write API documentation",
        "base_priority": 4,
        "estimated_hours": 2,
        "category": "documentation"
    },
    {
        "name": "Security audit and penetration testing",
        "base_priority": 8,
        "estimated_hours": 6,
        "category": "security"
    },
    {
        "name": "Implement webhook notifications",
        "base_priority": 5,
        "estimated_hours": 3,
        "category": "backend"
    },
    {
        "name": "Create monitoring dashboards",
        "base_priority": 5,
        "estimated_hours": 4,
        "category": "devops"
    }
]

# Dependency rules: task can depend on these categories
DEPENDENCY_RULES = {
    "security": ["architecture", "backend"],
    "frontend": ["architecture"],
    "testing": ["security", "frontend", "backend"],
    "performance": ["backend"],
    "devops": ["backend", "architecture"],
    "documentation": ["architecture", "backend"]
}


def calculate_weight(base_priority: int, deadline: datetime, estimated_hours: int) -> float:
    """Calculate task weight based on priority and time factors."""
    now = datetime.utcnow()
    hours_until_deadline = (deadline - now).total_seconds() / 3600
    
    # Deadline urgency factor
    if hours_until_deadline < 4:
        deadline_factor = 2.0
    elif hours_until_deadline < 24:
        deadline_factor = 1.5
    else:
        deadline_factor = 1.0
    
    # Effort factor (longer tasks need more attention)
    effort_factor = 1.0 + (estimated_hours / 8.0)
    
    # Final weight calculation
    weight = (base_priority / 10.0) * deadline_factor * effort_factor
    return round(weight, 2)


def seed_tasks(db: RushDB) -> list:
    """Create task records with dependencies."""
    
    # Check if data already exists
    existing = db.records.find({
        "labels": ["TASK"],
        "limit": 1
    })
    
    if existing.data:
        print("⚠️  Tasks already exist in the database. Skipping seed.")
        print("   Run 'python main.py' to see the existing tasks.")
        return []
    
    print("🌱 Seeding task data...")
    
    tasks_by_category = {}
    all_tasks = []
    
    with db.transactions.begin() as tx:
        for i, template in enumerate(TASK_TEMPLATES):
            # Generate realistic deadline
            days_until_deadline = randint(1, 14)
            deadline = datetime.utcnow() + timedelta(days=days_until_deadline)
            
            weight = calculate_weight(
                template["base_priority"],
                deadline,
                template["estimated_hours"]
            )
            
            task_data = {
                "name": template["name"],
                "priority": template["base_priority"],
                "weight": weight,
                "deadline": deadline.isoformat() + "Z",
                "estimated_hours": template["estimated_hours"],
                "category": template["category"],
                "status": "pending"
            }
            
            task = db.records.create(
                label="TASK",
                data=task_data,
                transaction=tx
            )
            
            all_tasks.append(task)
            
            if template["category"] not in tasks_by_category:
                tasks_by_category[template["category"]] = []
            tasks_by_category[template["category"]].append(task)
            
            if (i + 1) % 4 == 0:
                print(f"   Created {i + 1}/{len(TASK_TEMPLATES)} tasks...")
    
    print("🔗 Creating dependencies...")
    
    # Create dependency relationships
    for task in all_tasks:
        category = task["category"]
        allowed_deps = DEPENDENCY_RULES.get(category, [])
        
        for dep_category in allowed_deps:
            dep_tasks = tasks_by_category.get(dep_category, [])
            if dep_tasks:
                # Attach to a random task from the required category
                target = choice(dep_tasks)
                if target.id != task.id:
                    db.records.attach(
                        source=task,
                        target=target,
                        options={"type": "DEPENDS_ON", "direction": "out"}
                    )
    
    print(f"✅ Seeded {len(all_tasks)} tasks with dependencies")
    return all_tasks


def main():
    """Main seeding function."""
    load_dotenv()
    
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("❌ Error: RUSHDB_API_KEY not found in environment")
        print("   Please copy .env.example to .env and add your API key")
        return
    
    url = os.getenv("RUSHDB_URL")
    db = RushDB(api_key, url=url) if url else RushDB(api_key)
    
    try:
        tasks = seed_tasks(db)
        if tasks:
            print(f"\n📊 Summary: {len(tasks)} tasks created")
            categories = set(t["category"] for t in tasks)
            print(f"   Categories: {', '.join(sorted(categories))}")
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        raise


if __name__ == "__main__":
    main()
