"""
Seed script for bidirectional relationship example.

Creates a realistic agent memory graph with:
- 1 Agent profile
- 10 Memory nodes with semantic content
- 5 Task steps that reference memories
- 6 Concepts that memories are about
- Bidirectional relationships (USED / USED_BY, etc.)

Run this once before main.py to populate the database.
The script is idempotent: it checks for existing data before creating.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB

# Sample data for realistic agent memory
AGENT_DATA = {
    "name": "TaskPlanningAgent",
    "version": "1.2.0",
    "domain": "software development planning"
}

MEMORY_DATA = [
    {
        "content": "User requirements specify a REST API with authentication via JWT tokens. Response format should be JSON.",
        "importance": 0.9,
        "type": "requirement"
    },
    {
        "content": "Previous sprint completed 3 features: user profiles, team management, and notification system.",
        "importance": 0.7,
        "type": "history"
    },
    {
        "content": "Technical constraints: must integrate with existing PostgreSQL database and Redis cache layer.",
        "importance": 0.85,
        "type": "constraint"
    },
    {
        "content": "Q3 deadline is September 15th. Team velocity from Q2 was 42 story points per sprint.",
        "importance": 0.8,
        "type": "timeline"
    },
    {
        "content": "Stakeholder preferences: minimize API response time, prioritize mobile-friendly endpoints, include rate limiting.",
        "importance": 0.75,
        "type": "preference"
    },
    {
        "content": "API endpoints needed: /users, /teams, /notifications, /auth, /analytics.",
        "importance": 0.9,
        "type": "requirement"
    },
    {
        "content": "Code review feedback from last PR: need better error handling and input validation.",
        "importance": 0.6,
        "type": "feedback"
    },
    {
        "content": "Available team members: 3 backend, 2 frontend, 1 QA. Capacity is 80 points per sprint.",
        "importance": 0.85,
        "type": "resource"
    },
    {
        "content": "Architecture decision: use microservices pattern with API gateway for better scalability.",
        "importance": 0.8,
        "type": "decision"
    },
    {
        "content": "Testing requirements: 80% code coverage, integration tests for all endpoints, load testing for /analytics.",
        "importance": 0.75,
        "type": "requirement"
    }
]

CONCEPT_DATA = [
    {"name": "REST API", "category": "technology"},
    {"name": "authentication", "category": "security"},
    {"name": "database integration", "category": "infrastructure"},
    {"name": "project timeline", "category": "planning"},
    {"name": "team capacity", "category": "resource"},
    {"name": "code quality", "category": "process"}
]

TASK_STEPS_DATA = [
    {
        "action": "Analyze requirements",
        "description": "Review user stories and map to API endpoints",
        "step_order": 1,
        "status": "completed"
    },
    {
        "action": "Design database schema",
        "description": "Create ERD for users, teams, notifications tables",
        "step_order": 2,
        "status": "completed"
    },
    {
        "action": "Implement authentication",
        "description": "Build JWT-based auth with refresh tokens",
        "step_order": 3,
        "status": "in_progress"
    },
    {
        "action": "Create API endpoints",
        "description": "Implement CRUD for all resource types",
        "step_order": 4,
        "status": "planned"
    },
    {
        "action": "Performance testing",
        "description": "Load test /analytics endpoint with 10k concurrent users",
        "step_order": 5,
        "status": "planned"
    }
]


def check_existing_data(db):
    """Check if seed data already exists."""
    agents = db.records.find({"labels": ["AGENT"], "limit": 1})
    return len(agents) > 0


def create_vector_index(db):
    """Create the vector index for semantic search."""
    try:
        # Check for existing indexes
        existing = db.ai.indexes.find().data
        for idx in existing:
            if idx['label'] == 'MEMORY' and idx['propertyName'] == 'content':
                print(f"  Vector index already exists: {idx['label']}.{idx['propertyName']}")
                return idx
        
        # Create external index (we'll supply vectors)
        index = db.ai.indexes.create({
            "label": "MEMORY",
            "propertyName": "content",
            "sourceType": "external",
            "dimensions": 384,  # for all-MiniLM-L6-v2
            "similarityFunction": "cosine"
        })
        print(f"  Created vector index: {index.data.get('__id', index.id)}")
        return index
    except Exception as e:
        print(f"  Warning: Could not create vector index: {e}")
        return None


def seed(db):
    """Main seeding function."""
    print("\n=== Bidirectional Relationship Seeder ===\n")
    
    # Check for existing data
    if check_existing_data(db):
        print("Seed data already exists. Skipping...")
        print("Run 'main.py' to interact with existing data.")
        return False
    
    print("Creating vector index...")
    index = create_vector_index(db)
    
    # Create Agent
    print("Creating Agent...")
    agent = db.records.create(label="AGENT", data=AGENT_DATA)
    print(f"  Created agent: {agent.id}")
    
    # Create Concepts
    print("Creating Concepts...")
    concepts = []
    for concept_data in CONCEPT_DATA:
        concept = db.records.create(label="CONCEPT", data=concept_data)
        concepts.append(concept)
        print(f"  Created concept: {concept_data['name']}")
    
    # Create Memories with bidirectional relationships
    print("\nCreating Memories and relationships...")
    memories = []
    concept_map = {
        "requirement": concepts[0],  # REST API
        "history": concepts[3],       # project timeline
        "constraint": concepts[2],    # database integration
        "timeline": concepts[3],      # project timeline
        "preference": concepts[0],    # REST API
        "feedback": concepts[5],      # code quality
        "resource": concepts[4],      # team capacity
        "decision": concepts[2],      # database integration
    }
    
    for i, memory_data in enumerate(MEMORY_DATA):
        memory = db.records.create(label="MEMORY", data=memory_data)
        memories.append(memory)
        
        # Attach to Agent (HAS_MEMORY relationship)
        db.records.attach(source=agent, target=memory, options={"type": "HAS_MEMORY"})
        
        # Attach to related Concept (ABOUT relationship)
        memory_type = memory_data['type']
        if memory_type in concept_map:
            db.records.attach(source=memory, target=concept_map[memory_type], options={"type": "ABOUT"})
        
        print(f"  Memory {i+1}/10: {memory_data['content'][:50]}...")
    
    # Create Task Steps with USED relationships
    print("\nCreating Task Steps...")
    task_step_memories = [
        [0, 5],        # Step 1: Analyze requirements (memories 0, 5)
        [2, 8],        # Step 2: Design database (memories 2, 8)
        [0, 1, 4],     # Step 3: Implement auth (memories 0, 1, 4)
        [0, 5, 6],     # Step 4: Create API (memories 0, 5, 6)
        [3, 9],        # Step 5: Testing (memories 3, 9)
    ]
    
    tasks = []
    for i, task_data in enumerate(TASK_STEPS_DATA):
        task = db.records.create(label="TASK_STEP", data=task_data)
        tasks.append(task)
        
        # Attach memories used by this task (USED relationship)
        for memory_idx in task_step_memories[i]:
            memory = memories[memory_idx]
            db.records.attach(source=task, target=memory, options={"type": "USED"})
        
        print(f"  Task {i+1}: {task_data['action']} (used {len(task_step_memories[i])} memories)")
    
    print("\n=== Seed Complete ===")
    print(f"Created: 1 agent, {len(memories)} memories, {len(tasks)} tasks, {len(concepts)} concepts")
    print(f"Relationships: AGENT→MEMORY (10), MEMORY→CONCEPT (8), TASK→MEMORY (17)")
    print("\nRun 'python main.py' to query the bidirectional relationships.")
    
    return True


if __name__ == "__main__":
    api_token = os.getenv("RUSHDB_API_TOKEN")
    
    if not api_token:
        print("Error: RUSHDB_API_TOKEN not found in environment.")
        print("Copy .env.example to .env and add your API token.")
        sys.exit(1)
    
    db = RushDB(api_token)
    seed(db)
