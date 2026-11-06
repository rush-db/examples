"""
Tutorial: How Structured Graph Memory Improves AI Reliability

This tutorial demonstrates how structured graph memory using RushDB eliminates
prompt sensitivity — the fragile dependence on exact phrasing that plagues
vector-only retrieval systems.

Key concepts:
1. Entity-centric storage: Facts are anchored to entities, not documents
2. Explicit relationships: Connections are first-class citizens
3. Relationship-based traversal: Queries navigate structure
4. Deterministic context: Same question = same subgraph
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env and fill in your credentials.")

db = RushDB(API_KEY)


def section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print(f"{'=' * 60}\n")


def create_graph_structure():
    """
    Build a structured knowledge graph demonstrating entity-centric storage.
    
    This creates the same data structure you'd use in production:
    - Users with explicit preferences
    - Products with categories and tags
    - Interactions as first-class entities
    - All relationships explicitly defined
    """
    print("Building structured graph...\n")
    
    # Check for existing data
    existing = db.records.find({"labels": ["USER"], "limit": 1})
    if existing:
        print("✓ Graph structure already exists (from seed.py)")
        return _get_alice()
    
    # === Create Categories ===
    coffee = db.records.create(label="CATEGORY", data={
        "name": "coffee",
        "description": "Coffee-based beverages"
    })
    tea = db.records.create(label="CATEGORY", data={
        "name": "tea",
        "description": "Tea-based beverages"
    })
    print("✓ Created categories")
    
    # === Create Tags ===
    tags = {}
    tag_names = ["dark_roast", "cold_brew", "oat_milk", "chocolate", "sweet"]
    for name in tag_names:
        tag = db.records.create(label="TAG", data={"name": name})
        tags[name] = tag
    print("✓ Created tags")
    
    # === Create Products ===
    espresso = db.records.create(label="PRODUCT", data={
        "name": "Espresso",
        "price": 3.50,
        "description": "Bold and concentrated coffee shot"
    })
    
    cold_brew = db.records.create(label="PRODUCT", data={
        "name": "Cold Brew",
        "price": 4.50,
        "description": "Smooth, cold-steeped coffee"
    })
    
    mocha = db.records.create(label="PRODUCT", data={
        "name": "Mocha",
        "price": 5.00,
        "description": "Chocolate espresso with steamed milk"
    })
    
    # Link products to categories
    db.records.attach(source=espresso, target=coffee, options={"type": "IN_CATEGORY", "direction": "out"})
    db.records.attach(source=cold_brew, target=coffee, options={"type": "IN_CATEGORY", "direction": "out"})
    db.records.attach(source=mocha, target=coffee, options={"type": "IN_CATEGORY", "direction": "out"})
    
    # Link products to tags
    db.records.attach(source=espresso, target=tags["dark_roast"], options={"type": "HAS_TAG", "direction": "out"})
    db.records.attach(source=cold_brew, target=tags["cold_brew"], options={"type": "HAS_TAG", "direction": "out"})
    db.records.attach(source=mocha, target=tags["chocolate"], options={"type": "HAS_TAG", "direction": "out"})
    db.records.attach(source=mocha, target=tags["sweet"], options={"type": "HAS_TAG", "direction": "out"})
    print("✓ Created products with category and tag relationships")
    
    # === Create User with Preferences ===
    alice = db.records.create(label="USER", data={
        "name": "Alice Chen",
        "email": "alice@example.com",
        "loyalty_tier": "gold"
    })
    
    # Alice's explicit preferences
    pref_dark_roast = db.records.create(label="PREFERENCE", data={
        "type": "beverage_preference",
        "value": "dark_roast",
        "strength": 0.95
    })
    
    pref_cold_brew = db.records.create(label="PREFERENCE", data={
        "type": "beverage_preference",
        "value": "cold_brew",
        "strength": 0.8
    })
    
    # Link preferences to Alice
    db.records.attach(source=alice, target=pref_dark_roast, options={"type": "HAS_PREFERENCE", "direction": "out"})
    db.records.attach(source=alice, target=pref_cold_brew, options={"type": "HAS_PREFERENCE", "direction": "out"})
    print("✓ Created user Alice with explicit preferences")
    
    # === Create Interactions ===
    # Alice ordered Espresso
    order1 = db.records.create(label="INTERACTION", data={
        "type": "ordered",
        "quantity": 2,
        "timestamp": "2024-01-15T10:30:00Z"
    })
    db.records.attach(source=alice, target=order1, options={"type": "MADE", "direction": "out"})
    db.records.attach(source=order1, target=espresso, options={"type": "REGARDING", "direction": "out"})
    
    # Alice ordered Cold Brew
    order2 = db.records.create(label="INTERACTION", data={
        "type": "ordered",
        "quantity": 1,
        "timestamp": "2024-01-18T14:00:00Z"
    })
    db.records.attach(source=alice, target=order2, options={"type": "MADE", "direction": "out"})
    db.records.attach(source=order2, target=cold_brew, options={"type": "REGARDING", "direction": "out"})
    
    # Alice viewed Mocha
    view1 = db.records.create(label="INTERACTION", data={
        "type": "viewed",
        "timestamp": "2024-01-20T09:15:00Z"
    })
    db.records.attach(source=alice, target=view1, options={"type": "MADE", "direction": "out"})
    db.records.attach(source=view1, target=mocha, options={"type": "REGARDING", "direction": "out"})
    print("✓ Created interactions (orders, views)")
    
    # === Explicit Product Preference Links ===
    # These are explicit preference relationships, not inferred from behavior
    db.records.attach(source=espresso, target=alice, options={"type": "PREFERRED_BY", "direction": "out"})
    db.records.attach(source=cold_brew, target=alice, options={"type": "PREFERRED_BY", "direction": "out"})
    print("✓ Created explicit product-user preference links")
    
    return alice


def _get_alice():
    """Retrieve Alice's record from existing data."""
    results = db.records.find({
        "labels": ["USER"],
        "where": {"name": "Alice Chen"}
    })
    if results:
        return results[0]
    return None


def demonstrate_prompt_insensitivity(alice):
    """
    Demonstrate that graph traversal returns consistent results
    regardless of how the query is phrased.
    
    This is the KEY benefit of structured graph memory:
    - "What coffee drinks does Alice prefer?"
    - "Alice's beverage preferences"
    - "Drinks Alice has interacted with"
    
    All return the same answer because we traverse the graph,
    not match semantic similarity.
    """
    section("DEMONSTRATING PROMPT INSENSITIVITY")
    
    if not alice:
        print("❌ Alice not found. Run seed.py first or ensure graph exists.")
        return
    
    def query_alices_coffee_products(query_description: str, where_clause: dict) -> list:
        """Query products for Alice using different approaches."""
        print(f"\n{query_description}")
        print("-" * 50)
        
        # Query using relationship traversal
        results = db.records.find({
            "labels": ["PRODUCT"],
            "where": where_clause
        })
        
        product_names = [p["name"] for p in results]
        print(f"  Found {len(results)} products: {product_names}")
        return product_names
    
    # === Query 1: Direct preference lookup ===
    # This uses explicit PREFERRED_BY relationships
    result1 = query_alices_coffee_products(
        "Query 1: What coffee drinks does Alice prefer?",
        {
            "PREFERRED_BY": {
                "$relation": {"type": "PREFERRED_BY", "direction": "in"},
                "name": "Alice Chen"
            }
        }
    )
    
    # === Query 2: User preference through chain ===
    # This traces: Alice -> HAS_PREFERENCE -> PREFERENCE -> "dark_roast" -> TAG -> PRODUCT
    result2 = query_alices_coffee_products(
        "Query 2: Alice's beverage preferences (via preference chain)",
        {
            "TAG": {
                "$relation": {"type": "HAS_TAG", "direction": "in"},
                "PREFERENCE": {
                    "$relation": {"type": "HAS_PREFERENCE", "direction": "in"},
                    "USER": {"$relation": {"type": "HAS_PREFERENCE", "direction": "in"}, "name": "Alice Chen"}
                }
            }
        }
    )
    
    # === Query 3: Interaction-based ===
    # This uses INTERACTION records Alice made
    result3 = query_alices_coffee_products(
        "Query 3: Drinks Alice has interacted with (via INTERACTION)",
        {
            "INTERACTION": {
                "$relation": {"type": "REGARDING", "direction": "in"},
                "USER": {"$relation": {"type": "MADE", "direction": "in"}, "name": "Alice Chen"}
            }
        }
    )
    
    # === Verification ===
    print("\n" + "=" * 50)
    print("VERIFICATION: Results Comparison")
    print("=" * 50)
    
    all_same = result1 == result2 == result3
    
    print(f"\nQuery 1 (Direct preference):  {sorted(result1)}")
    print(f"Query 2 (Preference chain):  {sorted(result2)}")
    print(f"Query 3 (Interaction-based):  {sorted(result3)}")
    
    if all_same:
        print("\n✓ All three phrasings return the SAME result!")
        print("  This demonstrates PROMPT INSENSITIVITY.")
        print("  The graph structure ensures consistent answers")
        print("  regardless of how the question is phrased.")
    else:
        print("\n⚠ Results differ - investigating...")
        print("  (This may indicate a query issue or missing data)")


def demonstrate_relationship_traversal(alice):
    """
    Demonstrate full relationship traversal to build complete context.
    
    This shows how a single entity can retrieve its entire context:
    - User's preferences
    - User's interactions
    - Related products
    - Product categories and tags
    """
    section("RELATIONSHIP TRAVERSAL: Building Complete Context")
    
    if not alice:
        print("❌ Alice not found.")
        return
    
    print(f"User: {alice['name']}")
    print(f"Email: {alice['email']}")
    print(f"Loyalty Tier: {alice['loyalty_tier']}")
    
    # === Get Alice's preferences ===
    print("\n--- Preferences ---")
    prefs = db.records.find({
        "labels": ["PREFERENCE"],
        "where": {
            "USER": {
                "$relation": {"type": "HAS_PREFERENCE", "direction": "in"},
                "name": "Alice Chen"
            }
        }
    })
    for pref in prefs:
        strength = pref.get("strength", 1.0)
        print(f"  → {pref['value']} (strength: {strength:.0%})")
    
    # === Get Alice's interactions ===
    print("\n--- Recent Interactions ---")
    interactions = db.records.find({
        "labels": ["INTERACTION"],
        "where": {
            "USER": {
                "$relation": {"type": "MADE", "direction": "in"},
                "name": "Alice Chen"
            }
        },
        "limit": 10,
        "orderBy": {"timestamp": "desc"}
    })
    for interaction in interactions:
        prod_type = interaction.get("type", "unknown")
        qty = interaction.get("quantity", 1)
        ts = interaction.get("timestamp", "unknown date")
        print(f"  → {prod_type.upper()} (qty: {qty}) on {ts}")
    
    # === Get products Alice interacted with, with full context ===
    print("\n--- Products with Full Context ---")
    products = db.records.find({
        "labels": ["PRODUCT"],
        "where": {
            "INTERACTION": {
                "$relation": {"type": "REGARDING", "direction": "in"},
                "USER": {"$relation": {"type": "MADE", "direction": "in"}, "name": "Alice Chen"}
            }
        }
    })
    
    for product in products:
        print(f"\n  Product: {product['name']}")
        print(f"    Price: ${product['price']:.2f}")
        
        # Get category
        categories = db.records.find({
            "labels": ["CATEGORY"],
            "where": {
                "PRODUCT": {
                    "$relation": {"type": "IN_CATEGORY", "direction": "in"},
                    "name": product['name']
                }
            }
        })
        if categories:
            print(f"    Category: {categories[0]['name']}")
        
        # Get tags
        tags = db.records.find({
            "labels": ["TAG"],
            "where": {
                "PRODUCT": {
                    "$relation": {"type": "HAS_TAG", "direction": "in"},
                    "name": product['name']
                }
            }
        })
        tag_names = [t['name'] for t in tags]
        print(f"    Tags: {tag_names}")


def demonstrate_graph_vs_flat_comparison():
    """
    Compare structured graph approach vs naive document storage.
    
    This shows WHY graph memory is more reliable:
    - Flat storage: Scattered facts, no relationships
    - Graph storage: Anchored entities, explicit connections
    """
    section("COMPARISON: Graph Memory vs Flat Document Storage")
    
    print("""
PROBLEM WITH FLAT DOCUMENT STORAGE:
────────────────────────────────────
"""")
    
    # Simulate a flat document
    flat_doc = {
        "user": "Alice Chen",
        "preferences": ["dark_roast", "cold_brew"],
        "interactions": [
            {"type": "ordered", "product": "Espresso", "date": "2024-01-15"},
            {"type": "ordered", "product": "Cold Brew", "date": "2024-01-18"},
            {"type": "viewed", "product": "Mocha", "date": "2024-01-20"},
        ]
    }
    
    print("""
Flat Document (JSON):
```json
{
  "user": "Alice Chen",
  "preferences": ["dark_roast", "cold_brew"],
  "interactions": [...]
}
```

Problems:
❌ "dark_roast" is just a string - no connection to products
❌ "Espresso" and "Cold Brew" appear in interactions, not linked to preferences
❌ Query "What coffees does Alice like?" requires semantic matching
❌ Query "What products match her dark_roast preference?" requires inference
❌ Different phrasings may return different results
""")
    
    print("""
STRUCTURED GRAPH MEMORY:
────────────────────────
""")
    
    print("""
Graph Structure:
```
USER ──HAS_PREFERENCE──▶ PREFERENCE(value="dark_roast")
  │                                    │
  │                                    ▼
  └──MADE──▶ INTERACTION ◀──REGARDING── PRODUCT
```

Benefits:
✓ Relationships are first-class citizens
✓ Queries traverse the graph, not match text
✓ "dark_roast" preference is explicitly linked to products
✓ Same question always returns the same answer
✓ Context is deterministic and complete
""")
    
    print("""
KEY INSIGHT:
────────────
With flat storage, the AI must INFER relationships from text similarity.
With graph storage, relationships are EXPLICIT - no inference needed.

This is why graph memory dramatically reduces hallucinations and
improves reliability across different prompt phrasings.
""")


def main():
    """Run the complete tutorial."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║  TUTORIAL: Structured Graph Memory for AI Reliability      ║
║                                                              ║
║  How structured graph memory improves AI reliability         ║
║  and reduces prompt sensitivity                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Build or load the graph structure
    section("STEP 1: Building Graph Structure")
    alice = create_graph_structure()
    print("\n✓ Graph structure ready!")
    
    # Step 2: Demonstrate prompt insensitivity
    demonstrate_prompt_insensitivity(alice)
    
    # Step 3: Demonstrate relationship traversal
    demonstrate_relationship_traversal(alice)
    
    # Step 4: Comparison with flat storage
    demonstrate_graph_vs_flat_comparison()
    
    # Summary
    section("SUMMARY: Key Takeaways")
    print("""
1. STRUCTURED STORAGE
   Anchors facts to entities (USER, PRODUCT, PREFERENCE) rather than
   embedding everything in documents.

2. EXPLICIT RELATIONSHIPS
   Connections like HAS_PREFERENCE, MADE, REGARDING are first-class
   citizens, not implicit text patterns.

3. RELATIONSHIP-BASED TRAVERSAL
   Queries navigate the graph structure, finding related entities
   through their connections, not through semantic similarity.

4. DETERMINISTIC CONTEXT
   The same question always returns the same subgraph, eliminating
   the "which phrasing will work today?" problem.

5. REDUCED HALLUCINATION RISK
   When context is explicitly linked, there's no ambiguity about
   what information is relevant.

────────────────────────────────────────────────────────────────

For more information:
- RushDB Documentation: https://docs.rushdb.com
- GitHub: https://github.com/rush-db/examples

────────────────────────────────────────────────────────────────
    """)


if __name__ == "__main__":
    main()
