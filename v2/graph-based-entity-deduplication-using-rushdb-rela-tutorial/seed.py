#!/usr/bin/env python3
"""
Seed script for graph-based entity deduplication tutorial.

This script creates realistic customer data with intentional duplicates
to demonstrate graph-based deduplication strategies.

The data model includes:
- CUSTOMER: The entities we're deduplicating
- ORDER: Transactions linked to customers
- CONTACT: People who interact with customers
- ADDRESS: Physical locations
- COMPANY: Business associations

Duplicates are created by:
1. Multiple customer records sharing the same underlying person
2. Same orders linked to different customer records
3. Shared contacts and addresses between potential duplicates
"""

import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from faker import Faker
from dotenv import load_dotenv

from rushdb import RushDB

# Initialize Faker for realistic data generation
fake = Faker()
Faker.seed(42)
random.seed(42)

# Configuration
DUPLICATE_RATE = 0.25  # 25% of customers will have duplicates
SHARED_ORDER_RATE = 0.3  # 30% of duplicates share orders

# Load environment
load_dotenv()
API_TOKEN = os.getenv("RUSHDB_API_TOKEN")

if not API_TOKEN:
    raise ValueError("RUSHDB_API_TOKEN not found in environment. Copy .env.example to .env")


def cleanup_existing_data(db: RushDB) -> None:
    """Remove any existing tutorial data to ensure idempotency."""
    print("Cleaning up existing data...")
    
    labels_to_delete = ["CUSTOMER", "ORDER", "CONTACT", "ADDRESS", "COMPANY"]
    
    for label in labels_to_delete:
        db.records.delete_many({"labels": [label], "where": {}})
    
    print("  Cleaned up all existing records.")


def generate_base_customers(count: int) -> List[Dict[str, Any]]:
    """Generate base customer data without RushDB IDs yet."""
    customers = []
    
    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        # Generate realistic contact info
        company = fake.company().lower().replace(" ", "").replace(".", "")
        email = f"{first_name.lower()}.{last_name.lower()}@{company}.com"
        
        # Phone with various formats
        phone = fake.phone_number()
        
        customers.append({
            "customer_id": f"CUST_{i:04d}",
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "company": fake.company(),
            "registered_at": fake.date_time_between(
                start_date="-2y", end_date="-1d"
            ).isoformat(),
            "is_verified": random.choice([True, False, False]),
        })
    
    return customers


def create_duplicate_variants(
    base_customers: List[Dict[str, Any]], db: RushDB
) -> tuple:
    """
    Create duplicate variants of some customers.
    Returns customer records and metadata about duplicate relationships.
    """
    customer_records = []
    duplicate_metadata = {
        "shared_orders": [],  # (canonical_id, duplicate_id, order_ids)
        "shared_contacts": [],  # (canonical_id, duplicate_id, contact_ids)
        "shared_addresses": [],  # (canonical_id, duplicate_id, address_ids)
    }
    
    num_duplicates = int(len(base_customers) * DUPLICATE_RATE)
    duplicate_indices = random.sample(range(len(base_customers)), num_duplicates)
    
    for idx in duplicate_indices:
        original = base_customers[idx]
        
        # Create the original customer
        original_record = db.records.create(
            label="CUSTOMER",
            data={
                **original,
                "is_canonical": True,
                "deduplication_source": "seed",
            }
        )
        customer_records.append(original_record)
        
        # Create 1-2 duplicates with variations
        num_variants = random.randint(1, 2)
        
        for v in range(num_variants):
            # Create variant with slight differences
            variant_data = {
                **original,
                "email": variant_email(original["email"], v),
                "phone": variant_phone(original["phone"], v),
                "first_name": variant_name(original["first_name"], v),
                "is_canonical": False,
                "deduplication_source": "seed",
                "deduplication_group": original["customer_id"],
            }
            
            variant_record = db.records.create(
                label="CUSTOMER",
                data=variant_data
            )
            customer_records.append(variant_record)
            
            # Track shared relationships for deduplication verification
            if random.random() < SHARED_ORDER_RATE:
                # Will link orders later
                duplicate_metadata["shared_orders"].append(
                    (original_record.id, variant_record.id)
                )
            
            if random.random() < 0.4:
                duplicate_metadata["shared_contacts"].append(
                    (original_record.id, variant_record.id)
                )
            
            if random.random() < 0.3:
                duplicate_metadata["shared_addresses"].append(
                    (original_record.id, variant_record.id)
                )
    
    # Create non-duplicate customers
    non_dup_indices = [i for i in range(len(base_customers)) if i not in duplicate_indices]
    for idx in non_dup_indices:
        customer_data = base_customers[idx]
        customer_record = db.records.create(
            label="CUSTOMER",
            data={
                **customer_data,
                "is_canonical": True,
                "deduplication_source": "seed",
            }
        )
        customer_records.append(customer_record)
    
    return customer_records, duplicate_metadata


def variant_email(original_email: str, variant_num: int) -> str:
    """Create email variants with subtle differences."""
    local, domain = original_email.split("@")
    
    variants = [
        local.replace(".", ""),  # Remove dots
        f"{local}+work",  # Add tag
        local.replace(".", "_"),  # Underscores instead
        f"{local}1",  # Trailing number
    ]
    
    return variants[variant_num % len(variants)] + "@" + domain


def variant_phone(original_phone: str, variant_num: int) -> str:
    """Create phone variants."""
    # Just return with slight formatting change
    digits = "".join(c for c in original_phone if c.isdigit())
    
    variants = [
        f"+1-{digits[-10:-7]}-{digits[-7:-4]}-{digits[-4:]}",  # US format
        f"({digits[-10:-7]}) {digits[-7:-4]}-{digits[-4:]}",  # Parens format
        f"1{digits[-10:]}",  # Country code
    ]
    
    return variants[variant_num % len(variants)]


def variant_name(original_name: str, variant_num: int) -> str:
    """Create name variants."""
    if variant_num == 0:
        return original_name  # Same name
    elif variant_num == 1:
        return original_name[:3] + "j" + original_name[4:]  # Typo
    else:
        return original_name  # Same again


def create_orders(customer_records: List, duplicate_metadata: Dict) -> List:
    """Create orders for customers, with some shared between duplicates."""
    print("Creating orders...")
    orders = []
    
    # Create 2-5 orders per customer
    for customer in customer_records:
        num_orders = random.randint(2, 5)
        
        for i in range(num_orders):
            order = db.records.create(
                label="ORDER",
                data={
                    "order_id": f"ORD_{fake.uuid4()[:8]}",
                    "amount": round(random.uniform(25.0, 500.0), 2),
                    "currency": random.choice(["USD", "EUR", "GBP"]),
                    "status": random.choice(["completed", "shipped", "processing"]),
                    "created_at": fake.date_time_between(
                        start_date="-1y", end_date="now"
                    ).isoformat(),
                }
            )
            orders.append(order)
            
            # Link order to customer
            db.records.attach(
                source=order,
                target=customer,
                options={"type": "PLACED_BY", "direction": "out"}
            )
    
    # Create shared orders for some duplicate pairs
    print("Creating shared orders between duplicates...")
    for canonical_id, duplicate_id in duplicate_metadata["shared_orders"]:
        # Create 1-3 orders that both customers "placed"
        num_shared = random.randint(1, 3)
        
        for _ in range(num_shared):
            shared_order = db.records.create(
                label="ORDER",
                data={
                    "order_id": f"ORD_SHARED_{fake.uuid4()[:8]}",
                    "amount": round(random.uniform(50.0, 300.0), 2),
                    "currency": "USD",
                    "status": "completed",
                    "created_at": fake.date_time_between(
                        start_date="-6m", end_date="-1d"
                    ).isoformat(),
                    "is_shared": True,
                }
            )
            orders.append(shared_order)
            
            # Link to BOTH customers (this is the key signal!)
            db.records.attach(
                source=shared_order,
                target=canonical_id,
                options={"type": "PLACED_BY", "direction": "out"}
            )
            db.records.attach(
                source=shared_order,
                target=duplicate_id,
                options={"type": "PLACED_BY", "direction": "out"}
            )
            
            print(f"  Created shared order {shared_order.id}")
    
    return orders


def create_contacts(customer_records: List, duplicate_metadata: Dict) -> List:
    """Create contact records that reference customers."""
    print("Creating contacts...")
    contacts = []
    
    # Create contacts that reference customers
    for customer in customer_records:
        num_contacts = random.randint(1, 3)
        
        for i in range(num_contacts):
            contact = db.records.create(
                label="CONTACT",
                data={
                    "name": fake.name(),
                    "role": random.choice(["account_manager", "support", "billing"]),
                    "email": fake.company_email(),
                }
            )
            contacts.append(contact)
            
            # Link contact to customer
            db.records.attach(
                source=customer,
                target=contact,
                options={"type": "HAS_CONTACT", "direction": "out"}
            )
    
    # Create shared contacts for some duplicate pairs
    print("Creating shared contacts between duplicates...")
    for canonical_id, duplicate_id in duplicate_metadata["shared_contacts"]:
        num_shared = random.randint(1, 2)
        
        for _ in range(num_shared):
            shared_contact = db.records.create(
                label="CONTACT",
                data={
                    "name": fake.name(),
                    "role": "shared_support",
                    "email": fake.company_email(),
                    "is_shared": True,
                }
            )
            contacts.append(shared_contact)
            
            # Link to BOTH customers
            db.records.attach(
                source=canonical_id,
                target=shared_contact,
                options={"type": "HAS_CONTACT", "direction": "out"}
            )
            db.records.attach(
                source=duplicate_id,
                target=shared_contact,
                options={"type": "HAS_CONTACT", "direction": "out"}
            )
            
            print(f"  Created shared contact {shared_contact.id}")
    
    return contacts


def create_addresses(customer_records: List, duplicate_metadata: Dict) -> List:
    """Create address records that reference customers."""
    print("Creating addresses...")
    addresses = []
    
    for customer in customer_records:
        num_addresses = random.randint(1, 2)
        
        for i in range(num_addresses):
            address = db.records.create(
                label="ADDRESS",
                data={
                    "street": fake.street_address(),
                    "city": fake.city(),
                    "state": fake.state_abbr(),
                    "zip_code": fake.zipcode(),
                    "country": "US",
                    "type": random.choice(["shipping", "billing", "both"]),
                }
            )
            addresses.append(address)
            
            db.records.attach(
                source=customer,
                target=address,
                options={"type": "LOCATED_AT", "direction": "out"}
            )
    
    # Create shared addresses
    print("Creating shared addresses between duplicates...")
    for canonical_id, duplicate_id in duplicate_metadata["shared_addresses"]:
        shared_address = db.records.create(
            label="ADDRESS",
            data={
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "zip_code": fake.zipcode(),
                "country": "US",
                "type": "both",
                "is_shared": True,
            }
        )
        addresses.append(shared_address)
        
        db.records.attach(
            source=canonical_id,
            target=shared_address,
            options={"type": "LOCATED_AT", "direction": "out"}
        )
        db.records.attach(
            source=duplicate_id,
            target=shared_address,
            options={"type": "LOCATED_AT", "direction": "out"}
        )
        
        print(f"  Created shared address {shared_address.id}")
    
    return addresses


def main():
    """Main seeding function."""
    print("=" * 60)
    print("Graph-based Entity Deduplication - Data Seeding")
    print("=" * 60)
    
    # Initialize RushDB client
    url = os.getenv("RUSHDB_URL")
    db = RushDB(API_TOKEN, url=url) if url else RushDB(API_TOKEN)
    
    # Check for existing data
    existing = db.records.find({"labels": ["CUSTOMER"], "where": {"deduplication_source": "seed"}})
    
    if existing.data:
        print(f"\nFound {len(existing.data)} existing customer records from previous run.")
        response = input("Clean up and reseed? (y/N): ")
        if response.lower() != 'y':
            print("Skipping seed. Run main.py to perform deduplication on existing data.")
            return
        
        cleanup_existing_data(db)
    
    print("\nGenerating customer base data...")
    num_base_customers = 25
    base_customers = generate_base_customers(num_base_customers)
    print(f"  Generated {len(base_customers)} base customer records")
    
    print("\nCreating customers with duplicates...")
    customer_records, duplicate_metadata = create_duplicate_variants(
        base_customers, db
    )
    print(f"  Created {len(customer_records)} customer records")
    print(f"  - {len(base_customers)} canonical customers")
    print(f"  - {len(customer_records) - len(base_customers)} duplicate variants")
    
    # Create related entities
    orders = create_orders(customer_records, duplicate_metadata)
    contacts = create_contacts(customer_records, duplicate_metadata)
    addresses = create_addresses(customer_records, duplicate_metadata)
    
    # Summary
    print("\n" + "=" * 60)
    print("Seeding Complete!")
    print("=" * 60)
    print(f"  CUSTOMER records: {len(customer_records)}")
    print(f"  ORDER records: {len(orders)}")
    print(f"  CONTACT records: {len(contacts)}")
    print(f"  ADDRESS records: {len(addresses)}")
    print(f"\nShared relationships created:")
    print(f"  - Shared orders: {len(duplicate_metadata['shared_orders'])}")
    print(f"  - Shared contacts: {len(duplicate_metadata['shared_contacts'])}")
    print(f"  - Shared addresses: {len(duplicate_metadata['shared_addresses'])}")
    print("\nRun `python main.py` to perform graph-based deduplication!")


if __name__ == "__main__":
    main()
