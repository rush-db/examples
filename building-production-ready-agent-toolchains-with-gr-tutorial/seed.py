#!/usr/bin/env python3
"""
Seed script for the agent toolchain tutorial.

This script generates mock tools, agents, and tasks in RushDB to demonstrate
graph-native orchestration capabilities.

Run this once before main.py to populate the database with test data.
The script is idempotent - safe to run multiple times.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Please copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(API_KEY)

# Define mock tools with rich descriptions for semantic search
TOOLS = [
    {
        "name": "fetch_data",
        "description": "Retrieve data from external APIs or databases. Handles authentication, rate limiting, and pagination automatically. Supports REST endpoints, GraphQL queries, and SQL database connections.",
        "category": "data",
        "parameters": {"endpoint": "string", "filters": "object", "limit": "integer"},
    },
    {
        "name": "process_data",
        "description": "Transform and clean raw data. Handle missing values, normalize formats, deduplicate records, and apply business rules. Essential for preparing data for analysis.",
        "category": "data",
        "parameters": {"data": "array", "transformations": "object"},
    },
    {
        "name": "sentiment_analysis",
        "description": "Analyze text for emotional tone and opinion polarity. Classify text as positive, negative, or neutral. Extract sentiment scores and confidence levels. Useful for customer feedback analysis.",
        "category": "nlp",
        "parameters": {"text": "string", "language": "string"},
    },
    {
        "name": "text_summarizer",
        "description": "Generate concise summaries of long documents. Support extractive and abstractive summarization. Control summary length and preserve key information.",
        "category": "nlp",
        "parameters": {"document": "string", "max_length": "integer", "mode": "string"},
    },
    {
        "name": "keyword_extractor",
        "description": "Extract key terms and phrases from text. Identify important entities, themes, and topics. Generate keyword importance scores and frequency analysis.",
        "category": "nlp",
        "parameters": {"text": "string", "top_n": "integer", "method": "string"},
    },
    {
        "name": "generate_insights",
        "description": "Analyze data patterns and generate actionable insights. Identify trends, anomalies, and correlations. Create natural language explanations of findings.",
        "category": "analytics",
        "parameters": {"data": "array", "metrics": "array", "timeframe": "string"},
    },
    {
        "name": "send_notification",
        "description": "Send notifications via email, SMS, or webhooks. Support templated messages, scheduling, and delivery tracking. Handle multiple recipients and channels.",
        "category": "communication",
        "parameters": {"recipients": "array", "template": "string", "channel": "string"},
    },
    {
        "name": "schedule_task",
        "description": "Schedule tasks for future execution. Support cron expressions, delayed execution, and recurring schedules. Maintain task state and handle missed executions.",
        "category": "orchestration",
        "parameters": {"task": "string", "schedule": "string", "options": "object"},
    },
    {
        "name": "call_llm",
        "description": "Invoke large language model for text generation. Support various models, system prompts, and generation parameters. Handle token limits and response streaming.",
        "category": "ai",
        "parameters": {"prompt": "string", "model": "string", "temperature": "float"},
    },
    {
        "name": "transform_format",
        "description": "Convert data between formats. Transform JSON to CSV, XML to JSON, markdown to HTML, and more. Handle schema mapping and validation during conversion.",
        "category": "utility",
        "parameters": {"data": "any", "input_format": "string", "output_format": "string"},
    },
]

# Define mock agents with different intents
AGENTS = [
    {
        "name": "customer_insights_agent",
        "intent": "I need to analyze customer feedback and generate actionable insights about product satisfaction",
        "role": "Analyzes customer feedback to understand satisfaction trends and identify improvement areas",
    },
    {
        "name": "data_pipeline_agent",
        "intent": "Extract data from multiple sources, transform it, and load into a data warehouse",
        "role": "Orchestrates data pipelines for ETL operations with error handling and retry logic",
    },
    {
        "name": "notification_agent",
        "intent": "Monitor system events and send appropriate notifications to stakeholders",
        "role": "Monitors for important events and delivers notifications through appropriate channels",
    },
]

# Define execution tasks
TASKS = [
    {"name": "fetch_customer_reviews", "status": "completed", "result": "245 reviews fetched"},
    {"name": "clean_review_data", "status": "completed", "result": "198 valid reviews extracted"},
    {"name": "analyze_sentiment", "status": "completed", "result": "75% positive, 15% neutral, 10% negative"},
    {"name": "generate_summary", "status": "completed", "result": "Summary generated: 3 pages"},
    {"name": "extract_key_phrases", "status": "completed", "result": "50 key phrases extracted"},
    {"name": "identify_trends", "status": "pending", "result": None},
    {"name": "create_report", "status": "pending", "result": None},
    {"name": "send_digest", "status": "pending", "result": None},
]


def clear_existing_data():
    """Remove existing tutorial data to ensure clean seeding."""
    print("Clearing existing tutorial data...")
    
    labels_to_clear = ["TOOL", "AGENT", "TASK", "EXECUTION_TRACE", "CHECKPOINT"]
    
    for label in labels_to_clear:
        result = db.records.find({"labels": [label], "limit": 1000})
        if result.data:
            for record in result.data:
                db.records.delete(record_id=record.id)
            print(f"  Cleared {len(result.data)} {label} records")
    
    print("Existing data cleared.\n")


def seed_tools():
    """Create tool nodes and relationships."""
    print("=== Seeding Tools ===")
    
    tools = {}
    for i, tool_data in enumerate(TOOLS):
        tool = db.records.create(
            label="TOOL",
            data={
                "name": tool_data["name"],
                "description": tool_data["description"],
                "category": tool_data["category"],
                "parameters": tool_data["parameters"],
                "created_at": datetime.now().isoformat(),
            }
        )
        tools[tool_data["name"]] = tool
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(TOOLS)} tools...")
    
    # Create category groupings
    categories = {}
    for tool_data in TOOLS:
        category = tool_data["category"]
        if category not in categories:
            cat_node = db.records.create(
                label="CATEGORY",
                data={"name": category}
            )
            categories[category] = cat_node
            db.records.attach(
                source=tools[TOOLS[0]["name"]],  # We'll attach via the first tool
                target=cat_node,
                options={"type": "PART_OF_CATEGORY"}
            )
    
    print(f"✓ Created {len(tools)} TOOL nodes")
    return tools


def seed_agents(tools):
    """Create agent nodes and link to tools they can use."""
    print("\n=== Seeding Agents ===")
    
    agents = {}
    tool_names = list(tools.keys())
    
    for i, agent_data in enumerate(AGENTS):
        agent = db.records.create(
            label="AGENT",
            data={
                "name": agent_data["name"],
                "intent": agent_data["intent"],
                "role": agent_data["role"],
                "status": "active",
                "created_at": datetime.now().isoformat(),
            }
        )
        agents[agent_data["name"]] = agent
        
        # Link agent to relevant tools based on intent
        if "customer" in agent_data["intent"] or "feedback" in agent_data["intent"]:
            relevant_tools = ["fetch_data", "sentiment_analysis", "text_summarizer", 
                            "keyword_extractor", "generate_insights"]
        elif "data" in agent_data["intent"]:
            relevant_tools = ["fetch_data", "process_data", "transform_format",
                            "generate_insights", "schedule_task"]
        else:
            relevant_tools = ["call_llm", "send_notification", "generate_insights"]
        
        for tool_name in relevant_tools:
            if tool_name in tools:
                db.records.attach(
                    source=agent,
                    target=tools[tool_name],
                    options={"type": "CAN_USE"}
                )
        
        print(f"  Created {agent_data['name']} with {len(relevant_tools)} linked tools")
    
    print(f"✓ Created {len(agents)} AGENT nodes")
    return agents


def seed_tasks(agents):
    """Create task nodes and execution traces."""
    print("\n=== Seeding Tasks ===")
    
    tasks = {}
    agent_names = list(agents.keys())
    
    for i, task_data in enumerate(TASKS):
        task = db.records.create(
            label="TASK",
            data={
                "name": task_data["name"],
                "status": task_data["status"],
                "result": task_data["result"],
                "created_at": (datetime.now() - timedelta(hours=len(TASKS)-i)).isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
        )
        tasks[task_data["name"]] = task
        
        # Assign task to a random agent
        import random
        agent = agents[agent_names[i % len(agent_names)]]
        db.records.attach(
            source=task,
            target=agent,
            options={"type": "ASSIGNED_TO"}
        )
        
        # Create execution trace for completed tasks
        if task_data["status"] == "completed":
            trace = db.records.create(
                label="EXECUTION_TRACE",
                data={
                    "task_name": task_data["name"],
                    "status": "success",
                    "duration_ms": random.randint(100, 5000),
                    "timestamp": task_data.get("created_at", datetime.now().isoformat()),
                }
            )
            db.records.attach(
                source=task,
                target=trace,
                options={"type": "HAS_TRACE"}
            )
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(TASKS)} tasks...")
    
    # Create task dependencies
    task_order = ["fetch_customer_reviews", "clean_review_data", "analyze_sentiment",
                 "generate_summary", "extract_key_phrases", "identify_trends",
                 "create_report", "send_digest"]
    
    for i in range(len(task_order) - 1):
        if task_order[i] in tasks and task_order[i+1] in tasks:
            db.records.attach(
                source=tasks[task_order[i+1]],
                target=tasks[task_order[i]],
                options={"type": "DEPENDS_ON"}
            )
    
    print(f"✓ Created {len(tasks)} TASK nodes")
    return tasks


def create_sample_checkpoints(tasks):
    """Create sample checkpoint records for recovery demonstration."""
    print("\n=== Creating Checkpoints ===")
    
    checkpoint_data = [
        {
            "task_name": "clean_review_data",
            "checkpoint_at": "data_fetched",
            "state": {"records_fetched": 245, "validation_passed": True},
        },
        {
            "task_name": "analyze_sentiment",
            "checkpoint_at": "data_cleaned",
            "state": {"records_processed": 198, "quality_score": 0.87},
        },
    ]
    
    for cp_data in checkpoint_data:
        checkpoint = db.records.create(
            label="CHECKPOINT",
            data={
                "task_name": cp_data["task_name"],
                "checkpoint_at": cp_data["checkpoint_at"],
                "state": cp_data["state"],
                "created_at": datetime.now().isoformat(),
            }
        )
        print(f"  Created checkpoint: {cp_data['task_name']} -> {cp_data['checkpoint_at']}")
    
    print(f"✓ Created {len(checkpoint_data)} CHECKPOINT records")


def main():
    """Run the seeding process."""
    print("\n" + "="*60)
    print("  Agent Toolchain Tutorial - Data Seeding")
    print("="*60 + "\n")
    
    try:
        # Clear existing data first
        clear_existing_data()
        
        # Seed all data
        tools = seed_tools()
        agents = seed_agents(tools)
        tasks = seed_tasks(agents)
        create_sample_checkpoints(tasks)
        
        print("\n" + "="*60)
        print("  Seeding Complete!")
        print("="*60)
        print(f"\n✓ {len(TOOLS)} tools ready for semantic routing")
        print(f"✓ {len(AGENTS)} agents created with tool capabilities")
        print(f"✓ {len(TASKS)} tasks with execution history")
        print(f"\nRun 'python main.py' to execute the tutorial.\n")
        
    except Exception as e:
        print(f"\nError during seeding: {e}")
        print("\nMake sure your RUSHDB_API_KEY is valid and you have an active connection.")
        sys.exit(1)


if __name__ == "__main__":
    main()
