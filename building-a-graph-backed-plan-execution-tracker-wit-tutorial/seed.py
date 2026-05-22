"""
Seed script: Creates sample plans with milestones and cross-dependencies.

This demonstrates a realistic project execution scenario where:
- Milestones depend on each other across plans
- Some tasks are shared across milestones
- Status propagation matters for tracking
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env")

db = RushDB(API_KEY)


def clear_existing_data():
    """Remove any previously seeded data by label."""
    labels_to_clear = ["PLAN", "MILESTONE", "TASK", "TEAM"]
    for label in labels_to_clear:
        existing = db.records.find({"labels": [label]})
        if existing.data:
            db.records.delete({"labels": [label], "where": {}})
            print(f"  Cleared {len(existing.data)} existing {label} records")


def create_team_members():
    """Create team members who will be assigned tasks."""
    print("\n[1/6] Creating team members...")
    
    team_members = []
    members_data = [
        {"name": "Alice Chen", "role": "Engineering Lead", "team": "Platform"},
        {"name": "Bob Martinez", "role": "Backend Engineer", "team": "Platform"},
        {"name": "Carol Williams", "role": "Frontend Engineer", "team": "UI"},
        {"name": "David Kim", "role": "DevOps Engineer", "team": "Infrastructure"},
        {"name": "Eva Johnson", "role": "QA Lead", "team": "Quality"},
    ]
    
    for member_data in members_data:
        member = db.records.create(label="TEAM", data=member_data)
        team_members.append(member)
        print(f"  Created: {member['name']} ({member['role']})")
    
    return team_members


def create_platform_migration_plan(team_members):
    """Create a complex plan with interdependent milestones."""
    print("\n[2/6] Creating Platform Migration Plan...")
    
    plan = db.records.create(
        label="PLAN",
        data={
            "name": "Platform Migration v2.0",
            "description": "Migrate legacy system to new microservices architecture",
            "status": "in_progress",
            "priority": "high",
            "start_date": "2024-01-15",
            "target_date": "2024-03-30"
        }
    )
    print(f"  Created plan: {plan['name']}")
    
    # Create milestones in dependency order
    milestone_definitions = [
        {
            "name": "Infrastructure Setup",
            "description": "Set up Kubernetes clusters and networking",
            "order": 1,
            "status": "completed",
            "dependencies": []
        },
        {
            "name": "Database Migration",
            "description": "Migrate PostgreSQL to new schema and setup replication",
            "order": 2,
            "status": "completed",
            "dependencies": ["Infrastructure Setup"]
        },
        {
            "name": "API Gateway Development",
            "description": "Build and deploy new API gateway with rate limiting",
            "order": 3,
            "status": "in_progress",
            "dependencies": ["Infrastructure Setup"]
        },
        {
            "name": "Auth Service Implementation",
            "description": "Implement OAuth2 and JWT-based authentication",
            "order": 4,
            "status": "in_progress",
            "dependencies": ["API Gateway Development", "Database Migration"]
        },
        {
            "name": "Core Service Development",
            "description": "Develop the three core microservices",
            "order": 5,
            "status": "pending",
            "dependencies": ["Auth Service Implementation"]
        },
        {
            "name": "Integration Testing",
            "description": "End-to-end integration testing across all services",
            "order": 6,
            "status": "pending",
            "dependencies": ["Core Service Development", "Auth Service Implementation"]
        },
        {
            "name": "Performance Benchmarking",
            "description": "Load testing and performance optimization",
            "order": 7,
            "status": "pending",
            "dependencies": ["Integration Testing"]
        },
        {
            "name": "Production Deployment",
            "description": "Blue-green deployment to production",
            "order": 8,
            "status": "pending",
            "dependencies": ["Performance Benchmarking"]
        }
    ]
    
    created_milestones = {}
    
    for milestone_def in milestone_definitions:
        milestone = db.records.create(
            label="MILESTONE",
            data={
                "name": milestone_def["name"],
                "description": milestone_def["description"],
                "order": milestone_def["order"],
                "status": milestone_def["status"]
            }
        )
        
        # Link milestone to plan
        db.records.attach(
            source=plan,
            target=milestone,
            options={"type": "HAS_MILESTONE", "direction": "out"}
        )
        
        created_milestones[milestone['name']] = milestone
        print(f"  Created milestone: {milestone['name']} (status: {milestone['status']})")
        
        # Create tasks for each milestone
        create_tasks_for_milestone(milestone, team_members)
    
    # Now create dependencies between milestones
    print("\n[3/6] Creating milestone dependencies...")
    
    for milestone_def in milestone_definitions:
        milestone = created_milestones[milestone_def["name"]]
        
        for dep_name in milestone_def["dependencies"]:
            if dep_name in created_milestones:
                dep_milestone = created_milestones[dep_name]
                db.records.attach(
                    source=milestone,
                    target=dep_milestone,
                    options={"type": "DEPENDS_ON", "direction": "out"}
                )
                print(f"  {milestone['name']} depends on {dep_milestone['name']}")
    
    return plan, created_milestones


def create_tasks_for_milestone(milestone, team_members):
    """Create tasks for a milestone with assigned team members."""
    
    # Map milestone names to task definitions
    task_templates = {
        "Infrastructure Setup": [
            {"name": "Provision Kubernetes clusters", "status": "completed", "estimated_hours": 40},
            {"name": "Configure CNI networking", "status": "completed", "estimated_hours": 16},
            {"name": "Set up monitoring stack", "status": "completed", "estimated_hours": 24},
        ],
        "Database Migration": [
            {"name": "Design new schema", "status": "completed", "estimated_hours": 32},
            {"name": "Write migration scripts", "status": "completed", "estimated_hours": 24},
            {"name": "Setup replication", "status": "completed", "estimated_hours": 16},
        ],
        "API Gateway Development": [
            {"name": "Design gateway API", "status": "completed", "estimated_hours": 20},
            {"name": "Implement rate limiting", "status": "in_progress", "estimated_hours": 32},
            {"name": "Add request validation", "status": "pending", "estimated_hours": 16},
        ],
        "Auth Service Implementation": [
            {"name": "Implement OAuth2 flow", "status": "in_progress", "estimated_hours": 40},
            {"name": "Build JWT generation", "status": "in_progress", "estimated_hours": 24},
            {"name": "Create token refresh logic", "status": "pending", "estimated_hours": 16},
        ],
        "Core Service Development": [
            {"name": "Develop User Service", "status": "pending", "estimated_hours": 80},
            {"name": "Develop Order Service", "status": "pending", "estimated_hours": 80},
            {"name": "Develop Notification Service", "status": "pending", "estimated_hours": 60},
        ],
        "Integration Testing": [
            {"name": "Write integration test suite", "status": "pending", "estimated_hours": 48},
            {"name": "Test service mesh communication", "status": "pending", "estimated_hours": 24},
            {"name": "Verify data consistency", "status": "pending", "estimated_hours": 32},
        ],
        "Performance Benchmarking": [
            {"name": "Design load test scenarios", "status": "pending", "estimated_hours": 24},
            {"name": "Execute stress tests", "status": "pending", "estimated_hours": 40},
            {"name": "Optimize bottlenecks", "status": "pending", "estimated_hours": 48},
        ],
        "Production Deployment": [
            {"name": "Prepare deployment manifests", "status": "pending", "estimated_hours": 16},
            {"name": "Configure production environment", "status": "pending", "estimated_hours": 24},
            {"name": "Execute blue-green deployment", "status": "pending", "estimated_hours": 32},
        ],
    }
    
    tasks_data = task_templates.get(milestone['name'], [])
    
    for i, task_data in enumerate(tasks_data):
        # Assign to a team member (round-robin)
        assignee = team_members[i % len(team_members)]
        task_data['assignee_id'] = assignee.id
        task_data['assignee_name'] = assignee['name']
        
        task = db.records.create(label="TASK", data=task_data)
        
        # Link task to milestone
        db.records.attach(
            source=milestone,
            target=task,
            options={"type": "HAS_TASK", "direction": "out"}
        )


def create_ui_redesign_plan():
    """Create a second plan to demonstrate cross-plan dependencies."""
    print("\n[4/6] Creating UI Redesign Plan...")
    
    plan = db.records.create(
        label="PLAN",
        data={
            "name": "UI Redesign 2024",
            "description": "Complete redesign of customer-facing UI",
            "status": "planning",
            "priority": "medium",
            "start_date": "2024-02-01",
            "target_date": "2024-04-15"
        }
    )
    print(f"  Created plan: {plan['name']}")
    
    milestones = [
        {"name": "Design System Creation", "order": 1, "status": "in_progress",
         "description": "Create reusable component library and design tokens"},
        {"name": "Prototype Development", "order": 2, "status": "pending",
         "description": "Build interactive prototypes for key user flows",
         "dependencies": ["Design System Creation"]},
        {"name": "User Testing", "order": 3, "status": "pending",
         "description": "Conduct usability testing with target users",
         "dependencies": ["Prototype Development"]},
        {"name": "Component Implementation", "order": 4, "status": "pending",
         "description": "Implement all UI components in React",
         "dependencies": ["Design System Creation", "Prototype Development"]},
        {"name": "Final QA", "order": 5, "status": "pending",
         "description": "Accessibility and cross-browser testing",
         "dependencies": ["Component Implementation", "User Testing"]},
    ]
    
    created_milestones = {}
    
    for ms in milestones:
        milestone = db.records.create(
            label="MILESTONE",
            data={
                "name": ms["name"],
                "description": ms["description"],
                "order": ms["order"],
                "status": ms["status"]
            }
        )
        
        db.records.attach(
            source=plan,
            target=milestone,
            options={"type": "HAS_MILESTONE", "direction": "out"}
        )
        
        created_milestones[ms['name']] = milestone
        print(f"  Created milestone: {milestone['name']}")
        
        # Create basic tasks
        for j in range(3):
            task = db.records.create(
                label="TASK",
                data={
                    "name": f"Task {j + 1} for {milestone['name']}",
                    "status": "pending",
                    "estimated_hours": 16 + (j * 8)
                }
            )
            db.records.attach(
                source=milestone,
                target=task,
                options={"type": "HAS_TASK", "direction": "out"}
            )
    
    # Create internal dependencies
    for ms in milestones:
        milestone = created_milestones[ms['name']]
        for dep_name in ms.get('dependencies', []):
            if dep_name in created_milestones:
                db.records.attach(
                    source=milestone,
                    target=created_milestones[dep_name],
                    options={"type": "DEPENDS_ON", "direction": "out"}
                )
                print(f"  {milestone['name']} depends on {dep_name}")
    
    return plan


def create_cross_plan_dependency(platform_plan, ui_plan):
    """Demonstrate cross-plan milestone dependencies."""
    print("\n[5/6] Creating cross-plan dependency...")
    
    # UI redesign depends on the API Gateway from platform migration
    api_gateway = db.records.find({
        "labels": ["MILESTONE"],
        "where": {"name": "API Gateway Development"}
    })
    
    prototype_dev = db.records.find({
        "labels": ["MILESTONE"],
        "where": {"name": "Prototype Development", "PLAN": {"name": "UI Redesign 2024"}}
    })
    
    if api_gateway.data and prototype_dev.data:
        db.records.attach(
            source=prototype_dev.data[0],
            target=api_gateway.data[0],
            options={"type": "DEPENDS_ON", "direction": "out"}
        )
        print(f"  Cross-plan: 'Prototype Development' depends on 'API Gateway Development'")


def print_summary():
    """Print seeding summary."""
    print("\n[6/6] Summary...")
    
    plans = db.records.find({"labels": ["PLAN"]})
    milestones = db.records.find({"labels": ["MILESTONE"]})
    tasks = db.records.find({"labels": ["TASK"]})
    
    print(f"  Total Plans: {len(plans.data)}")
    print(f"  Total Milestones: {len(milestones.data)}")
    print(f"  Total Tasks: {len(tasks.data)}")
    
    # Count dependencies
    dependencies = db.records.find({"labels": ["MILESTONE"], "where": {"DEPENDS_ON": {"$exists": True}}})
    print(f"  Milestones with dependencies: {len(dependencies.data)}")


def main():
    print("=" * 60)
    print("RushDB Plan Execution Tracker - Data Seeding")
    print("=" * 60)
    
    # Check for existing data
    existing_plans = db.records.find({"labels": ["PLAN"]})
    if existing_plans.data:
        print(f"\nFound {len(existing_plans.data)} existing plans.")
        response = input("Clear existing data and reseed? (y/N): ")
        if response.lower() == 'y':
            clear_existing_data()
        else:
            print("Skipping seed. Existing data will be used.")
            return
    
    # Create data
    team_members = create_team_members()
    platform_plan, platform_milestones = create_platform_migration_plan(team_members)
    ui_plan = create_ui_redesign_plan()
    create_cross_plan_dependency(platform_plan, ui_plan)
    print_summary()
    
    print("\n" + "=" * 60)
    print("Seeding complete! Run 'python main.py' to explore the data.")
    print("=" * 60)


if __name__ == "__main__":
    main()
