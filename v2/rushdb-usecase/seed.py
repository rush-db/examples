#!/usr/bin/env python3
"""
RushDB Use Case: Developer Documentation Knowledge Graph Seeder

This script creates a knowledge graph representing developer documentation
with APIs, modules, and services. It demonstrates RushDB's unified
vector + graph data model.

Run this script once to populate the database with sample data.
Subsequent runs will skip seeding if data already exists.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer
import hashlib

# Initialize embedding model (all-MiniLM-L6-v2 is fast and accurate)
print("Loading embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


def generate_embedding(text: str) -> list:
    """Generate vector embedding for text content."""
    return embedding_model.encode(text).tolist()


def seed_data():
    """Seed the knowledge graph with developer documentation."""
    
    api_key = os.getenv('RUSHDB_API_KEY')
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Please create a .env file with your RushDB API key")
        sys.exit(1)
    
    db = RushDB(api_key)
    
    # Check if data already exists
    existing_apis = db.records.find({"labels": ["API"], "limit": 1})
    if existing_apis.data:
        print("\n✓ Data already exists. Skipping seed.")
        print("  To re-seed, delete existing records first.\n")
        return
    
    print("\n🚀 Seeding developer documentation knowledge graph...\n")
    
    # =========================================================================
    # Create API Records with Vector Embeddings
    # =========================================================================
    
    apis_data = [
        {
            "name": "POST /auth/login",
            "description": "Authenticate user with email and password. Returns JWT access token and refresh token. Token expires in 1 hour (access) and 7 days (refresh).",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "category": "Authentication"
        },
        {
            "name": "POST /auth/refresh",
            "description": "Exchange a valid refresh token for a new access token. Validates token signature and expiration.",
            "method": "POST",
            "path": "/api/v1/auth/refresh",
            "category": "Authentication"
        },
        {
            "name": "POST /auth/logout",
            "description": "Invalidate current session and revoke all tokens associated with the user session.",
            "method": "POST",
            "path": "/api/v1/auth/logout",
            "category": "Authentication"
        },
        {
            "name": "GET /users/{id}",
            "description": "Retrieve user profile by ID. Returns user metadata including name, email, and account status.",
            "method": "GET",
            "path": "/api/v1/users/{id}",
            "category": "User Management"
        },
        {
            "name": "PUT /users/{id}",
            "description": "Update user profile fields. Supports partial updates. Validates email uniqueness and password strength.",
            "method": "PUT",
            "path": "/api/v1/users/{id}",
            "category": "User Management"
        },
        {
            "name": "GET /orders",
            "description": "List all orders for authenticated user with pagination. Supports filtering by status, date range.",
            "method": "GET",
            "path": "/api/v1/orders",
            "category": "Orders"
        },
        {
            "name": "POST /orders",
            "description": "Create a new order. Validates inventory availability and applies pricing rules.",
            "method": "POST",
            "path": "/api/v1/orders",
            "category": "Orders"
        },
        {
            "name": "GET /products",
            "description": "Search and filter product catalog. Supports full-text search, category filters, price range.",
            "method": "GET",
            "path": "/api/v1/products",
            "category": "Products"
        },
        {
            "name": "GET /products/{id}",
            "description": "Get detailed product information including pricing, inventory count, and images.",
            "method": "GET",
            "path": "/api/v1/products/{id}",
            "category": "Products"
        },
        {
            "name": "POST /payments",
            "description": "Initiate payment transaction. Supports multiple payment methods including credit card and PayPal.",
            "method": "POST",
            "path": "/api/v1/payments",
            "category": "Payments"
        },
        {
            "name": "GET /cache/{key}",
            "description": "Retrieve cached data by key. Returns null if key doesn't exist or has expired.",
            "method": "GET",
            "path": "/api/v1/cache/{key}",
            "category": "Caching"
        },
        {
            "name": "POST /cache",
            "description": "Store data in cache with optional TTL. Supports automatic invalidation patterns.",
            "method": "POST",
            "path": "/api/v1/cache",
            "category": "Caching"
        },
        {
            "name": "POST /notifications",
            "description": "Send push notification or email to user. Supports template variables and scheduling.",
            "method": "POST",
            "path": "/api/v1/notifications",
            "category": "Notifications"
        },
        {
            "name": "GET /analytics/events",
            "description": "Query user analytics events with segmentation. Returns aggregated metrics and trends.",
            "method": "GET",
            "path": "/api/v1/analytics/events",
            "category": "Analytics"
        }
    ]
    
    print("Creating API records with embeddings...")
    api_records = []
    for i, api in enumerate(apis_data):
        embedding = generate_embedding(api["description"])
        record = db.records.create(
            label="API",
            data={
                "name": api["name"],
                "description": api["description"],
                "method": api["method"],
                "path": api["path"],
                "category": api["category"]
            },
            vectors=[{"propertyName": "description", "vector": embedding}]
        )
        api_records.append(record)
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(apis_data)} API records...")
    
    print(f"  ✓ Created {len(api_records)} API records with vector embeddings\n")
    
    # =========================================================================
    # Create Module Records (基础模块)
    # =========================================================================
    
    modules_data = [
        {"name": "JWT Module", "description": "Handles JSON Web Token creation, validation, and refresh logic"},
        {"name": "OAuth2 Provider", "description": "Implements OAuth2 authorization code and client credentials flows"},
        {"name": "Session Manager", "description": "Manages user sessions, track active connections, handle timeout"},
        {"name": "Rate Limiter", "description": "Enforces API rate limits per user and IP address"},
        {"name": "Database ORM", "description": "Object-relational mapping layer for PostgreSQL and MySQL"},
        {"name": "Redis Cache", "description": "Distributed caching with Redis, supports pub/sub and TTL"},
        {"name": "Email Service", "description": "Sends transactional emails via SendGrid with templates"},
        {"name": "Payment Gateway", "description": "Integrates with Stripe and PayPal for payment processing"},
        {"name": "Inventory Service", "description": "Tracks product stock levels and reservation logic"},
        {"name": "Analytics Pipeline", "description": "Processes and aggregates user behavior events in real-time"}
    ]
    
    print("Creating Module records...")
    module_records = []
    for module in modules_data:
        record = db.records.create(
            label="Module",
            data={
                "name": module["name"],
                "description": module["description"]
            }
        )
        module_records.append(record)
    print(f"  ✓ Created {len(module_records)} Module records\n")
    
    # =========================================================================
    # Create Service Records (业务服务)
    # =========================================================================
    
    services_data = [
        {"name": "Frontend Web App", "description": "React-based web client for end users"},
        {"name": "Mobile App Backend", "description": "Node.js backend serving iOS and Android apps"},
        {"name": "Admin Dashboard", "description": "Internal tool for customer support and operations"},
        {"name": "Order Processing Worker", "description": "Background job processor for order fulfillment"},
        {"name": "Email Worker", "description": "Background processor for sending transactional emails"},
        {"name": "Analytics Collector", "description": "Service that ingests and processes user events"},
        {"name": "Payment Processor", "description": "Handles payment webhook events and reconciliation"}
    ]
    
    print("Creating Service records...")
    service_records = []
    for service in services_data:
        record = db.records.create(
            label="Service",
            data={
                "name": service["name"],
                "description": service["description"]
            }
        )
        service_records.append(record)
    print(f"  ✓ Created {len(service_records)} Service records\n")
    
    # =========================================================================
    # Create Relationships
    # =========================================================================
    
    print("Creating relationships...")
    
    # Module -> API: IMPLEMENTS relationship
    # JWT Module implements auth/login and auth/refresh
    jwt_module = module_records[0]
    auth_login_api = api_records[0]  # POST /auth/login
    auth_refresh_api = api_records[1]  # POST /auth/refresh
    
    db.records.attach(source=jwt_module, target=auth_login_api, options={"type": "IMPLEMENTS"})
    db.records.attach(source=jwt_module, target=auth_refresh_api, options={"type": "IMPLEMENTS"})
    
    # Session Manager implements logout
    session_module = module_records[2]
    auth_logout_api = api_records[2]  # POST /auth/logout
    db.records.attach(source=session_module, target=auth_logout_api, options={"type": "IMPLEMENTS"})
    
    # Rate Limiter implements orders endpoint
    rate_limiter = module_records[3]
    orders_api = api_records[5]  # GET /orders
    db.records.attach(source=rate_limiter, target=orders_api, options={"type": "PROTECTS"})
    
    # Database ORM implements user and order endpoints
    db_orm = module_records[4]
    user_get_api = api_records[3]  # GET /users/{id}
    user_put_api = api_records[4]  # PUT /users/{id}
    orders_post_api = api_records[6]  # POST /orders
    
    db.records.attach(source=db_orm, target=user_get_api, options={"type": "BACKS"})
    db.records.attach(source=db_orm, target=user_put_api, options={"type": "BACKS"})
    db.records.attach(source=db_orm, target=orders_post_api, options={"type": "BACKS"})
    
    # Redis Cache implements cache endpoints
    redis_module = module_records[5]
    cache_get_api = api_records[10]  # GET /cache/{key}
    cache_post_api = api_records[11]  # POST /cache
    
    db.records.attach(source=redis_module, target=cache_get_api, options={"type": "POWERS"})
    db.records.attach(source=redis_module, target=cache_post_api, options={"type": "POWERS"})
    
    # Email Service implements notifications
    email_module = module_records[6]
    notification_api = api_records[12]  # POST /notifications
    db.records.attach(source=email_module, target=notification_api, options={"type": "POWERS"})
    
    # Payment Gateway implements payments
    payment_module = module_records[7]
    payment_api = api_records[9]  # POST /payments
    db.records.attach(source=payment_module, target=payment_api, options={"type": "POWERS"})
    
    # Inventory Service implements products
    inventory_module = module_records[8]
    products_api = api_records[7]  # GET /products
    products_detail_api = api_records[8]  # GET /products/{id}
    
    db.records.attach(source=inventory_module, target=products_api, options={"type": "BACKS"})
    db.records.attach(source=inventory_module, target=products_detail_api, options={"type": "BACKS"})
    
    # Analytics Pipeline implements analytics events
    analytics_module = module_records[9]
    analytics_api = api_records[13]  # GET /analytics/events
    db.records.attach(source=analytics_module, target=analytics_api, options={"type": "POWERS"})
    
    print("  ✓ Created Module -> API relationships\n")
    
    # =========================================================================
    # Service -> API: CONSUMES relationship
    # =========================================================================
    
    # Frontend Web App consumes auth, users, orders, products
    frontend = service_records[0]
    db.records.attach(source=frontend, target=auth_login_api, options={"type": "CONSUMES"})
    db.records.attach(source=frontend, target=auth_logout_api, options={"type": "CONSUMES"})
    db.records.attach(source=frontend, target=user_get_api, options={"type": "CONSUMES"})
    db.records.attach(source=frontend, target=orders_api, options={"type": "CONSUMES"})
    db.records.attach(source=frontend, target=products_api, options={"type": "CONSUMES"})
    db.records.attach(source=frontend, target=products_detail_api, options={"type": "CONSUMES"})
    
    # Mobile App Backend consumes auth, users, orders
    mobile_backend = service_records[1]
    db.records.attach(source=mobile_backend, target=auth_login_api, options={"type": "CONSUMES"})
    db.records.attach(source=mobile_backend, target=auth_refresh_api, options={"type": "CONSUMES"})
    db.records.attach(source=mobile_backend, target=user_get_api, options={"type": "CONSUMES"})
    db.records.attach(source=mobile_backend, target=user_put_api, options={"type": "CONSUMES"})
    db.records.attach(source=mobile_backend, target=orders_api, options={"type": "CONSUMES"})
    db.records.attach(source=mobile_backend, target=orders_post_api, options={"type": "CONSUMES"})
    
    # Admin Dashboard consumes users, products, orders
    admin_dashboard = service_records[2]
    db.records.attach(source=admin_dashboard, target=user_get_api, options={"type": "CONSUMES"})
    db.records.attach(source=admin_dashboard, target=user_put_api, options={"type": "CONSUMES"})
    db.records.attach(source=admin_dashboard, target=products_api, options={"type": "CONSUMES"})
    db.records.attach(source=admin_dashboard, target=orders_api, options={"type": "CONSUMES"})
    
    # Order Processing Worker consumes orders, products, payments, cache
    order_worker = service_records[3]
    db.records.attach(source=order_worker, target=orders_post_api, options={"type": "CONSUMES"})
    db.records.attach(source=order_worker, target=products_api, options={"type": "CONSUMES"})
    db.records.attach(source=order_worker, target=payment_api, options={"type": "CONSUMES"})
    db.records.attach(source=order_worker, target=cache_get_api, options={"type": "CONSUMES"})
    
    # Email Worker consumes notifications, cache
    email_worker = service_records[4]
    db.records.attach(source=email_worker, target=notification_api, options={"type": "CONSUMES"})
    db.records.attach(source=email_worker, target=user_get_api, options={"type": "CONSUMES"})
    
    # Analytics Collector consumes analytics events
    analytics_collector = service_records[5]
    db.records.attach(source=analytics_collector, target=analytics_api, options={"type": "CONSUMES"})
    
    # Payment Processor consumes payments, orders, notifications
    payment_processor = service_records[6]
    db.records.attach(source=payment_processor, target=payment_api, options={"type": "CONSUMES"})
    db.records.attach(source=payment_processor, target=orders_post_api, options={"type": "CONSUMES"})
    db.records.attach(source=payment_processor, target=notification_api, options={"type": "CONSUMES"})
    
    print("  ✓ Created Service -> API relationships\n")
    
    # =========================================================================
    # Create Vector Index
    # =========================================================================
    
    print("Creating vector index...")
    try:
        # Create external index with correct dimensions (384 for all-MiniLM-L6-v2)
        index = db.ai.indexes.create({
            "label": "API",
            "propertyName": "description",
            "sourceType": "external",
            "dimensions": 384,  # all-MiniLM-L6-v2 outputs 384-dimensional vectors
            "similarityFunction": "cosine"
        })
        print(f"  ✓ Vector index created: {index.data.get('__id', 'unknown')}")
        print(f"  ✓ Status: {index.data.get('status', 'unknown')}\n")
    except Exception as e:
        print(f"  ⚠ Index creation note: {e}\n")
    
    print("=" * 60)
    print("✅ Seeding complete!")
    print("=" * 60)
    print(f"\nCreated:")
    print(f"  • {len(api_records)} API records with vector embeddings")
    print(f"  • {len(module_records)} Module records")
    print(f"  • {len(service_records)} Service records")
    print(f"  • Multiple relationship types (IMPLEMENTS, BACKS, POWERS, PROTECTS, CONSUMES)")
    print(f"\nRun `python main.py` to see the demo queries!\n")


if __name__ == "__main__":
    seed_data()
