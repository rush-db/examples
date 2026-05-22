#!/usr/bin/env python3
"""
Seed script for Graph-Based Tool Selection example.
Creates a realistic tool registry with capabilities and dependencies.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rushdb import RushDB


# Sample data
TOOLS = [
    {
        "name": "WebFetchTool",
        "description": "Fetches HTML content from URLs, handles redirects and rate limiting",
        "version": "1.2.0",
        "category": "data_ingestion",
        "params": {"timeout": 30, "retries": 3}
    },
    {
        "name": "APIConnector",
        "description": "Connects to REST APIs with authentication, handles pagination and rate limits",
        "version": "2.0.1",
        "category": "data_ingestion",
        "params": {"auth_type": "bearer", "rate_limit": 100}
    },
    {
        "name": "FileReadTool",
        "description": "Reads local files with support for various formats including CSV, JSON, and Parquet",
        "version": "1.5.3",
        "category": "data_ingestion",
        "params": {"encoding": "utf-8", "buffer_size": 8192}
    },
    {
        "name": "FileWriteTool",
        "description": "Writes data to local files with automatic format detection and compression",
        "version": "1.4.2",
        "category": "data_output",
        "params": {"compression": "auto", "overwrite": False}
    },
    {
        "name": "DataPreprocessor",
        "description": "Cleans and transforms data with normalization, imputation, and feature engineering",
        "version": "3.1.0",
        "category": "data_processing",
        "params": {"normalize": True, "handle_missing": "interpolate"}
    },
    {
        "name": "StatisticalAnalyzer",
        "description": "Computes statistical metrics including mean, variance, correlations, and hypothesis tests",
        "version": "2.2.0",
        "category": "analytics",
        "params": {"confidence_level": 0.95, "tests": ["ttest", "anova"]}
    },
    {
        "name": "MLModelTrainer",
        "description": "Trains machine learning models with automatic hyperparameter tuning and cross-validation",
        "version": "4.0.0",
        "category": "ml",
        "params": {"algorithm": "auto", "cv_folds": 5, "early_stopping": True}
    },
    {
        "name": "DataAggregator",
        "description": "Aggregates data from multiple sources with join operations and group-by capabilities",
        "version": "2.3.1",
        "category": "data_processing",
        "params": {"join_types": ["inner", "outer", "cross"]}
    },
    {
        "name": "ReportGenerator",
        "description": "Generates formatted reports including tables, charts, and export to PDF or HTML",
        "version": "1.8.0",
        "category": "output",
        "params": {"format": "auto", "template": "default"}
    },
    {
        "name": "DataPipelineOrchestrator",
        "description": "Orchestrates complex data pipelines with task dependencies, retries, and monitoring",
        "version": "5.0.0",
        "category": "orchestration",
        "params": {"parallel_tasks": 10, "retry_policy": "exponential"}
    },
    {
        "name": "ETLProcessor",
        "description": "Full ETL pipeline processor with extraction, transformation, and loading capabilities",
        "version": "3.5.0",
        "category": "data_processing",
        "params": {"batch_size": 1000, "error_handling": "skip"}
    },
    {
        "name": "CacheManager",
        "description": "Manages cached data with TTL support and invalidation strategies",
        "version": "1.1.0",
        "category": "infrastructure",
        "params": {"default_ttl": 3600, "max_size": "1GB"}
    }
]

CAPABILITIES = [
    {"name": "read", "description": "Can read data from sources"},
    {"name": "write", "description": "Can write data to destinations"},
    {"name": "compute", "description": "Can perform computations"},
    {"name": "network", "description": "Can make network requests"},
    {"name": "transform", "description": "Can transform and manipulate data"},
    {"name": "orchestrate", "description": "Can coordinate other tools"},
    {"name": "persist", "description": "Can store data long-term"},
    {"name": "cache", "description": "Can cache data for performance"}
]

# Map tools to the capabilities they provide
TOOL_CAPABILITIES = {
    "WebFetchTool": ["network", "read"],
    "APIConnector": ["network", "read"],
    "FileReadTool": ["read"],
    "FileWriteTool": ["write", "persist"],
    "DataPreprocessor": ["transform", "compute"],
    "StatisticalAnalyzer": ["compute"],
    "MLModelTrainer": ["compute", "transform"],
    "DataAggregator": ["transform", "compute", "read"],
    "ReportGenerator": ["write", "compute"],
    "DataPipelineOrchestrator": ["orchestrate", "read", "write"],
    "ETLProcessor": ["read", "write", "transform", "network"],
    "CacheManager": ["cache", "persist"]
}

# Map dependencies between tools
TOOL_DEPENDENCIES = {
    "WebFetchTool": ["CacheManager"],
    "APIConnector": ["CacheManager"],
    "DataPreprocessor": ["FileReadTool", "CacheManager"],
    "StatisticalAnalyzer": ["DataPreprocessor"],
    "MLModelTrainer": ["DataPreprocessor", "CacheManager"],
    "DataAggregator": ["FileReadTool", "WebFetchTool", "APIConnector"],
    "ReportGenerator": ["DataAggregator", "FileWriteTool"],
    "DataPipelineOrchestrator": ["DataPreprocessor", "CacheManager", "FileWriteTool"],
    "ETLProcessor": ["DataPreprocessor", "FileReadTool", "FileWriteTool", "CacheManager"]
}


def check_existing_data(db: RushDB) -> bool:
    """Check if data already exists to avoid duplicate seeding."""
    result = db.records.find({"labels": ["TOOL"], "limit": 1})
    return len(result.data) > 0


def seed_tools_and_capabilities(db: RushDB) -> dict:
    """Create tools and capabilities in the graph."""
    print("\n=== SEEDING TOOL GRAPH ===")
    
    # Check if already seeded
    if check_existing_data(db):
        print("✓ Data already exists, skipping seed")
        return {"tools": db.records.find({"labels": ["TOOL"]}).data}
    
    # Create capabilities first
    cap_records = {}
    for cap in CAPABILITIES:
        cap_record = db.records.create(
            label="CAPABILITY",
            data=cap
        )
        cap_records[cap["name"]] = cap_record
        print(f"  ✓ Created capability: {cap['name']}")
    
    # Create tools and link to capabilities
    tool_records = {}
    for i, tool_data in enumerate(TOOLS, 1):
        tool_record = db.records.create(
            label="TOOL",
            data=tool_data
        )
        tool_records[tool_data["name"]] = tool_record
        
        # Link tool to its capabilities
        tool_caps = TOOL_CAPABILITIES.get(tool_data["name"], [])
        for cap_name in tool_caps:
            if cap_name in cap_records:
                db.records.attach(
                    source=tool_record,
                    target=cap_records[cap_name],
                    options={"type": "ENABLES"}
                )
        
        if i % 4 == 0:
            print(f"  ✓ Created {i}/{len(TOOLS)} tools...")
    
    print(f"✓ Created {len(tool_records)} tools")
    print(f"✓ Created {len(cap_records)} capabilities")
    
    return tool_records


def seed_dependencies(db: RushDB, tool_records: dict):
    """Create dependency relationships between tools."""
    dep_count = 0
    for tool_name, deps in TOOL_DEPENDENCIES.items():
        if tool_name not in tool_records:
            continue
        tool_record = tool_records[tool_name]
        
        for dep_name in deps:
            if dep_name not in tool_records:
                continue
            dep_record = tool_records[dep_name]
            db.records.attach(
                source=tool_record,
                target=dep_record,
                options={"type": "DEPENDS_ON"}
            )
            dep_count += 1
    
    print(f"✓ Created {dep_count} dependency relationships")


def create_capability_index(db: RushDB) -> str:
    """Create a vector index for semantic tool search."""
    # Check if index already exists
    indexes = db.ai.indexes.find().data
    for idx in indexes:
        if idx["label"] == "TOOL" and idx["propertyName"] == "description":
            print(f"✓ Capability index already exists (ID: {idx['__id']})")
            return idx["__id"]
    
    # Create new index
    index = db.ai.indexes.create({
        "label": "TOOL",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,  # MiniLM-L6-v2 output dimension
        "similarityFunction": "cosine"
    })
    
    index_id = index.data["__id"]
    print(f"✓ Built capability index (ID: {index_id})")
    
    return index_id


def main():
    """Run the seed script."""
    load_dotenv()
    
    api_token = os.environ.get("RUSHzDB_API_TOKEN")
    if not api_token:
        print("Error: RUSHzDB_API_TOKEN not found in environment")
        print("Copy .env.example to .env and add your token")
        sys.exit(1)
    
    db = RushDB(api_token)
    
    # Seed the data
    tool_records = seed_tools_and_capabilities(db)
    seed_dependencies(db, tool_records)
    index_id = create_capability_index(db)
    
    print("\n✓ Seeding complete!")
    return index_id


if __name__ == "__main__":
    main()
