"""
seed.py — Entity-aware chunking: seed a mock Python code base into RushDB.

Generates a realistic multi-file Python project (auth, API gateway, user service)
with typed entities and explicit cross-document relationships, then loads it into
RushDB. Safe to re-run: detects already-loaded data and skips re-creation.

Entities: FUNCTION, CLASS, API_ENDPOINT, ENV_VAR, CONFIG_KEY
Relationships: CALLS, IMPORTS, CONFIGURES, READS_ENV, RETURNS, HANDLES_ERROR
"""

import os
import random
import time
from datetime import datetime

from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
RUSHDB_URL = os.getenv("RUSHDB_URL") or None

if not API_KEY:
    raise RuntimeError(
        "RUSHDB_API_KEY not set. Copy .env.example to .env and fill in your key."
    )

db = RushDB(API_KEY, url=RUSHDB_URL) if RUSHDB_URL else RushDB(API_KEY)

# --------------------------------------------------------------------------- #
# Mock code base — entities and relationships for three Python modules
# --------------------------------------------------------------------------- #

ENTITIES = {
    "MODULE": [
        {
            "name": "auth.py",
            "path": "src/auth.py",
            "description": "Authentication service handling JWT token lifecycle, user login, and session management."
        },
        {
            "name": "api_gateway.py",
            "path": "src/api_gateway.py",
            "description": "FastAPI gateway managing route registration, middleware chaining, and request validation."
        },
        {
            "name": "user_service.py",
            "path": "src/user_service.py",
            "description": "User management service handling profile reads, settings retrieval, and DB queries."
        },
    ],
    "CLASS": [
        {
            "name": "JWTAuthenticator",
            "module": "auth.py",
            "description": "Handles JWT token creation, validation, and refresh. Depends on JWT_SECRET and JWT_ALGORITHM config.",
            "methods": ["create_token", "validate_token", "refresh_token"]
        },
        {
            "name": "TokenValidator",
            "module": "auth.py",
            "description": "Validates incoming bearer tokens against the configured secret and algorithm. Used by middleware.",
            "methods": ["validate", "decode_header", "check_expiry"]
        },
        {
            "name": "DatabaseConnection",
            "module": "auth.py",
            "description": "Manages PostgreSQL connection pool lifecycle. Reads DATABASE_URL from environment.",
            "methods": ["connect", "query", "close"]
        },
        {
            "name": "APIGateway",
            "module": "api_gateway.py",
            "description": "FastAPI app factory: registers routes, adds auth middleware, and starts the Uvicorn server.",
            "methods": ["create_app", "register_routes", "add_middleware"]
        },
        {
            "name": "RateLimiter",
            "module": "api_gateway.py",
            "description": "Token-bucket rate limiter using Redis. Reads RATE_LIMIT_REQUESTS and RATE_LIMIT_WINDOW from env.",
            "methods": ["check_limit", "record_hit"]
        },
        {
            "name": "UserService",
            "module": "user_service.py",
            "description": "Business logic for user profile, preferences, and settings. Reads from database via DBQuery.",
            "methods": ["get_profile", "update_settings", "get_user_settings"]
        },
        {
            "name": "DBQuery",
            "module": "user_service.py",
            "description": "Parameterized query executor for PostgreSQL. Prevents SQL injection. Used by UserService.",
            "methods": ["execute", "fetch_one", "fetch_all"]
        },
    ],
    "FUNCTION": [
        {
            "name": "login_user",
            "module": "auth.py",
            "description": "Authenticates username/password against the database. On success, calls create_token().",
            "calls": ["DatabaseConnection.query", "JWTAuthenticator.create_token"]
        },
        {
            "name": "create_token",
            "module": "auth.py",
            "description": "Creates a signed JWT with user_id and roles claims. Reads JWT_SECRET from config.",
            "calls": ["JWTAuthenticator.create_token"]
        },
        {
            "name": "validate_token",
            "module": "auth.py",
            "description": "High-level token validation entry point. Calls TokenValidator.validate() with bearer header.",
            "calls": ["TokenValidator.validate"]
        },
        {
            "name": "check_auth_middleware",
            "module": "api_gateway.py",
            "description": "FastAPI dependency that validates Authorization header. Calls validate_token() from auth.py.",
            "calls": ["validate_token"]
        },
        {
            "name": "register_user_routes",
            "module": "api_gateway.py",
            "description": "Wires up /users/profile, /users/settings, /users/update to UserService methods.",
            "calls": ["UserService.get_profile", "UserService.get_user_settings"]
        },
        {
            "name": "get_user_profile",
            "module": "user_service.py",
            "description": "Fetches user profile row from PostgreSQL. Calls DBQuery.fetch_one() with parameterized query.",
            "calls": ["DBQuery.fetch_one"]
        },
        {
            "name": "get_user_settings",
            "module": "user_service.py",
            "description": "Reads user preferences JSONB from DB. Reads DATABASE_URL from environment for connection.",
            "calls": ["DBQuery.fetch_one", "getenv"]
        },
        {
            "name": "execute_query",
            "module": "user_service.py",
            "description": "Wraps DBQuery.execute() with error handling and connection retry. Calls DatabaseConnection.query.",
            "calls": ["DBQuery.execute", "DatabaseConnection.query"]
        },
    ],
    "API_ENDPOINT": [
        {
            "method": "POST",
            "path": "/auth/login",
            "description": "Accepts JSON body {username, password}. Returns JWT on success, 401 on failure.",
            "calls": ["login_user"]
        },
        {
            "method": "POST",
            "path": "/auth/refresh",
            "description": "Accepts expired JWT in Authorization header. Returns new JWT if signature is valid.",
            "calls": ["JWTAuthenticator.refresh_token"]
        },
        {
            "method": "GET",
            "path": "/users/profile",
            "description": "Protected route. Returns authenticated user's profile. Calls get_user_profile().",
            "calls": ["get_user_profile"]
        },
        {
            "method": "GET",
            "path": "/users/settings",
            "description": "Protected route. Returns user preferences from PostgreSQL JSONB column.",
            "calls": ["get_user_settings"]
        },
        {
            "method": "PATCH",
            "path": "/users/update",
            "description": "Protected route. Updates user profile fields. Reads DATABASE_URL env for DB writes.",
            "calls": ["UserService.update_settings", "getenv"]
        },
    ],
    "ENV_VAR": [
        {
            "name": "DATABASE_URL",
            "description": "PostgreSQL connection string. Format: postgresql://user:pass@host:5432/db",
            "used_by": ["DatabaseConnection.connect", "get_user_settings", "execute_query"]
        },
        {
            "name": "JWT_SECRET",
            "description": "Secret key for HMAC-SHA256 JWT signing. Must be ≥32 random bytes.",
            "used_by": ["JWTAuthenticator.create_token", "TokenValidator.validate"]
        },
        {
            "name": "JWT_ALGORITHM",
            "description": "JWT signing algorithm. Valid values: HS256, HS384, HS512. Default: HS256.",
            "used_by": ["JWTAuthenticator.create_token", "TokenValidator.decode_header"]
        },
        {
            "name": "RATE_LIMIT_REQUESTS",
            "description": "Max requests per window for rate limiting. Default: 100.",
            "used_by": ["RateLimiter.check_limit"]
        },
        {
            "name": "RATE_LIMIT_WINDOW",
            "description": "Rate limit window in seconds. Default: 60.",
            "used_by": ["RateLimiter.check_limit"]
        },
        {
            "name": "LOG_LEVEL",
            "description": "Application log level. Valid values: DEBUG, INFO, WARNING, ERROR.",
            "used_by": ["APIGateway.create_app"]
        },
    ],
    "CONFIG_KEY": [
        {
            "name": "jwt_expiry_seconds",
            "value": "3600",
            "description": "JWT token time-to-live in seconds. Default 3600 (1 hour).",
            "configured_by": ["JWTAuthenticator.create_token"]
        },
        {
            "name": "db_connection_timeout",
            "value": "5",
            "description": "PostgreSQL connection timeout in seconds.",
            "configured_by": ["DatabaseConnection.connect"]
        },
        {
            "name": "rate_limit_enabled",
            "value": "true",
            "description": "Master switch for rate limiting. Set to false to disable.",
            "configured_by": ["RateLimiter.check_limit"]
        },
        {
            "name": "cors_origins",
            "value": "['http://localhost:3000']",
            "description": "Allowed CORS origins list as JSON array.",
            "configured_by": ["APIGateway.add_middleware"]
        },
    ],
}


def already_seeded():
    """Check if the seed data was already loaded by looking for known entities."""
    result = db.records.find({"labels": ["FUNCTION"], "limit": 1})
    return len(result.data) > 0


def create_entities():
    """Create all typed entities in RushDB, tracking them by name for linking."""
    created = {}  # label -> {name -> record}

    with db.transactions.begin() as tx:
        for label, entity_list in ENTITIES.items():
            created[label] = {}
            for entity in entity_list:
                record = db.records.create(
                    label=label,
                    data=entity,
                    transaction=tx
                )
                created[label][entity["name"]] = record

    return created


def link_relationships(created):
    """Create explicit edges between entities based on their declared relationships."""
    # Map entity names to (label, record) for lookup
    all_entities = {}
    for label, entries in created.items():
        for name, record in entries.items():
            all_entities[name] = (label, record)

    with db.transactions.begin() as tx:
        # FUNCTION -> FUNCTION (calls)
        for func_data in ENTITIES["FUNCTION"]:
            if "calls" not in func_data:
                continue
            source_record = created["FUNCTION"].get(func_data["name"])
            if not source_record:
                continue
            for callee_name in func_data["calls"]:
                if callee_name not in all_entities:
                    continue
                target_record = all_entities[callee_name][1]
                db.records.attach(
                    source=source_record,
                    target=target_record,
                    options={"type": "CALLS"},
                    transaction=tx
                )

        # API_ENDPOINT -> FUNCTION (uses)
        for endpoint_data in ENTITIES["API_ENDPOINT"]:
            source = created["API_ENDPOINT"].get(f"{endpoint_data['method']} {endpoint_data['path']}")
            if not source:
                continue
            for callee_name in endpoint_data.get("calls", []):
                if callee_name not in all_entities:
                    continue
                target_record = all_entities[callee_name][1]
                db.records.attach(
                    source=source,
                    target=target_record,
                    options={"type": "CALLS"},
                    transaction=tx
                )

        # CLASS -> FUNCTION (contains)
        for class_data in ENTITIES["CLASS"]:
            class_record = created["CLASS"].get(class_data["name"])
            if not class_record:
                continue
            for method_name in class_data.get("methods", []):
                method_record = created["FUNCTION"].get(method_name)
                if not method_record:
                    continue
                db.records.attach(
                    source=class_record,
                    target=method_record,
                    options={"type": "CONTAINS"},
                    transaction=tx
                )

        # CLASS -> CLASS (imports / depends on)
        class_imports = [
            ("JWTAuthenticator", "TokenValidator"),
            ("UserService", "DBQuery"),
            ("APIGateway", "RateLimiter"),
            ("check_auth_middleware", "validate_token"),
            ("execute_query", "DatabaseConnection"),
            ("get_user_settings", "DatabaseConnection"),
        ]
        for from_class, to_class in class_imports:
            src = created["FUNCTION"].get(from_class) or created["CLASS"].get(from_class)
            dst = created["CLASS"].get(to_class) or created["FUNCTION"].get(to_class)
            if src and dst:
                db.records.attach(
                    source=src,
                    target=dst,
                    options={"type": "DEPENDS_ON"},
                    transaction=tx
                )

        # FUNCTION / CLASS -> ENV_VAR (reads env)
        for env_data in ENTITIES["ENV_VAR"]:
            env_record = created["ENV_VAR"].get(env_data["name"])
            if not env_record:
                continue
            for consumer_name in env_data.get("used_by", []):
                if consumer_name not in all_entities:
                    continue
                consumer_record = all_entities[consumer_name][1]
                db.records.attach(
                    source=consumer_record,
                    target=env_record,
                    options={"type": "READS_ENV"},
                    transaction=tx
                )

        # CONFIG_KEY -> CLASS / FUNCTION (configures)
        for config_data in ENTITIES["CONFIG_KEY"]:
            cfg_record = created["CONFIG_KEY"].get(config_data["name"])
            if not cfg_record:
                continue
            for configurer_name in config_data.get("configured_by", []):
                if configurer_name not in all_entities:
                    continue
                configurer_record = all_entities[configurer_name][1]
                db.records.attach(
                    source=cfg_record,
                    target=configurer_record,
                    options={"type": "CONFIGS"},
                    transaction=tx
                )


def create_vector_index():
    """Create an external vector index on function/class bodies for semantic search."""
    indexes = db.ai.indexes.find().data
    for idx in indexes:
        if idx["label"] == "FUNCTION" and idx["propertyName"] == "description":
            print("  Vector index already exists, skipping creation.")
            return

    index = db.ai.indexes.create({
        "label": "FUNCTION",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine",
    })
    print(f"  Created vector index: {index.data.get('__id', index.id)}")


def main():
    print("\n" + "=" * 62)
    print("  Entity-Aware Chunking — Seed Script")
    print("=" * 62)

    if already_seeded():
        print("\n  [SKIP] Data already exists. To re-seed, delete records first.")
        print("  Running link+vector steps only.\n")
    else:
        print("\n  [1/2] Creating entities...")
        start = time.time()
        created = create_entities()
        elapsed = time.time() - start
        total = sum(len(v) for v in ENTITIES.values())
        print(f"  Created {total} entities in {elapsed:.1f}s")

    print("\n  [2/2] Creating relationships...")
    start = time.time()
    link_relationships(created)
    elapsed = time.time() - start
    print(f"  Linked all entities in {elapsed:.1f}s")

    print("\n  [3/3] Setting up vector index...")
    create_vector_index()

    print("\n  ✓ Seed complete. Run `python main.py` to execute the demo.\n")


if __name__ == "__main__":
    main()
