# Rate Limiting Implementation for RushDB Query APIs

A production-ready rate limiting system using RushDB as the state store for tracking API usage, enforcing quotas, and managing request windows.

## What This Demonstrates

- **Sliding Window Rate Limiting**: Accurate rate limiting using timestamp-based request tracking
- **Per-Client Quotas**: Configurable rate limits per client ID with Knowledge Unit (KU) budget tracking
- **Atomic Updates**: Using RushDB transactions for consistent counter updates under concurrent load
- **Usage Statistics**: Querying aggregated usage patterns for monitoring and billing
- **Configurable Rules**: Storing rate limit rules as RushDB records for dynamic configuration

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  API Request    │────▶│  RushDB Rate     │────▶│  RushDB     │
│  (client_id)    │     │  Limiter         │     │  (state)    │
└─────────────────┘     └──────────────────┘     └─────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  RATE_LIMIT_RULE  │  Configuration per client
                    │  REQUEST_LOG       │  Timestamped request records
                    │  KU_USAGE          │  Knowledge Unit tracking
                    └───────────────────┘
```

## Prerequisites

- Python 3.9+
- RushDB account ([free tier available](https://rushdb.com/pricing))
- API key from RushDB dashboard

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_KEY
```

### 3. Seed Initial Data

```bash
python seed.py
```

This creates sample rate limit rules for different client tiers.

## Running the Example

```bash
python main.py
```

### Expected Output

```
=== Rate Limiting Demo with RushDB ===

[1] Creating rate limit configurations...
   ✓ Created rate limit for 'client_premium': 1000 req/min
   ✓ Created rate limit for 'client_free': 100 req/min
   ✓ Created rate limit for 'client_enterprise': unlimited (KU: 10000)

[2] Testing rate limit enforcement...
   ✓ Request 1 allowed (remaining: 99/100)
   ✓ Request 2 allowed (remaining: 98/100)
   ✗ Request 3 REJECTED - limit exceeded (retry in 45s)

[3] Checking rate limit status...
   Status for 'client_free': 98/100 requests, resets in 45s

[4] Querying usage statistics...
   Total requests (client_free, last hour): 2
   Total KU used: 10.5

[5] Simulating concurrent requests...
   Processed 10 requests, 8 allowed, 2 rejected
```

## Key Implementation Details

### Sliding Window Algorithm

The rate limiter uses a sliding window approach where requests are tracked with precise timestamps. This provides smoother rate limiting compared to fixed windows:

```python
def _check_rate_limit(self, client_id: str) -> tuple[bool, int, datetime]:
    # Count requests in the current window
    window_start = datetime.utcnow() - timedelta(seconds=window_seconds)
    recent_requests = self.db.records.find({
        "labels": ["REQUEST_LOG"],
        "where": {
            "client_id": client_id,
            "timestamp": {"$gte": window_start.isoformat()}
        }
    })
    # Allow if under limit
    return len(recent_requests.data) < max_requests
```

### Atomic Updates with Transactions

Request logging uses RushDB transactions to ensure atomic updates under concurrent load:

```python
with self.db.transactions.begin() as tx:
    self.db.records.create(
        label="REQUEST_LOG",
        data=log_entry,
        transaction=tx
    )
    self.db.records.create(
        label="KU_USAGE",
        data=ku_entry,
        transaction=tx
    )
```

### Per-Client Configuration

Rate limit rules are stored as RushDB records, enabling dynamic configuration without code changes:

```python
# Find rule for client
rules = self.db.records.find({
    "labels": ["RATE_LIMIT_RULE"],
    "where": {"client_id": client_id}
})
```

## Project Structure

```
rate-limiting-implementation-for-rushdb-query-apis-tutorial/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example       # Environment template
├── main.py            # Demo implementation
└── seed.py            # Seed data script
```

## Customization

### Adjusting Default Limits

Modify `DEFAULT_MAX_REQUESTS` and `DEFAULT_WINDOW_SECONDS` in `main.py`.

### Adding Custom Rules

Use the `create_client_config()` method to add client-specific limits:

```python
limiter.create_client_config(
    client_id="my_client",
    max_requests=500,
    window_seconds=60,
    quota_ku=5000  # Optional KU budget
)
```

### Changing Algorithm

Swap `check_rate_limit()` implementation for token bucket or Leaky Bucket algorithms if preferred.

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://docs.rushdb.com/sdk/python)
- [Knowledge Units Pricing](https://rushdb.com/pricing)


## License

MIT License - Use freely for learning and production systems.
