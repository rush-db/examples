"""
Seed script: Generates a realistic code repository graph in RushDB.

Creates 3 mock Python projects with realistic file structures,
functions, classes, and dependency relationships.

This script is idempotent - safe to run multiple times.
"""

import os
import random
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
url = os.getenv("RUSHDB_URL")

if not api_key:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(api_key, url=url) if url else RushDB(api_key)

# Mock repository data - realistic Python project structures
REPOSITORIES = [
    {
        "name": "auth-service",
        "description": "Authentication and authorization microservice",
        "language": "python",
        "stars": 1247,
    },
    {
        "name": "data-pipeline",
        "description": "ETL pipeline for processing user events",
        "language": "python",
        "stars": 892,
    },
    {
        "name": "api-gateway",
        "description": "Central API gateway with rate limiting",
        "language": "python",
        "stars": 2156,
    },
]

# Realistic file structures per repository
FILE_STRUCTURES = {
    "auth-service": [
        {"path": "src/__init__.py", "type": "module"},
        {"path": "src/models.py", "type": "module"},
        {"path": "src/auth.py", "type": "module"},
        {"path": "src/jwt.py", "type": "module"},
        {"path": "src/oauth.py", "type": "module"},
        {"path": "src/middleware.py", "type": "module"},
        {"path": "src/database.py", "type": "module"},
        {"path": "tests/__init__.py", "type": "test"},
        {"path": "tests/test_auth.py", "type": "test"},
        {"path": "tests/test_jwt.py", "type": "test"},
        {"path": "requirements.txt", "type": "config"},
    ],
    "data-pipeline": [
        {"path": "pipeline/__init__.py", "type": "module"},
        {"path": "pipeline/etl.py", "type": "module"},
        {"path": "pipeline/extractors.py", "type": "module"},
        {"path": "pipeline/transformers.py", "type": "module"},
        {"path": "pipeline/loaders.py", "type": "module"},
        {"path": "pipeline/validators.py", "type": "module"},
        {"path": "pipeline/schedulers.py", "type": "module"},
        {"path": "tests/test_etl.py", "type": "test"},
        {"path": "requirements.txt", "type": "config"},
    ],
    "api-gateway": [
        {"path": "gateway/__init__.py", "type": "module"},
        {"path": "gateway/server.py", "type": "module"},
        {"path": "gateway/routes.py", "type": "module"},
        {"path": "gateway/middleware.py", "type": "module"},
        {"path": "gateway/ratelimit.py", "type": "module"},
        {"path": "gateway/cache.py", "type": "module"},
        {"path": "gateway/proxy.py", "type": "module"},
        {"path": "tests/test_gateway.py", "type": "test"},
        {"path": "requirements.txt", "type": "config"},
    ],
}

# Function signatures and descriptions for realistic code
FUNCTION_TEMPLATES = [
    {
        "name": "authenticate_user",
        "doc": "Authenticate a user with username and password. Returns a user object on success.",
        "params": ["username", "password"],
    },
    {
        "name": "verify_token",
        "doc": "Verify JWT token validity and return decoded payload.",
        "params": ["token"],
    },
    {
        "name": "create_access_token",
        "doc": "Create a new JWT access token for the given user.",
        "params": ["user_id", "expires_in"],
    },
    {
        "name": "hash_password",
        "doc": "Hash a password using bcrypt with automatic salt generation.",
        "params": ["password"],
    },
    {
        "name": "verify_password",
        "doc": "Verify a password against a stored hash.",
        "params": ["password", "hashed"],
    },
    {
        "name": "get_user_by_email",
        "doc": "Retrieve a user record by their email address.",
        "params": ["email"],
    },
    {
        "name": "create_user",
        "doc": "Create a new user record in the database.",
        "params": ["email", "password", "name"],
    },
    {
        "name": "extract_data",
        "doc": "Extract data from the source system with pagination support.",
        "params": ["source", "query"],
    },
    {
        "name": "transform_records",
        "doc": "Apply transformations to records based on configured rules.",
        "params": ["records", "schema"],
    },
    {
        "name": "load_to_destination",
        "doc": "Load transformed data into the target destination.",
        "params": ["data", "destination"],
    },
    {
        "name": "validate_schema",
        "doc": "Validate data against a JSON schema definition.",
        "params": ["data", "schema"],
    },
    {
        "name": "check_rate_limit",
        "doc": "Check if a client has exceeded their rate limit quota.",
        "params": ["client_id"],
    },
    {
        "name": "apply_ratelimit",
        "doc": "Apply rate limiting middleware to an API route.",
        "params": ["request", "tier"],
    },
    {
        "name": "cache_response",
        "doc": "Cache an API response with TTL support.",
        "params": ["key", "value", "ttl"],
    },
    {
        "name": "get_cached",
        "doc": "Retrieve a cached response by key.",
        "params": ["key"],
    },
]

CLASS_TEMPLATES = [
    {
        "name": "User",
        "doc": "Represents a user in the authentication system.",
        "methods": ["get_id", "get_email", "is_active"],
    },
    {
        "name": "TokenManager",
        "doc": "Manages creation and validation of JWT tokens.",
        "methods": ["create", "verify", "refresh", "revoke"],
    },
    {
        "name": "OAuthProvider",
        "doc": "Base class for OAuth 2.0 providers.",
        "methods": ["authorize", "get_token", "get_user_info"],
    },
    {
        "name": "ETLPipeline",
        "doc": "Orchestrates the extract-transform-load workflow.",
        "methods": ["run", "pause", "resume", "get_status"],
    },
    {
        "name": "DataExtractor",
        "doc": "Base extractor for various data sources.",
        "methods": ["connect", "extract", "disconnect"],
    },
    {
        "name": "RateLimiter",
        "doc": "Token bucket rate limiter implementation.",
        "methods": ["acquire", "reset", "get_remaining"],
    },
    {
        "name": "CacheManager",
        "doc": "Multi-layer caching with LRU eviction.",
        "methods": ["get", "set", "delete", "clear"],
    },
]


def clear_existing_data():
    """Remove existing seed data for clean re-seeding."""
    print("Clearing existing data...")
    
    labels_to_delete = ["FUNCTION", "CLASS", "FILE", "REPOSITORY"]
    
    for label in labels_to_delete:
        result = db.records.find({"labels": [label], "limit": 100})
        while result.data:
            for record in result.data:
                db.records.delete(record_id=record.id)
            result = db.records.find({"labels": [label], "limit": 100})
    
    print("Existing data cleared.")


def create_repositories():
    """Create repository nodes."""
    print("\nCreating repositories...")
    repos = {}
    
    for i, repo_data in enumerate(REPOSITORIES):
        repo = db.records.create(
            label="REPOSITORY",
            data={
                "name": repo_data["name"],
                "description": repo_data["description"],
                "language": repo_data["language"],
                "stars": repo_data["stars"],
            }
        )
        repos[repo_data["name"]] = repo
        
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} repositories...")
    
    print(f"  Created {len(repos)} repositories")
    return repos


def create_files(repos):
    """Create file nodes and link to repositories."""
    print("\nCreating files...")
    all_files = []
    
    for repo_name, files_config in FILE_STRUCTURES.items():
        repo = repos[repo_name]
        
        for i, file_config in enumerate(files_config):
            file_record = db.records.create(
                label="FILE",
                data={
                    "path": file_config["path"],
                    "name": Path(file_config["path"]).name,
                    "extension": Path(file_config["path"]).suffix,
                    "type": file_config["type"],
                }
            )
            
            # Link file to repository
            db.records.attach(
                source=repo,
                target=file_record,
                options={"type": "CONTAINS"}
            )
            
            all_files.append(file_record)
            
            if len(all_files) % 10 == 0:
                print(f"  Created {len(all_files)} files...")
    
    print(f"  Created {len(all_files)} files")
    return all_files


def create_functions(files):
    """Create function nodes and link to files."""
    print("\nCreating functions...")
    functions = []
    
    # Filter to only module-type files (not tests/config)
    module_files = [f for f in files if f["type"] == "module"]
    
    for i, file_record in enumerate(module_files):
        # Add 3-6 functions per module file
        num_functions = random.randint(3, 6)
        selected_funcs = random.sample(FUNCTION_TEMPLATES, num_functions)
        
        for func_template in selected_funcs:
            func_record = db.records.create(
                label="FUNCTION",
                data={
                    "name": func_template["name"],
                    "doc": func_template["doc"],
                    "params": func_template["params"],
                    "lines": random.randint(10, 100),
                }
            )
            
            # Link function to its defining file
            db.records.attach(
                source=file_record,
                target=func_record,
                options={"type": "DEFINES"}
            )
            
            functions.append(func_record)
        
        if (i + 1) % 10 == 0:
            print(f"  Created {len(functions)} functions...")
    
    print(f"  Created {len(functions)} functions")
    return functions


def create_classes(files):
    """Create class nodes and link to files."""
    print("\nCreating classes...")
    classes = []
    
    module_files = [f for f in files if f["type"] == "module"]
    
    for i, file_record in enumerate(module_files):
        # Add 1-3 classes per module file
        num_classes = random.randint(1, 3)
        selected_classes = random.sample(CLASS_TEMPLATES, min(num_classes, len(CLASS_TEMPLATES)))
        
        for cls_template in selected_classes:
            class_record = db.records.create(
                label="CLASS",
                data={
                    "name": cls_template["name"],
                    "doc": cls_template["doc"],
                    "num_methods": len(cls_template["methods"]),
                }
            )
            
            # Link class to its defining file
            db.records.attach(
                source=file_record,
                target=class_record,
                options={"type": "DEFINES"}
            )
            
            # Create method functions
            for method_name in cls_template["methods"]:
                method_record = db.records.create(
                    label="FUNCTION",
                    data={
                        "name": method_name,
                        "doc": f"{cls_template['name']}.{method_name} method",
                        "params": ["self"],
                        "lines": random.randint(5, 30),
                        "is_method": True,
                    }
                )
                
                db.records.attach(
                    source=class_record,
                    target=method_record,
                    options={"type": "METHOD"}
                )
            
            classes.append(class_record)
        
        if (i + 1) % 10 == 0:
            print(f"  Created {len(classes)} classes...")
    
    print(f"  Created {len(classes)} classes")
    return classes


def create_imports(files, functions):
    """Create import relationships between files and call relationships between functions."""
    print("\nCreating import relationships...")
    
    module_files = [f for f in files if f["type"] == "module"]
    
    # Create file-to-file import relationships
    for i, source_file in enumerate(module_files):
        # Each file imports 1-3 other files
        num_imports = random.randint(1, min(3, len(module_files) - 1))
        other_files = [f for f in module_files if f.id != source_file.id]
        imported_files = random.sample(other_files, min(num_imports, len(other_files)))
        
        for target_file in imported_files:
            db.records.attach(
                source=source_file,
                target=target_file,
                options={"type": "IMPORTS"}
            )
    
    print(f"  Created file import relationships")
    
    # Create function call relationships
    print("Creating function call relationships...")
    
    for i, caller in enumerate(functions[:50]):  # Limit to avoid too many relationships
        num_calls = random.randint(1, 3)
        other_funcs = [f for f in functions if f.id != caller.id]
        called_funcs = random.sample(other_funcs, min(num_calls, len(other_funcs)))
        
        for callee in called_funcs:
            db.records.attach(
                source=caller,
                target=callee,
                options={"type": "CALLS"}
            )
    
    print(f"  Created function call relationships")


def create_cross_repo_dependencies(repos):
    """Create cross-repository import relationships."""
    print("\nCreating cross-repository dependencies...")
    
    repo_list = list(repos.values())
    
    # auth-service is depended on by others
    auth_repo = repos["auth-service"]
    
    for repo_name, repo in repos.items():
        if repo_name != "auth-service":
            # Create cross-repo dependency
            db.records.attach(
                source=repo,
                target=auth_repo,
                options={"type": "IMPORTS"}
            )
    
    print("  Created cross-repository dependencies")


def main():
    """Main seeding function."""
    print("=" * 60)
    print("RushDB Code Repository Graph Seeder")
    print("=" * 60)
    
    # Clear existing seed data
    clear_existing_data()
    
    # Create graph entities
    repos = create_repositories()
    files = create_files(repos)
    functions = create_functions(files)
    classes = create_classes(files)
    
    # Create relationships
    create_imports(files, functions)
    create_cross_repo_dependencies(repos)
    
    print("\n" + "=" * 60)
    print("Seeding complete!")
    print("=" * 60)
    print(f"  Repositories: {len(repos)}")
    print(f"  Files: {len(files)}")
    print(f"  Functions: {len(functions)}")
    print(f"  Classes: {len(classes)}")
    print("\nRun `python main.py` to explore the graph.")


if __name__ == "__main__":
    main()
