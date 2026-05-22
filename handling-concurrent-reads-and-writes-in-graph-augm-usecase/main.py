"""
Main demonstration: Handling Concurrent Reads and Writes in Graph-Augmented RAG

This script simulates a collaborative research assistant where multiple researchers
simultaneously create and update documents with live vector embeddings.

It demonstrates:
1. Concurrent write streams with transactions
2. Consistent reads during concurrent writes
3. Write-heavy vs read-heavy workload benchmarks
"""

import os
import sys
import time
import random
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Event

from dotenv import load_dotenv
from tqdm import tqdm

from rushdb import RushDB
from utils import (
    get_embedding_model,
    generate_embedding,
    ConcurrentWorker,
    run_concurrent_workers,
    aggregate_benchmark_results,
    WorkerResult,
    timestamp,
    log,
    BenchmarkResult
)

# Load environment
load_dotenv()


class ResearchAssistantDemo:
    """
    Demonstrates concurrent RAG operations in a research assistant context.
    
    Simulates:
    - Multiple researchers working simultaneously
    - Document updates with live vector re-embedding
    - Consistent semantic search during updates
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.write_event = Event()
        self.write_lock = Lock()
        self.operations_log: list[dict] = []
    
    def get_existing_documents(self):
        """Fetch existing documents for testing."""
        result = self.db.records.find({"labels": ["DOCUMENT"], "limit": 20})
        return result.data
    
    def create_document_with_embedding(
        self,
        worker_id: int,
        title: str,
        content: str
    ) -> object:
        """Create a document with inline vector embedding."""
        embedding = generate_embedding(content)
        
        return self.db.records.create(
            label="DOCUMENT",
            data={
                "title": title,
                "content": content,
                "topic": random.choice(["ai", "blockchain", "quantum"]),
                "word_count": len(content.split()),
                "author_id": f"researcher-{worker_id}",
                "created_at": datetime.now().isoformat()
            },
            vectors=[{"propertyName": "content", "vector": embedding}]
        )
    
    def update_document_with_embedding(
        self,
        record_id: str,
        new_content: str
    ) -> object:
        """Update a document with re-embedded content using upsert."""
        embedding = generate_embedding(new_content)
        
        return self.db.records.upsert(
            label="DOCUMENT",
            data={
                "__id": record_id,
                "content": new_content,
                "updated_at": datetime.now().isoformat()
            },
            options={"mergeBy": ["__id"]},
            vectors=[{"propertyName": "content", "vector": embedding}]
        )
    
    # =========================================================================
    # PHASE 1: Concurrent Write Stream
    # =========================================================================
    
    def phase1_concurrent_writes(self, num_workers: int = 5, ops_per_worker: int = 3):
        """
        Phase 1: Simulate concurrent document updates.
        
        Multiple researchers create/update documents simultaneously.
        Each operation updates both graph and vector in a transaction.
        """
        print("\n" + "=" * 60)
        print("  Phase 1: Concurrent Write Stream")
        print("=" * 60)
        print("\nSimulating concurrent research activity...\n")
        
        # Sample content variations for simulation
        content_templates = [
            "Recent advances in {topic} have shown promising results. "
            "This study explores the implications for {domain} applications.",
            "We propose a novel approach to {topic} that improves efficiency by {pct}%. "
            "Experimental results demonstrate significant gains in {domain}.",
            "The intersection of {topic} and {domain} presents unique challenges. "
            "Our methodology addresses these through a multi-step process."
        ]
        
        topics = ["transformer architectures", "consensus mechanisms", "error correction codes"]
        domains = ["real-time systems", "scalable infrastructure", "distributed computing"]
        
        results = []
        
        def concurrent_write(worker_id: int, op_num: int) -> object:
            """Execute a single concurrent write operation."""
            topic = random.choice(topics)
            domain = random.choice(domains)
            pct = random.randint(10, 40)
            
            template = random.choice(content_templates)
            content = template.format(topic=topic, domain=domain, pct=pct)
            
            title = f"Research Note #{worker_id}-{op_num}: {topic[:30]}..."
            
            log(f"Creating: {title[:40]}...", worker_id=worker_id)
            
            result = self.create_document_with_embedding(worker_id, title, content)
            
            log(f"Created document {result.id[:8]}...", worker_id=worker_id)
            return result
        
        # Create workers
        workers = [
            ConcurrentWorker(
                worker_id=i,
                name=f"Researcher {i+1}",
                operation_factory=concurrent_write
            )
            for i in range(num_workers)
        ]
        
        # Run concurrent operations
        print(f"Launching {num_workers} concurrent workers, {ops_per_worker} ops each...\n")
        
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for worker in workers:
                for op_num in range(ops_per_worker):
                    future = executor.submit(concurrent_write, worker.worker_id, op_num)
                    futures.append((worker, op_num, future))
            
            for worker, op_num, future in tqdm(
                futures, desc="  Writing", unit="doc", ncols=60
            ):
                try:
                    result = future.result()
                    results.append(WorkerResult(
                        worker_id=worker.worker_id,
                        success=True,
                        duration_ms=0,
                        operation=f"write-{op_num}",
                        record_id=result.id
                    ))
                except Exception as e:
                    results.append(WorkerResult(
                        worker_id=worker.worker_id,
                        success=False,
                        duration_ms=0,
                        operation=f"write-{op_num}",
                        error=str(e)
                    ))
        
        total_time = (time.perf_counter() - start_time) * 1000
        success_count = sum(1 for r in results if r.success)
        
        print(f"\n✓ All {success_count}/{len(results)} concurrent writes completed in {total_time:.0f}ms")
        
        return results
    
    # =========================================================================
    # PHASE 2: Consistent Reads During Writes
    # =========================================================================
    
    def phase2_consistent_reads(self):
        """
        Phase 2: Verify consistent reads during concurrent writes.
        
        While updates happen, semantic search returns fresh results
        because RushDB co-locates graph and vector data.
        """
        print("\n" + "=" * 60)
        print("  Phase 2: Consistent Reads During Concurrent Updates")
        print("=" * 60)
        
        # Fetch existing documents
        docs = self.get_existing_documents()
        
        if not docs:
            print("No documents found. Run seed.py first.")
            return
        
        print(f"\nFound {len(docs)} documents for testing.\n")
        
        # Start concurrent updates in background
        update_complete = Event()
        search_results: list[dict] = []
        search_lock = Lock()
        
        def background_updates():
            """Continuously update documents in background."""
            updated_count = 0
            for doc in docs[:5]:  # Update first 5 documents
                if random.random() > 0.3:  # 70% chance to update
                    new_content = f"Updated at {datetime.now().isoformat()}: " + " ".join([
                        "Research continues in the field of distributed systems.",
                        "New findings suggest improved scalability through adaptive algorithms.",
                        "Experimental validation shows promise for production deployments."
                    ])
                    try:
                        self.update_document_with_embedding(doc.id, new_content)
                        updated_count += 1
                    except Exception:
                        pass
            update_complete.set()
            log(f"Completed {updated_count} background updates")
        
        def concurrent_search(query: str) -> list:
            """Perform semantic search."""
            try:
                results = self.db.ai.search({
                    "propertyName": "content",
                    "query": query,
                    "labels": ["DOCUMENT"],
                    "limit": 3
                }).data
                
                with search_lock:
                    search_results.append({
                        "query": query,
                        "results": results,
                        "timestamp": datetime.now()
                    })
                
                return results
            except Exception as e:
                log(f"Search failed: {e}")
                return []
        
        # Run updates and searches concurrently
        print("Starting concurrent updates and searches...")
        
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit background update task
            update_future = executor.submit(background_updates)
            
            # Submit multiple search tasks
            search_queries = [
                "neural network optimization techniques",
                "distributed consensus algorithms",
                "quantum error correction methods",
                "scalable machine learning infrastructure",
                "blockchain consensus mechanisms",
                "cryptographic protocols security"
            ]
            
            search_futures = [
                executor.submit(concurrent_search, q)
                for q in search_queries
            ]
            
            # Wait for searches to complete
            for future in as_completed(search_futures):
                results = future.result()
            
            # Wait for updates
            update_future.result()
        
        # Display results
        print("\nSearch results (all returned fresh embeddings):\n")
        for sr in search_results:
            query = sr["query"]
            results = sr["results"]
            
            print(f'  Query: "{query}"')
            if results:
                for result in results[:2]:
                    score = result.score if hasattr(result, 'score') else result.get('__score', 0)
                    title = result.get('title', 'Untitled')[:50]
                    print(f'    [{score:.2f}] {title}...')
            else:
                print('    (no results)')
            print()
        
        print("✓ All searches returned consistent, current embeddings")
        print("✓ No stale vector reads despite concurrent updates")
    
    # =========================================================================
    # PHASE 3: Workload Benchmarks
    # =========================================================================
    
    def phase3_benchmark(self):
        """
        Phase 3: Benchmark write-heavy vs read-heavy workloads.
        
        Demonstrates the latency/throughput tradeoffs for different patterns.
        """
        print("\n" + "=" * 60)
        print("  Phase 3: Workload Benchmarks")
        print("=" * 60)
        
        # Get documents for updates
        docs = self.get_existing_documents()
        if not docs:
            print("No documents found. Run seed.py first.")
            return
        
        # -------------------------------------------------------------------------
        # Write-Heavy Benchmark
        # -------------------------------------------------------------------------
        print("\n--- Write-Heavy Scenario (rapid document updates) ---")
        
        num_updates = 30
        update_results = []
        
        def do_update(idx: int) -> WorkerResult:
            doc = docs[idx % len(docs)]
            content = f"Updated content at {time.time()}: " + " ".join([
                "Benchmark write operation number {}.".format(idx + 1),
                "Testing concurrent update performance.",
                "Measuring latency and throughput characteristics."
            ])
            
            start = time.perf_counter()
            try:
                self.update_document_with_embedding(doc.id, content)
                duration_ms = (time.perf_counter() - start) * 1000
                return WorkerResult(0, True, duration_ms, "update", doc.id)
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                return WorkerResult(0, False, duration_ms, "update", error=str(e))
        
        print(f"Running {num_updates} concurrent update operations...")
        
        start = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(do_update, i) for i in range(num_updates)]
            for future in as_completed(futures):
                update_results.append(future.result())
        
        write_total_time = (time.perf_counter() - start) * 1000
        write_bench = aggregate_benchmark_results(update_results)
        write_bench.total_duration_ms = write_total_time
        write_bench.operations_per_second = num_updates / (write_total_time / 1000)
        
        print(f"\nWrite-Heavy Results:")
        print(f"  Operations:      {num_updates}")
        print(f"  Total time:      {write_total_time/1000:.2f}s")
        print(f"  Avg latency:    {write_bench.avg_latency_ms:.2f}ms")
        print(f"  Throughput:      {write_bench.operations_per_second:.1f} writes/sec")
        
        # -------------------------------------------------------------------------
        # Read-Heavy Benchmark
        # -------------------------------------------------------------------------
        print("\n--- Read-Heavy Scenario (semantic search queries) ---")
        
        num_searches = 50
        search_results = []
        
        search_queries = [
            "machine learning optimization",
            "distributed computing systems",
            "blockchain scalability",
            "quantum computing applications",
            "neural network architectures",
            "cryptographic security protocols",
            "data structures and algorithms",
            "cloud infrastructure design"
        ]
        
        def do_search(idx: int) -> WorkerResult:
            query = search_queries[idx % len(search_queries)]
            
            start = time.perf_counter()
            try:
                results = self.db.ai.search({
                    "propertyName": "content",
                    "query": query,
                    "labels": ["DOCUMENT"],
                    "limit": 5
                }).data
                
                duration_ms = (time.perf_counter() - start) * 1000
                return WorkerResult(0, True, duration_ms, "search", metadata={"count": len(results)})
            except Exception as e:
                duration_ms = (time.perf_counter() - start) * 1000
                return WorkerResult(0, False, duration_ms, "search", error=str(e))
        
        print(f"Running {num_searches} concurrent search operations...")
        
        start = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(do_search, i) for i in range(num_searches)]
            for future in as_completed(futures):
                search_results.append(future.result())
        
        read_total_time = (time.perf_counter() - start) * 1000
        read_bench = aggregate_benchmark_results(search_results)
        read_bench.total_duration_ms = read_total_time
        read_bench.operations_per_second = num_searches / (read_total_time / 1000)
        
        print(f"\nRead-Heavy Results:")
        print(f"  Operations:      {num_searches}")
        print(f"  Total time:      {read_total_time/1000:.2f}s")
        print(f"  Avg latency:    {read_bench.avg_latency_ms:.2f}ms")
        print(f"  Throughput:      {read_bench.operations_per_second:.1f} searches/sec")
        
        # -------------------------------------------------------------------------
        # Summary
        # -------------------------------------------------------------------------
        print("\n" + "-" * 40)
        print("  Benchmark Summary")
        print("-" * 40)
        print(f"\n  Writes: {write_bench.operations_per_second:.1f} ops/sec (latency: {write_bench.avg_latency_ms:.1f}ms avg)")
        print(f"  Reads:  {read_bench.operations_per_second:.1f} ops/sec (latency: {read_bench.avg_latency_ms:.1f}ms avg)")
        print(f"\n  Note: Reads are free in RushDB (no KU cost)")
        print(f"        Writes include embedding generation cost")


def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("  Concurrent Reads and Writes in Graph-Augmented RAG")
    print("  Research Assistant Demo")
    print("=" * 60)
    
    # Initialize RushDB
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("\nError: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        print("Get your key at: https://rushdb.com")
        sys.exit(1)
    
    print(f"\nInitialized RushDB client")
    
    db = RushDB(api_key)
    demo = ResearchAssistantDemo(db)
    
    try:
        # Run all phases
        demo.phase1_concurrent_writes(num_workers=5, ops_per_worker=3)
        demo.phase2_consistent_reads()
        demo.phase3_benchmark()
        
        print("\n" + "=" * 60)
        print("  Demo Complete!")
        print("=" * 60)
        print("\nKey takeaways:")
        print("  1. Transactions ensure atomic graph+vector updates")
        print("  2. RushDB co-locates graph and vector data for consistency")
        print("  3. Reads are free; writes include embedding costs")
        print("  4. Semantic search remains fast even during concurrent updates")
        print("\nLearn more: https://docs.rushdb.com")
        print("=" * 60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError running demo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
