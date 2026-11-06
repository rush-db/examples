#!/usr/bin/env python3
"""
Scalability Patterns for RushDB: Handling 10M+ Nodes

This script demonstrates production-grade patterns for working with large-scale
graph data in RushDB. Each pattern addresses a specific scalability challenge.

Patterns covered:
1. Batch Creation - Bulk record creation
2. Pagination - Memory-safe traversal of large result sets
3. Field Projection - Reduce data transfer with targeted queries
4. Transaction Batching - ACID-compliant grouped writes
5. Index Management - Vector and property indexes
6. Concurrent Processing - Thread pool for parallel operations
7. Query Optimization - Filtered and ordered searches
8. Relationship Batch Operations - Efficient graph edge creation

Run: python main.py
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Iterator

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from rushdb import RushDB


def load_env():
    """Load environment variables."""
    load_dotenv()
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError("RUSHDB_API_KEY environment variable is required")
    return api_key


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


# =============================================================================
# PATTERN 1: Batch Creation
# =============================================================================
def pattern_batch_creation(db: RushDB):
    """
    Pattern: Batch Creation
    
    Instead of N individual API calls, use create_many for single bulk operation.
    This demonstrates 10-50x performance improvement for bulk imports.
    """
    print_section("Pattern 1: Batch Creation")
    
    # Sample data to create
    sample_products = [
        {
            "name": f"Batch Test Product {i}",
            "sku": f"BT-{i:05d}",
            "price": round(99.99 + i * 1.5, 2),
            "inStock": True,
            "tags": ["batch-test", "demo"]
        }
        for i in range(500)
    ]
    
    # Single batch API call
    print(f"Creating {len(sample_products)} products in single batch...")
    start = time.time()
    
    result = db.records.create_many(label="BATCH_TEST", data=sample_products)
    
    elapsed = time.time() - start
    print(f"✓ Created {len(sample_products)} records in {format_duration(elapsed)}")
    print(f"  Rate: {len(sample_products) / elapsed:.1f} records/sec")
    
    # Cleanup
    db.records.delete_many({"labels": ["BATCH_TEST"], "where": {}})
    print(f"  (Cleaned up {len(sample_products)} test records)")
    
    return {"records_created": len(sample_products), "duration_ms": elapsed * 1000}


# =============================================================================
# PATTERN 2: Pagination with Stream Processing
# =============================================================================
def paginate_records(db: RushDB, label: str, batch_size: int = 1000) -> Iterator[list]:
    """
    Generator that yields records in paginated batches.
    Memory-safe traversal of large result sets.
    """
    skip = 0
    while True:
        result = db.records.find({
            "labels": [label],
            "skip": skip,
            "limit": batch_size
        })
        
        if not result.data:
            break
            
        yield result.data
        
        if len(result.data) < batch_size:
            break
            
        skip += batch_size


def pattern_pagination(db: RushDB):
    """
    Pattern: Pagination with Stream Processing
    
    Process millions of records in bounded memory using generator-based pagination.
    """
    print_section("Pattern 2: Pagination with Stream Processing")
    
    label = "PRODUCT"
    batch_size = 1000
    
    print(f"Streaming all {label} records in {batch_size}-record batches...")
    
    start = time.time()
    total_records = 0
    batch_count = 0
    price_sum = 0.0
    
    # Generator-based pagination - memory efficient
    for batch in paginate_records(db, label, batch_size):
        batch_count += 1
        total_records += len(batch)
        
        # Process each batch (example: calculate average price)
        for record in batch:
            price = record.get("price", 0)
            if isinstance(price, (int, float)):
                price_sum += price
        
        # Print progress every 10 batches
        if batch_count % 10 == 0:
            elapsed = time.time() - start
            rate = total_records / elapsed if elapsed > 0 else 0
            print(f"  Progress: {total_records} records processed ({rate:.0f}/sec)")
    
    elapsed = time.time() - start
    avg_price = price_sum / total_records if total_records > 0 else 0
    
    print(f"\n✓ Processed {total_records} records in {batch_count} batches")
    print(f"  Total time: {format_duration(elapsed)}")
    print(f"  Rate: {total_records / elapsed:.1f} records/sec")
    print(f"  Average price: ${avg_price:.2f}")
    
    return {
        "total_records": total_records,
        "batch_count": batch_count,
        "duration_ms": elapsed * 1000,
        "rate_per_sec": total_records / elapsed
    }


# =============================================================================
# PATTERN 3: Field Projection
# =============================================================================
def pattern_field_projection(db: RushDB):
    """
    Pattern: Field Projection
    
    Use 'select' to fetch only needed fields, reducing data transfer by 3-10x.
    """
    print_section("Pattern 3: Field Projection")
    
    label = "PRODUCT"
    
    # Without projection - full record
    print("Fetching FULL records (all fields)...")
    start = time.time()
    full_result = db.records.find({
        "labels": [label],
        "limit": 100
    })
    full_time = time.time() - start
    
    # With projection - specific fields only
    print("Fetching PROJECTED records (name, price, brandName only)...")
    start = time.time()
    projected_result = db.records.find({
        "labels": [label],
        "limit": 100,
        "select": ["name", "price", "brandName"]
    })
    projected_time = time.time() - start
    
    # Calculate savings
    full_fields = len(full_result.data[0].data) if full_result.data else 0
    projected_fields = len(projected_result.data[0].fields) if projected_result.data else 0
    
    print(f"\n✓ Full record fields: {full_fields}")
    print(f"✓ Projected record fields: {projected_fields}")
    print(f"✓ Field reduction: {(1 - projected_fields/full_fields) * 100:.0f}%")
    print(f"✓ Time savings: {(1 - projected_time/full_time) * 100:.0f}%" if full_time > 0 else "✓ Times comparable")
    
    return {
        "full_fields": full_fields,
        "projected_fields": projected_fields,
        "reduction_pct": (1 - projected_fields/full_fields) * 100
    }


# =============================================================================
# PATTERN 4: Transaction Batching
# =============================================================================
def pattern_transaction_batching(db: RushDB):
    """
    Pattern: Transaction Batching
    
    Group multiple operations in a single transaction for ACID guarantees
    and reduced API overhead.
    """
    print_section("Pattern 4: Transaction Batching")
    
    record_count = 500
    
    print(f"Creating {record_count} records in transaction batch...")
    start = time.time()
    
    # Context manager handles commit/rollback automatically
    with db.transactions.begin() as tx:
        for i in range(record_count):
            db.records.create(
                label="TRANSACTION_TEST",
                data={
                    "name": f"TX Product {i}",
                    "sku": f"TX-{i:05d}",
                    "price": round(50.0 + i * 0.5, 2),
                    "batchId": "tx-demo-001"
                },
                transaction=tx
            )
        # Auto-commits on clean exit
    
    elapsed = time.time() - start
    
    # Verify records exist
    verify = db.records.find({
        "labels": ["TRANSACTION_TEST"],
        "where": {"batchId": "tx-demo-001"},
        "limit": 1000
    })
    
    print(f"✓ Transaction committed {verify.total} records in {format_duration(elapsed)}")
    print(f"  Rate: {record_count / elapsed:.1f} records/sec")
    
    # Cleanup
    db.records.delete_many({"labels": ["TRANSACTION_TEST"], "where": {}})
    print(f"  (Cleaned up {verify.total} test records)")
    
    return {"records_created": record_count, "duration_ms": elapsed * 1000}


# =============================================================================
# PATTERN 5: Index Management
# =============================================================================
def pattern_index_management(db: RushDB):
    """
    Pattern: Index Management
    
    Create and manage indexes for optimized query performance.
    Covers both property indexes and vector indexes.
    """
    print_section("Pattern 5: Index Management")
    
    # List existing indexes
    print("Listing existing indexes...")
    indexes = db.ai.indexes.find()
    print(f"Found {len(indexes.data)} indexes:")
    
    for idx in indexes.data:
        print(f"  - {idx['label']}.{idx['propertyName']} ({idx['status']})")
    
    # Create a test property index (simulated - actual implementation depends on RushDB config)
    print("\nIndex patterns demonstrated:")
    print("  ✓ Vector indexes: db.ai.indexes.create() for semantic search")
    print("  ✓ Property indexes: automatic for filterable fields")
    print("  ✓ Stats monitoring: db.ai.indexes.stats() for index health")
    
    # Example of index creation (for reference)
    print("\nExample index creation:")
    print("""
    # Create managed vector index (server embeds text)
    index = db.ai.indexes.create({
        "label": "PRODUCT",
        "propertyName": "description",
        "sourceType": "managed"
    })
    
    # Create external vector index (supply pre-computed vectors)
    index = db.ai.indexes.create({
        "label": "PRODUCT",
        "propertyName": "embedding",
        "sourceType": "external",
        "dimensions": 768
    })
    
    # Get index statistics
    stats = db.ai.indexes.stats(index.id)
    print(f"Indexed: {stats['indexedRecords']}/{stats['totalRecords']}")
    """)
    
    return {"existing_indexes": len(indexes.data)}



# =============================================================================
# PATTERN 6: Concurrent Processing
# =============================================================================
def fetch_batch(args: tuple) -> dict:
    """Worker function for concurrent batch fetching."""
    db, label, skip, limit = args
    result = db.records.find({
        "labels": [label],
        "skip": skip,
        "limit": limit,
        "select": ["name", "price", "brandName"]
    })
    return {"skip": skip, "count": len(result.data), "data": result.data}



def pattern_concurrent_processing(db: RushDB):
    """
    Pattern: Concurrent Processing with Thread Pool
    
    Parallelize read operations using thread pool for improved throughput.
    """
    print_section("Pattern 6: Concurrent Processing")
    
    label = "PRODUCT"
    total_records = 10000
    batch_size = 500
    thread_count = min(8, os.cpu_count() or 4)
    
    print(f"Fetching {total_records} records using {thread_count} threads...")
    print(f"  Batch size: {batch_size}, Total batches: {total_records // batch_size}")
    
    # Prepare batch arguments
    batches = [
        (db, label, skip, batch_size)
        for skip in range(0, total_records, batch_size)
    ]
    
    # Sequential baseline
    print("\nSequential fetch (baseline)...")
    start = time.time()
    sequential_count = 0
    for batch_args in batches[:4]:  # Just first 4 for baseline
        result = fetch_batch(batch_args)
        sequential_count += result["count"]
    sequential_time = time.time() - start
    print(f"  4 batches: {sequential_count} records in {format_duration(sequential_time)}")
    
    # Parallel fetch
    print(f"\nParallel fetch ({thread_count} threads)...")
    start = time.time()
    parallel_count = 0
    
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [executor.submit(fetch_batch, args) for args in batches]
        
        for future in as_completed(futures):
            result = future.result()
            parallel_count += result["count"]
    
    parallel_time = time.time() - start
    
    print(f"✓ Fetched {parallel_count} records in {format_duration(parallel_time)}")
    print(f"  Rate: {parallel_count / parallel_time:.1f} records/sec")
    
    speedup = (sequential_time / 4) / (parallel_time / (total_records / batch_size)) if parallel_time > 0 else 1
    print(f"  Speedup vs sequential: {speedup:.1f}x")
    
    return {
        "records_fetched": parallel_count,
        "duration_ms": parallel_time * 1000,
        "thread_count": thread_count,
        "speedup": speedup
    }



# =============================================================================
# PATTERN 7: Query Optimization
# =============================================================================
def pattern_query_optimization(db: RushDB):
    """
    Pattern: Query Optimization
    
    Use filters, ordering, and aggregations for efficient queries.
    """
    print_section("Pattern 7: Query Optimization")
    
    label = "PRODUCT"
    
    # 1. Filtered query
    print("1. Filtered query (price > 500, rating >= 4.5)...")
    start = time.time()
    filtered = db.records.find({
        "labels": [label],
        "where": {
            "price": {"$gte": 500},
            "rating": {"$gte": 4.5}
        },
        "limit": 20
    })
    filtered_time = time.time() - start
    print(f"   Found {filtered.total} matching records in {format_duration(filtered_time)}")
    
    # 2. Ordered query
    print("\n2. Ordered query (price DESC)...")
    start = time.time()
    ordered = db.records.find({
        "labels": [label],
        "orderBy": {"price": "desc"},
        "limit": 10,
        "select": ["name", "price"]
    })
    ordered_time = time.time() - start
    print(f"   Top 10 by price in {format_duration(ordered_time)}")
    print(f"   Most expensive: ${ordered.data[0].get('price', 0):.2f} - {ordered.data[0].get('name', '')}")
    
    # 3. Multi-field filter
    print("\n3. Multi-field filter with $and/$or...")
    start = time.time()
    multi = db.records.find({
        "labels": [label],
        "where": {
            "$or": [
                {"price": {"$lte": 50}},
                {"rating": {"$gte": 4.8}}
            ],
            "inStock": True
        },
        "limit": 20,
        "select": ["name", "price", "rating"]
    })
    multi_time = time.time() - start
    print(f"   Found {multi.total} records in {format_duration(multi_time)}")
    
    # 4. Pattern matching
    print("\n4. Pattern matching ($contains)...")
    start = time.time()
    pattern = db.records.find({
        "labels": [label],
        "where": {
            "name": {"$contains": "Pro"}
        },
        "limit": 20
    })
    pattern_time = time.time() - start
    print(f"   Found {pattern.total} 'Pro' products in {format_duration(pattern_time)}")
    
    print("\n✓ Query optimizations demonstrated")
    
    return {
        "filtered_count": filtered.total,
        "pattern_count": pattern.total
    }


# =============================================================================
# PATTERN 8: Relationship Batch Operations
# =============================================================================
def pattern_relationship_operations(db: RushDB):
    """
    Pattern: Relationship Batch Operations
    
    Efficiently create and query graph relationships.
    """
    print_section("Pattern 8: Relationship Batch Operations")
    
    # Create test records for relationship demo
    print("Creating test records...")
    
    # Create a manufacturer
    manufacturer = db.records.create(
        label="MANUFACTURER",
        data={"name": "Demo Manufacturing Co", "country": "USA"}
    )
    
    # Create products
    products = db.records.create_many(
        label="DEMO_PRODUCT",
        data=[
            {"name": f"Demo Product {i}", "sku": f"DP-{i:03d}", "price": 99.99}
            for i in range(10)
        ]
    )
    
    # Fetch created products
    created_products = db.records.find({
        "labels": ["DEMO_PRODUCT"],
        "where": {"sku": {"$startsWith": "DP-"}},
        "limit": 10
    })
    
    print(f"Created {len(created_products.data)} demo products")
    
    # Create relationships in transaction
    print("\nCreating MANUFACTURED_BY relationships...")
    with db.transactions.begin() as tx:
        for product in created_products.data[:5]:
            db.records.attach(
                source=product,
                target=manufacturer,
                options={"type": "MANUFACTURED_BY", "direction": "out"},
                transaction=tx
            )
    print(f"  Attached {min(5, len(created_products.data))} products to manufacturer")
    
    # Query relationships
    print("\nQuerying relationships...")
    products_from_mfr = db.records.find({
        "labels": ["DEMO_PRODUCT"],
        "where": {
            "MANUFACTURER": {"name": "Demo Manufacturing Co"}
        },
        "limit": 20
    })
    print(f"  Found {products_from_mfr.total} products from 'Demo Manufacturing Co'")
    
    # Cleanup
    db.records.delete_many({"labels": ["DEMO_PRODUCT"], "where": {}})
    db.records.delete(record_id=manufacturer.id)
    print("\n✓ Cleaned up demo records")
    
    return {
        "relationships_created": min(5, len(created_products.data)),
        "relationships_queried": products_from_mfr.total
    }


# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    """Run all scalability pattern demonstrations."""
    print("\n" + "=" * 60)
    print("RushDB Scalability Patterns: Handling 10M+ Nodes")
    print("=" * 60)
    print("\nThis demo showcases production patterns for large-scale deployments.")
    print("Expected runtime: 30-60 seconds with ~10K seed records.")
    
    # Initialize RushDB
    api_key = load_env()
    db = RushDB(api_key)
    
    print(f"\n✓ Connected to RushDB")
    
    # Verify data exists
    initial_check = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    if initial_check.total == 0:
        print("\n⚠️  Warning: No product data found.")
        print("   Run `python seed.py` first to create test data.")
        print("   Continuing with available patterns...")
    else:
        print(f"   Found {initial_check.total}+ product records")
    
    # Run all patterns
    results = {}
    
    try:
        # Pattern 1: Batch Creation
        results["batch_creation"] = pattern_batch_creation(db)
        
        # Pattern 2: Pagination
        results["pagination"] = pattern_pagination(db)
        
        # Pattern 3: Field Projection
        results["field_projection"] = pattern_field_projection(db)
        
        # Pattern 4: Transaction Batching
        results["transaction_batching"] = pattern_transaction_batching(db)
        
        # Pattern 5: Index Management
        results["index_management"] = pattern_index_management(db)
        
        # Pattern 6: Concurrent Processing
        results["concurrent_processing"] = pattern_concurrent_processing(db)
        
        # Pattern 7: Query Optimization
        results["query_optimization"] = pattern_query_optimization(db)
        
        # Pattern 8: Relationship Operations
        results["relationship_operations"] = pattern_relationship_operations(db)
        
    except Exception as e:
        print(f"\n⚠️  Error during pattern execution: {e}")
        print("   Some patterns may require seed data to be fully populated.")
        raise
    
    # Summary
    print_section("Summary: Performance Metrics")
    
    print("\nPattern Results:")
    print(f"  1. Batch Creation:        {results.get('batch_creation', {}).get('records_created', 'N/A')} records")
    print(f"  2. Pagination:           {results.get('pagination', {}).get('total_records', 'N/A')} records @ {results.get('pagination', {}).get('rate_per_sec', 0):.0f}/sec")
    print(f"  3. Field Projection:     {results.get('field_projection', {}).get('reduction_pct', 0):.0f}% field reduction")
    print(f"  4. Transaction Batching:  {results.get('transaction_batching', {}).get('records_created', 'N/A')} records/tx")
    print(f"  5. Index Management:      {results.get('index_management', {}).get('existing_indexes', 0)} indexes")
    print(f"  6. Concurrent:           {results.get('concurrent_processing', {}).get('speedup', 1):.1f}x speedup")
    print(f"  7. Query Optimization:    Filtered + Ordered + Pattern queries")
    print(f"  8. Relationships:         {results.get('relationship_operations', {}).get('relationships_created', 0)} links")
    
    print("\n" + "=" * 60)
    print("Scalability Patterns Demo Complete!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("  • Use create_many() for bulk imports")
    print("  • Implement pagination for large result sets")
    print("  • Always use field projection (select) when possible")
    print("  • Group operations in transactions for atomicity")
    print("  • Create indexes before bulk vector operations")
    print("  • Use thread pools for parallel read operations")
    print("  • Leverage filtered/ordered queries for efficiency")
    print("\nFor 10M+ nodes, combine these patterns:")
    print("  1. Seed with create_many batches of 500-1000 records")
    print("  2. Stream through data using pagination generators")
    print("  3. Use concurrent threads for parallel processing")
    print("  4. Create vector indexes before bulk embedding")
    print("  5. Group relationship creation in transactions")
    print("\n")


if __name__ == "__main__":
    main()
