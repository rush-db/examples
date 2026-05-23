"""
Streaming ingestion pipeline for agent interaction logs.

This module implements the core pipeline logic that:
1. Consumes events from a streaming source
2. Batches them for efficient writes
3. Persists them to RushDB with proper relationships
4. Handles errors and provides observability
"""
import os
import time
from typing import Generator, List, Dict, Any, Optional
from dotenv import load_dotenv

from rushdb import RushDB
from simulator import EventSimulator, BatchEventBuffer


class StreamingPipeline:
    """
    Main streaming pipeline class.
    
    Manages the flow of events from source to RushDB storage,
    including batching, transactions, and relationship creation.
    """
    
    def __init__(
        self,
        api_token: str,
        url: Optional[str] = None,
        batch_size: int = 10,
        stream_delay: float = 0.1,
    ):
        """
        Initialize the streaming pipeline.
        
        Args:
            api_token: RushDB API token
            url: Optional self-hosted URL
            batch_size: Number of events per batch write
            stream_delay: Delay between events in simulation (seconds)
        """
        self.db = RushDB(api_token, url=url) if url else RushDB(api_token)
        self.batch_size = batch_size
        self.stream_delay = stream_delay
        self.simulator = EventSimulator()
        
        # Statistics
        self.stats = {
            "events_processed": 0,
            "batches_committed": 0,
            "errors": 0,
            "start_time": None,
        }
    
    def ingest_stream(
        self,
        session_count: int = 3,
        on_batch: Optional[callable] = None,
    ) -> Dict[str, int]:
        """
        Ingest events from the stream into RushDB.
        
        Args:
            session_count: Number of sessions to generate
            on_batch: Optional callback for batch completion (batch_num, events)
            
        Returns:
            Statistics dictionary with ingestion results
        """
        self.stats["start_time"] = time.time()
        buffer = BatchEventBuffer(batch_size=self.batch_size)
        
        # Track created records for relationship linking
        sessions: Dict[str, Any] = {}
        
        print(f"[STREAM] Starting streaming pipeline simulation...")
        print(f"[STREAM] Generating {session_count} sessions with events")
        
        # Stream events from simulator
        for event_data in self.simulator.stream_events(session_count):
            # Simulate real-time delay
            time.sleep(self.stream_delay)
            
            # Handle different label types
            label = event_data["label"]
            data = event_data["data"]
            
            # Track sessions for relationship linking
            if label == "SESSION" and data.get("type") == "session_start":
                session_id = data.get("session_id")
                if session_id:
                    sessions[session_id] = None  # Will be populated after creation
            
            # Add to buffer
            completed_batches = buffer.add(event_data)
            
            # Process completed batches
            for batch in completed_batches:
                batch_num = self.stats["batches_committed"] + 1
                self._process_batch(batch, sessions)
                self.stats["batches_committed"] += 1
                
                if on_batch:
                    on_batch(batch_num, batch)
        
        # Flush remaining events
        final_batches = buffer.flush()
        for batch in final_batches:
            batch_num = self.stats["batches_committed"] + 1
            self._process_batch(batch, sessions)
            self.stats["batches_committed"] += 1
            
            if on_batch:
                on_batch(batch_num, batch)
        
        # Calculate duration
        if self.stats["start_time"]:
            duration = time.time() - self.stats["start_time"]
            self.stats["duration_seconds"] = duration
        
        print(f"[STREAM] Pipeline completed: {self.stats['events_processed']} events in {self.stats['batches_committed']} batches")
        
        return self.stats
    
    def _process_batch(
        self,
        batch: List[Dict[str, Any]],
        sessions: Dict[str, Any],
    ) -> None:
        """
        Process a batch of events and write to RushDB.
        
        Groups events by label and uses create_many for efficient writes.
        Uses transactions for atomic commits.
        """
        # Group events by label
        by_label: Dict[str, List[Dict[str, Any]]] = {}
        for event_data in batch:
            label = event_data["label"]
            if label not in by_label:
                by_label[label] = []
            by_label[label].append(event_data["data"])
        
        # Process each label group
        with self.db.transactions.begin() as tx:
            for label, events in by_label.items():
                if label == "SESSION":
                    # Session events: create individually to get IDs
                    for event_data in events:
                        record = self.db.records.create(
                            label="SESSION",
                            data=event_data,
                            transaction=tx
                        )
                        # Track for relationship linking
                        session_id = event_data.get("session_id")
                        if session_id and event_data.get("type") == "session_start":
                            sessions[session_id] = record
                else:
                    # Message, ToolCall, ToolResult: bulk create
                    created = self.db.records.create_many(
                        label=label,
                        data=events,
                        transaction=tx
                    )
                    
                    # Link events to their session
                    for record in (created.data if hasattr(created, 'data') else []):
                        event_session_id = record.data.get("session_id")
                        if event_session_id and event_session_id in sessions:
                            session_record = sessions[event_session_id]
                            if session_record:
                                self.db.records.attach(
                                    source=record,
                                    target=session_record,
                                    options={"type": "BELONGS_TO"},
                                    transaction=tx
                                )
        
        self.stats["events_processed"] += len(batch)
        batch_num = self.stats["batches_committed"] + 1
        print(f"[BATCH] Committed batch {batch_num}: {len(batch)} events")
    
    def ingest_with_upsert(
        self,
        session_count: int = 3,
        merge_by: List[str] = None,
    ) -> Dict[str, int]:
        """
        Alternative ingestion method using upsert for idempotent writes.
        
        Useful for handling deduplication and stateful events like tool results.
        """
        self.stats = {
            "events_processed": 0,
            "batches_committed": 0,
            "errors": 0,
            "start_time": time.time(),
        }
        
        merge_by = merge_by or ["event_id"]
        
        print(f"[STREAM] Starting upsert-mode ingestion...")
        
        for event_data in self.simulator.stream_events(session_count):
            time.sleep(self.stream_delay)
            
            label = event_data["label"]
            data = event_data["data"]
            
            # Use upsert for idempotent writes
            try:
                self.db.records.upsert(
                    label=label,
                    data=data,
                    options={"mergeBy": merge_by}
                )
                self.stats["events_processed"] += 1
                
                if self.stats["events_processed"] % self.batch_size == 0:
                    print(f"[BATCH] Processed {self.stats['events_processed']} events")
                    
            except Exception as e:
                self.stats["errors"] += 1
                print(f"[ERROR] Failed to upsert event: {e}")
        
        self.stats["duration_seconds"] = time.time() - self.stats["start_time"]
        print(f"[STREAM] Upsert ingestion completed: {self.stats['events_processed']} events, {self.stats['errors']} errors")
        
        return self.stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Return current pipeline statistics."""
        return self.stats.copy()


def run_pipeline():
    """Main entry point for running the pipeline."""
    # Load environment
    load_dotenv()
    
    api_token = os.getenv("RUSHDB_API_TOKEN")
    if not api_token:
        raise ValueError("RUSHDB_API_TOKEN not found in environment")
    
    # Configuration
    batch_size = int(os.getenv("BATCH_SIZE", "10"))
    stream_delay = float(os.getenv("STREAM_DELAY", "0.1"))
    session_count = int(os.getenv("DEMO_EVENT_COUNT", "50")) // 15  # Estimate sessions from event count
    
    # Initialize and run pipeline
    pipeline = StreamingPipeline(
        api_token=api_token,
        batch_size=batch_size,
        stream_delay=stream_delay,
    )
    
    stats = pipeline.ingest_stream(session_count=session_count)
    
    return stats
