#!/usr/bin/env python3
"""
Seed script for fraud detection dataset.

Generates a realistic fraud detection dataset:
- Legitimate accounts with normal transaction patterns
- Suspicious accounts with fraud-like behavior
- Known fraud patterns for similarity comparison
- Historical transactions for baseline analysis

This script is idempotent — safe to run multiple times.
"""

import os
import sys
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from rushdb import RushDB
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

# =============================================================================
# CONFIGURATION
# =============================================================================

NUM_LEGITIMATE_ACCOUNTS = 50
NUM_SUSPICIOUS_ACCOUNTS = 10
NUM_NORMAL_TRANSACTIONS = 100
NUM_SUSPICIOUS_TRANSACTIONS = 50
NUM_KNOWN_FRAUD_PATTERNS = 5

VECTOR_DIMENSIONS = 128  # Simplified for demo; production would use 768/1536

# =============================================================================
# MOCK EMBEDDING GENERATOR
# =============================================================================

def generate_mock_embedding(text: str, dimensions: int = VECTOR_DIMENSIONS) -> List[float]:
    """
    Generate a deterministic mock embedding from text.
    
    In production, replace with actual embedding API (OpenAI, Cohere, etc.)
    This mock ensures reproducible results for the demo.
    """
    # Create a pseudo-embedding based on text hash
    seed = sum(ord(c) * (i + 1) for i, c in enumerate(text.lower()))
    random.seed(seed)
    
    # Generate normalized random vector
    vector = [random.uniform(-1, 1) for _ in range(dimensions)]
    
    # Normalize to unit length (cosine similarity works on unit vectors)
    magnitude = sum(v**2 for v in vector) ** 0.5
    vector = [v / magnitude for v in vector]
    
    return vector


def generate_fraud_embedding() -> List[float]:
    """
    Generate embeddings that are deliberately similar to fraud patterns.
    """
    fraud_seed = random.randint(1000, 9999)
    random.seed(fraud_seed)
    
    # Create a "fraud-like" vector direction
    vector = [random.uniform(0.7, 1.0) if i % 3 == 0 else random.uniform(-0.3, 0.3) 
              for i in range(VECTOR_DIMENSIONS)]
    
    # Normalize
    magnitude = sum(v**2 for v in vector) ** 0.5
    vector = [v / magnitude for v in vector]
    
    return vector


# =============================================================================
# FRAUD PATTERN DEFINITIONS
# =============================================================================

KNOWN_FRAUD_PATTERNS = [
    {
        "pattern_id": "FRAUD_001",
        "description": "Multiple rapid international wire transfers to new recipients",
        "amount_range": (5000, 50000),
        "risk_level": "critical"
    },
    {
        "pattern_id": "FRAUD_002",
        "description": "Structuring deposits just below reporting threshold",
        "amount_range": (8000, 9900),
        "risk_level": "high"
    },
    {
        "pattern_id": "FRAUD_003",
        "description": "New account receiving large transfers then immediate withdrawal",
        "amount_range": (10000, 100000),
        "risk_level": "critical"
    },
    {
        "pattern_id": "FRAUD_004",
        "description": "Mystery shopping scam check deposit with overpayment",
        "amount_range": (2000, 5000),
        "risk_level": "medium"
    },
    {
        "pattern_id": "FRAUD_005",
        "description": "Business account with personal expense pattern",
        "amount_range": (500, 5000),
        "risk_level": "medium"
    }
]

NORMAL_TRANSACTION_TYPES = [
    "Grocery store purchase",
    "Monthly salary deposit",
    "Utility bill payment",
    "Online subscription renewal",
    "Restaurant purchase",
    "Gas station transaction",
    "Pharmacy prescription",
    "Doctor visit co-pay",
    "Amazon order",
    "Netflix subscription",
    "Spotify subscription",
    "Public transit fare",
    "Parking meter",
    "ATM withdrawal",
    "Bank transfer to savings",
    "Rent payment",
    "Insurance premium",
    "Phone bill payment",
    "Internet service",
    "Cable TV subscription"
]

SUSPICIOUS_TRANSACTION_TYPES = [
    "Urgent wire transfer to overseas account",
    "Multiple cash advances same day",
    "Large check deposit followed by immediate withdrawal",
    "International money order deposit",
    "Gift card purchase with credit card",
    "Bitcoin ATM withdrawal large amount",
    "Wire transfer to newly added beneficiary",
    "Cash deposit through night drop",
    "Multiple money orders deposited",
    "Overpayment refund request transaction"
]

# =============================================================================
# MAIN SEEDING LOGIC
# =============================================================================

def check_existing_data(db: RushDB) -> bool:
    """Check if data already exists to avoid duplicate seeding."""
    try:
        result = db.records.find({"labels": ["FRAUD_PATTERN"], "limit": 1})
        return len(result) > 0
    except Exception:
        return False


def create_vector_index(db: RushDB) -> str:
    """Create or verify vector index for transaction descriptions."""
    print("[1/5] Creating vector index for transactions...", end=" ", flush=True)
    
    # Check if index already exists
    try:
        indexes = db.ai.indexes.find()
        for idx in indexes:
            if idx.get("label") == "TRANSACTION" and idx.get("propertyName") == "description":
                print("exists")
                return idx.get("__id")
    except Exception:
        pass
    
    # Create new index
    index = db.ai.indexes.create({
        "label": "TRANSACTION",
        "propertyName": "description",
        "sourceType": "external",
        "dimensions": VECTOR_DIMENSIONS,
        "similarityFunction": "cosine"
    })
    
    print("created")
    return index.id


def create_accounts(db: RushDB, legitimate: int, suspicious: int) -> tuple:
    """Create legitimate and suspicious accounts."""
    print(f"[2/5] Creating accounts ({legitimate} legitimate + {suspicious} suspicious)...", end=" ", flush=True)
    
    legitimate_accounts = []
    suspicious_accounts = []
    
    # Legitimate accounts
    for i in range(legitimate):
        account = db.records.create(
            label="ACCOUNT",
            data={
                "account_id": f"acc_normal_{i+1:03d}",
                "account_type": "personal",
                "kyc_status": "verified",
                "risk_score": random.uniform(0.05, 0.25),
                "account_age_days": random.randint(180, 3650),
                "country": fake.country_code()
            }
        )
        legitimate_accounts.append(account)
    
    # Suspicious accounts
    for i in range(suspicious):
        account = db.records.create(
            label="ACCOUNT",
            data={
                "account_id": f"acc_suspicious_{i+1:03d}",
                "account_type": random.choice(["personal", "business"]),
                "kyc_status": random.choice(["pending", "verified"]),
                "risk_score": random.uniform(0.6, 0.95),
                "account_age_days": random.randint(1, 90),  # New accounts
                "country": fake.country_code(),
                "flagged": True
            }
        )
        suspicious_accounts.append(account)
    
    print(f"{legitimate + suspicious} accounts created")
    return legitimate_accounts, suspicious_accounts


def create_fraud_patterns(db: RushDB) -> List:
    """Create known fraud pattern records with embeddings."""
    print("[3/5] Creating known fraud patterns ({0} examples)...".format(NUM_KNOWN_FRAUD_PATTERNS), end=" ", flush=True)
    
    fraud_records = []
    
    for pattern in KNOWN_FRAUD_PATTERNS[:NUM_KNOWN_FRAUD_PATTERNS]:
        embedding = generate_fraud_embedding()
        
        record = db.records.create(
            label="FRAUD_PATTERN",
            data={
                "pattern_id": pattern["pattern_id"],
                "description": pattern["description"],
                "risk_level": pattern["risk_level"],
                "amount_min": pattern["amount_range"][0],
                "amount_max": pattern["amount_range"][1],
                "detected_at": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            },
            vectors=[{
                "propertyName": "description",
                "vector": embedding
            }]
        )
        fraud_records.append(record)
    
    print("done")
    return fraud_records


def create_normal_transactions(db: RushDB, accounts: List, count: int) -> List:
    """Create normal transaction history for legitimate accounts."""
    print(f"[4/5] Creating transaction history for legitimate accounts...", end=" ", flush=True)
    
    transactions = []
    
    for i in range(count):
        account = random.choice(accounts)
        description = random.choice(NORMAL_TRANSACTION_TYPES)
        
        tx = db.transactions.begin()
        try:
            transaction = db.records.create(
                label="TRANSACTION",
                data={
                    "tx_id": f"txn_normal_{i+1:04d}",
                    "amount": random.uniform(5, 500),
                    "description": description,
                    "currency": "USD",
                    "status": "completed",
                    "timestamp": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat()
                },
                transaction=tx
            )
            
            # Link to account (no vector for normal transactions to save KU)
            db.records.attach(
                source=transaction,
                target=account,
                options={"type": "SENT_FROM", "direction": "out"},
                transaction=tx
            )
            
            tx.commit()
            transactions.append(transaction)
            
        except Exception as e:
            tx.rollback()
            raise e
        
        if (i + 1) % 50 == 0:
            print(f"{i + 1} transactions created", end=" ", flush=True)
    
    print(f"{count} transactions created")
    return transactions


def create_suspicious_transactions(db: RushDB, accounts: List, fraud_patterns: List, count: int) -> List:
    """Create suspicious transactions that match fraud patterns."""
    print(f"[5/5] Creating suspicious transactions...", end=" ", flush=True)
    
    transactions = []
    
    for i in range(count):
        account = random.choice(accounts)
        pattern = random.choice(fraud_patterns)
        description = random.choice(SUSPICIOUS_TRANSACTION_TYPES)
        
        # Generate embedding similar to fraud pattern
        embedding = generate_fraud_embedding()
        
        tx = db.transactions.begin()
        try:
            transaction = db.records.create(
                label="TRANSACTION",
                data={
                    "tx_id": f"txn_suspicious_{i+1:04d}",
                    "amount": random.uniform(pattern.data["amount_min"], pattern.data["amount_max"]),
                    "description": description,
                    "currency": "USD",
                    "status": "pending_review",
                    "pattern_match": pattern.data["pattern_id"],
                    "timestamp": datetime.now().isoformat()
                },
                vectors=[{
                    "propertyName": "description",
                    "vector": embedding
                }],
                transaction=tx
            )
            
            # Link to suspicious account
            db.records.attach(
                source=transaction,
                target=account,
                options={"type": "SENT_FROM", "direction": "out"},
                transaction=tx
            )
            
            tx.commit()
            transactions.append(transaction)
            
        except Exception as e:
            tx.rollback()
            raise e
        
        if (i + 1) % 25 == 0:
            print(f"{i + 1} transactions created", end=" ", flush=True)
    
    print(f"{count} transactions created")
    return transactions


def main():
    """Main seeding function."""
    print("\n" + "="*70)
    print("  SEEDING FRAUD DETECTION DATASET")
    print("="*70 + "\n")
    
    # Initialize RushDB client
    api_token = os.environ.get("RUSHDB_API_TOKEN")
    if not api_token:
        print("ERROR: RUSHDB_API_TOKEN not found in environment.")
        print("Set it in .env file or export RUSHDB_API_TOKEN=<your_token>")
        sys.exit(1)
    
    db = RushDB(api_token)
    
    # Check for existing data
    if check_existing_data(db):
        print("⚠️  Dataset already exists. Skipping seed (idempotent).")
        print("   To reseed, delete existing records first.")
        return
    
    start_time = time.time()
    
    try:
        # Create vector index
        index_id = create_vector_index(db)
        
        # Create accounts
        legitimate_accounts, suspicious_accounts = create_accounts(
            db, 
            NUM_LEGITIMATE_ACCOUNTS, 
            NUM_SUSPICIOUS_ACCOUNTS
        )
        
        # Create fraud patterns (with vectors)
        fraud_patterns = create_fraud_patterns(db)
        
        # Create normal transactions (no vectors)
        normal_transactions = create_normal_transactions(
            db, 
            legitimate_accounts, 
            NUM_NORMAL_TRANSACTIONS
        )
        
        # Create suspicious transactions (with vectors)
        suspicious_transactions = create_suspicious_transactions(
            db,
            suspicious_accounts,
            fraud_patterns,
            NUM_SUSPICIOUS_TRANSACTIONS
        )
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*70)
        print("  DATASET SEEDED SUCCESSFULLY")
        print("="*70)
        print(f"\n  Total time: {elapsed:.1f}s")
        print(f"\n  Records created:")
        print(f"    - {NUM_LEGITIMATE_ACCOUNTS} legitimate accounts")
        print(f"    - {NUM_SUSPICIOUS_ACCOUNTS} suspicious accounts")
        print(f"    - {NUM_KNOWN_FRAUD_PATTERNS} fraud pattern records (with vectors)")
        print(f"    - {NUM_NORMAL_TRANSACTIONS} normal transactions")
        print(f"    - {NUM_SUSPICIOUS_TRANSACTIONS} suspicious transactions (with vectors)")
        print(f"    - Vector index: {index_id}")
        print("\n" + "="*70)
        
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
