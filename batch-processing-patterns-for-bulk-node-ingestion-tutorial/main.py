"""
Batch Processing Patterns for Bulk Node Ingestion

A comprehensive tutorial demonstrating RushDB's batch processing capabilities.
Each pattern showcases a different approach to efficiently ingest large volumes
of data while handling errors and monitoring progress.
"""

import os
import time
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
db = RushDB(api_key=os.getenv('RUSHDB_API_KEY'))


# ============================================================================
# PATTERN 1: Basic Batch Creation with create_many()
# ============================================================================

def pattern_basic_batch():
    """
    Demonstrates: db.records.create_many()
    
    The simplest batch pattern. Creates multiple records in a single call.
    Best for datasets under 1,000 records.
    """
    print("\n" + "=" * 60)
    print("PATTERN 1: Basic Batch Creation")
    print("=" * 60)
    
    # Sample batch data
    batch_data = [
        {"name": f"Batch Product {i}", "price": 99.99 + i, "category": "Electronics"}
        for i in range(100)
    ]
    
    start_time = time.time()
    
    # Single call creates all 100 records
    result = db.records.create_many(label="BATCH_PRODUCT", data=batch_data)
    
    elapsed = time.time() - start_time
    throughput = len(batch_data) / elapsed if elapsed > 0 else 0
    
    print(f"  Records created: {len(batch_data)}")
    print(f"  Time elapsed: {elapsed:.3f}s")
    print(f"  Throughput: {throughput:.1f} records/sec")
    print(f"  Status: {'✓ Success' if result else '✗ Failed'}")
    
    return len(batch_data)


# ============================================================================
# PATTERN 2: Chunked Processing for Large Datasets
# ============================================================================

def pattern_chunked_processing():
    """
    Demonstrates: Streaming large datasets in configurable chunks
    
    For datasets > 1,000 records, chunked processing prevents timeouts
    and provides progress visibility.
    """
    print("\n" + "=" * 60)
    print("PATTERN 2: Chunked Processing")
    print("=" * 60)
    
    total_records = 1000
    chunk_size = 50  # Optimal for 1K-10K datasets
    
    print(f"  Processing {total_records} records in chunks of {chunk_size}...")
    
    created = 0
    start_time = time.time()
    
    for i in range(0, total_records, chunk_size):
        # Generate chunk data
        chunk = [
            {
                "sku": f"CHUNK-{i + j:05d}",
                "name": f"Chunked Product {i + j}",
                "price": 49.99 + (i + j) * 0.5,
                "quantity": random.randint(1, 100)
            }
            for j in range(1, min(chunk_size, total_records - i) + 1)
        ]
        
        # Process chunk
        db.records.create_many(label="CHUNK_PRODUCT", data=chunk)
        created += len(chunk)
        
        # Progress indicator (every 200 records)
        if created % 200 == 0 or created == total_records:
            elapsed = time.time() - start_time
            pct = (created / total_records) * 100
            print(f"  Progress: {created}/{total_records} ({pct:.0f}%) - {elapsed:.1f}s elapsed")
    
    elapsed = time.time() - start_time
    throughput = total_records / elapsed if elapsed > 0 else 0
    
    print(f"\n  ✓ Completed: {created} records in {elapsed:.2f}s ({throughput:.1f} rec/sec)")
    
    return created


# ============================================================================
# PATTERN 3: Transaction Batching
# ============================================================================

def pattern_transaction_batch():
    """
    Demonstrates: Transaction batching with rollback support
    
    Wraps batch operations in a transaction for atomicity.
    If any record fails, all changes are rolled back.
    """
    print("\n" + "=" * 60)
    print("PATTERN 3: Transaction Batching")
    print("=" * 60)
    
    batch_size = 100
    batch_data = [
        {"name": f"Transaction Product {i}", "status": "pending", "value": i * 10}
        for i in range(batch_size)
    ]
    
    print(f"  Creating {batch_size} records in a single transaction...")
    start_time = time.time()
    
    # Use context manager for automatic commit/rollback
    try:
        with db.transactions.begin() as tx:
            for record in batch_data:
                db.records.create(
                    label="TX_PRODUCT",
                    data=record,
                    transaction=tx
                )
            # Context manager auto-commits on clean exit
            
        elapsed = time.time() - start_time
        throughput = batch_size / elapsed if elapsed > 0 else 0
        
        print(f"  ✓ Transaction committed: {batch_size} records")
        print(f"  Time elapsed: {elapsed:.3f}s")
        print(f"  Throughput: {throughput:.1f} records/sec")
        
        return batch_size
        
    except Exception as e:
        print(f"  ✗ Transaction rolled back: {str(e)}")
        return 0


# ============================================================================
# PATTERN 4: Bulk Upsert with Merge Keys
# ============================================================================

def pattern_bulk_upsert():
    """
    Demonstrates: Bulk upsert with conflict resolution
    
    Uses mergeBy to update existing records or create new ones.
    Idempotent pattern ideal for data synchronization.
    """
    print("\n" + "=" * 60)
    print("PATTERN 4: Bulk Upsert")
    print("=" * 60)
    
    # First, create initial records
    initial_data = [
        {"sku": f"UPSERT-{i:03d}", "name": f"Original Product {i}", "price": 100 + i}
        for i in range(100)
    ]
    
    print("  Phase 1: Creating initial 100 records...")
    db.records.create_many(label="UPSERT_PRODUCT", data=initial_data)
    
    # Now upsert with updates (same SKUs, different prices)
    updated_data = [
        {"sku": f"UPSERT-{i:03d}", "name": f"Updated Product {i}", "price": 200 + i, "updated": True}
        for i in range(100)
    ]
    
    # Add 20 new records (upsert will create these)
    updated_data.extend([
        {"sku": f"UPSERT-NEW-{i:03d}", "name": f"New Product {i}", "price": 50 + i}
        for i in range(20)
    ])
    
    print("  Phase 2: Upserting 120 records (100 updates + 20 new)...")
    start_time = time.time()
    
    # Upsert each record (RushDB doesn't have batch upsert, so we iterate)
    updated = 0
    for record in updated_data:
        db.records.upsert(
            label="UPSERT_PRODUCT",
            data=record,
            options={"mergeBy": ["sku"]}
        )
        updated += 1
        if updated % 50 == 0:
            print(f"    Processed {updated}/120 records...")
    
    elapsed = time.time() - start_time
    
    # Verify results
    all_records = db.records.find({"labels": ["UPSERT_PRODUCT"]})
    updated_count = sum(1 for r in all_records.data if r.get("updated", False))
    new_count = sum(1 for r in all_records.data if "UPSERT-NEW-" in r.get("sku", ""))
    
    print(f"\n  ✓ Upsert complete: {elapsed:.2f}s")
    print(f"  Total records: {all_records.total} (100 original + 20 new)")
    print(f"  Updated records: {updated_count}")
    print(f"  New records: {new_count}")
    
    return all_records.total


# ============================================================================
# PATTERN 5: Error Handling with Retry Logic
# ============================================================================

def pattern_error_handling():
    """
    Demonstrates: Robust error handling with exponential backoff
    
    Handles transient failures gracefully with retry logic.
    Essential for production batch processing.
    """
    print("\n" + "=" * 60)
    print("PATTERN 5: Error Handling with Retry")
    print("=" * 60)
    
    def retry_with_backoff(func, max_retries=3, base_delay=0.1):
        """Retry decorator with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                print(f"    Attempt {attempt + 1} failed: {str(e)}")
                print(f"    Retrying in {delay:.1f}s...")
                time.sleep(delay)
    
    batch_data = [
        {"name": f"Retry Product {i}", "attempt": i}
        for i in range(50)
    ]
    
    print(f"  Processing 50 records with retry logic...")
    start_time = time.time()
    
    successful = 0
    failed = 0
    
    for record in batch_data:
        try:
            def create_record():
                return db.records.create(label="RETRY_PRODUCT", data=record)
            
            retry_with_backoff(create_record)
            successful += 1
            
        except Exception as e:
            failed += 1
            print(f"    ✗ Failed after retries: {record['name']}")
    
    elapsed = time.time() - start_time
    throughput = len(batch_data) / elapsed if elapsed > 0 else 0
    
    print(f"\n  Results: {successful} successful, {failed} failed")
    print(f"  Time: {elapsed:.2f}s ({throughput:.1f} rec/sec)")
    
    return successful


# ============================================================================
# PATTERN 6: Batch Size Optimization Benchmark
# ============================================================================

def pattern_batch_optimization():
    """
    Demonstrates: Finding optimal batch size for your workload
    
    Tests different chunk sizes to find the best throughput.
    """
    print("\n" + "=" * 60)
    print("PATTERN 6: Batch Size Optimization")
    print("=" * 60)
    
    batch_sizes = [10, 25, 50, 100]
    total_records = 200  # Test with same total for fair comparison
    
    results = []
    
    for chunk_size in batch_sizes:
        # Clear existing test data
        db.records.delete_many({"labels": ["BENCHMARK"], "where": {}})
        
        print(f"\n  Testing chunk size: {chunk_size}")
        start_time = time.time()
        
        for i in range(0, total_records, chunk_size):
            chunk = [
                {"name": f"Benchmark {i + j}", "value": i + j}
                for j in range(min(chunk_size, total_records - i))
            ]
            db.records.create_many(label="BENCHMARK", data=chunk)
        
        elapsed = time.time() - start_time
        throughput = total_records / elapsed if elapsed > 0 else 0
        
        results.append({
            "chunk_size": chunk_size,
            "elapsed": elapsed,
            "throughput": throughput
        })
        
        print(f"    {total_records} records in {elapsed:.3f}s ({throughput:.1f} rec/sec)")
    
    # Find optimal
    optimal = max(results, key=lambda r: r["throughput"])
    
    print(f"\n  Optimal chunk size: {optimal['chunk_size']}")
    print(f"  Best throughput: {optimal['throughput']:.1f} records/sec")
    
    return results


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all batch processing patterns."""
    print("\n" + "=" * 60)
    print("RushDB Batch Processing Patterns Tutorial")
    print("=" * 60)
    print(f"\nConfigured RushDB endpoint: {os.getenv('RUSHDB_URL', 'cloud')}")
    
    # Run patterns
    summary = {
        "basic_batch": pattern_basic_batch(),
        "chunked_processing": pattern_chunked_processing(),
        "transaction_batch": pattern_transaction_batch(),
        "bulk_upsert": pattern_bulk_upsert(),
        "error_handling": pattern_error_handling(),
        "batch_optimization": pattern_batch_optimization()
    }
    
    # Summary
    total_created = sum(
        v for k, v in summary.items() 
        if k != "batch_optimization"
    )
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total records created: ~{total_created + 120}")
    print(f"  Patterns demonstrated: 6")
    print(f"\n  Batch processing with RushDB is production-ready!")
    print(f"  Documentation: https://docs.rushdb.com")


if __name__ == "__main__":
    main()
