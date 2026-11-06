#!/usr/bin/env python3
"""
Seed script for entity clustering tutorial.
Creates a synthetic organizational network with employees, teams, projects, and skills.
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker
from dotenv import load_dotenv

from rushdb import RushDB

fake = Faker()
Faker.seed(42)
random.seed(42)

load_dotenv()

DEPARTMENTS = ["Engineering", "Marketing", "Sales", "Operations", "HR", "Finance"]
SKILL_CATEGORIES = {
    "Engineering": ["Python", "TypeScript", "Rust", "Go", "Kubernetes", "AWS", "Docker"],
    "Marketing": ["SEO", "Content", "Analytics", "PPC", "Social Media", "Email"],
    "Sales": ["Negotiation", "CRM", "Prospecting", "Closing", "Presentation"],
    "Operations": ["Logistics", "Process Optimization", "Supply Chain", "Quality Control"],
    "HR": ["Recruiting", "Onboarding", "Performance", "Compensation", "Training"],
    "Finance": ["Accounting", "Forecasting", "Compliance", "Audit", "Tax"]
}

PROJECT_TYPES = [
    "Platform Migration", "Customer Portal", "Data Pipeline", 
    "Mobile App", "Analytics Dashboard", "Security Audit",
    "API Gateway", "Machine Learning", "DevOps Automation"
]


def check_data_exists() -> bool:
    """Check if data has already been seeded."""
    db = RushDB(os.getenv("RUSHDB_API_KEY"))
    try:
        result = db.records.find({"labels": ["EMPLOYEE"], "limit": 1})
        return result.total > 0
    except Exception:
        return False
    finally:
        del db


def generate_employees(count: int = 150) -> list[dict]:
    """Generate employee records."""
    employees = []
    for i in range(count):
        dept = random.choice(DEPARTMENTS)
        employee = {
            "employeeId": f"EMP-{1000 + i}",
            "name": fake.name(),
            "email": fake.unique.email(),
            "department": dept,
            "title": fake.job(),
            "hireDate": fake.date_between(start_date="-5y", end_date="today").isoformat(),
            "performanceScore": round(random.uniform(3.0, 5.0), 2),
            "salaryBand": random.randint(50, 200) * 1000
        }
        employees.append(employee)
    return employees


def generate_teams(count: int = 40) -> list[dict]:
    """Generate team records."""
    teams = []
    for i in range(count):
        dept = random.choice(DEPARTMENTS)
        team = {
            "teamId": f"TEAM-{2000 + i}",
            "name": f"{dept} Team {i % 5 + 1}",
            "department": dept,
            "budget": random.randint(100000, 2000000),
            "established": fake.date_between(start_date="-10y", end_date="-1y").isoformat()
        }
        teams.append(team)
    return teams


def generate_projects(count: int = 25) -> list[dict]:
    """Generate project records."""
    projects = []
    for i in range(count):
        project = {
            "projectId": f"PROJ-{3000 + i}",
            "name": random.choice(PROJECT_TYPES),
            "status": random.choice(["Active", "Completed", "Planning", "On Hold"]),
            "startDate": fake.date_between(start_date="-2y", end_date="today").isoformat(),
            "priority": random.choice(["Critical", "High", "Medium", "Low"]),
            "budget": random.randint(50000, 500000)
        }
        if project["status"] == "Completed":
            project["endDate"] = fake.date_between(
                start_date=datetime.fromisoformat(project["startDate"]),
                end_date="today"
            ).isoformat()
        projects.append(project)
    return projects


def generate_skills() -> list[dict]:
    """Generate skill records."""
    skills = []
    skill_id = 4000
    for category, skill_list in SKILL_CATEGORIES.items():
        for skill in skill_list:
            skills.append({
                "skillId": f"SKILL-{skill_id}",
                "name": skill,
                "category": category,
                "proficiency": random.choice(["Beginner", "Intermediate", "Advanced", "Expert"])
            })
            skill_id += 1
    return skills


def seed_database():
    """Seed RushDB with organizational network data."""
    print("Seeding entities...")
    
    db = RushDB(os.getenv("RUSHDB_API_KEY"))
    
    employees = generate_employees(150)
    teams = generate_teams(40)
    projects = generate_projects(25)
    skills = generate_skills()
    
    print(f"  Creating {len(employees)} EMPLOYEE records...")
    created_employees = db.records.create_many(label="EMPLOYEE", data=employees)
    print(f"  ✓ Created {len(employees)} EMPLOYEE records")
    
    print(f"  Creating {len(teams)} TEAM records...")
    created_teams = db.records.create_many(label="TEAM", data=teams)
    print(f"  ✓ Created {len(teams)} TEAM records")
    
    print(f"  Creating {len(projects)} PROJECT records...")
    created_projects = db.records.create_many(label="PROJECT", data=projects)
    print(f"  ✓ Created {len(projects)} PROJECT records")
    
    print(f"  Creating {len(skills)} SKILL records...")
    created_skills = db.records.create_many(label="SKILL", data=skills)
    print(f"  ✓ Created {len(skills)} SKILL records")
    
    print("  Creating relationships...")
    _create_relationships(db, created_employees, created_teams, created_projects, created_skills)
    
    print("Seeding complete.\n")
    del db


def _create_relationships(db, employees, teams, projects, skills):
    """Create relationships between entities."""
    
    tx = db.transactions.begin()
    rel_count = 0
    
    for employee in employees[:100]:
        if random.random() < 0.7:
            team = random.choice(teams)
            try:
                db.records.attach(
                    source=employee,
                    target=team,
                    options={"type": "MEMBER_OF", "direction": "out"},
                    transaction=tx
                )
                rel_count += 1
            except Exception:
                pass
    
    for team in teams:
        for project in projects[:5]:
            if random.random() < 0.5:
                try:
                    db.records.attach(
                        source=team,
                        target=project,
                        options={"type": "WORKS_ON", "direction": "out"},
                        transaction=tx
                    )
                    rel_count += 1
                except Exception:
                    pass
    
    for employee in employees:
        employee_skills = random.sample(skills, random.randint(1, 4))
        for skill in employee_skills:
            try:
                db.records.attach(
                    source=employee,
                    target=skill,
                    options={"type": "HAS_SKILL", "direction": "out"},
                    transaction=tx
                )
                rel_count += 1
            except Exception:
                pass
    
    tx.commit()
    print(f"  ✓ Created {rel_count} relationship links")


def save_mock_data():
    """Save mock data to JSON file for reference."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    data = {
        "employees": generate_employees(150),
        "teams": generate_teams(40),
        "projects": generate_projects(25),
        "skills": generate_skills()
    }
    
    with open(data_dir / "entities.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"  ✓ Saved mock data to {data_dir / 'entities.json'}")


if __name__ == "__main__":
    if check_data_exists():
        print("Data already exists. Skipping seed.")
        print("Run 'python main.py' to execute clustering algorithms.")
    else:
        seed_database()
        save_mock_data()
