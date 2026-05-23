"""
Seed script: Creates a tool registry graph in RushDB.

This script is idempotent - safe to run multiple times.
It first checks if data already exists, and skips seeding if found.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


from rushdb import RushDB


# Tool definitions - a realistic AI agent toolkit
TOOLS = [
    {
        "name": "read_file",
        "description": "Read contents of a file from the filesystem",
        "parameters": {"path": "string", "encoding": "string"},
        "returnType": "string",
        "provides": ["file contents", "raw data"],
        "category": "file_operations",
    },
    {
        "name": "write_file",
        "description": "Write content to a file",
        "parameters": {"path": "string", "content": "string", "append": "boolean"},
        "returnType": "boolean",
        "provides": ["file write", "data persistence"],
        "category": "file_operations",
    },
    {
        "name": "list_directory",
        "description": "List contents of a directory",
        "parameters": {"path": "string", "recursive": "boolean"},
        "returnType": "array",
        "provides": ["directory listing", "file inventory"],
        "category": "file_operations",
    },
    {
        "name": "web_search",
        "description": "Search the web for information",
        "parameters": {"query": "string", "limit": "integer", "source": "string"},
        "returnType": "array",
        "provides": ["external data", "web content", "current information"],
        "category": "search",
    },
    {
        "name": "vector_search",
        "description": "Perform similarity search on vector embeddings",
        "parameters": {"query": "string", "index": "string", "limit": "integer"},
        "returnType": "array",
        "provides": ["similarity search", "context retrieval", "semantic match"],
        "category": "search",
    },
    {
        "name": "semantic_lookup",
        "description": "Find relevant context using semantic similarity",
        "parameters": {"query": "string", "threshold": "float", "limit": "integer"},
        "returnType": "array",
        "provides": ["semantic search", "context", "data analysis"],
        "category": "search",
    },
    {
        "name": "calculator",
        "description": "Perform mathematical calculations",
        "parameters": {"expression": "string", "precision": "integer"},
        "returnType": "object",
        "provides": ["computation", "numeric data", "data processing"],
        "category": "computation",
    },
    {
        "name": "formatter",
        "description": "Format data into various output formats",
        "parameters": {"data": "any", "format": "string", "template": "string"},
        "returnType": "string",
        "provides": ["data formatting", "output generation"],
        "category": "computation",
    },
    {
        "name": "validator",
        "description": "Validate data against schemas and rules",
        "parameters": {"data": "any", "schema": "object", "strict": "boolean"},
        "returnType": "object",
        "provides": ["validation", "data verification", "schema checking"],
        "category": "computation",
    },
    {
        "name": "executor",
        "description": "Execute system commands or code",
        "parameters": {"command": "string", "timeout": "integer", "cwd": "string"},
        "returnType": "object",
        "provides": ["command execution", "system operations"],
        "category": "system",
    },
    {
        "name": "logger",
        "description": "Log messages with various severity levels",
        "parameters": {"message": "string", "level": "string", "metadata": "object"},
        "returnType": "boolean",
        "provides": ["logging", "audit trail", "event tracking"],
        "category": "system",
    },
    {
        "name": "notifier",
        "description": "Send notifications via various channels",
        "parameters": {"channel": "string", "recipient": "string", "message": "string"},
        "returnType": "boolean",
        "provides": ["notifications", "alerts", "messaging"],
        "category": "system",
    },
]

# Relationship definitions: source -> target with type
RELATIONSHIPS = [
    # Search tools
    ("semantic_lookup", "vector_search", "CALLS"),
    ("semantic_lookup", "validator", "REQUIRES"),
    
    # File operations dependencies
    ("write_file", "read_file", "DEPENDS_ON"),
    ("list_directory", "read_file", "DEPENDS_ON"),
    
    # Validation chain
    ("validator", "logger", "REQUIRES"),
    ("validator", "notifier", "CALLS"),
    
    # Formatter dependencies
    ("formatter", "validator", "REQUIRES"),
    ("formatter", "logger", "REQUIRES"),
    ("formatter", "notifier", "CALLS"),
    
    # Executor dependencies
    ("executor", "logger", "REQUIRES"),
    ("executor", "notifier", "CALLS"),
    ("executor", "validator", "REQUIRES"),
    ("executor", "formatter", "REQUIRES"),
    
    # Web search chain
    ("semantic_lookup", "web_search", "DEPENDS_ON"),
    
    # Calculator integration
    ("calculator", "formatter", "CALLS"),
    ("calculator", "validator", "REQUIRES"),
    
    # Logger foundation
    ("notifier", "logger", "REQUIRES"),
    ("logger", "notifier", "PROVIDES"),  # Logger enables notifications
]


def check_existing_data(db: RushDB) -> bool:
    """Check if tool registry already exists."""
    existing = db.records.find({"labels": ["TOOL"], "limit": 1})
    return len(existing) > 0


def create_tool_registry(db: RushDB) -> dict:
    """Create all tools and return a mapping of name -> record."""
    print("Creating tool registry...")
    
    tool_map = {}
    with db.transactions.begin() as tx:
        for i, tool_def in enumerate(TOOLS):
            tool = db.records.create(
                label="TOOL",
                data=tool_def,
                transaction=tx
            )
            tool_map[tool_def["name"]] = tool
            
            if (i + 1) % 5 == 0:
                print(f"  Created {i + 1}/{len(TOOLS)} tools...")
    
    print(f"  Created {len(TOOLS)} tools total.")
    return tool_map


def create_relationships(db: RushDB, tool_map: dict) -> None:
    """Create all tool relationships."""
    print("Creating tool relationships...")
    
    with db.transactions.begin() as tx:
        for i, (source_name, target_name, rel_type) in enumerate(RELATIONSHIPS):
            source = tool_map.get(source_name)
            target = tool_map.get(target_name)
            
            if source and target:
                db.records.attach(
                    source=source,
                    target=target,
                    options={"type": rel_type},
                    transaction=tx
                )
                
                if (i + 1) % 6 == 0:
                    print(f"  Created {i + 1}/{len(RELATIONSHIPS)} relationships...")
    
    print(f"  Created {len(RELATIONSHIPS)} relationships total.")


def main():
    """Main seeding function."""
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY environment variable not set.")
        print("Please add it to .env or set it in your environment.")
        sys.exit(1)
    
    db = RushDB(api_key)
    
    # Check for existing data
    if check_existing_data(db):
        print("Tool registry already exists. Skipping seeding.")
        print("To reseed, first delete the existing data.")
        
        # Show current stats
        all_tools = db.records.find({"labels": ["TOOL"]})
        print(f"Current data: {len(all_tools)} tools loaded.")
        return
    
    print("\n=== Seed Tool Registry ===\n")
    
    tool_map = create_tool_registry(db)
    create_relationships(db, tool_map)
    
    print("\n✓ Tool registry created successfully!")
    print(f"  - {len(TOOLS)} tools")
    print(f"  - {len(RELATIONSHIPS)} relationships")


if __name__ == "__main__":
    main()
