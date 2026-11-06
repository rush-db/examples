"""
Rate Limiting Implementation for RushDB Query APIs

This module demonstrates a production-ready rate limiting system that uses
RushDB as the state store for tracking API usage, enforcing quotas, and
managing request windows.

Key Concepts Demonstrated:
1. Sliding Window Rate Limiting - Accurate request tracking using timestamps
2. Per-Client Configuration - Stored as RushDB records for dynamic management
3. Knowledge Unit Budget Tracking - Monitor and enforce KU consumption
4. Atomic Updates - Using RushDB transactions for consistency
5. Usage Statistics - Query aggregated patterns for monitoring

Usage:
    from main import RateLimiterDemo
    
    demo = RateLimiterDemo(api_key="your_key")
    demo.run_all_demos()
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


from rushdb import RushDB

# =============================================================================
# Data Models
# =============================================================================

@dataclass
class RateLimitConfig:
    """Rate limit configuration for a client/endpoint."""
    client_id: str
    max_requests: int
    window_seconds: int
    quota_ku: Optional[int] = None
    tier: str = "default"


@dataclass
class RateLimitStatus:
    """Current rate limit status for a client/endpoint."""
    allowed: bool
    remaining: int
    total_limit: int
    reset_at: datetime
    retry_after: Optional[int] = None
    ku_remaining: Optional[int] = None


@dataclass
class UsageStats:
    """Usage statistics for a client."""
    total_requests: int
    total_ku: float
    window_requests: int
    window_ku: float
    period_start: datetime
    period_end: datetime


# =============================================================================
# Core Rate Limiter Implementation
# =============================================================================

class RushDBRateLimiter:
    """
    Rate limiter that uses RushDB to store and track rate limit state.
    
    This implementation uses a sliding window algorithm where requests are
    tracked with timestamps, enabling accurate rate limiting across time windows.
    
    The limiter maintains three record types:
    - RATE_LIMIT_RULE: Per-client configuration
    - REQUEST_LOG: Timestamped request records for window tracking
    - KU_USAGE: Knowledge Unit consumption tracking
    
    Attributes:
        db: RushDB client instance
        default_max_requests: Fallback limit if no rule exists
        default_window_seconds: Fallback window if no rule exists
    """
    
    def __init__(
        self,
        api_key: str,
        url: Optional[str] = None,
        default_max_requests: int = 100,
        default_window_seconds: int = 60
    ):
        self.db = RushDB(api_key, url=url) if url else RushDB(api_key)
        self.default_max_requests = default_max_requests
        self.default_window_seconds = default_window_seconds
        self._ensure_schema()
    
    def _ensure_schema(self) -> None:
        """
        Ensure the rate limiting schema exists in RushDB.
        Creates a marker record if no rules exist to initialize the label.
        """
        existing = self.db.records.find({"labels": ["RATE_LIMIT_RULE"]})
        if existing.total == 0:
            self.db.records.create(
                label="RATE_LIMIT_RULE",
                data={
                    "client_id": "_init_marker",
                    "max_requests": 100,
                    "window_seconds": 60,
                    "tier": "system"
                }
            )
    
    def _get_config(self, client_id: str) -> RateLimitConfig:
        """
        Retrieve rate limit configuration for a client.
        
        Args:
            client_id: Unique identifier for the client
            
        Returns:
            RateLimitConfig with client-specific or default limits
        """
        rules = self.db.records.find({
            "labels": ["RATE_LIMIT_RULE"],
            "where": {"client_id": client_id}
        })
        
        if rules.total > 0:
            rule = rules.data[0]
            return RateLimitConfig(
                client_id=client_id,
                max_requests=rule.data.get("max_requests", self.default_max_requests),
                window_seconds=rule.data.get("window_seconds", self.default_window_seconds),
                quota_ku=rule.data.get("quota_ku"),
                tier=rule.data.get("tier", "default")
            )
        
        # Return default config for unknown clients
        return RateLimitConfig(
            client_id=client_id,
            max_requests=self.default_max_requests,
            window_seconds=self.default_window_seconds
        )
    
    def _count_requests_in_window(
        self,
        client_id: str,
        window_seconds: int
    ) -> Tuple[int, datetime]:
        """
        Count requests from the current sliding window.
        
        Args:
            client_id: Client identifier
            window_seconds: Size of the sliding window
            
        Returns:
            Tuple of (request_count, oldest_request_timestamp)
        """
        window_start = datetime.utcnow() - timedelta(seconds=window_seconds)
        
        recent_requests = self.db.records.find({
            "labels": ["REQUEST_LOG"],
            "where": {
                "client_id": client_id,
                "timestamp": {"$gte": window_start.isoformat()}
            },
            "orderBy": {"timestamp": "asc"},
            "limit": 1000
        })
        
        count = recent_requests.total
        oldest_ts = None
        
        if count > 0:
            oldest_record = recent_requests.data[0]
            oldest_ts = datetime.fromisoformat(oldest_record.data["timestamp"])
        
        return count, oldest_ts
    
    def check_rate_limit(
        self,
        client_id: str,
        endpoint: str = "default",
        ku_cost: float = 0.5,
        simulate: bool = False
    ) -> RateLimitStatus:
        """
        Check if a request is allowed under rate limits.
        
        This method:
        1. Retrieves the client's rate limit configuration
        2. Counts requests in the current sliding window
        3. Returns status indicating if request should proceed
        
        Args:
            client_id: Client identifier for rate limiting
            endpoint: API endpoint being accessed (for logging)
            ku_cost: Knowledge Unit cost of this operation
            simulate: If True, check limits without logging the request
            
        Returns:
            RateLimitStatus with allowed/rejected decision and metadata
        """
        config = self._get_config(client_id)
        window_start = datetime.utcnow() - timedelta(seconds=config.window_seconds)
        
        # Count current requests in window
        current_count, oldest_ts = self._count_requests_in_window(
            client_id,
            config.window_seconds
        )
        
        # Check KU budget if configured
        ku_remaining = None
        if config.quota_ku:
            ku_used = self._get_ku_usage(client_id)
            ku_remaining = max(0, config.quota_ku - ku_used)
            
            if ku_cost > ku_remaining:
                return RateLimitStatus(
                    allowed=False,
                    remaining=0,
                    total_limit=config.max_requests,
                    reset_at=datetime.utcnow() + timedelta(seconds=config.window_seconds),
                    retry_after=config.window_seconds,
                    ku_remaining=ku_remaining
                )
        
        # Check request limit
        if current_count >= config.max_requests:
            retry_after = 0
            if oldest_ts:
                retry_after = int((oldest_ts + timedelta(seconds=config.window_seconds) - datetime.utcnow()).total_seconds())
                retry_after = max(0, retry_after)
            
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                total_limit=config.max_requests,
                reset_at=datetime.utcnow() + timedelta(seconds=retry_after) if retry_after > 0 else window_start,
                retry_after=retry_after if retry_after > 0 else config.window_seconds,
                ku_remaining=ku_remaining
            )
        
        # Request is allowed - log it
        if not simulate:
            self._log_request(client_id, endpoint, ku_cost)
        
        return RateLimitStatus(
            allowed=True,
            remaining=config.max_requests - current_count - 1,
            total_limit=config.max_requests,
            reset_at=datetime.utcnow() + timedelta(seconds=config.window_seconds),
            ku_remaining=ku_remaining
        )
    
    def _log_request(
        self,
        client_id: str,
        endpoint: str,
        ku_cost: float
    ) -> None:
        """
        Log a request and KU usage using a transaction for atomicity.
        """
        timestamp = datetime.utcnow().isoformat()
        
        with self.db.transactions.begin() as tx:
            # Log the request
            self.db.records.create(
                label="REQUEST_LOG",
                data={
                    "client_id": client_id,
                    "endpoint": endpoint,
                    "ku_cost": ku_cost,
                    "timestamp": timestamp
                },
                transaction=tx
            )
            
            # Log KU usage
            self.db.records.create(
                label="KU_USAGE",
                data={
                    "client_id": client_id,
                    "amount": ku_cost,
                    "timestamp": timestamp,
                    "type": "request"
                },
                transaction=tx
            )
    
    def _get_ku_usage(self, client_id: str) -> float:
        """
        Get total KU usage for a client.
        """
        usage = self.db.records.find({
            "labels": ["KU_USAGE"],
            "where": {"client_id": client_id}
        })
        
        total = sum(r.data.get("amount", 0) for r in usage.data)
        return total
    
    def create_client_config(
        self,
        client_id: str,
        max_requests: int,
        window_seconds: int,
        tier: str = "custom",
        quota_ku: Optional[int] = None
    ) -> dict:
        """
        Create or update rate limit configuration for a client.
        
        Args:
            client_id: Unique client identifier
            max_requests: Maximum requests allowed in window
            window_seconds: Size of the rate limit window
            tier: Client tier name for categorization
            quota_ku: Optional monthly KU budget
            
        Returns:
            Created/updated record data
        """
        data = {
            "client_id": client_id,
            "max_requests": max_requests,
            "window_seconds": window_seconds,
            "tier": tier,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        if quota_ku is not None:
            data["quota_ku"] = quota_ku
        
        record = self.db.records.upsert(
            label="RATE_LIMIT_RULE",
            data=data,
            options={"mergeBy": ["client_id"]}
        )
        
        return record.data
    
    def get_usage_stats(
        self,
        client_id: str,
        hours: int = 1
    ) -> UsageStats:
        """
        Get usage statistics for a client over a time period.
        
        Args:
            client_id: Client identifier
            hours: Time period in hours (default: 1)
            
        Returns:
            UsageStats with aggregated metrics
        """
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(hours=hours)
        
        requests = self.db.records.find({
            "labels": ["REQUEST_LOG"],
            "where": {
                "client_id": client_id,
                "timestamp": {"$gte": period_start.isoformat()}
            }
        })
        
        ku_records = self.db.records.find({
            "labels": ["KU_USAGE"],
            "where": {
                "client_id": client_id,
                "timestamp": {"$gte": period_start.isoformat()}
            }
        })
        
        total_requests = requests.total
        total_ku = sum(r.data.get("ku_cost", 0) for r in requests.data)
        
        return UsageStats(
            total_requests=total_requests,
            total_ku=total_ku,
            window_requests=total_requests,
            window_ku=total_ku,
            period_start=period_start,
            period_end=period_end
        )
    
    def get_rate_limit_status(self, client_id: str) -> RateLimitStatus:
        """
        Get current rate limit status without consuming a request.
        Useful for checking quota before making API calls.
        """
        return self.check_rate_limit(client_id, simulate=True)



# =============================================================================
# Demo Runner
# =============================================================================

class RateLimiterDemo:
    """
    Demonstration of the RushDB-based rate limiter.
    
    This class runs through various scenarios showing how the rate limiter
    works in practice, including configuration, enforcement, and monitoring.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the demo.
        
        Args:
            api_key: RushDB API key. Falls back to environment variable.
        """
        self.api_key = api_key or os.getenv("RUSHDB_API_KEY")
        if not self.api_key:
            raise ValueError(
                "RUSHDB_API_KEY not found. "
                "Please set it in .env or pass it directly."
            )
        
        url = os.getenv("RUSHDB_URL")
        self.db = RushDB(self.api_key, url=url) if url else RushDB(self.api_key)
        self.limiter = RushDBRateLimiter(self.api_key, url=url)
    
    def demo_1_create_configs(self) -> None:
        """
        Demo 1: Creating rate limit configurations.
        """
        print("\n[Demo 1] Creating Rate Limit Configurations")
        print("-" * 50)
        
        configs = [
            ("client_premium", 1000, 60),
            ("client_free", 100, 60),
            ("client_enterprise", 10000, 60, 100000)  # With KU budget
        ]
        
        for config_data in configs:
            client_id = config_data[0]
            max_req = config_data[1]
            window = config_data[2]
            ku_budget = config_data[3] if len(config_data) > 3 else None
            
            result = self.limiter.create_client_config(
                client_id=client_id,
                max_requests=max_req,
                window_seconds=window,
                quota_ku=ku_budget
            )
            
            budget_str = f", KU budget: {ku_budget:,}" if ku_budget else ""
            print(f"   ✓ {client_id}: {max_req:,} req/{window}s{budget_str}")
    
    def demo_2_rate_limit_enforcement(self) -> None:
        """
        Demo 2: Demonstrating rate limit enforcement.
        """
        print("\n[Demo 2] Rate Limit Enforcement")
        print("-" * 50)
        
        # Use a test client with low limits
        test_client = "demo_test_client"
        self.limiter.create_client_config(
            client_id=test_client,
            max_requests=3,
            window_seconds=60
        )
        
        print(f"   Testing with '{test_client}' (limit: 3 req/min)")
        print()
        
        for i in range(5):
            status = self.limiter.check_rate_limit(
                client_id=test_client,
                endpoint="/api/test",
                ku_cost=0.5
            )
            
            if status.allowed:
                print(f"   ✓ Request {i+1}: ALLOWED (remaining: {status.remaining}/{status.total_limit})")
            else:
                print(f"   ✗ Request {i+1}: REJECTED (retry in {status.retry_after}s)")
    
    def demo_3_status_check(self) -> None:
        """
        Demo 3: Checking rate limit status without consuming requests.
        """
        print("\n[Demo 3] Rate Limit Status Check")
        print("-" * 50)
        
        test_clients = ["client_free", "client_premium", "client_enterprise"]
        
        for client in test_clients:
            status = self.limiter.get_rate_limit_status(client)
            
            ku_info = ""
            if status.ku_remaining is not None:
                ku_info = f", KU remaining: {status.ku_remaining:,}"
            
            print(f"   {client}:")
            print(f"      Requests: {status.remaining}/{status.total_limit}")
            print(f"      Window resets at: {status.reset_at.strftime('%H:%M:%S')}{ku_info}")
    
    def demo_4_usage_statistics(self) -> None:
        """
        Demo 4: Querying usage statistics.
        """
        print("\n[Demo 4] Usage Statistics")
        print("-" * 50)
        
        stats = self.limiter.get_usage_stats("client_free", hours=1)
        
        print(f"   client_free (last hour):")
        print(f"      Total requests: {stats.total_requests}")
        print(f"      Total KU consumed: {stats.total_ku:.2f}")
        print(f"      Period: {stats.period_start.strftime('%H:%M')} - {stats.period_end.strftime('%H:%M')}")
    
    def demo_5_concurrent_simulation(self) -> None:
        """
        Demo 5: Simulating concurrent requests.
        """
        print("\n[Demo 5] Concurrent Request Simulation")
        print("-" * 50)
        
        test_client = "demo_concurrent"
        self.limiter.create_client_config(
            client_id=test_client,
            max_requests=10,
            window_seconds=60
        )
        
        results = {"allowed": 0, "rejected": 0}
        
        # Simulate concurrent requests
        def make_request(request_id: int) -> bool:
            status = self.limiter.check_rate_limit(
                client_id=test_client,
                endpoint="/api/concurrent-test",
                ku_cost=0.5
            )
            return status.allowed
        
        print(f"   Simulating 15 concurrent requests for '{test_client}' (limit: 10)...")
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(15)]
            for future in as_completed(futures):
                if future.result():
                    results["allowed"] += 1
                else:
                    results["rejected"] += 1
        
        print(f"   Results: {results['allowed']} allowed, {results['rejected']} rejected")
    
    def demo_6_ku_budget_tracking(self) -> None:
        """
        Demo 6: Knowledge Unit budget tracking.
        """
        print("\n[Demo 6] KU Budget Tracking")
        print("-" * 50)
        
        test_client = "demo_ku_client"
        self.limiter.create_client_config(
            client_id=test_client,
            max_requests=1000,
            window_seconds=60,
            quota_ku=100  # Low budget for demo
        )
        
        status = self.limiter.get_rate_limit_status(test_client)
        print(f"   Initial KU budget: 100 KU")
        print(f"   Initial remaining: {status.ku_remaining} KU")
        
        # Make some requests
        for i in range(3):
            self.limiter.check_rate_limit(
                client_id=test_client,
                endpoint="/api/heavy-operation",
                ku_cost=5.0  # Heavy operation
            )
        
        status = self.limiter.get_rate_limit_status(test_client)
        print(f"   After 3 heavy requests (15 KU): {status.ku_remaining} KU remaining")
    
    def run_all_demos(self) -> None:
        """
        Run all demonstration scenarios.
        """
        print("=" * 60)
        print("RushDB Rate Limiting Implementation - Demo")
        print("=" * 60)
        print(f"\nAPI Key: {self.api_key[:8]}...{self.api_key[-4:]}")
        
        self.demo_1_create_configs()
        self.demo_2_rate_limit_enforcement()
        self.demo_3_status_check()
        self.demo_4_usage_statistics()
        self.demo_5_concurrent_simulation()
        self.demo_6_ku_budget_tracking()
        
        print("\n" + "=" * 60)
        print("All demos completed successfully!")
        print("=" * 60)



# =============================================================================
# Main Entry Point
# =============================================================================


def main():
    """
    Main entry point for the rate limiting demo.
    """
    # Verify API key is available
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment")
        print("\nPlease set up your environment:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your RushDB API key to .env")
        print("  3. Run: python seed.py (optional, for initial data)")
        print("  4. Run: python main.py")
        sys.exit(1)
    
    # Run demos
    demo = RateLimiterDemo()
    demo.run_all_demos()



if __name__ == "__main__":
    main()
