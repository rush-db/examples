"""
Seed script for the Chunk-Level vs Document-Level Linking tutorial.
Generates a realistic knowledge base with articles, sections, and paragraphs.
Idempotent: checks for existing data before seeding.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
url = os.getenv("RUSHDB_URL")
db = RushDB(api_key, url=url) if url else RushDB(api_key)

# Sample data for realistic knowledge base
ARTICLES = [
    {
        "slug": "intro-to-rushdb",
        "title": "Introduction to RushDB",
        "author": "Alice Chen",
        "category": "Getting Started",
        "sections": [
            {
                "title": "What is RushDB?",
                "paragraphs": [
                    "RushDB is a full-cycle memory layer for AI applications, combining property graph storage with vector search capabilities.",
                    "Unlike traditional databases, RushDB provides a zero-schema API that adapts to your data model.",
                    "It sits between your application and Neo4j, handling the complexity of graph traversal and indexing.",
                ]
            },
            {
                "title": "Core Concepts",
                "paragraphs": [
                    "Records are the fundamental unit — typed key-value objects stored as Neo4j nodes.",
                    "Labels define record types, similar to table names but more flexible.",
                    "Relationships are first-class citizens, enabling rich graph traversal.",
                    "Properties form a shared vocabulary layer across all labels.",
                ]
            },
            {
                "title": "Getting Started",
                "paragraphs": [
                    "Install the Python SDK: pip install rushdb>=2.0.0",
                    "Create a record: db.records.create(label='USER', data={'name': 'Alice'})",
                    "Query with find: db.records.find({'labels': ['USER'], 'where': {'name': 'Alice'}})",
                    "Attach relationships: db.records.attach(source=user, target=article, options={'type': 'AUTHORED'})",
                ]
            }
        ]
    },
    {
        "slug": "graph-data-modeling",
        "title": "Graph Data Modeling Patterns",
        "author": "Bob Martinez",
        "category": "Architecture",
        "sections": [
            {
                "title": "Document-Level Modeling",
                "paragraphs": [
                    "Document-level linking treats entire records as atomic units.",
                    "Use cases: hierarchical categories, organizational structures, navigation trees.",
                    "Benefits: simpler queries, faster bulk operations, clear ownership boundaries.",
                    "Trade-offs: less flexible granular access, larger result sets for detailed queries.",
                ]
            },
            {
                "title": "Chunk-Level Modeling",
                "paragraphs": [
                    "Chunk-level linking breaks content into granular segments.",
                    "Use cases: RAG pipelines, fine-grained retrieval, content similarity search.",
                    "Benefits: precise retrieval, better relevance, support for semantic search.",
                    "Trade-offs: more relationships to manage, complex traversal patterns.",
                ]
            },
            {
                "title": "Choosing Your Strategy",
                "paragraphs": [
                    "Start with document-level for navigation-heavy applications.",
                    "Add chunk-level when you need granular retrieval or RAG capabilities.",
                    "Consider hybrid: document links for structure, chunk links for content.",
                    "Measure query patterns before optimizing — premature optimization is costly.",
                ]
            }
        ]
    },
    {
        "slug": "vector-search-fundamentals",
        "title": "Vector Search Fundamentals",
        "author": "Carol Zhang",
        "category": "AI Features",
        "sections": [
            {
                "title": "Understanding Embeddings",
                "paragraphs": [
                    "Embeddings convert text into numerical vectors that capture semantic meaning.",
                    "Similar concepts produce vectors that are close together in high-dimensional space.",
                    "RushDB supports both managed embeddings (server-side) and external embeddings.",
                    "Vector dimensions depend on your embedding model (e.g., 768 for many sentence transformers).",
                ]
            },
            {
                "title": "Index Configuration",
                "paragraphs": [
                    "Create an index: db.ai.indexes.create({'label': 'ARTICLE', 'propertyName': 'body'})",
                    "For external embeddings, specify dimensions and sourceType.",
                    "Choose similarity function: cosine, euclidean, or dot product.",
                    "Monitor index stats to ensure proper indexing.",
                ]
            },
            {
                "title": "Semantic Search Queries",
                "paragraphs": [
                    "Basic search: db.ai.search({'propertyName': 'body', 'query': 'graph traversal', 'labels': ['ARTICLE']})",
                    "Filtered search: add 'where' clause for metadata filtering.",
                    "Limit results: use 'limit' parameter (default 10).",
                    "Results include __score for relevance ranking.",
                ]
            }
        ]
    },
    {
        "slug": "transactions-and-data-integrity",
        "title": "Transactions and Data Integrity",
        "author": "Alice Chen",
        "category": "Advanced Topics",
        "sections": [
            {
                "title": "ACID Transactions",
                "paragraphs": [
                    "RushDB transactions wrap multiple operations in an atomic unit.",
                    "Begin transaction: tx = db.transactions.begin()",
                    "Commit on success: tx.commit()",
                    "Rollback on failure: tx.rollback()",
                ]
            },
            {
                "title": "Context Manager Pattern",
                "paragraphs": [
                    "Use context managers for cleaner transaction handling.",
                    "Syntax: with db.transactions.begin() as tx:",
                    "Auto-commits on clean exit, auto-rollbacks on exception.",
                    "Don't call tx.commit() inside the with block.",
                ]
            },
            {
                "title": "Common Patterns",
                "paragraphs": [
                    "Create with transaction: db.records.create(label='X', data={}, transaction=tx)",
                    "Batch operations: create_many within transaction for bulk imports.",
                    "Relationship creation: db.records.attach(source, target, options, transaction=tx)",
                    "Verify with find after commit to confirm persistence.",
                ]
            }
        ]
    },
    {
        "slug": "production-deployment",
        "title": "Production Deployment Guide",
        "author": "Dave Johnson",
        "category": "Deployment",
        "sections": [
            {
                "title": "Self-Hosting Options",
                "paragraphs": [
                    "RushDB supports self-hosted deployment via BYOC (Bring Your Own Neo4j).",
                    "Use Neo4j Community for development, Enterprise for production clustering.",
                    "Connection string format: bolt://host:7687 or neo4j+s://host:7687",
                    "Ensure proper network security groups allow Neo4j traffic.",
                ]
            },
            {
                "title": "Scaling Considerations",
                "paragraphs": [
                    "RushDB charges by Knowledge Units (KU) for writes only.",
                    "Reads and queries are always free.",
                    "Plan for write volume when estimating costs.",
                    "Monitor KU usage via dashboard for optimization opportunities.",
                ]
            },
            {
                "title": "Monitoring and Debugging",
                "paragraphs": [
                    "Check index stats: db.ai.indexes.stats(index_id)",
                    "Query raw Cypher for debugging: db.query.raw('MATCH (n) RETURN count(n)')",
                    "Review ontology: db.ai.getOntologyMarkdown() for schema overview.",
                    "Use transactions for batch operations to minimize overhead.",
                ]
            }
        ]
    }
]

# Related article pairs for cross-document linking
RELATED_PAIRS = [
    ("intro-to-rushdb", "graph-data-modeling"),
    ("intro-to-rushdb", "vector-search-fundamentals"),
    ("graph-data-modeling", "vector-search-fundamentals"),
    ("transactions-and-data-integrity", "production-deployment"),
    ("graph-data-modeling", "production-deployment"),
]

# Keywords for cross-chunk linking (paragraphs about same topics)
CROSS_CHUNK_LINKS = {
    "neo4j": [("intro-to-rushdb", 0, 2), ("production-deployment", 0, 0)],
    "relationships": [("intro-to-rushdb", 1, 2), ("graph-data-modeling", 0, 3)],
    "embedding": [("vector-search-fundamentals", 0, 0), ("vector-search-fundamentals", 0, 1)],
    "transaction": [("intro-to-rushdb", 2, 3), ("transactions-and-data-integrity", 0, 0)],
}


def check_existing_data():
    """Check if data already exists to avoid re-seeding."""
    existing = db.records.find({"labels": ["ARTICLE"], "limit": 1})
    return existing.total > 0


def seed_data():
    """Seed the knowledge base with articles, sections, and paragraphs."""
    print("Seeding knowledge base...\n")
    
    # Track created records for linking
    article_records = {}
    section_records = {}
    paragraph_records = {}
    
    for idx, article_data in enumerate(ARTICLES):
        print(f"  Creating article: {article_data['title']}")
        
        # Create article (document-level)
        article = db.records.create(
            label="ARTICLE",
            data={
                "slug": article_data["slug"],
                "title": article_data["title"],
                "author": article_data["author"],
                "category": article_data["category"]
            }
        )
        article_records[article_data["slug"]] = article
        
        # Create sections and paragraphs (chunk-level)
        for section_idx, section_data in enumerate(article_data["sections"]):
            section = db.records.create(
                label="SECTION",
                data={
                    "title": section_data["title"],
                    "order": section_idx
                }
            )
            section_records[(article_data["slug"], section_idx)] = section
            
            # Link section to article (document-level: parent relationship)
            db.records.attach(
                source=section,
                target=article,
                options={"type": "BELONGS_TO", "direction": "out"}
            )
            
            # Create paragraphs
            for para_idx, para_text in enumerate(section_data["paragraphs"]):
                paragraph = db.records.create(
                    label="PARAGRAPH",
                    data={
                        "content": para_text,
                        "order": para_idx
                    }
                )
                paragraph_records[(article_data["slug"], section_idx, para_idx)] = paragraph
                
                # Link paragraph to section (chunk-level: parent relationship)
                db.records.attach(
                    source=paragraph,
                    target=section,
                    options={"type": "PART_OF", "direction": "out"}
                )
                
                # Link paragraph to article (chunk-level: cross-reference base)
                db.records.attach(
                    source=paragraph,
                    target=article,
                    options={"type": "FROM_ARTICLE", "direction": "out"}
                )
                
                # Link consecutive paragraphs (chunk-level: sequential)
                if para_idx > 0:
                    prev_paragraph = paragraph_records[(article_data["slug"], section_idx, para_idx - 1)]
                    db.records.attach(
                        source=prev_paragraph,
                        target=paragraph,
                        options={"type": "NEXT", "direction": "out"}
                    )
                
                # Link first paragraph of section to section (chunk-level: entry point)
                if para_idx == 0:
                    db.records.attach(
                        source=section,
                        target=paragraph,
                        options={"type": "STARTS_WITH", "direction": "out"}
                    )
        
        # Link last paragraph of section to section (chunk-level: end point)
        section = section_records[(article_data["slug"], len(article_data["sections"]) - 1)]
        last_para = paragraph_records[(article_data["slug"), len(article_data["sections"]) - 1, len(article_data["sections"][-1]["paragraphs"]) - 1]
        db.records.attach(
            source=section,
            target=last_para,
            options={"type": "ENDS_WITH", "direction": "out"}
        )
        
        if (idx + 1) % 100 == 0:
            print(f"    Processed {idx + 1} articles...")
    
    print(f"\n  Created {len(article_records)} articles")
    print(f"  Created {len(section_records)} sections")
    print(f"  Created {len(paragraph_records)} paragraphs")
    
    # Create cross-article relationships (document-level)
    print("\n  Creating cross-article relationships...")
    for slug_a, slug_b in RELATED_PAIRS:
        if slug_a in article_records and slug_b in article_records:
            db.records.attach(
                source=article_records[slug_a],
                target=article_records[slug_b],
                options={"type": "RELATED_TO", "direction": "out"}
            )
            db.records.attach(
                source=article_records[slug_b],
                target=article_records[slug_a],
                options={"type": "RELATED_TO", "direction": "out"}
            )
    
    # Create cross-chunk relationships (chunk-level)
    print("  Creating cross-chunk relationships...")
    for keyword, links in CROSS_CHUNK_LINKS.items():
        for slug_a, sec_a, para_a in links:
            for slug_b, sec_b, para_b in links:
                if (slug_a, sec_a, para_a) < (slug_b, sec_b, para_b):
                    para_a_record = paragraph_records.get((slug_a, sec_a, para_a))
                    para_b_record = paragraph_records.get((slug_b, sec_b, para_b))
                    if para_a_record and para_b_record:
                        db.records.attach(
                            source=para_a_record,
                            target=para_b_record,
                            options={"type": "REFERENCES", "direction": "out"}
                        )
                        db.records.attach(
                            source=para_b_record,
                            target=para_a_record,
                            options={"type": "REFERENCES", "direction": "out"}
                        )
    
    # Create author links (document-level)
    print("  Creating author relationships...")
    author_articles = {}
    for slug, article in article_records.items():
        author_name = article.data.get("author")
        if author_name not in author_articles:
            author_record = db.records.create(
                label="AUTHOR",
                data={"name": author_name}
            )
            author_articles[author_name] = author_record
        
        db.records.attach(
            source=article,
            target=author_articles[author_name],
            options={"type": "WRITTEN_BY", "direction": "out"}
        )
    
    print("\n✓ Seeding complete!")
    return {
        "articles": len(article_records),
        "sections": len(section_records),
        "paragraphs": len(paragraph_records),
        "authors": len(author_articles)
    }


def main():
    print("=" * 60)
    print("RushDB Knowledge Base Seeder")
    print("=" * 60)
    
    # Check for existing data
    if check_existing_data():
        print("\n⚠ Data already exists. Skipping seed.")
        print("Delete existing records to re-seed, or run main.py directly.\n")
        return
    
    # Run seeding
    stats = seed_data()
    
    print("\n" + "=" * 60)
    print("Seeding Statistics")
    print("=" * 60)
    for key, value in stats.items():
        print(f"  {key.capitalize()}: {value}")
    print("\nRun 'python main.py' to see the linking strategies in action.\n")


if __name__ == "__main__":
    main()
