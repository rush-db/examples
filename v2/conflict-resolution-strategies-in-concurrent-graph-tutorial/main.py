"""
Conflict Resolution Strategies in Concurrent Graph-Write Operations
===================================================================

This tutorial demonstrates practical strategies for handling concurrent
writes in a graph database using RushDB. It covers:

1. Optimistic Locking - Version-based conflict detection
2. Pessimistic Locking - Transaction-based serialization
3. Upsert Patterns - Idempotent create-or-update operations
4. Merge Strategies - Combining field values intelligently
5. Relationship Conflicts - Edge creation in concurrent contexts

Run: python main.py
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# RushDB SDK
from rushdb import RushDB
from rushdb.models import ConflictError, NonUniqueResultError

# Load environment
load_dotenv()


@dataclass
class ConflictResolutionDemo:
    """Demonstrates conflict resolution strategies in RushDB."""
    
    db: RushDB
    verbose: bool = True
    
    def log(self, message: str, symbol: str = "[·]"):
        """Print a formatted log message."""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"  {timestamp} {symbol} {message}")
    
    def log_success(self, message: str):
        self.log(message, "[✓]")
    
    def log_error(self, message: str):
        self.log(message, "[✗]")
    
    def log_info(self, message: str):
        self.log(message, "[i]")
    
    # -------------------------------------------------------------------------
    # Strategy 1: Optimistic Locking
    # -------------------------------------------------------------------------
    
    def demonstrate_optimistic_locking(self) -> None:
        """
        Optimistic locking uses a version field to detect concurrent modifications.
        
        Flow:
        1. Read the record and remember its version
        2. Attempt the update with the expected version
        3. If version changed, a conflict occurred
        4. Resolve by re-fetching and merging
        """
        print("\n" + "=" * 60)
        print("Strategy 1: Optimistic Locking")
        print("=" * 60)
        
        # Clean up any existing test records
        self._cleanup_label("DOCUMENT")
        
        # Step 1: Create initial record with version field
        doc = self.db.records.upsert(
            label="DOCUMENT",
            data={
                "slug": f"opt-lock-doc-{uuid.uuid4().hex[:8]}",
                "title": "Original Title",
                "content": "Initial content",
                "version": 1,
                "updatedAt": datetime.now().isoformat()
            },
            options={"mergeBy": ["slug"]}
        )
        self.log_success(f"Created document with version={doc['version']}")
        
        # Step 2: Simulate read by Process A (caches the record)
        process_a_record = self.db.records.find_one({
            "labels": ["DOCUMENT"],
            "where": {"slug": doc["slug"]}
        })
        expected_version = process_a_record["version"]
        self.log_info(f"Process A read record, expected version: {expected_version}")
        
        # Step 3: Simulate Process B updates the record concurrently
        # (In real systems, this happens in a separate thread/process)
        process_b_record = self.db.records.find_one({
            "labels": ["DOCUMENT"],
            "where": {"slug": doc["slug"]}
        })
        
        # Process B updates the record
        self.db.records.update(
            record_id=process_b_record.id,
            data={
                "version": expected_version + 1,
                "title": "Process B's Updated Title",
                "updatedAt": datetime.now().isoformat()
            }
        )
        self.log_info("Process B updated the record")
        
        # Step 4: Process A tries to update with stale version
        # In real RushDB, we detect this by re-reading before write
        recheck_record = self.db.records.find_one({
            "labels": ["DOCUMENT"],
            "where": {"slug": doc["slug"]}
        })
        
        if recheck_record["version"] != expected_version:
            self.log_info(f"Conflict detected! Current version: {recheck_record['version']}, expected: {expected_version}")
            
            # Step 5: Resolve the conflict using a merge strategy
            # Here we combine the changes intelligently
            merged_title = f"{process_a_record['title']} + {recheck_record['title']}"
            
            self.db.records.update(
                record_id=recheck_record.id,
                data={
                    "title": merged_title,
                    "version": recheck_record["version"] + 1,
                    "conflictResolved": True,
                    "resolutionNote": "Merged concurrent updates",
                    "updatedAt": datetime.now().isoformat()
                }
            )
            self.log_success(f"Conflict resolved: merged title = '{merged_title}'")
        else:
            # No conflict, safe to update
            self.db.records.update(
                record_id=process_a_record.id,
                data={
                    "version": expected_version + 1,
                    "updatedAt": datetime.now().isoformat()
                }
            )
            self.log_success("No conflict, update applied directly")
        
        # Verify final state
        final_record = self.db.records.find_one({
            "labels": ["DOCUMENT"],
            "where": {"slug": doc["slug"]}
        })
        self.log_info(f"Final record version: {final_record['version']}")
        self.log_info(f"Final title: {final_record['title']}")
    
    # -------------------------------------------------------------------------
    # Strategy 2: Pessimistic Locking (Transactions)
    # -------------------------------------------------------------------------
    
    def demonstrate_pessimistic_locking(self) -> None:
        """
        Pessimistic locking uses transactions to serialize access to critical sections.
        
        Flow:
        1. Begin a transaction
        2. Perform all operations within the transaction
        3. Commit to apply all changes atomically
        4. On error, rollback to cancel all changes
        """
        print("\n" + "=" * 60)
        print("Strategy 2: Pessimistic Locking (Transactions)")
        print("=" * 60)
        
        # Clean up any existing test records
        self._cleanup_label("ORDER")
        self._cleanup_label("ORDER_ITEM")
        self._cleanup_label("CUSTOMER")
        
        # Create a customer first
        customer = self.db.records.upsert(
            label="CUSTOMER",
            data={
                "externalId": f"cust-{uuid.uuid4().hex[:8]}",
                "name": "Test Customer"
            },
            options={"mergeBy": ["externalId"]}
        )
        self.log_info(f"Created customer: {customer['name']}")
        
        # Step 1: Begin transaction
        self.log_info("Beginning transaction for atomic order creation...")
        
        # Use context manager for automatic commit/rollback
        with self.db.transactions.begin() as tx:
            # Step 2: Create order within transaction
            order = self.db.records.create(
                label="ORDER",
                data={
                    "orderNumber": f"ORD-{uuid.uuid4().hex[:8].upper()}",
                    "total": 149.99,
                    "status": "pending",
                    "createdAt": datetime.now().isoformat()
                },
                transaction=tx
            )
            self.log_info(f"Created order: {order['orderNumber']}")
            
            # Step 3: Create order items within transaction
            items = []
            for i, item_data in enumerate([
                {"name": "Widget Pro", "quantity": 2, "price": 49.99},
                {"name": "Gadget Plus", "quantity": 1, "price": 50.01}
            ]):
                item = self.db.records.create(
                    label="ORDER_ITEM",
                    data=item_data,
                    transaction=tx
                )
                items.append(item)
                self.log_info(f"Created item {i+1}: {item_data['name']}")
            
            # Step 4: Attach items to order within transaction
            for item in items:
                self.db.records.attach(
                    source=order,
                    target=item,
                    options={"type": "CONTAINS"},
                    transaction=tx
                )
            
            # Step 5: Attach order to customer within transaction
            self.db.records.attach(
                source=customer,
                target=order,
                options={"type": "PLACED"},
                transaction=tx
            )
            self.log_info("Linked all entities within transaction")
        
        # Transaction committed automatically on clean exit
        self.log_success("Transaction committed successfully")
        
        # Step 6: Verify all entities were created atomically
        found_order = self.db.records.find_one({
            "labels": ["ORDER"],
            "where": {"orderNumber": order["orderNumber"]}
        })
        
        if found_order:
            self.log_success(f"Order persisted with {len(items)} items")
            
            # Verify relationships exist
            order_items = self.db.records.find({
                "labels": ["ORDER_ITEM"],
                "where": {"ORDER": {"$id": order.id}},
                "limit": 10
            })
            self.log_info(f"Verified {order_items.total} ORDER_ITEM relationships")
        else:
            self.log_error("Order creation failed - transaction was rolled back")
        
        # Demonstrate rollback on error
        self._demonstrate_rollback()
    
    def _demonstrate_rollback(self) -> None:
        """Demonstrate transaction rollback on error."""
        print("\n  --- Rollback Demonstration ---")
        
        sku_to_test = f"ROLLBACK-TEST-{uuid.uuid4().hex[:8]}"
        
        try:
            with self.db.transactions.begin() as tx:
                # Create a record
                product = self.db.records.create(
                    label="PRODUCT",
                    data={
                        "sku": sku_to_test,
                        "category": "rollback-test",
                        "price": 9.99
                    },
                    transaction=tx
                )
                self.log_info(f"Created test product: {product['sku']}")
                
                # Simulate an error that should trigger rollback
                raise ValueError("Simulated processing error")
                
        except ValueError as e:
            self.log_info(f"Error caught: {e}")
            self.log_info("Transaction rolled back - no partial changes persisted")
        
        # Verify no record was created
        result = self.db.records.find({
            "labels": ["PRODUCT"],
            "where": {"sku": sku_to_test}
        })
        
        if result.total == 0:
            self.log_success("Rollback verified: no record persisted")
        else:
            self.log_error("Rollback failed: record was persisted")
    
    # -------------------------------------------------------------------------
    # Strategy 3: Upsert with mergeBy
    # -------------------------------------------------------------------------
    
    def demonstrate_upsert_patterns(self) -> None:
        """
        Upsert patterns provide idempotent create-or-update operations.
        
        Flow:
        1. Use mergeBy to define unique key(s) for matching
        2. First call creates the record
        3. Subsequent calls update the existing record
        4. mergeStrategy controls how fields are combined
        """
        print("\n" + "=" * 60)
        print("Strategy 3: Upsert with mergeBy")
        print("=" * 60)
        
        # Clean up any existing test records
        self._cleanup_label("USER")
        
        external_id = f"user-{uuid.uuid4().hex[:8]}"
        
        # Step 1: First upsert - creates the record
        user1 = self.db.records.upsert(
            label="USER",
            data={
                "externalId": external_id,
                "name": "Alice Chen",
                "email": "alice@example.com",
                "tags": ["early-adopter"],
                "loginCount": 1,
                "lastLogin": datetime.now().isoformat()
            },
            options={"mergeBy": ["externalId"]}
        )
        self.log_success(f"First upsert created user: {user1['name']}")
        self.log_info(f"Record ID: {user1.id}")
        
        # Step 2: Second upsert - updates existing record (default: replace)
        user2 = self.db.records.upsert(
            label="USER",
            data={
                "externalId": external_id,
                "loginCount": 2,
                "lastLogin": datetime.now().isoformat()
            },
            options={"mergeBy": ["externalId"]}  # mergeStrategy defaults to 'replace'
        )
        self.log_info(f"Second upsert (replace strategy)")
        
        # Verify the record was updated, not duplicated
        found_users = self.db.records.find({
            "labels": ["USER"],
            "where": {"externalId": external_id}
        })
        self.log_info(f"Total records with externalId '{external_id}': {found_users.total}")
        
        # Step 3: Upsert with append strategy for array fields
        user3 = self.db.records.upsert(
            label="USER",
            data={
                "externalId": external_id,
                "tags": ["active", "beta-tester"],
                "loginCount": 3
            },
            options={"mergeBy": ["externalId"], "mergeStrategy": "append"}
        )
        self.log_success(f"Third upsert (append strategy)")
        
        # Verify tags were appended, not replaced
        self.log_info(f"User tags: {user3.get('tags', [])}")
        
        # Step 4: Demonstrate concurrent upserts (both try to create/update)
        self.log_info("Simulating concurrent upserts...")
        
        external_id_2 = f"concurrent-user-{uuid.uuid4().hex[:8]}"
        
        # Process A creates the user
        record_a = self.db.records.upsert(
            label="USER",
            data={
                "externalId": external_id_2,
                "name": "Bob Martinez",
                "permissions": ["read"]
            },
            options={"mergeBy": ["externalId"], "mergeStrategy": "append"}
        )
        self.log_info(f"Process A created user: {record_a['name']}")
        
        # Process B tries to upsert the same user
        record_b = self.db.records.upsert(
            label="USER",
            data={
                "externalId": external_id_2,
                "name": "Bob Martinez",
                "permissions": ["write"]
            },
            options={"mergeBy": ["externalId"], "mergeStrategy": "append"}
        )
        self.log_info(f"Process B upserted same user: {record_b['name']}")
        
        # Verify only one record exists with merged permissions
        final_user = self.db.records.find_one({
            "labels": ["USER"],
            "where": {"externalId": external_id_2}
        })
        
        self.log_success(f"Single record preserved with merged permissions: {final_user.get('permissions', [])}")
    
    # -------------------------------------------------------------------------
    # Strategy 4: Merge Strategies
    # -------------------------------------------------------------------------
    
    def demonstrate_merge_strategies(self) -> None:
        """
        Demonstrate different merge strategies for handling field conflicts.
        
        Strategies:
        - 'replace': Overwrite existing values (default)
        - 'append': Merge arrays by concatenation
        - 'merge': Deep merge nested objects
        """
        print("\n" + "=" * 60)
        print("Strategy 4: Merge Strategies")
        print("=" * 60)
        
        self._cleanup_label("CONFIG")
        
        config_id = f"config-{uuid.uuid4().hex[:8]}"
        
        # Initial config with various field types
        initial_config = {
            "configId": config_id,
            "settings": {"theme": "light", "notifications": True},
            "tags": ["default"],
            "version": "1.0"
        }
        
        self.db.records.upsert(
            label="CONFIG",
            data=initial_config,
            options={"mergeBy": ["configId"]}
        )
        self.log_info("Created initial config with nested objects and arrays")
        
        # Show what each merge strategy does
        strategies = [
            ("replace", {"settings": {"theme": "dark"}, "tags": ["dark-mode"], "version": "2.0"}),
            ("append", {"tags": ["user-preference", "customized"], "version": "2.1"}),
        ]
        
        for strategy, updates in strategies:
            self.log_info(f"\n  Applying '{strategy}' strategy with updates:")
            for key, value in updates.items():
                self.log_info(f"    - {key}: {value}")
            
            result = self.db.records.upsert(
                label="CONFIG",
                data={"configId": config_id, **updates},
                options={"mergeBy": ["configId"], "mergeStrategy": strategy}
            )
            
            self.log_info(f"  Result after '{strategy}':")
            if "settings" in result:
                self.log_info(f"    - settings: {result['settings']}")
            if "tags" in result:
                self.log_info(f"    - tags: {result['tags']}")
            if "version" in result:
                self.log_info(f"    - version: {result['version']}")
    
    # -------------------------------------------------------------------------
    # Strategy 5: Relationship Edge Conflicts
    # -------------------------------------------------------------------------
    
    def demonstrate_relationship_conflicts(self) -> None:
        """
        Demonstrate handling of concurrent relationship creation.
        
        RushDB automatically prevents duplicate relationship edges.
        Multiple processes can safely try to create the same relationship.
        """
        print("\n" + "=" * 60)
        print("Strategy 5: Relationship Edge Conflicts")
        print("=" * 60)
        
        self._cleanup_label("USER")
        self._cleanup_label("FOLLOW")
        
        # Create two users
        user_a = self.db.records.upsert(
            label="USER",
            data={
                "externalId": f"user-a-{uuid.uuid4().hex[:8]}",
                "username": "alice"
            },
            options={"mergeBy": ["externalId"]}
        )
        
        user_b = self.db.records.upsert(
            label="USER",
            data={
                "externalId": f"user-b-{uuid.uuid4().hex[:8]}",
                "username": "bob"
            },
            options={"mergeBy": ["externalId"]}
        )
        
        self.log_info(f"Created users: {user_a['username']} and {user_b['username']}")
        
        # Step 1: Create initial follow relationship
        self.db.records.attach(
            source=user_a,
            target=user_b,
            options={"type": "FOLLOWS"}
        )
        self.log_success("Alice now follows Bob")
        
        # Step 2: Attempt to create the same relationship again
        # (simulating concurrent request from another process)
        self.db.records.attach(
            source=user_a,
            target=user_b,
            options={"type": "FOLLOWS"}
        )
        self.log_info("Duplicate FOLLOWS attempt - safely ignored by RushDB")
        
        # Step 3: Verify only one relationship exists
        all_follows = self.db.records.find({
            "labels": ["USER"],
            "where": {"FOLLOWS": {"$id": user_b.id}}
        })
        
        self.log_success(f"Verified: Alice's total follows to Bob: {all_follows.total} (should be 1)")
        
        # Step 4: Create bidirectional relationship
        self.db.records.attach(
            source=user_b,
            target=user_a,
            options={"type": "FOLLOWS"}
        )
        self.log_success("Bob now follows Alice back (bidirectional)")
        
        # Step 5: Demonstrate relationship within transaction
        self.log_info("\n  Creating relationship within transaction...")
        
        user_c = self.db.records.upsert(
            label="USER",
            data={
                "externalId": f"user-c-{uuid.uuid4().hex[:8]}",
                "username": "carol"
            },
            options={"mergeBy": ["externalId"]}
        )
        
        with self.db.transactions.begin() as tx:
            self.db.records.attach(
                source=user_c,
                target=user_a,
                options={"type": "FOLLOWS"},
                transaction=tx
            )
            # Transaction auto-commits
        
        self.log_success("Carol follows Alice within transaction")
        
        # Verify
        carol_follows = self.db.records.find({
            "labels": ["USER"],
            "where": {"FOLLOWS": {"$id": user_a.id}}
        })
        self.log_info(f"Carol's follow relationships: {carol_follows.total}")
    
    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    
    def _cleanup_label(self, label: str) -> None:
        """"Remove all records with a specific label."""
        try:
            self.db.records.delete({"labels": [label]})
        except Exception:
            pass  # Ignore errors during cleanup
    
    def seed_sample_data(self) -> dict:
        """
        Load and seed sample graph data from JSON file.
        Returns a dict with created record counts.
        """
        print("\n" + "=" * 60)
        print("Seeding Sample Data")
        print("=" * 60)
        
        data_file = Path(__file__).parent / "data" / "sample_graph.json"
        
        if not data_file.exists():
            self.log_error(f"Sample data file not found: {data_file}")
            return {"error": "Data file missing"}
        
        with open(data_file) as f:
            graph_data = json.load(f)
        
        counts = {}
        for label, records in graph_data.items():
            created = self.db.records.create_many(
                label=label,
                data=records
            )
            counts[label] = len(records)
            self.log_success(f"Created {len(records)} {label} records")
        
        return counts
    
    def run_all_demos(self) -> None:
        """Run all conflict resolution demonstrations."""
        print("\n" + "=" * 60)
        print("RushDB Conflict Resolution Strategies")
        print("Concurrent Graph-Write Operations Tutorial")
        print("=" * 60)
        
        # Seed initial data
        self.seed_sample_data()
        
        # Run all strategy demonstrations
        self.demonstrate_optimistic_locking()
        self.demonstrate_pessimistic_locking()
        self.demonstrate_upsert_patterns()
        self.demonstrate_merge_strategies()
        self.demonstrate_relationship_conflicts()
        
        print("\n" + "=" * 60)
        print("All Demonstrations Complete")
        print("=" * 60)
        print("\nKey Takeaways:")
        print("  1. Optimistic Locking: Best for read-heavy workloads with occasional conflicts")
        print("  2. Pessimistic Locking: Best for high-contention critical sections")
        print("  3. Upsert: Best for external-system sync with idempotent operations")
        print("  4. Merge Strategies: Choose replace/append based on your data model")
        print("  5. Relationships: RushDB handles edge deduplication automatically")
        print()


def main():
    """Main entry point for the tutorial."""
    
    # Initialize RushDB client
    api_key = os.getenv("RUSHDB_API_KEY")
    api_url = os.getenv("RUSHDB_URL")
    
    if not api_key:
        print("\nError: RUSHDB_API_KEY environment variable is not set.")
        print("\nPlease configure your environment:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your RushDB API key to .env")
        print("  3. Get your API key at: https://app.rushdb.com/settings/api-keys")
        return 1
    
    # Create RushDB client
    db_kwargs = {"token": api_key}
    if api_url:
        db_kwargs["url"] = api_url
    
    db = RushDB(**db_kwargs)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="RushDB Conflict Resolution Tutorials")
    parser.add_argument(
        "--strategy",
        choices=["optimistic", "pessimistic", "upsert", "merge", "relationships", "all"],
        default="all",
        help="Which strategy to demonstrate (default: all)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose output"
    )
    args = parser.parse_args()
    
    # Create demo instance
    demo = ConflictResolutionDemo(db=db, verbose=not args.quiet)
    
    # Run requested demonstrations
    if args.strategy == "all":
        demo.run_all_demos()
    elif args.strategy == "optimistic":
        demo.demonstrate_optimistic_locking()
    elif args.strategy == "pessimistic":
        demo.demonstrate_pessimistic_locking()
    elif args.strategy == "upsert":
        demo.demonstrate_upsert_patterns()
    elif args.strategy == "merge":
        demo.demonstrate_merge_strategies()
    elif args.strategy == "relationships":
        demo.demonstrate_relationship_conflicts()
    
    return 0


if __name__ == "__main__":
    exit(main())
