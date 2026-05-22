"""
Tutorial: How to Model Entity Relationships for Cross-Document Reference in RushDB

This script demonstrates RushDB's property graph capabilities for modeling
cross-document relationships — a common pattern in content management, 
knowledge bases, and collaborative platforms.

Key patterns covered:
1. Querying records by related entity properties
2. Filtering across relationship types
3. Cross-document reference traversal
4. Transactional consistency for complex operations
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Initialize RushDB client
load_dotenv()
TOKEN = os.getenv("RUSHDB_TOKEN")
if not TOKEN:
    raise ValueError("RUSHDB_TOKEN not found in environment. Copy .env.example to .env")

db = RushDB(TOKEN)


def print_section(title):
    """Format output with section headers."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_basic_relationship_creation():
    """Demonstrate creating entities and their relationships."""
    print_section("1. BASIC ENTITY & RELATIONSHIP CREATION")
    
    # Create two entities
    author = db.records.create(
        label="AUTHOR",
        data={"name": "Frank Miller", "email": "frank@example.com", "expertise": "writing"}
    )
    
    article = db.records.create(
        label="ARTICLE",
        data={"title": "Getting Started with RushDB", "status": "published"}
    )
    
    # Create a relationship using attach()
    # direction="out" means: author -> article
    db.records.attach(
        source=author,
        target=article,
        options={"type": "WRITTEN_BY", "direction": "out"}
    )
    
    print(f"\nCreated Author: {author['name']} (id: {author.id})")
    print(f"Created Article: '{article['title']}' (id: {article.id})")
    print(f"Linked them with relationship type: WRITTEN_BY")
    
    return author, article


def demo_query_by_related_property():
    """Demonstrate querying records by properties of related entities.
    
    This is a powerful pattern: find all ARTICLES where the related AUTHOR
    has a specific email address. No JOINs needed — the graph handles it.
    """
    print_section("2. QUERY BY RELATED ENTITY PROPERTY")
    
    print("\nFinding all articles written by 'alice@techcorp.io'...")
    
    # Use the label of the related record as the key in "where"
    # The $relation operator specifies relationship type and direction
    articles = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "AUTHOR": {
                "$relation": {"type": "WRITTEN_BY", "direction": "in"},
                "email": "alice@techcorp.io"
            }
        }
    })
    
    print(f"\nFound {len(articles.data)} article(s) by Alice Chen:")
    for article in articles.data:
        print(f"  - '{article['title']}' (status: {article['status']})")
    
    # Alternative: simpler query without specifying relationship type
    # RushDB infers the relationship from the label filter
    print("\n--- Alternative: Implicit relationship filter ---")
    print("Finding all articles by authors with 'techcorp.io' domain...")
    
    articles_by_techcorp = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "AUTHOR": {
                "email": {"$contains": "techcorp.io"}
            }
        },
        "limit": 10
    })
    
    print(f"Found {len(articles_by_techcorp.data)} article(s)")
    for article in articles_by_techcorp.data:
        print(f"  - '{article['title']}'")


def demo_filter_by_tag():
    """Query articles that have specific tags."""
    print_section("3. FILTERING BY TAG RELATIONSHIPS")
    
    print("\nFinding all 'python' related articles...")
    
    python_articles = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "TAG": {
                "$relation": {"type": "TAGGED_WITH", "direction": "in"},
                "name": "python"
            }
        }
    })
    
    print(f"\nFound {len(python_articles.data)} Python-related article(s):")
    for article in python_articles.data:
        print(f"  - '{article['title']}'")
    
    # Find articles with multiple specific tags
    print("\n--- Finding articles tagged with both 'async' AND 'python' ---")
    
    async_python_articles = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "TAG": {
                "name": {"$in": ["async", "python"]}
            }
        },
        "limit": 20
    })
    
    # Deduplicate since articles can match multiple tags
    seen_titles = set()
    for article in async_python_articles.data:
        if article['title'] not in seen_titles:
            seen_titles.add(article['title'])
            print(f"  - '{article['title']}'")


def demo_cross_document_references():
    """Query articles that reference other articles."""
    print_section("4. CROSS-DOCUMENT REFERENCE TRAVERSAL")
    
    print("\nFinding articles that reference other articles...")
    
    # Find articles with outgoing REFERENCES relationships
    articles_with_refs = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "ARTICLE": {
                "$relation": {"type": "REFERENCES", "direction": "out"}
            }
        },
        "limit": 10
    })
    
    print(f"\nFound {len(articles_with_refs.data)} article(s) with cross-references:")
    for article in articles_with_refs.data:
        print(f"  - '{article['title']}'")
    
    # For each article, we can find what it references
    print("\n--- Detailed reference links ---")
    for article in articles_with_refs.data[:3]:
        # Query the target articles (incoming from this article)
        refs = db.records.find({
            "labels": ["ARTICLE"],
            "where": {
                "ARTICLE": {
                    "$relation": {"type": "REFERENCES", "direction": "in", "sourceId": article.id}
                }
            }
        })
        if refs.data:
            ref_titles = [r['title'] for r in refs.data]
            print(f"  '{article['title']}' references: {ref_titles}")


def demo_query_by_category():
    """Find articles in specific categories."""
    print_section("5. FILTERING BY CATEGORY")
    
    print("\nFinding articles in the 'Architecture' category...")
    
    arch_articles = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "CATEGORY": {
                "$relation": {"type": "BELONGS_TO", "direction": "in"},
                "name": "Architecture"
            }
        }
    })
    
    print(f"\nFound {len(arch_articles.data)} Architecture article(s):")
    for article in arch_articles.data:
        print(f"  - '{article['title']}'")


def demo_author_statistics():
    """Calculate statistics across the relationship graph."""
    print_section("6. RELATIONSHIP STATISTICS")
    
    print("\nCalculating article counts per author...")
    
    authors = db.records.find({"labels": ["AUTHOR"], "limit": 10})
    
    stats = []
    for author in authors.data:
        # Count articles by this author
        article_count = len(db.records.find({
            "labels": ["ARTICLE"],
            "where": {
                "AUTHOR": {
                    "$relation": {"type": "WRITTEN_BY", "direction": "in"},
                    "email": author['email']
                }
            }
        }).data)
        stats.append((author['name'], article_count))
    
    # Sort by article count descending
    stats.sort(key=lambda x: x[1], reverse=True)
    
    print("\nAuthor productivity ranking:")
    for i, (name, count) in enumerate(stats, 1):
        print(f"  {i}. {name}: {count} article(s)")


def demo_transactional_consistency():
    """Demonstrate transactional operations for complex graph updates."""
    print_section("7. TRANSACTIONAL CONSISTENCY")
    
    print("\nCreating a complete document with relationships in a transaction...")
    
    # Using context manager for automatic commit/rollback
    with db.transactions.begin() as tx:
        # Create a new author
        new_author = db.records.create(
            label="AUTHOR",
            data={"name": "Grace Hopper", "email": "grace@tutorial.dev", "expertise": "compilers"},
            transaction=tx
        )
        
        # Create multiple articles
        article1 = db.records.create(
            label="ARTICLE",
            data={"title": "Introduction to Compilers", "status": "draft", "read_time": 25},
            transaction=tx
        )
        
        article2 = db.records.create(
            label="ARTICLE",
            data={"title": "Advanced Parsing Techniques", "status": "draft", "read_time": 30},
            transaction=tx
        )
        
        # Link author to both articles
        db.records.attach(source=new_author, target=article1, options={"type": "WRITTEN_BY"}, transaction=tx)
        db.records.attach(source=new_author, target=article2, options={"type": "WRITTEN_BY"}, transaction=tx)
        
        # Create a cross-reference between articles
        db.records.attach(source=article1, target=article2, options={"type": "REFERENCES"}, transaction=tx)
        
        # Create a tag
        compiler_tag = db.records.create(label="TAG", data={"name": "compilers", "category": "concept"}, transaction=tx)
        
        # Tag both articles
        db.records.attach(source=article1, target=compiler_tag, options={"type": "TAGGED_WITH"}, transaction=tx)
        db.records.attach(source=article2, target=compiler_tag, options={"type": "TAGGED_WITH"}, transaction=tx)
        
        # Transaction auto-commits on successful exit
        print(f"\nTransaction committed successfully!")
        print(f"  Created author: {new_author['name']}")
        print(f"  Created 2 articles linked to author")
        print(f"  Created cross-reference between articles")
        print(f"  Created and applied tag: '{compiler_tag['name']}'")


def demo_upsert_with_relationships():
    """Demonstrate upsert pattern for updating entities with relationships."""
    print_section("8. UPSERT WITH RELATIONSHIPS")
    
    print("\nUpserting an author and maintaining relationships...")
    
    # Upsert will update if exists, create if not
    author = db.records.upsert(
        label="AUTHOR",
        data={"email": "alice@techcorp.io", "name": "Alice Chen Updated", "expertise": "python"},
        options={"mergeBy": ["email"]}
    )
    
    print(f"\nUpserted author: {author['name']}")
    print(f"  Email: {author['email']}")
    print(f"  Expertise: {author['expertise']}")
    print(f"  Record ID: {author.id}")
    print("\nNote: mergeBy ensures we update Alice's record, not create a duplicate.")


def demo_comprehensive_query():
    """Show a complex query combining multiple relationship filters."""
    print_section("9. COMPLEX MULTI-RELATIONSHIP QUERY")
    
    print("\nFinding published articles that:")
    print("  - Are written by authors with 5+ years experience")
    print("  - Belong to 'Development' category")
    print("  - Are tagged with 'performance'")
    
    complex_results = db.records.find({
        "labels": ["ARTICLE"],
        "where": {
            "status": "published",
            "AUTHOR": {
                "$relation": {"type": "WRITTEN_BY", "direction": "in"},
                "years_exp": {"$gte": 5}
            },
            "CATEGORY": {
                "$relation": {"type": "BELONGS_TO", "direction": "in"},
                "name": "Development"
            },
            "TAG": {
                "$relation": {"type": "TAGGED_WITH", "direction": "in"},
                "name": "performance"
            }
        },
        "limit": 20
    })
    
    print(f"\nFound {len(complex_results.data)} matching article(s):")
    for article in complex_results.data:
        print(f"  - '{article['title']}'")


def show_entity_counts():
    """Display current entity counts by label."""
    print_section("ENTITY COUNTS IN DATABASE")
    
    labels = db.labels.find({})
    
    print("\nRecords by label:")
    for label_result in labels.data:
        print(f"  {label_result.name}: {label_result.count}")


def main():
    """Run the complete tutorial."""
    print("\n" + "=" * 70)
    print("  RUSHDB TUTORIAL: Entity Relationships for Cross-Document Reference")
    print("=" * 70)
    
    # Show current state
    show_entity_counts()
    
    # Run all demonstrations
    demo_basic_relationship_creation()
    demo_query_by_related_property()
    demo_filter_by_tag()
    demo_cross_document_references()
    demo_query_by_category()
    demo_author_statistics()
    demo_transactional_consistency()
    demo_upsert_with_relationships()
    demo_comprehensive_query()
    
    # Final state
    show_entity_counts()
    
    print("\n" + "=" * 70)
    print("  Tutorial Complete!")
    print("=" * 70)
    print("\nKey takeaways:")
    print("  1. Use labels to define entity types (AUTHOR, ARTICLE, TAG, etc.)")
    print("  2. Use attach() to create directed relationships between records")
    print("  3. Query by related properties using the related entity's label")
    print("  4. Use $relation to specify relationship type and direction")
    print("  5. Wrap complex operations in transactions for consistency")
    print("  6. Upsert with mergeBy for idempotent entity updates")
    print("\nLearn more: https://docs.rushdb.com")


if __name__ == "__main__":
    main()
