"""
Tutorial: Building Hierarchical Memory Structures with Parent-Child Relationships

This script demonstrates how to use RushDB to model, create, and query
hierarchical data structures like organizational charts, file systems,
product taxonomies, and comments threads.

For senior engineers looking to understand graph-based memory patterns.
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

db = RushDB(API_KEY)


def example_1_build_category_tree():
    """
    Example 1: Building a Category Tree
    
    Demonstrates creating parent-child relationships between records.
    We build a simple hierarchy: Electronics > Computers > Laptops/Smartphones
    """
    print("\n--- Example 1: Building a Category Tree ---")
    
    # Create top-level categories
    electronics = db.records.create(
        label="CATEGORY",
        data={"name": "Electronics", "description": "Electronic devices"}
    )
    print(f"Created category: {electronics['name']}")
    
    computers = db.records.create(
        label="CATEGORY",
        data={"name": "Computers", "description": "Computing devices"}
    )
    print(f"Created category: {computers['name']}")
    
    laptops = db.records.create(
        label="CATEGORY",
        data={"name": "Laptops", "description": "Portable computers"}
    )
    print(f"Created category: {laptops['name']}")
    
    smartphones = db.records.create(
        label="CATEGORY",
        data={"name": "Smartphones", "description": "Mobile phones"}
    )
    print(f"Created category: {smartphones['name']}")
    
    # Create parent-child links using attach()
    # The direction is FROM parent TO child
    db.records.attach(
        source=electronics,
        target=computers,
        options={"type": "PARENT_OF"}
    )
    print(f"Linked Computers → Electronics (PARENT_OF)")
    
    db.records.attach(
        source=computers,
        target=laptops,
        options={"type": "PARENT_OF"}
    )
    print(f"Linked Laptops → Computers (PARENT_OF)")
    
    db.records.attach(
        source=computers,
        target=smartphones,
        options={"type": "PARENT_OF"}
    )
    print(f"Linked Smartphones → Computers (PARENT_OF)")
    
    return {
        "electronics": electronics,
        "computers": computers,
        "laptops": laptops,
        "smartphones": smartphones,
    }


def example_2_query_related_records(categories):
    """
    Example 2: Querying Related Records
    
    Demonstrates how to query records based on their relationships.
    This is the key to traversing hierarchical structures.
    """
    print("\n--- Example 2: Querying Related Records ---")
    
    # 2a. Find direct children of a category
    # direction: "in" means we're looking for records that POINT TO our filter target
    print("\nFinding Laptops under Computers...")
    children = db.records.find({
        "labels": ["CATEGORY"],
        "where": {
            "CATEGORY": {
                "$relation": {"type": "PARENT_OF", "direction": "in"},
                "name": "Computers"
            }
        }
    })
    child_names = [c["name"] for c in children]
    print(f"Found {len(children)} categories under Computers: {', '.join(child_names)}")
    
    # 2b. Recursive query: find all descendants of a top-level category
    # We need to traverse multiple levels
    print("\nFinding all descendants of Electronics...")
    
    # Level 1: Get direct children
    level_1 = db.records.find({
        "labels": ["CATEGORY"],
        "where": {
            "CATEGORY": {
                "$relation": {"type": "PARENT_OF", "direction": "in"},
                "name": "Electronics"
            }
        }
    })
    
    all_descendants = []
    for level_1_cat in level_1:
        all_descendants.append(level_1_cat["name"])
        
        # Level 2: Get children of each level-1 category
        level_2 = db.records.find({
            "labels": ["CATEGORY"],
            "where": {
                "CATEGORY": {
                    "$relation": {"type": "PARENT_OF", "direction": "in"},
                    "name": level_1_cat["name"]
                }
            }
        })
        for level_2_cat in level_2:
            all_descendants.append(level_2_cat["name"])
    
    print(f"Descendants of Electronics: {', '.join(all_descendants)}")
    
    # 2c. Reverse traversal: find the parent of a category
    # direction: "out" means we're looking for records our target POINTS TO
    print("\nFinding category hierarchy by reverse traversal...")
    
    laptops = categories["laptops"]
    
    # Find parent
    parents = db.records.find({
        "labels": ["CATEGORY"],
        "where": {
            "CATEGORY": {
                "$relation": {"type": "PARENT_OF", "direction": "out"},
                "name": laptops["name"]
            }
        }
    })
    if parents:
        print(f"Parent of {laptops['name']}: {parents[0]['name']}")
    
    # Find grandparent
    if parents:
        grandparents = db.records.find({
            "labels": ["CATEGORY"],
            "where": {
                "CATEGORY": {
                    "$relation": {"type": "PARENT_OF", "direction": "out"},
                    "name": parents[0]["name"]
                }
            }
        })
        if grandparents:
            print(f"Grandparent of {laptops['name']}: {grandparents[0]['name']}")


def example_3_attach_leaf_records(categories):
    """
    Example 3: Attaching Leaf Records
    
    Demonstrates how to attach data records (products, employees, files)
    to their containing category in the hierarchy.
    """
    print("\n--- Example 3: Attaching Leaf Records ---")
    
    # Create sample products
    products = [
        {"name": "ProBook 15", "price": 1299.99, "brand": "TechCorp"},
        {"name": "UltraSlim 13", "price": 1599.99, "brand": "SlimTech"},
        {"name": "GamerPro X", "price": 1899.99, "brand": "GameGear"},
        {"name": "Business Elite", "price": 1499.99, "brand": "TechCorp"},
        {"name": "StudentMate", "price": 699.99, "brand": "EduDevices"},
    ]
    
    laptops_category = categories["laptops"]
    
    for product_data in products:
        product = db.records.create(label="PRODUCT", data=product_data)
        
        # Attach product to its category
        db.records.attach(
            source=product,
            target=laptops_category,
            options={"type": "BELONGS_TO"}
        )
        print(f"Attached product: {product['name']} → {laptops_category['name']}")
    
    # Query products in a category
    print("\nFinding products in Laptops category...")
    products_in_laptops = db.records.find({
        "labels": ["PRODUCT"],
        "where": {
            "CATEGORY": {
                "$relation": {"type": "BELONGS_TO", "direction": "in"},
                "name": "Laptops"
            }
        }
    })
    print(f"Found {len(products_in_laptops)} products in Laptops category")
    
    return products_in_laptops


def example_4_batch_transactions():
    """
    Example 4: Batch Operations with Transactions
    
    Demonstrates using transactions to batch multiple operations.
    All operations either succeed together or rollback together.
    """
    print("\n--- Example 4: Batch Operations with Transactions ---")
    
    # Using context manager for automatic commit/rollback
    with db.transactions.begin() as tx:
        # Create multiple records in a batch
        category = db.records.create(
            label="CATEGORY",
            data={"name": "Gaming", "description": "Gaming products"},
            transaction=tx
        )
        
        products = [
            {"name": "Gaming Chair Pro", "price": 449.99},
            {"name": "RGB Keyboard", "price": 159.99},
            {"name": "4K Gaming Monitor", "price": 799.99},
        ]
        
        created_products = []
        for product_data in products:
            product = db.records.create(
                label="PRODUCT",
                data=product_data,
                transaction=tx
            )
            created_products.append(product)
            
            # Attach within transaction
            db.records.attach(
                source=product,
                target=category,
                options={"type": "BELONGS_TO"},
                transaction=tx
            )
        
        print(f"Created category: {category['name']}")
        print(f"Created {len(created_products)} products in batch")
        
        # Context manager auto-commits on successful exit
        # No need to call tx.commit() explicitly


def example_5_deep_traversal():
    """
    Example 5: Deep Traversal (Multi-level)
    
    Demonstrates traversing a multi-level hierarchy to find all
    products under a top-level category.
    """
    print("\n--- Example 5: Deep Traversal (Multi-level) ---")
    
    def get_all_descendants(category_name, visited=None):
        """Recursively get all descendant categories."""
        if visited is None:
            visited = []
        
        if category_name in visited:
            return visited
            
        children = db.records.find({
            "labels": ["CATEGORY"],
            "where": {
                "CATEGORY": {
                    "$relation": {"type": "PARENT_OF", "direction": "in"},
                    "name": category_name
                }
            }
        })
        
        for child in children:
            visited.append(child["name"])
            get_all_descendants(child["name"], visited)
        
        return visited
    
    def count_products_in_category(category_name):
        """Count products directly in a category."""
        results = db.records.find({
            "labels": ["PRODUCT"],
            "where": {
                "CATEGORY": {
                    "$relation": {"type": "BELONGS_TO", "direction": "in"},
                    "name": category_name
                }
            }
        })
        return len(results)
    
    # Get all descendants of Electronics
    descendants = get_all_descendants("Electronics")
    print(f"All categories under Electronics: {descendants}")
    
    # Find products under each descendant category
    print("\nProducts under Electronics (2 levels deep):")
    
    # Direct children of Electronics
    direct_children = db.records.find({
        "labels": ["CATEGORY"],
        "where": {
            "CATEGORY": {
                "$relation": {"type": "PARENT_OF", "direction": "in"},
                "name": "Electronics"
            }
        }
    })
    
    for child in direct_children:
        print(f"  - {child['name']}")
        
        # Grandchildren of Electronics (products at this level)
        grandchildren = db.records.find({
            "labels": ["CATEGORY"],
            "where": {
                "CATEGORY": {
                    "$relation": {"type": "PARENT_OF", "direction": "in"},
                    "name": child["name"]
                }
            }
        })
        
        for grandchild in grandchildren:
            product_count = count_products_in_category(grandchild["name"])
            print(f"    - {grandchild['name']} (with {product_count} products)")


def cleanup_demo_data():
    """Remove the demo records we created."""
    print("\n--- Cleanup ---")
    
    # Delete demo categories and products
    db.records.delete_many({"labels": ["CATEGORY"], "where": {}})
    db.records.delete_many({"labels": ["PRODUCT"], "where": {}})
    
    print("Cleaned up demo records")


def main():
    """Run all tutorial examples."""
    print("=== Hierarchical Memory Structures with RushDB ===")
    
    # Example 1: Build the hierarchy
    categories = example_1_build_category_tree()
    
    # Example 2: Query relationships
    example_2_query_related_records(categories)
    
    # Example 3: Attach leaf records
    example_3_attach_leaf_records(categories)
    
    # Example 4: Batch operations
    example_4_batch_transactions()
    
    # Example 5: Deep traversal
    example_5_deep_traversal()
    
    # Optional cleanup
    # Uncomment to remove all created records:
    # cleanup_demo_data()
    
    print("\n=== Tutorial Complete ===")
    print("\nKey Takeaways:")
    print("  1. Use db.records.attach() to create parent-child links")
    print("  2. Query with $relation.direction: 'in' for children, 'out' for parents")
    print("  3. Chain queries for multi-level traversal")
    print("  4. Use transactions for atomic batch operations")


if __name__ == "__main__":
    main()
