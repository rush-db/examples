#!/usr/bin/env python3
"""
Seed script for the Prompt Optimization demo.

Creates technical documentation records with vector embeddings and establishes
documentation hierarchy relationships in RushDB.

This script is idempotent — it checks for existing data before seeding.
"""

import os
import json
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)

# Initialize embedding model
print("Loading embedding model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2')
EMBEDDING_DIM = 384

# Sample technical documentation for a developer tools company
DOCUMENTATION_DATA = [
    # API & Configuration
    {
        "title": "Environment Variables Reference",
        "category": "configuration",
        "body": "Environment variables control runtime behavior. KEY=value format. Use NODE_ENV for environment (development/production). RUSHDB_API_KEY for authentication. DEBUG=true enables verbose logging. PORT=3000 sets the server port. DATABASE_URL for connection string.",
        "tags": ["config", "environment", "setup"]
    },
    {
        "title": "Configuration File Syntax",
        "category": "configuration",
        "body": "Config files support JSON, YAML, and TOML formats. JSON: {key: value}. YAML: key: value. TOML: key = value. Environment variable substitution: ${VAR_NAME} or $VAR_NAME. Secret management: use --env-file flag or secrets manager integration.",
        "tags": ["config", "file", "json", "yaml", "toml"]
    },
    {
        "title": "CLI Command Reference",
        "category": "api",
        "body": "CLI commands: init (create project), build (compile assets), deploy (push to cloud), logs (view runtime), status (health check). Global flags: --verbose, --json (machine-readable output), --dry-run (preview without execution). Use --help for command-specific help.",
        "tags": ["cli", "command", "terminal"]
    },
    
    # Deployment & Infrastructure
    {
        "title": "Container Deployment Guide",
        "category": "deployment",
        "body": "Deploy using Docker containers. Dockerfile multi-stage builds reduce image size. Use ENTRYPOINT and CMD correctly. Health check endpoint at /health. Environment variables via --env flag or .env file. Volume mounts for persistent data. docker-compose for local development. Kubernetes deployment uses helm charts.",
        "tags": ["docker", "container", "deployment", "kubernetes"]
    },
    {
        "title": "CI/CD Pipeline Configuration",
        "category": "deployment",
        "body": "CI/CD pipelines run on commits. Stages: lint, test, build, deploy. Use caching for dependencies. Parallel jobs with stage-level parallelism. Environment promotion: dev -> staging -> production. Secrets via environment variables in pipeline settings. Artifacts pass between stages.",
        "tags": ["ci", "cd", "pipeline", "github-actions", "gitlab"]
    },
    {
        "title": "Serverless Deployment",
        "category": "deployment",
        "body": "Serverless functions auto-scale. Handler function receives event and context. Memory and timeout configurable. Cold starts affect latency. Use connection pooling for database access. Environment variables via dashboard or CLI. Max execution time: 900 seconds. Concurrency: 1000 per region by default.",
        "tags": ["serverless", "lambda", "function", "scaling"]
    },
    
    # Development Workflow
    {
        "title": "Hot Reload Development",
        "category": "development",
        "body": "Hot reload updates changed files without restart. Webpack-dev-server and Vite support HMR. React Fast Refresh for components. CSS changes apply immediately. File watching uses chokidar. Network errors fallback to full reload. Configure watch paths in webpack.config.js or vite.config.ts.",
        "tags": ["hot-reload", "hmr", "development", "webpack", "vite"]
    },
    {
        "title": "Tree Shaking Optimization",
        "category": "development",
        "body": "Tree shaking removes unused code from bundles. ES modules (import/export) required. Side effects in modules prevent shaking. Mark libraries as side-effect-free. Use production mode (NODE_ENV=production). Terser identifies unreachable code. Analyze bundle with webpack-bundle-analyzer. CommonJS requires Babel transform.",
        "tags": ["tree-shaking", "optimization", "bundle", "webpack"]
    },
    {
        "title": "TypeScript Configuration",
        "category": "development",
        "body": "tsconfig.json controls TypeScript compilation. target: ES2020 specifies output. module: commonjs for Node, esnext for bundlers. strict: true enables all checks. paths: for aliases. include/exclude for file globbing. build mode for project references. Watch mode for incremental compilation.",
        "tags": ["typescript", "config", "tsconfig"]
    },
    {
        "title": "Debugging in Development",
        "category": "troubleshooting",
        "body": "Debug with console.log or debugger statement. VS Code launch.json for attach debugging. Node --inspect flag enables Chrome DevTools. Source maps for minified code. Console methods: log, warn, error, debug. Performance profiling with performance.mark(). Memory leaks use heap snapshots.",
        "tags": ["debug", "development", "vscode", "node"]
    },
    
    # Authentication & Security
    {
        "title": "API Key Authentication",
        "category": "authentication",
        "body": "API keys authenticate requests. Pass via Authorization header: Bearer <key>. Environment variable: API_KEY. Keys have scopes (read, write, admin). Rotate keys via dashboard. Rate limits: 1000 requests/minute. Invalid keys return 401. Store keys securely, never commit to git.",
        "tags": ["auth", "api-key", "security"]
    },
    {
        "title": "OAuth 2.0 Integration",
        "category": "authentication",
        "body": "OAuth 2.0 flow: authorize -> token -> API calls. Grant types: authorization code (web apps), client credentials (server-to-server). Scopes limit access. Access tokens expire (1 hour default). Refresh tokens for renewal. PKCE for public clients. Redirect URI must be registered.",
        "tags": ["oauth", "auth", "security", "token"]
    },
    {
        "title": "JWT Token Validation",
        "category": "authentication",
        "body": "JWT tokens contain claims (user info). Validate signature using public key. Check expiration (exp claim). Verify audience (aud claim). Issuer validation (iss claim). Store secret securely. Refresh tokens before expiry. Revoke tokens via blocklist.",
        "tags": ["jwt", "token", "auth", "security"]
    },
    
    # Performance & Optimization
    {
        "title": "Caching Strategies",
        "category": "performance",
        "body": "Caching reduces latency and load. Cache-Control header: max-age, no-cache, no-store. ETag for conditional requests. CDN caching for static assets. Redis for application cache. Cache invalidation: time-based, event-based, or manual. LRU eviction for memory limits.",
        "tags": ["cache", "performance", "redis", "cdn"]
    },
    {
        "title": "Database Connection Pooling",
        "category": "performance",
        "body": "Connection pooling reuses database connections. Pool size affects throughput. Min connections: 5-10. Max connections: 20-50 based on DB. Connection timeout: 30 seconds. Idle timeout: 10 minutes. Health check query validates connections. PgBouncer or ProxySQL for connection management.",
        "tags": ["database", "pool", "performance", "postgres"]
    },
    {
        "title": "API Rate Limiting",
        "category": "performance",
        "body": "Rate limiting prevents abuse. Token bucket algorithm. Headers: X-RateLimit-Limit, X-RateLimit-Remaining. 429 Too Many Requests on limit. Retry-After header for backoff. Configurable limits per endpoint. IP-based and user-based limits. Distributed rate limiting uses Redis.",
        "tags": ["rate-limit", "api", "performance"]
    },
    
    # Monitoring & Observability
    {
        "title": "Logging Best Practices",
        "category": "monitoring",
        "body": "Structured logging with JSON format. Log levels: debug, info, warn, error, fatal. Include request ID for tracing. Timestamps in UTC. Sensitive data redaction. Log aggregation with ELK or Loki. Log sampling for high-volume paths. Async logging avoids blocking.",
        "tags": ["logging", "monitoring", "observability"]
    },
    {
        "title": "Health Check Endpoints",
        "category": "monitoring",
        "body": "Health endpoints report service status. /health for liveness (is running). /ready for readiness (can accept traffic). Checks: database, cache, external services. Return 200 OK or 503 Service Unavailable. Response includes component status. Timeout after 3 seconds.",
        "tags": ["health", "monitoring", "kubernetes"]
    },
    {
        "title": "Distributed Tracing Setup",
        "category": "monitoring",
        "body": "Distributed tracing tracks requests across services. Trace ID propagates via headers. Spans measure individual operations. OpenTelemetry for instrumentation. Jaeger or Zipkin for collection. Sample 10% of traffic in production. Context carries user info.",
        "tags": ["tracing", "opentelemetry", "monitoring", "debug"]
    },
    
    # Error Handling
    {
        "title": "Error Response Format",
        "category": "api",
        "body": "Error responses follow RFC 7807 (Problem Details). Fields: type (error code), title, detail, instance. HTTP status codes: 400 bad request, 401 unauthorized, 403 forbidden, 404 not found, 429 rate limited, 500 internal error. Stack traces only in development.",
        "tags": ["error", "api", "rest"]
    },
    {
        "title": "Retry Logic Implementation",
        "category": "troubleshooting",
        "body": "Retry transient failures with exponential backoff. Max retries: 3-5. Base delay: 1 second. Jitter prevents thundering herd. Retry on: 429, 500, 502, 503, 504. Don't retry on: 400, 401, 403, 404. Idempotent operations safe to retry. Circuit breaker prevents cascade failures.",
        "tags": ["retry", "resilience", "error-handling"]
    },
    {
        "title": "Graceful Shutdown",
        "category": "troubleshooting",
        "body": "Graceful shutdown handles in-flight requests. SIGTERM triggers shutdown. Stop accepting new requests. Complete existing requests. Close database connections. Flush logs. Exit with code 0. Timeout: 30 seconds before force kill. Health check returns 503 during shutdown.",
        "tags": ["shutdown", "signal", "deployment"]
    }
]


def check_existing_data():
    """Check if documentation already exists in the database."""
    try:
        result = db.records.find({"labels": ["DOCUMENTATION"], "limit": 1})
        return len(result.data) > 0
    except Exception:
        return False


def create_vector_index():
    """Create vector index for documentation body content."""
    try:
        indexes = db.ai.indexes.find()
        for idx in indexes.data:
            if idx['label'] == 'DOCUMENTATION' and idx['propertyName'] == 'body':
                print(f"Vector index already exists: {idx['label']}.{idx['propertyName']}")
                return
    except Exception:
        pass
    
    print("Creating vector index for DOCUMENTATION.body...")
    response = db.ai.indexes.create({
        "label": "DOCUMENTATION",
        "propertyName": "body",
        "sourceType": "external",
        "dimensions": EMBEDDING_DIM,
        "similarityFunction": "cosine"
    })
    print(f"Index created: {response.data.get('__id', 'unknown')}")


def seed_documentation():
    """Seed the database with technical documentation."""
    print(f"\nSeeding {len(DOCUMENTATION_DATA)} documentation records...\n")
    
    vectors_to_upsert = []
    
    for i, doc in enumerate(DOCUMENTATION_DATA):
        # Create documentation record
        record = db.records.create(
            label="DOCUMENTATION",
            data={
                "title": doc["title"],
                "category": doc["category"],
                "body": doc["body"],
                "tags": doc["tags"]
            }
        )
        
        # Generate embedding for the body
        vector = model.encode(doc["body"]).tolist()
        vectors_to_upsert.append({
            "recordId": record.id,
            "vector": vector
        })
        
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1}/{len(DOCUMENTATION_DATA)} records...")
    
    # Get the index ID
    indexes = db.ai.indexes.find()
    index_id = None
    for idx in indexes.data:
        if idx['label'] == 'DOCUMENTATION' and idx['propertyName'] == 'body':
            index_id = idx.get('__id') or idx.get('id')
            break
    
    if index_id:
        print(f"\nUpserting {len(vectors_to_upsert)} vectors...")
        db.ai.indexes.upsert_vectors(index_id, {"items": vectors_to_upsert})
        print("Vectors indexed successfully")
    
    print("\nDocumentation seeding complete!")
    return len(DOCUMENTATION_DATA)


def setup_category_relationships():
    """Create relationships between documentation by category."""
    print("\nSetting up category relationships...")
    
    categories = {}
    docs = db.records.find({"labels": ["DOCUMENTATION"]})
    
    for doc in docs:
        category = doc.data.get("category", "uncategorized")
        if category not in categories:
            categories[category] = []
        categories[category].append(doc)
    
    # Link documents within same category
    for category, docs_list in categories.items():
        if len(docs_list) > 1:
            for i, doc in enumerate(docs_list):
                for j, related in enumerate(docs_list):
                    if i < j:
                        db.records.attach(
                            source=doc,
                            target=related,
                            options={"type": "RELATED_TO", "direction": "out"}
                        )
    
    print(f"  Created cross-references for {len(categories)} categories")


def main():
    print("=" * 60)
    print("RushDB Prompt Optimization - Data Seeding")
    print("=" * 60)
    
    # Check if data already exists
    if check_existing_data():
        print("\nDocumentation already exists in the database.")
        print("Skipping seeding. To re-seed, delete existing records first.\n")
        return
    
    # Create vector index
    create_vector_index()
    
    # Seed documentation
    count = seed_documentation()
    
    # Setup relationships
    setup_category_relationships()
    
    print("\n" + "=" * 60)
    print(f"Seeding complete! {count} documentation records ready.")
    print("=" * 60)


if __name__ == "__main__":
    main()
