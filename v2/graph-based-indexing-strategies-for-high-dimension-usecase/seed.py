"""
seed.py — Populates the Nexus Enterprise Platform support knowledge graph.

This script creates a realistic graph with:
  - Products → Components → Support Teams → Agents
  - Escalated Tickets → Resolutions → Documentation
  - Relationships connecting all entities

The script is idempotent: it clears existing data before seeding.
Progress is printed every 100 records.
"""

import os
import sys
import random
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load .env before importing RushDB
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# ─── Configuration ────────────────────────────────────────────────────────────

RUSHDB_API_KEY = os.environ.get("RUSHDB_API_KEY")
RUSHDB_URL = os.environ.get("RUSHDB_URL")

if not RUSHDB_API_KEY:
    print("❌  RUSHDB_API_KEY is not set. Copy .env.example to .env and fill it in.")
    sys.exit(1)

# ─── Embedding model (local, no API key needed) ─────────────────────────────────

print("📦  Loading embedding model (all-MiniLM-L6-v2)...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension


def embed(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    return embedder.encode(texts, normalize_embeddings=True).tolist()


# ─── Domain data ───────────────────────────────────────────────────────────────

PRODUCTS = [
    {"name": "Nexus API Gateway", "tier": "Enterprise", "description": "Central API gateway managing traffic routing, rate limiting, and request authentication for all Nexus services."},
    {"name": "Nexus Auth Service", "tier": "Enterprise", "description": "Identity and access management service handling SSO, OAuth2, MFA, and LDAP integration."},
    {"name": "Nexus Data Lake", "tier": "Standard", "description": "Petabyte-scale analytical data warehouse with SQL query engine and streaming ingestion pipelines."},
    {"name": "Nexus Event Bus", "tier": "Enterprise", "description": "Distributed event streaming backbone based on Kafka, providing durable pub/sub messaging across services."},
    {"name": "Nexus Workflow Engine", "tier": "Enterprise", "description": "Low-code workflow orchestration platform for automating business processes with human approval steps."},
    {"name": "Nexus Notification Hub", "tier": "Standard", "description": "Multi-channel notification service (email, SMS, push, Slack) with template management and delivery tracking."},
]

COMPONENTS = [
    {"name": "API Gateway Core", "slug": "api-gateway-core", "product": "Nexus API Gateway"},
    {"name": "Rate Limiter Module", "slug": "rate-limiter", "product": "Nexus API Gateway"},
    {"name": "OAuth2 / OIDC Provider", "slug": "auth-oauth2", "product": "Nexus Auth Service"},
    {"name": "LDAP Directory Connector", "slug": "auth-ldap", "product": "Nexus Auth Service"},
    {"name": "Data Lake Query Engine", "slug": "datalake-query", "product": "Nexus Data Lake"},
    {"name": "Data Lake Ingestion API", "slug": "datalake-ingest", "product": "Nexus Data Lake"},
    {"name": "Event Bus Broker Cluster", "slug": "eventbus-broker", "product": "Nexus Event Bus"},
    {"name": "Event Bus Schema Registry", "slug": "eventbus-schema", "product": "Nexus Event Bus"},
    {"name": "Workflow Builder UI", "slug": "workflow-ui", "product": "Nexus Workflow Engine"},
    {"name": "Workflow Execution Engine", "slug": "workflow-executor", "product": "Nexus Workflow Engine"},
    {"name": "Notification Delivery Service", "slug": "notify-delivery", "product": "Nexus Notification Hub"},
    {"name": "Notification Template Engine", "slug": "notify-templates", "product": "Nexus Notification Hub"},
]

TEAMS = [
    {"name": "Enterprise Support", "slug": "enterprise-support", "priority": "P1"},
    {"name": "Developer Platform", "slug": "dev-platform", "priority": "P2"},
    {"name": "Security Operations", "slug": "security-ops", "priority": "P1"},
]

AGENTS = [
    {"name": "Sarah Chen", "team": "Enterprise Support", "role": "Senior Support Engineer"},
    {"name": "Marcus Johnson", "team": "Enterprise Support", "role": "Support Lead"},
    {"name": "Priya Patel", "team": "Developer Platform", "role": "Developer Support Engineer"},
    {"name": "Alex Rivera", "team": "Developer Platform", "role": "Technical Account Manager"},
    {"name": "Jordan Kim", "team": "Security Operations", "role": "Security Engineer"},
    {"name": "Morgan Lee", "team": "Security Operations", "role": "Security Lead"},
]

# Tickets are seeded with realistic data and embedded descriptions
TICKET_TEMPLATES = [
    {"severity": "Critical", "category": "Outage", "component": "auth-oauth2",
     "title": "Auth service SSO timeout causing widespread login failures",
     "description": "Multiple enterprise customers report SSO timeouts lasting 30-60 seconds after IdP configuration change deployed at 14:00 UTC. Affects all downstream services requiring auth tokens."},
    {"severity": "Critical", "category": "Outage", "component": "eventbus-broker",
     "title": "Event Bus broker cluster partition failure during peak traffic",
     "description": "Kafka broker nodes losing quorum after network partition. Consumer lag growing to 2M+ messages. Incident started at 09:30 UTC during weekly reporting job."},
    {"severity": "High", "category": "Degradation", "component": "auth-ldap",
     "title": "LDAP sync timeout during bulk user import in enterprise tenant",
     "description": "LDAP connector timing out when syncing >5000 users. Connection pool exhaustion suspected. Customer is mid-migration and unable to provision new users."},
    {"severity": "High", "category": "Degradation", "component": "auth-oauth2",
     "title": "MFA provider certificate expiry causing MFA loop on login",
     "description": "Okta OIDC certificate expired without auto-renewal triggering. Users with MFA enabled enter redirect loop. Root cert rotated manually by customer 3rd-party team."},
    {"severity": "High", "category": "Bug", "component": "api-gateway-core",
     "title": "API gateway dropping long-running WebSocket connections after 60s",
     "description": "Clients report unexpected disconnection of WebSocket sessions after 60 seconds of inactivity. Keep-alive headers appear to be ignored by gateway v3.14 configuration."},
    {"severity": "High", "category": "Degradation", "component": "datalake-ingest",
     "title": "Data Lake ingestion throughput dropped to 10% of baseline",
     "description": "Streaming ingestion via Kafka connector producing at ~500 records/sec vs normal 50K/sec. No config changes on customer side. Checkpoint lag visible in Kafka consumer group."},
    {"severity": "Medium", "category": "Bug", "component": "rate-limiter",
     "title": "Rate limiter not respecting per-client overrides from API config",
     "description": "Global rate limit of 1000 req/min applied even for clients with explicit 10000 req/min override in API configuration. Override stored in Redis but gateway not reading it."},
    {"severity": "Medium", "category": "Config", "component": "workflow-executor",
     "title": "Workflow executor not loading updated environment variables on restart",
     "description": "Workflows fail after pod restart because cached env vars not refreshed from ConfigMap. Workaround: manual pod deletion forces fresh init — but this is disruptive."},
    {"severity": "Low", "category": "Request", "component": "notify-templates",
     "title": "Request for Liquid template syntax support in notification templates",
     "description": "Customer wants to use Liquid template syntax for conditional content in email templates. Currently only basic variable substitution is supported. Feature request submitted."},
    {"severity": "Medium", "category": "Degradation", "component": "eventbus-schema",
     "title": "Schema Registry schema auto-registration not working for Avro topics",
     "description": "Avro-encoded topics not auto-registering schemas. Schema compatibility mode set to BACKWARD but registration endpoint returns 409 with 'Schema not found' error."},
    {"severity": "Medium", "category": "Bug", "component": "datalake-query",
     "title": "Query engine returning incorrect results for JOIN with NULL keys",
     "description": "SQL JOIN on nullable foreign key column returns 0 rows instead of filtering out NULLs gracefully. Query works with COALESCE workaround. Reproducible on any nullable FK join."},
    {"severity": "Low", "category": "Config", "component": "api-gateway-core",
     "title": "CORS preflight requests failing for domains with special characters",
     "description": "CORS validation fails for origin domains containing unicode characters. ASCII-only domains work fine. Regex pattern in gateway CORS config not unicode-aware."},
    {"severity": "High", "category": "Bug", "component": "auth-oauth2",
     "title": "Auth token refresh race condition causing 401 storm",
     "description": "Under high concurrency, multiple threads simultaneously detect token expiry and attempt refresh. Race condition results in some requests getting 401 before new token is distributed."},
    {"severity": "Critical", "category": "Outage", "component": "auth-ldap",
     "title": "Auth service intermittent outage with LDAP back-end",
     "description": "LDAP service experiencing intermittent connection failures. Auth service returns 503 for 2-5% of requests. LDAP logs show connection reset by peer. Customer network team investigating upstream."},
    {"severity": "Medium", "category": "Bug", "component": "workflow-ui",
     "title": "Workflow builder canvas zoom controls unresponsive in Firefox 120",
     "description": "Mouse wheel zoom on workflow canvas does not work in Firefox 120+. Chrome and Edge unaffected. CSS transform origin point calculation off by one event preventing zoom handler."},
]

RESOLUTIONS = [
    {"rootCause": "Misconfigured OIDC provider JWKS endpoint — IdP changed from Okta to Azure AD without updating gateway trust store.",
     "solution": "Updated gateway JWKS URI config to point to Azure AD discovery endpoint. Forced cache invalidation on public key cache (TTL 5 min, was 60 min). Added monitoring alert on JWKS fetch errors.",
     "effectiveness": 5.0,
     "ticket_component": "auth-oauth2"},
    {"rootCause": "Kafka min.insync.replicas=2 with 3-node cluster; one node network partition caused ISR to drop below min ISR, pausing producers.",
     "solution": "Increased min.insync.replicas to 2 (was 2, confirmed). Added Rack-awareness topology to prevent single AZ failure from splitting quorum. Deployed Kafka 3.6 upgrade with improved partition leadership re-election.",
     "effectiveness": 4.5,
     "ticket_component": "eventbus-broker"},
    {"rootCause": "LDAP connector default connection timeout of 5 seconds too short for large directory sync; pool exhaustion from 20 parallel threads hitting timeout.",
     "solution": "Increased connection timeout to 30s, reduced parallelism to 5 threads with exponential backoff retry (3 attempts). Added per-tenant rate limiting on sync operations.",
     "effectiveness": 4.0,
     "ticket_component": "auth-ldap"},
    {"rootCause": "Okta OIDC signing certificate rotation not propagated to Nexus trust store; cert expired at midnight UTC causing all MFA-authenticated requests to fail.",
     "solution": "Customer rotated cert on Okta side; we re-imported new x5c into gateway trust store and set up cert expiry monitoring 30 days in advance. Added automated cert check in deployment pipeline.",
     "effectiveness": 5.0,
     "ticket_component": "auth-oauth2"},
    {"rootCause": "Gateway WebSocket keep-alive ping disabled by default in v3.14 config template; clients sending ping frames were being silently dropped.",
     "solution": "Enabled WINDOW_TICK setting in gateway config. Added connection health-check endpoint returning latency metric. Added client-side reconnection logic with exponential backoff.",
     "effectiveness": 4.0,
     "ticket_component": "api-gateway-core"},
    {"rootCause": "Kafka consumer checkpoint lag due to slow partition reassignment after broker restart; ingestion workers not recovering properly.",
     "solution": "Reset consumer group offsets to earliest for affected partitions. Added consumer lag alerting at 100K threshold. Updated consumer to commit offsets more frequently (every 100 msgs vs every 1000).",
     "effectiveness": 4.5,
     "ticket_component": "datalake-ingest"},
    {"rootCause": "Rate limit override values stored in Redis but read from in-memory cache in gateway; cache invalidated on config change but not on per-client config update.",
     "solution": "Added Redis keyspace notifications to trigger cache invalidation on rate limit config changes. Moved rate limit override lookup to Redis direct read with 30s local TTL.",
     "effectiveness": 4.5,
     "ticket_component": "rate-limiter"},
    {"rootCause": "Workflow executor loading environment variables at process init only; ConfigMap changes not triggering pod roll restart.",
     "solution": "Implemented inotify-based ConfigMap watcher in executor init script. Pod now restarts gracefully on ConfigMap change. Added config version checksum validation.",
     "effectiveness": 4.0,
     "ticket_component": "workflow-executor"},
]

DOCS = [
    {"title": "API Gateway Configuration Reference", "category": "Reference",
     "body": "Complete reference for all Nexus API Gateway configuration parameters including rate limits, CORS settings, JWT validation, request transformation, circuit breaker thresholds, and observability exporters."},
    {"title": "SSO Configuration and Troubleshooting", "category": "Troubleshooting",
     "body": "Step-by-step guide for configuring SSO with Okta, Azure AD, and Google Workspace. Covers common issues including certificate expiration, JWKS endpoint misconfiguration, attribute mapping, and MFA loop problems."},
    {"title": "LDAP / SAML Integration Guide", "category": "Setup",
     "body": "Guide for integrating Nexus Auth Service with enterprise LDAP directories (Active Directory, OpenLDAP) and SAML 2.0 identity providers. Includes connection pooling, timeout tuning, group sync, and SSL certificate configuration."},
    {"title": "Multi-Factor Authentication Setup", "category": "Setup",
     "body": "Configure TOTP, SMS, email, and hardware security key MFA for your Nexus organization. Covers MFA policy enforcement, exemptions, backup codes, and integration with IdPs supporting FIDO2/WebAuthn."},
    {"title": "Data Lake Query Engine Best Practices", "category": "Best Practices",
     "body": "Optimize Data Lake query performance with proper table partitioning, partitioning strategies, join ordering, predicate pushdown, and result caching. Includes query profiling tools and EXPLAIN plan interpretation."},
    {"title": "Event Bus Schema Registry Guide", "category": "Reference",
     "body": "Manage Avro and JSON Schema compatibility for Event Bus topics. Covers schema registration, evolution rules, backward/forward compatibility testing, and cross-topic dependency management."},
    {"title": "Workflow Engine Operator Guide", "category": "Operations",
     "body": "Operational runbook for Nexus Workflow Engine including deployment, scaling, monitoring with Prometheus/Grafana, health checks, rolling updates, and incident response procedures."},
    {"title": "Identity Provider Migration Playbook", "category": "Operations",
     "body": "Procedure for migrating from one IdP to another (e.g., Okta to Azure AD) with zero downtime. Includes token migration, session invalidation, certificate rotation, and rollback steps."},
    {"title": "Notification Hub Template Reference", "category": "Reference",
     "body": "Template syntax reference for Nexus Notification Hub. Covers variable substitution, conditional logic, loop syntax, personalization tokens, and multi-channel adaptation for email, SMS, and push."},
    {"title": "Auth Service Release Notes v4.2", "category": "Reference",
     "body": "Release notes for Nexus Auth Service v4.2 including new OAuth2 PKCE flow support, improved token refresh latency, new LDAP connection pooling algorithm, and security patches for CVE-2024-XXXX."},
]

# Map component slugs to team slugs for escalation routing
COMPONENT_TEAM_MAP = {
    "api-gateway-core": "enterprise-support",
    "rate-limiter": "enterprise-support",
    "auth-oauth2": "security-ops",
    "auth-ldap": "security-ops",
    "datalake-query": "dev-platform",
    "datalake-ingest": "dev-platform",
    "eventbus-broker": "enterprise-support",
    "eventbus-schema": "dev-platform",
    "workflow-ui": "dev-platform",
    "workflow-executor": "dev-platform",
    "notify-delivery": "dev-platform",
    "notify-templates": "dev-platform",
}

# ─── Init RushDB ───────────────────────────────────────────────────────────────

if RUSHDB_URL:
    db = RushDB(RUSHDB_API_KEY, url=RUSHDB_URL)
else:
    db = RushDB(RUSHDB_API_KEY)

print(f"✅  Connected to RushDB (labels: {db.labels.count() if hasattr(db.labels, 'count') else 'N/A'})")

# ─── Cleanup (idempotent seed) ─────────────────────────────────────────────────

print("\n🧹  Clearing existing data (idempotent seed)...")

for label in ["RESOLUTION", "DOCUMENTATION", "TICKET", "AGENT", "TEAM", "COMPONENT", "PRODUCT"]:
    try:
        db.records.delete_many({"labels": [label], "where": {}})
    except Exception:
        pass

# Clean up any existing vector indexes
try:
    existing_indexes = db.ai.indexes.find()
    for idx in existing_indexes:
        db.ai.indexes.delete(idx["__id"])
except Exception:
    pass

print("✅  Cleanup complete.")

# ─── Create vector index for documentation body ────────────────────────────────

print("\n📐  Creating vector index for documentation body...")
index = db.ai.indexes.create({
    "label": "DOCUMENTATION",
    "propertyName": "body",
    "sourceType": "external",
    "dimensions": EMBEDDING_DIM,
    "similarityFunction": "cosine",
})
index_id = index.data["__id"]
print(f"✅  Vector index created: {index_id}")

# ─── Seed: Products ───────────────────────────────────────────────────────────

print("\n🌱  Seeding products...")
products = {}
for i, p in enumerate(PRODUCTS):
    record = db.records.create(
        label="PRODUCT",
        data={"name": p["name"], "tier": p["tier"], "description": p["description"]},
        vectors=[{"propertyName": "description", "vector": embed([p["description"]])[0]}],
    )
    products[p["name"]] = record
    if (i + 1) % 100 == 0:
        print(f"  [{i+1}/{len(PRODUCTS)}] products created")
print(f"✅  Created {len(products)} products")

# ─── Seed: Components ─────────────────────────────────────────────────────────

print("\n🔩  Seeding components...")
components = {}
for i, c in enumerate(COMPONENTS):
    record = db.records.create(
        label="COMPONENT",
        data={"name": c["name"], "slug": c["slug"]},
    )
    products[c["product"]].attach(
        target=record,
        options={"type": "HAS_COMPONENT"},
    )
    components[c["slug"]] = record
    if (i + 1) % 100 == 0:
        print(f"  [{i+1}/{len(COMPONENTS)}] components created")
print(f"✅  Created {len(components)} components")

# ─── Seed: Teams ──────────────────────────────────────────────────────────────

print("\n👥  Seeding support teams...")
teams = {}
for i, t in enumerate(TEAMS):
    record = db.records.create(
        label="TEAM",
        data={"name": t["name"], "slug": t["slug"], "priority": t["priority"]},
    )
    teams[t["slug"]] = record
    if (i + 1) % 100 == 0:
        print(f"  [{i+1}/{len(TEAMS)}] teams created")
print(f"✅  Created {len(teams)} teams")

# ─── Seed: Agents ──────────────────────────────────────────────────────────────

print("\n🧑‍💻  Seeding support agents...")
for i, a in enumerate(AGENTS):
    record = db.records.create(
        label="AGENT",
        data={"name": a["name"], "role": a["role"]},
    )
    # Attach agent to their team
    record.attach(
        target=teams[a["team"]],
        options={"type": "MEMBER_OF", "direction": "out"},
    )
    if (i + 1) % 100 == 0:
        print(f"  [{i+1}/{len(AGENTS)}] agents created")
print(f"✅  Created {len(AGENTS)} agents")

# ─── Seed: Tickets ─────────────────────────────────────────────────────────────

print("\n🎫  Seeding escalated tickets...")
SEVERITY_ORDER = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
STATUSES = ["RESOLVED", "RESOLVED", "RESOLVED", "ESCALATED"]  # weighted toward RESOLVED

tickets = []
base_time = datetime(2025, 1, 1)

for i, t in enumerate(TICKET_TEMPLATES):
    status = random.choice(STATUSES)
    created_at = (base_time + timedelta(days=random.randint(0, 180), hours=random.randint(0, 23))).isoformat()
    record = db.records.create(
        label="TICKET",
        data={
            "ticketId": f"TKT-{1000 + i + 1}",
            "title": t["title"],
            "description": t["description"],
            "severity": t["severity"],
            "severityRank": SEVERITY_ORDER[t["severity"]],
            "category": t["category"],
            "status": status,
            "escalated": True,
            "createdAt": created_at,
        },
    )
    # Link ticket to component
    record.attach(
        target=components[t["component"]],
        options={"type": "AFFECTS_COMPONENT", "direction": "out"},
    )
    # Route to team via component
    team_slug = COMPONENT_TEAM_MAP.get(t["component"])
    if team_slug:
        record.attach(
            target=teams[team_slug],
            options={"type": "ESCALATED_TO", "direction": "out"},
        )
    tickets.append(record)
    if (i + 1) % 100 == 0:
        print(f"  [{i+1}/{len(TICKET_TEMPLATES)}] tickets created")
print(f"✅  Created {len(tickets)} tickets")

# ─── Seed: Resolutions ─────────────────────────────────────────────────────────

print("\n✅  Seeding resolutions...")
resolutions = []
for i, r in enumerate(RESOLUTIONS):
    record = db.records.create(
        label="RESOLUTION",
        data={
            "rootCause": r["rootCause"],
            "solution": r["solution"],
            "effectiveness": r["effectiveness"],
        },
    )
    # Link resolution to the component it addresses
    comp_record = components.get(r["ticket_component"])
    if comp_record:
        record.attach(
            target=comp_record,
            options={"type": "ADDRESSES_COMPONENT", "direction": "out"},
        )
    # For resolved tickets: link resolution to first matching ticket
    for ticket in tickets:
        if ticket["ticketId"][-1] == chr(ord('1') + i):
            record.attach(
                target=ticket,
                options={"type": "RESOLVES", "direction": "out"},
            )
            break
    resolutions.append(record)
    if (i + 1) % 100 == 0:
        print(f"  [{i+1}/{len(RESOLUTIONS)}] resolutions created")
print(f"✅  Created {len(resolutions)} resolutions")

# ─── Seed: Documentation ────────────────────────────────────────────────────────

print("\n📄  Seeding documentation articles...")
doc_vectors = embed([d["body"] for d in DOCS])

doc_items = []
for i, d in enumerate(DOCS):
    record = db.records.create(
        label="DOCUMENTATION",
        data={
            "title": d["title"],
            "category": d["category"],
            "body": d["body"],
        },
        vectors=[{"propertyName": "body", "vector": doc_vectors[i]}],
    )
    doc_items.append(record)
    if (i + 1) % 100 == 0:
        print(f"  [{i+1}/{len(DOCS)}] documents created")
print(f"✅  Created {len(doc_items)} documentation articles")

# ─── Upsert vector index ───────────────────────────────────────────────────────

print("\n📐  Upserting document vectors into index...")
db.ai.indexes.upsert_vectors(
    index_id,
    {
        "items": [
            {"recordId": doc.id, "vector": doc_vectors[i]}
            for i, doc in enumerate(doc_items)
        ]
    },
)

# ─── Verify index ─────────────────────────────────────────────────────────────

time.sleep(1)  # Brief wait for index to settle
stats = db.ai.indexes.stats(index_id)
print(f"\n✅  Index stats: {stats.get('indexedRecords', '?')} / {stats.get('totalRecords', '?')} records indexed")

# ─── Summary ──────────────────────────────────────────────────────────────────

print("\n╔════════════════════════════════════════════════════════╗")
print("║              Seed Complete — Graph Summary            ║")
print("╚════════════════════════════════════════════════════════╝")
all_labels = [
    ("PRODUCT", 6),
    ("COMPONENT", 12),
    ("TEAM", 3),
    ("AGENT", 6),
    ("TICKET", 15),
    ("RESOLUTION", 8),
    ("DOCUMENTATION", 10),
]
for label, count in all_labels:
    print(f"  {label:<15} {count} records")
print("\n✅  Run `python main.py` to execute the RAG query demos.")
