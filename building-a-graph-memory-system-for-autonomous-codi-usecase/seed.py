#!/usr/bin/env python3
"""
Seed script for the graph memory system demo.

Creates a realistic codebase graph with:
- Files and functions (code entities)
- Bugs with root causes
- Investigation trails showing what was already checked
- Dependency relationships between code entities

This demonstrates the graph structure that enables efficient bug hunting
without re-reading the entire codebase each session.
"""

import os
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Mock data for the codebase
from data.mock_entities import (
    DIRECTORIES,
    FILES,
    FUNCTIONS,
    BUGS,
    HISTORICAL_INVESTIGATIONS,
)

# RushDB SDK
from rushdb import RushDB



def load_env():
    """Load environment variables."""
    load_dotenv()
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError(
            "RUSHDB_API_KEY not found in environment.\n"
            "Get your free API key at: https://app.rushdb.com\n"
            "Then add it to .env or export RUSHDB_API_KEY=your_key"
        )
    return api_key


def create_codebase_graph(db: RushDB) -> dict:
    """
    Creates the code entity graph: directories, files, and functions.
    """
    print("\n📁 Creating code entity records (files, functions, modules)...")
    
    created = {"directories": [], "files": [], "functions": []}
    
    # Create directories
    for i, directory in enumerate(DIRECTORIES):
        dir_record = db.records.create(
            label="DIRECTORY",
            data={
                "path": directory["path"],
                "description": directory["description"],
                "type": "directory",
            }
        )
        created["directories"].append(dir_record)
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(DIRECTORIES)} directories...")
    
    print(f"  ✓ Created {len(created['directories'])} directories")
    
    # Create files
    file_map = {}  # path -> record for linking
    for i, file in enumerate(FILES):
        file_record = db.records.create(
            label="FILE",
            data={
                "path": file["path"],
                "type": file["type"],
                "dir": file["dir"],
            }
        )
        created["files"].append(file_record)
        file_map[file["path"]] = file_record
        
        # Link file to its directory
        dir_record = created["directories"][
            next((j for j, d in enumerate(DIRECTORIES) if d["path"] == file["dir"]), 0)
        ]
        db.records.attach(
            source=file_record,
            target=dir_record,
            options={"type": "LOCATED_IN", "direction": "out"}
        )
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(FILES)} files...")
    
    print(f"  ✓ Created {len(created['files'])} files")
    
    # Create functions and link to their files
    for i, func in enumerate(FUNCTIONS):
        func_record = db.records.create(
            label="FUNCTION",
            data={
                "name": func["name"],
                "file": func["file"],
                "summary": func["summary"],
            }
        )
        created["functions"].append(func_record)
        
        # Link function to its defining file
        if func["file"] in file_map:
            db.records.attach(
                source=func_record,
                target=file_map[func["file"]],
                options={"type": "DEFINED_IN", "direction": "out"}
            )
        
        # Link to functions it calls
        for called_func_name in func["calls"]:
            called_func = next(
                (f for f in FUNCTIONS if f["name"] == called_func_name), None
            )
            if called_func:
                called_record = db.records.create(
                    label="FUNCTION",
                    data={
                        "name": called_func_name,
                        "file": called_func["file"],
                        "summary": called_func["summary"],
                    }
                )
                db.records.attach(
                    source=func_record,
                    target=called_record,
                    options={"type": "CALLS", "direction": "out"}
                )
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(FUNCTIONS)} functions...")
    
    print(f"  ✓ Created {len(created['functions'])} functions")
    
    return created


def create_bugs_and_investigations(db: RushDB, file_map: dict) -> dict:
    """
    Creates bugs with their root causes and investigation trails.
    """
    print("\n🐛 Creating bugs with dependency chains and investigation trails...")
    
    created = {"bugs": [], "investigations": [], "investigated_files": []}
    
    for i, bug in enumerate(BUGS):
        # Create the bug record
        bug_record = db.records.create(
            label="BUG",
            data={
                "id": bug["id"],
                "title": bug["title"],
                "severity": bug["severity"],
                "description": bug["description"],
            }
        )
        created["bugs"].append(bug_record)
        
        # Link to root cause file
        root_cause_file = file_map.get(bug["root_cause"]["file"])
        if root_cause_file:
            db.records.attach(
                source=bug_record,
                target=root_cause_file,
                options={"type": "ROOT_CAUSE_IN", "direction": "out"}
            )
        
        # Create investigation record
        investigation = db.records.create(
            label="INVESTIGATION",
            data={
                "bug_id": bug["id"],
                "timestamp": "2024-01-15T10:30:00Z",
                "status": "completed",
            }
        )
        created["investigations"].append(investigation)
        
        # Link investigation to bug
        db.records.attach(
            source=investigation,
            target=bug_record,
            options={"type": "FOR_BUG", "direction": "out"}
        )
        
        # Record what was investigated and the outcome
        for trail_item in bug["investigation_trail"]:
            file_record = file_map.get(trail_item["file"])
            if file_record:
                # Link investigation to file
                db.records.attach(
                    source=investigation,
                    target=file_record,
                    options={"type": "INVESTIGATED", "direction": "out"}
                )
                created["investigated_files"].append(file_record)
                
                # If this was ruled out, record that
                if trail_item["result"] == "ruled_out":
                    db.records.create(
                        label="INVESTIGATION_FINDING",
                        data={
                            "investigation_id": investigation.id,
                            "file": trail_item["file"],
                            "result": "ruled_out",
                            "reason": trail_item["reason"],
                        }
                    )
                elif trail_item["result"] == "root_cause":
                    db.records.create(
                        label="INVESTIGATION_FINDING",
                        data={
                            "investigation_id": investigation.id,
                            "file": trail_item["file"],
                            "result": "root_cause",
                            "reason": trail_item["reason"],
                            "function": bug["root_cause"]["function"],
                            "line": bug["root_cause"]["line"],
                            "issue_description": bug["root_cause"]["issue"],
                        }
                    )
        
        print(f"  Created BUG-{bug['id'].split('-')[1']}: {bug['title'][:50]}...")
    
    print(f"  ✓ Created {len(created['bugs'])} bugs with investigation trails")
    
    return created


def create_historical_investigations(db: RushDB) -> None:
    """
    Creates historical investigation data for learning patterns.
    """
    print("\n📚 Creating historical investigation records...")
    
    for inv in HISTORICAL_INVESTIGATIONS:
        db.records.create(
            label="HISTORICAL_INVESTIGATION",
            data={
                "bug_id": inv["bug_id"],
                "title": inv["title"],
                "root_cause_file": inv["root_cause_file"],
                "time_to_fix": inv["time_to_fix"],
                "files_investigated": inv["files_investigated"],
            }
        )
    
    print(f"  ✓ Created {len(HISTORICAL_INVESTIGATIONS)} historical records")


def check_if_seeded(db: RushDB) -> bool:
    """Check if the database already has seed data."""
    result = db.records.find({"labels": ["BUG"], "limit": 1})
    return len(result.data) > 0



def seed_database():
    """Main seeding function."""
    print("=" * 60)
    print("🌳 Graph Memory System - Database Seeder")
    print("=" * 60)
    
    # Load RushDB connection
    api_key = load_env()
    db = RushDB(api_key)
    
    # Check if already seeded
    if check_if_seeded(db):
        print("\n⚠️  Database already contains seed data.")
        print("   Run 'python main.py' to see the demo without reseeding.")
        response = input("   Reseed anyway? (y/N): ")
        if response.lower() != "y":
            print("Aborted.")
            return
        print("Reseeding...")
    
    # Create the graph
    created = create_codebase_graph(db)
    
    # Create file map for linking
    file_map = {f.data["path"]: f for f in created["files"]}
    
    # Create bugs and investigations
    bug_data = create_bugs_and_investigations(db, file_map)
    
    # Create historical investigations
    create_historical_investigations(db)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Graph memory seeded successfully!")
    print("=" * 60)
    print(f"""
Statistics:
  - {len(DIRECTORIES)} directories
  - {len(FILES)} files  
  - {len(FUNCTIONS)} functions
  - {len(BUGS)} bugs with investigation trails
  - {len(HISTORICAL_INVESTIGATIONS)} historical investigations
  
The graph is now ready for the demo.
Run 'python main.py' to see the graph memory system in action.
""")


if __name__ == "__main__":
    seed_database()
