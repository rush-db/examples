"""
Seed script for Context Recycling demonstration.

Creates a realistic knowledge graph representing a software company's
projects, team members, technologies, and dependencies.

This script is idempotent - safe to run multiple times.
"""

import os
import random
import time
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env and add your key.")

db = RushDB(API_KEY)

# Realistic seed data
PROJECTS = [
    {"name": "Project Atlas", "description": "Core infrastructure modernization initiative", "status": "active", "priority": "high"},
    {"name": "Project Beacon", "description": "Customer-facing analytics dashboard", "status": "active", "priority": "high"},
    {"name": "Project Chronos", "description": "Time-series monitoring system", "status": "active", "priority": "medium"},
    {"name": "Project Delta", "description": "Legacy system migration to cloud", "status": "paused", "priority": "low"},
    {"name": "Project Echo", "description": "Real-time collaboration features", "status": "active", "priority": "high"},
    {"name": "Project Foundry", "description": "Internal developer tools platform", "status": "active", "priority": "medium"},
    {"name": "Project Ganymede", "description": "Mobile application redesign", "status": "active", "priority": "medium"},
    {"name": "Project Helios", "description": "API gateway and rate limiting", "status": "completed", "priority": "low"},
]

TEAM_MEMBERS = [
    {"name": "Alice Chen", "role": "Tech Lead", "department": "Platform", "email": "alice.chen@company.com"},
    {"name": "Bob Martinez", "role": "Senior Engineer", "department": "Backend", "email": "bob.martinez@company.com"},
    {"name": "Carol Williams", "role": "Engineering Manager", "department": "Product", "email": "carol.williams@company.com"},
    {"name": "David Kim", "role": "Staff Engineer", "department": "Infrastructure", "email": "david.kim@company.com"},
    {"name": "Eva Singh", "role": "Senior Engineer", "department": "Frontend", "email": "eva.singh@company.com"},
    {"name": "Frank Johnson", "role": "DevOps Engineer", "department": "Infrastructure", "email": "frank.johnson@company.com"},
    {"name": "Grace Lee", "role": "Data Engineer", "department": "Analytics", "email": "grace.lee@company.com"},
    {"name": "Henry Brown", "role": "Security Engineer", "department": "Security", "email": "henry.brown@company.com"},
    {"name": "Iris Wang", "role": "Product Manager", "department": "Product", "email": "iris.wang@company.com"},
    {"name": "Jack Taylor", "role": "QA Lead", "department": "Quality", "email": "jack.taylor@company.com"},
    {"name": "Kate Anderson", "role": "Frontend Engineer", "department": "Frontend", "email": "kate.anderson@company.com"},
    {"name": "Leo Garcia", "role": "Backend Engineer", "department": "Backend", "email": "leo.garcia@company.com"},
]

TECHNOLOGIES = [
    {"name": "Python", "category": "Language", "version": "3.11"},
    {"name": "TypeScript", "category": "Language", "version": "5.2"},
    {"name": "Go", "category": "Language", "version": "1.21"},
    {"name": "Rust", "category": "Language", "version": "1.72"},
    {"name": "PostgreSQL", "category": "Database", "version": "15"},
    {"name": "Redis", "category": "Cache", "version": "7.2"},
    {"name": "Kafka", "category": "Messaging", "version": "3.6"},
    {"name": "Kubernetes", "category": "Orchestration", "version": "1.28"},
    {"name": "React", "category": "Framework", "version": "18.2"},
    {"name": "FastAPI", "category": "Framework", "version": "0.104"},
    {"name": "GraphQL", "category": "API", "version": "16"},
    {"name": "gRPC", "category": "API", "version": "1.59"},
    {"name": "Terraform", "category": "IaC", "version": "1.6"},
    {"name": "Prometheus", "category": "Monitoring", "version": "2.48"},
    {"name": "RushDB", "category": "Database", "version": "2.0"},
]

# Project-Technology assignments (realistic mappings)
PROJECT_TECH_ASSIGNMENTS = {
    "Project Atlas": ["Python", "Go", "PostgreSQL", "Redis", "Kafka", "Kubernetes", "Terraform", "Prometheus", "RushDB"],
    "Project Beacon": ["TypeScript", "React", "GraphQL", "PostgreSQL", "Redis", "Kafka"],
    "Project Chronos": ["Python", "Go", "Kafka", "PostgreSQL", "Prometheus", "RushDB"],
    "Project Delta": ["Python", "Terraform", "Kubernetes", "PostgreSQL"],
    "Project Echo": ["TypeScript", "React", "GraphQL", "gRPC", "Redis", "Kafka"],
    "Project Foundry": ["Go", "Rust", "Kubernetes", "Terraform"],
    "Project Ganymede": ["TypeScript", "React", "GraphQL", "Redis"],
    "Project Helios": ["Go", "gRPC", "Redis", "PostgreSQL", "Kubernetes"],
}

# Project-Team assignments (realistic team compositions)
PROJECT_MEMBER_ASSIGNMENTS = {
    "Project Atlas": ["Alice Chen", "Bob Martinez", "David Kim", "Frank Johnson", "Henry Brown"],
    "Project Beacon": ["Carol Williams", "Eva Singh", "Kate Anderson", "Grace Lee"],
    "Project Chronos": ["Alice Chen", "Grace Lee", "Leo Garcia"],
    "Project Delta": ["David Kim", "Frank Johnson"],
    "Project Echo": ["Carol Williams", "Eva Singh", "Kate Anderson", "Jack Taylor", "Leo Garcia"],
    "Project Foundry": ["Alice Chen", "David Kim", "Frank Johnson", "Henry Brown"],
    "Project Ganymede": ["Eva Singh", "Kate Anderson", "Iris Wang", "Jack Taylor"],
    "Project Helios": ["Bob Martinez", "Leo Garcia", "Henry Brown"],
}

# Project dependencies (realistic)
PROJECT_DEPENDENCIES = {
    "Project Atlas": [],  # Foundation project, no dependencies
    "Project Beacon": ["Project Atlas", "Project Chronos"],
    "Project Chronos": ["Project Atlas"],
    "Project Delta": ["Project Atlas"],
    "Project Echo": ["Project Atlas", "Project Beacon"],
    "Project Foundry": ["Project Atlas"],
    "Project Ganymede": ["Project Echo"],
    "Project Helios": ["Project Atlas"],
}


def cleanup_existing_data():
    """Remove any existing records from previous runs."""
    print("\nCleaning up existing data...")
    
    # Delete in order respecting relationships
    for label in ["WORKS_ON", "USES", "DEPENDS_ON", "PROJECT", "TEAM_MEMBER", "TECHNOLOGY"]:
        try:
            db.records.delete_many({"labels": [label], "where": {}})
        except Exception:
            pass  # Ignore if no records exist
    
    print("  ✓ Cleanup complete")


def seed_data():
    """Main seeding function."""
    print("\n" + "="*60)
    print("SEEDING KNOWLEDGE GRAPH")
    print("="*60)
    
    cleanup_existing_data()
    
    # Track created records for relationship creation
    project_records = {}
    member_records = {}
    tech_records = {}
    
    # Create Projects
    print("\nCreating PROJECT records...")
    for i, project in enumerate(PROJECTS, 1):
        record = db.records.create(
            label="PROJECT",
            data={
                "name": project["name"],
                "description": project["description"],
                "status": project["status"],
                "priority": project["priority"],
                "slug": project["name"].lower().replace(" ", "-"),
            }
        )
        project_records[project["name"]] = record
        if i % 4 == 0:
            print(f"  ✓ Created {i}/{len(PROJECTS)} projects")
    print(f"  ✓ Created {len(PROJECTS)} PROJECT records")
    
    # Create Team Members
    print("\nCreating TEAM_MEMBER records...")
    for i, member in enumerate(TEAM_MEMBERS, 1):
        record = db.records.create(
            label="TEAM_MEMBER",
            data={
                "name": member["name"],
                "role": member["role"],
                "department": member["department"],
                "email": member["email"],
                "slug": member["name"].lower().replace(" ", "-"),
            }
        )
        member_records[member["name"]] = record
        if i % 4 == 0:
            print(f"  ✓ Created {i}/{len(TEAM_MEMBERS)} members")
    print(f"  ✓ Created {len(TEAM_MEMBERS)} TEAM_MEMBER records")
    
    # Create Technologies
    print("\nCreating TECHNOLOGY records...")
    for i, tech in enumerate(TECHNOLOGIES, 1):
        record = db.records.create(
            label="TECHNOLOGY",
            data={
                "name": tech["name"],
                "category": tech["category"],
                "version": tech["version"],
                "slug": tech["name"].lower(),
            }
        )
        tech_records[tech["name"]] = record
        if i % 5 == 0:
            print(f"  ✓ Created {i}/{len(TECHNOLOGIES)} technologies")
    print(f"  ✓ Created {len(TECHNOLOGIES)} TECHNOLOGY records")
    
    # Create relationships using transactions
    print("\nCreating relationships...")
    
    relationships_created = 0
    
    with db.transactions.begin() as tx:
        # Project -> Team Member (WORKS_ON)
        works_on_count = 0
        for project_name, members in PROJECT_MEMBER_ASSIGNMENTS.items():
            project = project_records[project_name]
            for member_name in members:
                member = member_records[member_name]
                db.records.attach(
                    source=project,
                    target=member,
                    options={"type": "WORKS_ON", "direction": "out"},
                    transaction=tx
                )
                works_on_count += 1
        print(f"  ✓ Created {works_on_count} WORKS_ON relationships")
        relationships_created += works_on_count
        
        # Project -> Technology (USES)
        uses_count = 0
        for project_name, techs in PROJECT_TECH_ASSIGNMENTS.items():
            project = project_records[project_name]
            for tech_name in techs:
                tech = tech_records[tech_name]
                db.records.attach(
                    source=project,
                    target=tech,
                    options={"type": "USES", "direction": "out"},
                    transaction=tx
                )
                uses_count += 1
        print(f"  ✓ Created {uses_count} USES relationships")
        relationships_created += uses_count
        
        # Project -> Project Dependency (DEPENDS_ON)
        depends_count = 0
        for project_name, dependencies in PROJECT_DEPENDENCIES.items():
            project = project_records[project_name]
            for dep_name in dependencies:
                dep_project = project_records[dep_name]
                db.records.attach(
                    source=project,
                    target=dep_project,
                    options={"type": "DEPENDS_ON", "direction": "out"},
                    transaction=tx
                )
                depends_count += 1
        print(f"  ✓ Created {depends_count} DEPENDS_ON relationships")
        relationships_created += depends_count
    
    print(f"\n{'='*60}")
    print(f"SEEDING COMPLETE")
    print(f"  • {len(PROJECTS)} projects")
    print(f"  • {len(TEAM_MEMBERS)} team members")
    print(f"  • {len(TECHNOLOGIES)} technologies")
    print(f"  • {relationships_created} relationships")
    print(f"{'='*60}")
    
    return {
        "project_records": project_records,
        "member_records": member_records,
        "tech_records": tech_records,
    }


if __name__ == "__main__":
    seed_data()
    print("\nRun `python main.py` to see the context recycling demonstration.")
