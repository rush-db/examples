#!/usr/bin/env python3
"""
Seed script for Context Recycling Tutorial.

Creates a company knowledge graph with:
- 1 Company (TechCorp)
- 4 Employees with roles and departments
- 3 Projects with statuses and deadlines
- 8 Documents (specs, roadmaps, reports)

Run this once before executing main.py.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import RushDB
from rushdb import RushDB

fake = Faker()
Faker.seed(42)
random.seed(42)

# =============================================================================
# Domain Data Templates
# =============================================================================

DEPARTMENTS = ["Engineering", "Product", "Design", "Data Science"]
ROLES = {
    "Engineering": ["Senior Engineer", "Staff Engineer", "Tech Lead", "Backend Developer", "Frontend Developer"],
    "Product": ["Product Manager", "Technical PM", "Product Owner"],
    "Design": ["Senior Designer", "UX Researcher", "UI Designer"],
    "Data Science": ["ML Engineer", "Data Analyst", "Research Scientist"],
}

PROJECT_TEMPLATES = [
    {
        "name": "AI Platform",
        "status": "active",
        "description": "Building next-generation AI-powered platform features",
        "documents": [
            {"title": "AI Platform Architecture v2", "type": "spec", "content": "Multi-tenant ML inference infrastructure with auto-scaling."},
            {"title": "Q1 Roadmap", "type": "roadmap", "content": "Ship recommendation engine by March, fraud detection by May."},
            {"title": "Model Performance Report", "type": "report", "content": "Current accuracy 94.2%, latency p99 < 100ms."},
        ],
    },
    {
        "name": "Mobile App Rewrite",
        "status": "active",
        "description": "Complete rewrite of mobile app using React Native",
        "documents": [
            {"title": "Mobile Architecture Spec", "type": "spec", "content": "Cross-platform architecture with native module bridges."},
            {"title": "Feature Timeline", "type": "roadmap", "content": "Beta release in 8 weeks, GA in 12 weeks."},
            {"title": "User Research Summary", "type": "report", "content": "78% of users want offline mode, 65% want dark mode."},
        ],
    },
    {
        "name": "Legacy API Migration",
        "status": "planning",
        "description": "Migrating from REST to GraphQL and modernizing auth",
        "documents": [
            {"title": "Migration Strategy", "type": "spec", "content": "Strangler fig pattern with dual-write period."},
            {"title": "Deprecation Timeline", "type": "roadmap", "content": "Phase out v1 endpoints over 6 months."},
        ],
    },
]

# =============================================================================
# Seed Function
# =============================================================================

def seed_database():
    """Seed RushDB with company knowledge graph."""
    
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("❌ Error: RUSHDB_API_KEY not found in environment")
        print("   Please copy .env.example to .env and add your API key")
        sys.exit(1)
    
    print("🌱 Seeding RushDB with company knowledge graph...")
    
    db = RushDB(api_key)
    
    # Check for existing data
    existing_company = db.records.find({"labels": ["COMPANY"], "where": {"name": "TechCorp"}})
    if existing_company.total > 0:
        print("⚠️  TechCorp already exists. Skipping seed (idempotent).")
        print("   Delete existing records to re-seed.")
        return
    
    with db.transactions.begin() as tx:
        # Create the company
        company = db.records.create(
            label="COMPANY",
            data={
                "name": "TechCorp",
                "founded": 2018,
                "hq": "San Francisco",
                "employees_count": 4,
            },
            transaction=tx,
        )
        print(f"   ✅ Created company: {company['name']}")
        
        # Create employees
        employees = []
        for i, dept in enumerate(DEPARTMENTS[:4]):
            role = random.choice(ROLES[dept])
            employee = db.records.create(
                label="EMPLOYEE",
                data={
                    "name": fake.name(),
                    "email": fake.company_email(),
                    "role": role,
                    "department": dept,
                    "joined_at": fake.date_between(start_date="-3y", end_date="-6m").isoformat(),
                },
                transaction=tx,
            )
            employees.append(employee)
            
            # Link employee to company
            db.records.attach(
                source=employee,
                target=company,
                options={"type": "MEMBER_OF"},
                transaction=tx,
            )
        
        print(f"   ✅ Created {len(employees)} employees")
        
        # Create projects and documents
        projects = []
        docs_created = 0
        
        for proj_template in PROJECT_TEMPLATES:
            # Assign 1-2 employees to each project
            proj_employees = random.sample(employees, k=random.randint(1, 2))
            
            # Create deadline 1-6 months from now
            deadline = datetime.now() + timedelta(days=random.randint(30, 180))
            
            project = db.records.create(
                label="PROJECT",
                data={
                    "name": proj_template["name"],
                    "status": proj_template["status"],
                    "description": proj_template["description"],
                    "deadline": deadline.isoformat(),
                    "priority": random.choice(["high", "medium", "low"]),
                },
                transaction=tx,
            )
            projects.append(project)
            
            # Link company to project
            db.records.attach(
                source=company,
                target=project,
                options={"type": "HAS"},
                transaction=tx,
            )
            
            # Link employees to project
            for emp in proj_employees:
                db.records.attach(
                    source=emp,
                    target=project,
                    options={"type": "WORKS_ON"},
                    transaction=tx,
                )
            
            # Create documents
            for doc_template in proj_template["documents"]:
                doc = db.records.create(
                    label="DOCUMENT",
                    data={
                        "title": doc_template["title"],
                        "type": doc_template["type"],
                        "content": doc_template["content"],
                        "created_at": fake.date_between(start_date="-6m", end_date="-1d").isoformat(),
                    },
                    transaction=tx,
                )
                docs_created += 1
                
                # Link project to document
                db.records.attach(
                    source=project,
                    target=doc,
                    options={"type": "HAS_DOC"},
                    transaction=tx,
                )
                
                # Link primary author
                author = random.choice(proj_employees)
                db.records.attach(
                    source=doc,
                    target=author,
                    options={"type": "AUTHORED_BY"},
                    transaction=tx,
                )
        
        print(f"   ✅ Created {len(projects)} projects with {docs_created} documents")
    
    print("\n✅ Seeding complete! Ready for context recycling demo.")

# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    seed_database()
