"""
Utility functions for the concurrent RAG demo.

Handles:
- Embedding generation with caching
- Concurrent worker simulation
- Timing and metrics utilities
"""

import time
import threading
import random
from datetime import datetime
from typing import Callable, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from sentence_transformers import SentenceTransformer

# Lazy-load embedding model
_embedding_model: Optional[SentenceTransformer] = None
_model_lock = threading.Lock()


def get_embedding_model() -> SentenceTransformer:
    """Get or initialize the shared embedding model (thread-safe)."""
    global _embedding_model
    
    if _embedding_model is None:
        with _model_lock:
            if _embedding_model is None:
                _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    return _embedding_model


def generate_embedding(text: str) -> list:
    """Generate embedding vector for text."""
    model = get_embedding_model()
    return model.encode(text).tolist()


@dataclass
class WorkerResult:
    """Result from a concurrent worker execution."""
    worker_id: int
    success: bool
    duration_ms: float
    operation: str
    record_id: Optional[str] = None
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Aggregated benchmark results."""
    total_operations: int
    total_duration_ms: float
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    success_count: int
    failure_count: int
    operations_per_second: float

    def __str__(self) -> str:
        return f"""Benchmark Results:
  Total operations: {self.total_operations}
  Total time:      {self.total_duration_ms/1000:.2f}s
  Avg latency:     {self.avg_latency_ms:.2f}ms
  Min latency:     {self.min_latency_ms:.2f}ms
  Max latency:     {self.max_latency_ms:.2f}ms
  Success/Fail:    {self.success_count}/{self.failure_count}
  Throughput:      {self.operations_per_second:.1f} ops/sec"""


class ConcurrentWorker:
    """
    Simulates a researcher making concurrent operations.
    
    Each worker operates independently with its own:
    - Identity (name, ID)
    - Operation sequence
    - Timing
    """
    
    def __init__(
        self,
        worker_id: int,
        name: str,
        operation_factory: Callable[[int], dict]
    ):
        self.worker_id = worker_id
        self.name = name
        self.operation_factory = operation_factory
        self.results: list[WorkerResult] = []
        
        # Research areas for realistic simulation
        self.topics = [
            "neural networks", "distributed systems", "cryptography",
            "optimization algorithms", "data structures", "machine learning"
        ]
        self.action_verbs = ["Updating", "Creating", "Refining", "Expanding", "Reviewing"]
    
    def execute_operation(self, operation_type: str, db_operation: Callable) -> WorkerResult:
        """Execute a single operation and record timing."""
        start = time.perf_counter()
        
        try:
            result = db_operation()
            duration_ms = (time.perf_counter() - start) * 1000
            
            return WorkerResult(
                worker_id=self.worker_id,
                success=True,
                duration_ms=duration_ms,
                operation=operation_type,
                record_id=result.id if hasattr(result, 'id') else None
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            return WorkerResult(
                worker_id=self.worker_id,
                success=False,
                duration_ms=duration_ms,
                operation=operation_type,
                error=str(e)
            )
    
    def simulate_researcher_activity(self) -> str:
        """Generate a realistic activity description."""
        verb = random.choice(self.action_verbs)
        topic = random.choice(self.topics)
        return f"{verb} document on {topic}"


def run_concurrent_workers(
    workers: list[ConcurrentWorker],
    db_operation: Callable,
    operations_per_worker: int = 3,
    max_workers: int = 5
) -> list[WorkerResult]:
    """
    Run operations concurrently using a thread pool.
    
    Args:
        workers: List of worker configurations
        db_operation: Function to execute (receives worker_id, operation_num)
        operations_per_worker: Number of operations per worker
        max_workers: Maximum concurrent threads
    
    Returns:
        List of all WorkerResult objects
    """
    results: list[WorkerResult] = []
    lock = threading.Lock()
    
    def worker_task(worker: ConcurrentWorker, op_num: int) -> WorkerResult:
        try:
            result = worker.execute_operation(
                f"Op {op_num}",
                lambda: db_operation(worker.worker_id, op_num)
            )
            with lock:
                results.append(result)
            return result
        except Exception as e:
            result = WorkerResult(
                worker_id=worker.worker_id,
                success=False,
                duration_ms=0,
                operation=f"Op {op_num}",
                error=str(e)
            )
            with lock:
                results.append(result)
            return result
    
    tasks = []
    for worker in workers:
        for op_num in range(operations_per_worker):
            tasks.append((worker, op_num))
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(worker_task, worker, op_num)
            for worker, op_num in tasks
        ]
        
        for future in as_completed(futures):
            pass  # Results already collected via lock
    
    return results


def aggregate_benchmark_results(results: list[WorkerResult]) -> BenchmarkResult:
    """Aggregate worker results into benchmark metrics."""
    if not results:
        return BenchmarkResult(
            total_operations=0,
            total_duration_ms=0,
            avg_latency_ms=0,
            min_latency_ms=0,
            max_latency_ms=0,
            success_count=0,
            failure_count=0,
            operations_per_second=0
        )
    
    durations = [r.duration_ms for r in results]
    success_count = sum(1 for r in results if r.success)
    failure_count = len(results) - success_count
    total_duration = sum(durations)
    
    return BenchmarkResult(
        total_operations=len(results),
        total_duration_ms=sum(durations),
        avg_latency_ms=total_duration / len(results),
        min_latency_ms=min(durations),
        max_latency_ms=max(durations),
        success_count=success_count,
        failure_count=failure_count,
        operations_per_second=len(results) / (max(durations) / 1000) if max(durations) > 0 else 0
    )


def format_duration(ms: float) -> str:
    """Format milliseconds into human-readable string."""
    if ms < 1:
        return f"{ms*1000:.2f}µs"
    elif ms < 1000:
        return f"{ms:.2f}ms"
    else:
        return f"{ms/1000:.2f}s"


def timestamp() -> str:
    """Get current timestamp for logging."""
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def log(message: str, worker_id: Optional[int] = None) -> None:
    """Print a timestamped log message."""
    prefix = f"[{timestamp()}]"
    if worker_id is not None:
        prefix += f" [Worker-{worker_id}]"
    print(f"{prefix} {message}")
