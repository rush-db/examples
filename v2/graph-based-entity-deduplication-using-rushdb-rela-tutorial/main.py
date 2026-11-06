#!/usr/bin/env python3
"""
Graph-based Entity Deduplication using RushDB Relationships

This tutorial demonstrates how to identify and merge duplicate customer entities
by analyzing their relationship graphs rather than just property matching.

Key concepts:
1. Relationship-based similarity scoring
2. Union-Find for transitive duplicate detection
3. Graph consolidation while preserving relationships
"""

import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

from dotenv import load_dotenv

from rushdb import RushDB

# Load environment
load_dotenv()
API_TOKEN = os.getenv("RUSHDB_API_TOKEN")

if not API_TOKEN:
    raise ValueError("RUSHDB_API_TOKEN not found in environment. Copy .env.example to .env")

# Deduplication thresholds
SIMILARITY_THRESHOLD = 0.5  # Minimum score to consider as duplicate
PHONE_PREFIX_WEIGHT = 0.15
EMAIL_DOMAIN_WEIGHT = 0.20
NAME_SIMILARITY_WEIGHT = 0.10
SHARED_ORDER_WEIGHT = 0.35
SHARED_CONTACT_WEIGHT = 0.25
SHARED_ADDRESS_WEIGHT = 0.05


@dataclass
class CustomerSignal:
    """Container for deduplication signals between two customers."""
    customer_a_id: str
    customer_b_id: str
    email_domain_match: bool = False
    phone_prefix_match: bool = False
    name_similarity: float = 0.0
    shared_orders: int = 0
    shared_contacts: int = 0
    shared_addresses: int = 0
    total_related_entities: int = 0

    @property
    def similarity_score(self) -> float:
        """Calculate overall similarity score based on weighted signals."""
        score = 0.0
        
        if self.email_domain_match:
            score += EMAIL_DOMAIN_WEIGHT
        
        if self.phone_prefix_match:
            score += PHONE_PREFIX_WEIGHT
        
        if self.name_similarity > 0.5:
            score += NAME_SIMILARITY_WEIGHT * (self.name_similarity - 0.5) * 2
        
        # Normalize shared entities by potential maximum
        if self.total_related_entities > 0:
            order_ratio = min(self.shared_orders / 3, 1.0)
            contact_ratio = min(self.shared_contacts / 2, 1.0)
            address_ratio = min(self.shared_addresses / 1, 1.0)
            
            score += SHARED_ORDER_WEIGHT * order_ratio
            score += SHARED_CONTACT_WEIGHT * contact_ratio
            score += SHARED_ADDRESS_WEIGHT * address_ratio
        
        return min(score, 1.0)


class UnionFind:
    """Union-Find data structure for clustering duplicate entities."""
    
    def __init__(self):
        self.parent: Dict[str, str] = {}
        self.rank: Dict[str, int] = {}
    
    def add(self, item: str) -> None:
        """Add a new element to the structure."""
        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0
    
    def find(self, item: str) -> str:
        """Find the root/canonical element of the set."""
        if item not in self.parent:
            self.add(item)
        
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])  # Path compression
        
        return self.parent[item]
    
    def union(self, item_a: str, item_b: str) -> None:
        """Merge the sets containing item_a and item_b."""
        root_a = self.find(item_a)
        root_b = self.find(item_b)
        
        if root_a != root_b:
            # Union by rank
            if self.rank[root_a] < self.rank[root_b]:
                self.parent[root_a] = root_b
            elif self.rank[root_a] > self.rank[root_b]:
                self.parent[root_b] = root_a
            else:
                self.parent[root_b] = root_a
                self.rank[root_a] += 1
    
    def get_clusters(self) -> Dict[str, Set[str]]:
        """Get all clusters as {root_id: {member_ids}}."""
        clusters: Dict[str, Set[str]] = defaultdict(set)
        
        for item in self.parent:
            root = self.find(item)
            clusters[root].add(item)
        
        return dict(clusters)


class GraphDeduplicator:
    """
    Graph-based entity deduplication engine.
    
    Identifies duplicate customers by analyzing their relationship graphs
    and shared properties, then merges them while preserving all connections.
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.customers: List[Any] = []
        self.customer_by_id: Dict[str, Any] = {}
        self.related_entities: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: {"orders": set(), "contacts": set(), "addresses": set()}
        )
    
    def load_customers(self) -> int:
        """Load all customer records and their relationships."""
        print("Loading customer records...")
        
        result = self.db.records.find({
            "labels": ["CUSTOMER"],
            "where": {}
        })
        
        self.customers = result.data
        
        for customer in self.customers:
            self.customer_by_id[customer.id] = customer
        
        print(f"  Loaded {len(self.customers)} customers")
        
        # Load related entities for each customer
        self._load_related_entities()
        
        return len(self.customers)
    
    def _load_related_entities(self) -> None:
        """Load all orders, contacts, and addresses for customers."""
        print("Loading related entities...")
        
        # Find all orders
        orders = self.db.records.find({"labels": ["ORDER"], "where": {}})
        
        for order in orders.data:
            # Find which customer placed this order
            placed_by = self.db.records.find({
                "labels": ["CUSTOMER"],
                "where": {
                    "ORDER": {"$relation": {"type": "PLACED_BY", "direction": "in"}}
                }
            })
            
            for customer in placed_by.data:
                self.related_entities[customer.id]["orders"].add(order.id)
        
        # Find all contacts
        contacts = self.db.records.find({"labels": ["CONTACT"], "where": {}})
        
        for contact in contacts.data:
            # Find customers linked to this contact
            has_contact = self.db.records.find({
                "labels": ["CUSTOMER"],
                "where": {
                    "CONTACT": {"$relation": {"type": "HAS_CONTACT", "direction": "out"}}
                }
            })
            
            for customer in has_contact.data:
                self.related_entities[customer.id]["contacts"].add(contact.id)
        
        # Find all addresses
        addresses = self.db.records.find({"labels": ["ADDRESS"], "where": {}})
        
        for address in addresses.data:
            # Find customers at this address
            located_at = self.db.records.find({
                "labels": ["CUSTOMER"],
                "where": {
                    "ADDRESS": {"$relation": {"type": "LOCATED_AT", "direction": "out"}}
                }
            })
            
            for customer in located_at.data:
                self.related_entities[customer.id]["addresses"].add(address.id)
        
        total_related = sum(
            len(entities) 
            for entities in self.related_entities.values()
        )
        print(f"  Loaded {total_related} related entity links")
    
    def _extract_email_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address."""
        if not email or "@" not in email:
            return None
        return email.split("@")[-1].lower()
    
    def _extract_phone_prefix(self, phone: str) -> Optional[str]:
        """Extract area/code prefix from phone number."""
        if not phone:
            return None
        # Extract first 3 digits after stripping non-numerics (except leading +)
        digits = "".join(c for c in phone if c.isdigit())
        if len(digits) >= 3:
            return digits[:3]
        return None
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate name similarity using simple character-based approach.
        For production, use more sophisticated methods like Jaro-Winkler or Levenshtein.
        """
        if not name1 or not name2:
            return 0.0
        
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        if name1 == name2:
            return 1.0
        
        # Simple overlap coefficient
        set1 = set(name1)
        set2 = set(name2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def analyze_pair(self, customer_a: Any, customer_b: Any) -> CustomerSignal:
        """
        Analyze two customers to detect deduplication signals.
        
        Returns a CustomerSignal with all detected relationships and similarities.
        """
        signal = CustomerSignal(
            customer_a_id=customer_a.id,
            customer_b_id=customer_b.id
        )
        
        email_a = customer_a.get("email", "")
        email_b = customer_b.get("email", "")
        
        domain_a = self._extract_email_domain(email_a)
        domain_b = self._extract_email_domain(email_b)
        
        if domain_a and domain_b and domain_a == domain_b:
            signal.email_domain_match = True
        
        phone_a = self._extract_phone_prefix(customer_a.get("phone", ""))
        phone_b = self._extract_phone_prefix(customer_b.get("phone", ""))
        
        if phone_a and phone_b and phone_a == phone_b:
            signal.phone_prefix_match = True
        
        # Name similarity (check first and last name separately)
        first_sim = self._calculate_name_similarity(
            customer_a.get("first_name", ""),
            customer_b.get("first_name", "")
        )
        last_sim = self._calculate_name_similarity(
            customer_a.get("last_name", ""),
            customer_b.get("last_name", "")
        )
        signal.name_similarity = (first_sim + last_sim) / 2
        
        # Shared entities analysis
        entities_a = self.related_entities.get(customer_a.id, {
            "orders": set(), "contacts": set(), "addresses": set()
        })
        entities_b = self.related_entities.get(customer_b.id, {
            "orders": set(), "contacts": set(), "addresses": set()
        })
        
        signal.shared_orders = len(entities_a["orders"] & entities_b["orders"])
        signal.shared_contacts = len(entities_a["contacts"] & entities_b["contacts"])
        signal.shared_addresses = len(entities_a["addresses"] & entities_b["addresses"])
        
        signal.total_related_entities = (
            len(entities_a["orders"]) + len(entities_b["orders"]) +
            len(entities_a["contacts"]) + len(entities_b["contacts"]) +
            len(entities_a["addresses"]) + len(entities_b["addresses"])
        )
        
        return signal
    
    def find_duplicate_clusters(self) -> List[Tuple[List[Any], CustomerSignal]]:
        """
        Find all duplicate clusters using relationship analysis.
        
        Returns a list of (cluster_members, representative_signal) tuples.
        """
        print("\nAnalyzing relationship graph for duplicate detection...")
        
        uf = UnionFind()
        pair_signals: List[CustomerSignal] = []
        
        # Compare all pairs of customers
        total_pairs = len(self.customers) * (len(self.customers) - 1) // 2
        print(f"  Analyzing {total_pairs} customer pairs...")
        
        analyzed = 0
        for i, customer_a in enumerate(self.customers):
            for customer_b in self.customers[i + 1:]:
                signal = self.analyze_pair(customer_a, customer_b)
                
                if signal.similarity_score >= SIMILARITY_THRESHOLD:
                    uf.union(customer_a.id, customer_b.id)
                    pair_signals.append(signal)
                    print(f"    Match found: {customer_a.get('email', 'N/A')} <-> {customer_b.get('email', 'N/A')} (score: {signal.similarity_score:.2f})")
                
                analyzed += 1
                if analyzed % 100 == 0:
                    print(f"  Progress: {analyzed}/{total_pairs} pairs analyzed")
        
        # Get clusters
        clusters = uf.get_clusters()
        
        # Filter to only clusters with multiple members (actual duplicates)
        duplicate_clusters = []
        
        for root_id, member_ids in clusters.items():
            if len(member_ids) > 1:
                members = [
                    self.customer_by_id[mid] 
                    for mid in member_ids 
                    if mid in self.customer_by_id
                ]
                
                # Find representative signal for this cluster
                rep_signal = None
                for sig in pair_signals:
                    if sig.customer_a_id in member_ids and sig.customer_b_id in member_ids:
                        rep_signal = sig
                        break
                
                duplicate_clusters.append((members, rep_signal))
        
        print(f"\n  Found {len(duplicate_clusters)} duplicate clusters")
        
        return duplicate_clusters
    
    def select_canonical_customer(self, cluster: List[Any]) -> Any:
        """
        Select the canonical (master) customer from a duplicate cluster.
        
        Selection criteria:
        1. Most relationships (orders, contacts, addresses)
        2. Verified status
        3. Most complete data
        """
        def score_customer(customer: Any) -> Tuple[int, bool, int]:
            entities = self.related_entities.get(customer.id, {
                "orders": set(), "contacts": set(), "addresses": set()
            })
            relationship_count = (
                len(entities["orders"]) +
                len(entities["contacts"]) +
                len(entities["addresses"])
            )
            is_verified = customer.get("is_verified", False)
            data_completeness = sum(
                1 for field in ["email", "phone", "first_name", "last_name"]
                if customer.get(field)
            )
            
            return (relationship_count, is_verified, data_completeness)
        
        # Sort by score (descending)
        return max(cluster, key=score_customer)
    
    def merge_duplicates(
        self, 
        cluster: List[Any], 
        canonical: Any,
        signal: Optional[CustomerSignal]
    ) -> Dict[str, int]:
        """
        Merge duplicate records into the canonical record.
        
        Returns statistics about the merge operation.
        """
        stats = {
            "relationships_preserved": 0,
            "properties_merged": 0,
            "duplicates_deleted": 0,
        }
        
        duplicates = [c for c in cluster if c.id != canonical.id]
        
        for duplicate in duplicates:
            # Transfer all relationships to canonical
            # Orders
            duplicate_orders = self.db.records.find({
                "labels": ["ORDER"],
                "where": {
                    "CUSTOMER": {
                        "$relation": {"type": "PLACED_BY", "direction": "in"},
                        "$id": duplicate.id
                    }
                }
            })
            
            for order in duplicate_orders.data:
                # Check if already linked
                existing_orders = self.db.records.find({
                    "labels": ["ORDER"],
                    "where": {
                        "CUSTOMER": {
                            "$relation": {"type": "PLACED_BY", "direction": "in"},
                            "$id": canonical.id
                        }
                    }
                })
                
                if order.id not in [o.id for o in existing_orders.data]:
                    self.db.records.attach(
                        source=order,
                        target=canonical,
                        options={"type": "PLACED_BY", "direction": "out"}
                    )
                    stats["relationships_preserved"] += 1
            
            # Contacts
            duplicate_contacts = self.db.records.find({
                "labels": ["CONTACT"],
                "where": {
                    "CUSTOMER": {
                        "$relation": {"type": "HAS_CONTACT", "direction": "out"},
                        "$id": duplicate.id
                    }
                }
            })
            
            for contact in duplicate_contacts.data:
                existing_contacts = self.db.records.find({
                    "labels": ["CONTACT"],
                    "where": {
                        "CUSTOMER": {
                            "$relation": {"type": "HAS_CONTACT", "direction": "out"},
                            "$id": canonical.id
                        }
                    }
                })
                
                if contact.id not in [c.id for c in existing_contacts.data]:
                    self.db.records.attach(
                        source=canonical,
                        target=contact,
                        options={"type": "HAS_CONTACT", "direction": "out"}
                    )
                    stats["relationships_preserved"] += 1
            
            # Addresses
            duplicate_addresses = self.db.records.find({
                "labels": ["ADDRESS"],
                "where": {
                    "CUSTOMER": {
                        "$relation": {"type": "LOCATED_AT", "direction": "out"},
                        "$id": duplicate.id
                    }
                }
            })
            
            for address in duplicate_addresses.data:
                existing_addresses = self.db.records.find({
                    "labels": ["ADDRESS"],
                    "where": {
                        "CUSTOMER": {
                            "$relation": {"type": "LOCATED_AT", "direction": "out"},
                            "$id": canonical.id
                        }
                    }
                })
                
                if address.id not in [a.id for a in existing_addresses.data]:
                    self.db.records.attach(
                        source=canonical,
                        target=address,
                        options={"type": "LOCATED_AT", "direction": "out"}
                    )
                    stats["relationships_preserved"] += 1
            
            # Merge properties (canonical wins on conflicts)
            for field in ["email", "phone", "first_name", "last_name", "company"]:
                if not canonical.get(field) and duplicate.get(field):
                    canonical.update({field: duplicate.get(field)})
                    stats["properties_merged"] += 1
            
            # Mark as merged and delete
            duplicate.update({
                "merged_into": canonical.id,
                "merged_at": __import__("datetime").datetime.now().isoformat(),
                "deduplication_source": "graph_analysis"
            })
            
            self.db.records.delete(record_id=duplicate.id)
            stats["duplicates_deleted"] += 1
        
        # Update canonical with merge metadata
        canonical.update({
            "deduplicated": True,
            "deduplication_source": "graph_analysis",
            "deduplicated_at": __import__("datetime").datetime.now().isoformat(),
            "duplicates_merged": len(duplicates)
        })
        
        return stats
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the full deduplication pipeline.
        
        Returns statistics about the operation.
        """
        print("=" * 60)
        print("Graph-based Entity Deduplication")
        print("=" * 60)
        
        # Load data
        total_customers = self.load_customers()
        
        # Find duplicate clusters
        clusters = self.find_duplicate_clusters()
        
        if not clusters:
            print("\nNo duplicate clusters found.")
            return {
                "total_customers": total_customers,
                "duplicate_groups": 0,
                "records_merged": 0,
                "relationships_preserved": 0,
            }
        
        # Process each cluster
        print("\n" + "-" * 60)
        print("Merging Duplicate Clusters")
        print("-" * 60)
        
        total_stats = {
            "duplicate_groups": len(clusters),
            "records_merged": 0,
            "relationships_preserved": 0,
            "properties_merged": 0,
        }
        
        for i, (cluster, signal) in enumerate(clusters, 1):
            print(f"\nDuplicate Group #{i}:")
            
            canonical = self.select_canonical_customer(cluster)
            
            print(f"  Canonical: {canonical.id}")
            print(f"    Name: {canonical.get('first_name', '')} {canonical.get('last_name', '')}")
            print(f"    Email: {canonical.get('email', 'N/A')}")
            print(f"  Merging {len(cluster) - 1} duplicate(s)")
            
            if signal:
                print(f"  Shared signals:")
                if signal.email_domain_match:
                    print(f"    - Email domain match: {self._extract_email_domain(canonical.get('email', ''))}")
                if signal.phone_prefix_match:
                    print(f"    - Phone prefix match")
                if signal.shared_orders > 0:
                    print(f"    - Shared orders: {signal.shared_orders}")
                if signal.shared_contacts > 0:
                    print(f"    - Shared contacts: {signal.shared_contacts}")
                if signal.shared_addresses > 0:
                    print(f"    - Shared addresses: {signal.shared_addresses}")
                print(f"    - Confidence: {signal.similarity_score:.2f}")
            
            stats = self.merge_duplicates(cluster, canonical, signal)
            total_stats["records_merged"] += stats["duplicates_deleted"]
            total_stats["relationships_preserved"] += stats["relationships_preserved"]
            total_stats["properties_merged"] += stats["properties_merged"]
            
            print(f"  Result: {stats['relationships_preserved']} relationships preserved")
        
        # Final summary
        print("\n" + "=" * 60)
        print("Deduplication Complete")
        print("=" * 60)
        print(f"  Total customer records: {total_customers}")
        print(f"  Duplicate groups resolved: {total_stats['duplicate_groups']}")
        print(f"  Records merged: {total_stats['records_merged']}")
        print(f"  Relationships preserved: {total_stats['relationships_preserved']}")
        print(f"  Properties merged: {total_stats['properties_merged']}")
        print(f"  Unique customers remaining: {total_customers - total_stats['records_merged']}")
        
        return {
            "total_customers": total_customers,
            **total_stats,
        }


def main():
    """Main entry point for the deduplication script."""
    # Initialize RushDB client
    url = os.getenv("RUSHDB_URL")
    db = RushDB(API_TOKEN, url=url) if url else RushDB(API_TOKEN)
    
    # Run deduplication
    deduplicator = GraphDeduplicator(db)
    stats = deduplicator.run()
    
    return stats


if __name__ == "__main__":
    main()
