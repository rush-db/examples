"""
Chunk-Level vs Document-Level Linking Strategies in RushDB
===========================================================

This tutorial demonstrates two fundamental graph modeling approaches
using a technical documentation knowledge base as the real-world context.

Document-Level Strategy: Entire records linked to each other
Chunk-Level Strategy: Granular content segments linked for precise retrieval

Run seed.py first to populate the database with sample data.
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
url = os.getenv("RUSHDB_URL")
db = RushDB(api_key, url=url) if url else RushDB(api_key)


def print_header(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def print_subheader(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


# =============================================================================
# DOCUMENT-LEVEL LINKING STRATEGY
# =============================================================================

def demonstrate_document_level():
    """
    Document-level linking treats entire records as atomic units.
    Use cases: navigation, taxonomy, organizational structures.
    """
    print_header("DOCUMENT-LEVEL LINKING STRATEGY")
    
    print("\nApproach: Entire articles linked to each other and to authors.")
    print("Granularity: Article → Section (parent only)")
    print("Query focus: Navigation, taxonomy, authorship tracking")
    
    # ---------------------------------------------------------------------
    # Example 1: Find all articles by an author
    # ---------------------------------------------------------------------
    print_subheader("Example 1: Find articles by author")
    
    author_result = db.records.find({
        "labels": ["AUTHOR"],
        "where": {"name": "Alice Chen"}
    })
    
    if author_result.total > 0:
        author = author_result.data[0]
        print(f"Author: {author.data.get('name')}")
        
        # Follow WRITTEN_BY relationships to find articles
        articles = db.records.find({
            "labels": ["ARTICLE"],
            "where": {
                "AUTHOR": {
                    "$relation": {"type": "WRITTEN_BY", "direction": "in"},
                    "name": "Alice Chen"
                }
            }
        })
        
        print(f"Articles written by Alice Chen: {articles.total}")
        for article in articles.data:
            print(f"  - {article.data.get('title')} (category: {article.data.get('category')})")
    
    # ---------------------------------------------------------------------
    # Example 2: Navigate related articles
    # ---------------------------------------------------------------------
    print_subheader("Example 2: Navigate related articles")
    
    target_article = db.records.find({
        "labels": ["ARTICLE"],
        "where": {"slug": "intro-to-rushdb"}
    })
    
    if target_article.total > 0:
        article = target_article.data[0]
        print(f"Starting from: {article.data.get('title')}")
        
        # Follow RELATED_TO relationships
        related = db.records.find({
            "labels": ["ARTICLE"],
            "where": {
                "ARTICLE": {
                    "$relation": {"type": "RELATED_TO", "direction": "in"},
                    "slug": "intro-to-rushdb"
                }
            }
        })
        
        print(f"Related articles: {related.total}")
        for rel_article in related.data:
            print(f"  → {rel_article.data.get('title')}")
    
    # ---------------------------------------------------------------------
    # Example 3: Category-based navigation
    # ---------------------------------------------------------------------
    print_subheader("Example 3: Category-based organization")
    
    categories_result = db.records.find({
        "labels": ["ARTICLE"],
        "where": {"category": "Architecture"}
    })
    
    print(f"Articles in 'Architecture' category: {categories_result.total}")
    for art in categories_result.data:
        print(f"  - {art.data.get('title')} by {art.data.get('author')}")
    
    # ---------------------------------------------------------------------
    # Example 4: Traverse article → section hierarchy
    # ---------------------------------------------------------------------
    print_subheader("Example 4: Article → Section hierarchy")
    
    article_result = db.records.find({
        "labels": ["ARTICLE"],
        "where": {"slug": "graph-data-modeling"}
    })
    
    if article_result.total > 0:
        article = article_result.data[0]
        print(f"Article: {article.data.get('title')}")
        
        # Find sections belonging to this article
        sections = db.records.find({
            "labels": ["SECTION"],
            "where": {
                "ARTICLE": {
                    "$relation": {"type": "BELONGS_TO", "direction": "in"},
                    "slug": "graph-data-modeling"
                }
            },
            "orderBy": {"order": "asc"}
        })
        
        print(f"Sections: {sections.total}")
        for section in sections.data:
            print(f"  {section.data.get('order') + 1}. {section.data.get('title')}")
    
    print("\n✓ Document-level strategy: simple traversal, clear boundaries")


# =============================================================================
# CHUNK-LEVEL LINKING STRATEGY
# =============================================================================

def demonstrate_chunk_level():
    """
    Chunk-level linking breaks content into granular segments.
    Use cases: RAG pipelines, fine-grained retrieval, content similarity.
    """
    print_header("CHUNK-LEVEL LINKING STRATEGY")
    
    print("\nApproach: Paragraphs as atomic units with rich cross-references.")
    print("Granularity: Article → Section → Paragraph (full hierarchy)")
    print("Query focus: Precise retrieval, semantic search, content relationships")
    
    # ---------------------------------------------------------------------
    # Example 1: Walk through a section's paragraphs sequentially
    # ---------------------------------------------------------------------
    print_subheader("Example 1: Sequential paragraph traversal")
    
    # Find a section
    section_result = db.records.find({
        "labels": ["SECTION"],
        "where": {"title": "Core Concepts"}
    })
    
    if section_result.total > 0:
        section = section_result.data[0]
        print(f"Section: {section.data.get('title')}")
        
        # Find the first paragraph (via STARTS_WITH)
        start_result = db.records.find({
            "labels": ["PARAGRAPH"],
            "where": {
                "SECTION": {
                    "$relation": {"type": "STARTS_WITH", "direction": "in"},
                    "title": "Core Concepts"
                }
            }
        })
        
        if start_result.total > 0:
            current = start_result.data[0]
            print("\nParagraphs (via NEXT relationships):")
            
            visited = set()
            while current and current.id not in visited:
                visited.add(current.id)
                order = current.data.get("order", 0) + 1
                content = current.data.get("content", "")[:60] + "..."
                print(f"  [{order}] {content}")
                
                # Follow NEXT relationship to next paragraph
                next_result = db.records.find({
                    "labels": ["PARAGRAPH"],
                    "where": {
                        "PARAGRAPH": {
                            "$relation": {"type": "NEXT", "direction": "in"},
                            "id": current.id
                        }
                    }
                })
                
                if next_result.total > 0:
                    current = next_result.data[0]
                else:
                    break
    
    # ---------------------------------------------------------------------
    # Example 2: Find all paragraphs referencing a specific topic
    # ---------------------------------------------------------------------
    print_subheader("Example 2: Cross-chunk references (topic linking)")
    
    # Find paragraphs with REFERENCES relationships (cross-chunk)
    referenced_paragraphs = db.records.find({
        "labels": ["PARAGRAPH"],
        "where": {
            "PARAGRAPH": {"$relation": {"type": "REFERENCES", "direction": "out"}}
        },
        "limit": 10
    })
    
    print(f"Paragraphs with cross-chunk references: {referenced_paragraphs.total}")
    
    for para in referenced_paragraphs.data[:5]:
        content_preview = para.data.get("content", "")[:50] + "..."
        print(f"  - {content_preview}")
        
        # Show what it references
        refs = db.records.find({
            "labels": ["PARAGRAPH"],
            "where": {
                "PARAGRAPH": {
                    "$relation": {"type": "REFERENCES", "direction": "in"},
                    "id": para.id
                }
            }
        })
        
        for ref in refs.data:
            # Get the article this paragraph belongs to
            article_result = db.records.find({
                "labels": ["ARTICLE"],
                "where": {
                    "PARAGRAPH": {
                        "$relation": {"type": "FROM_ARTICLE", "direction": "in"},
                        "id": ref.id
                    }
                }
            })
            if article_result.total > 0:
                print(f"    → References content from: {article_result.data[0].data.get('title')}")
    
    # ---------------------------------------------------------------------
    # Example 3: Trace paragraph back to article (granular path)
    # ---------------------------------------------------------------------
    print_subheader("Example 3: Full hierarchy traversal (Article → Section → Paragraph)")
    
    # Pick a paragraph and trace its full lineage
    para_result = db.records.find({"labels": ["PARAGRAPH"], "limit": 1})
    
    if para_result.total > 0:
        paragraph = para_result.data[0]
        print(f"Starting paragraph: {paragraph.data.get('content')[:40]}...")
        
        # Find its parent section
        parent_section = db.records.find({
            "labels": ["SECTION"],
            "where": {
                "PARAGRAPH": {
                    "$relation": {"type": "PART_OF", "direction": "in"},
                    "id": paragraph.id
                }
            }
        })
        
        if parent_section.total > 0:
            section = parent_section.data[0]
            print(f"  Parent section: {section.data.get('title')}")
            
            # Find grandparent article
            parent_article = db.records.find({
                "labels": ["ARTICLE"],
                "where": {
                    "SECTION": {
                        "$relation": {"type": "BELONGS_TO", "direction": "in"},
                        "id": section.id
                    }
                }
            })
            
            if parent_article.total > 0:
                article = parent_article.data[0]
                print(f"    Parent article: {article.data.get('title')}")
                print(f"      Author: {article.data.get('author')}")
                print(f"      Category: {article.data.get('category')}")
    
    # ---------------------------------------------------------------------
    # Example 4: Get all content from an article via chunks
    # ---------------------------------------------------------------------
    print_subheader("Example 4: Reconstruct article content from chunks")
    
    target = db.records.find({
        "labels": ["ARTICLE"],
        "where": {"slug": "intro-to-rushdb"}
    })
    
    if target.total > 0:
        article = target.data[0]
        print(f"Reconstructing: {article.data.get('title')}")
        
        # Get all paragraphs from this article (via FROM_ARTICLE)
        paragraphs = db.records.find({
            "labels": ["PARAGRAPH"],
            "where": {
                "ARTICLE": {
                    "$relation": {"type": "FROM_ARTICLE", "direction": "in"},
                    "slug": "intro-to-rushdb"
                }
            },
            "orderBy": {"order": "asc"}
        })
        
        print(f"\nTotal paragraph chunks: {paragraphs.total}")
        print("\nContent reconstruction:")
        for idx, para in enumerate(paragraphs.data):
            print(f"  [{idx + 1}] {para.data.get('content')}")
    
    print("\n✓ Chunk-level strategy: granular access, precise retrieval")


# =============================================================================
# HYBRID APPROACH: COMBINING BOTH STRATEGIES
# =============================================================================

def demonstrate_hybrid_approach():
    """
    Hybrid approach uses document-level for structure and chunk-level for content.
    Best of both worlds: easy navigation + precise retrieval.
    """
    print_header("HYBRID APPROACH: DOCUMENT + CHUNK LEVEL")
    
    print("\nStrategy: Document links for navigation, chunk links for content access.")
    print("Use case: Complex systems requiring both browsing and detailed retrieval.")
    
    # ---------------------------------------------------------------------
    # Example: Find related content at both levels
    # ---------------------------------------------------------------------
    print_subheader("Example: Dual-level related content search")
    
    # Start with an article
    source = db.records.find({
        "labels": ["ARTICLE"],
        "where": {"slug": "graph-data-modeling"}
    })
    
    if source.total > 0:
        article = source.data[0]
        print(f"Source article: {article.data.get('title')}")
        
        # Document-level: Find related articles
        doc_related = db.records.find({
            "labels": ["ARTICLE"],
            "where": {
                "ARTICLE": {
                    "$relation": {"type": "RELATED_TO", "direction": "in"},
                    "slug": "graph-data-modeling"
                }
            }
        })
        
        print(f"\n[Document-level] Related articles: {doc_related.total}")
        for rel in doc_related.data:
            print(f"  → {rel.data.get('title')}")
        
        # Chunk-level: Find related paragraphs across articles
        # Get paragraphs from this article
        article_paras = db.records.find({
            "labels": ["PARAGRAPH"],
            "where": {
                "ARTICLE": {
                    "$relation": {"type": "FROM_ARTICLE", "direction": "in"},
                    "slug": "graph-data-modeling"
                }
            },
            "limit": 5
        })
        
        print(f"\n[Chunk-level] Cross-referenced content:")
        for para in article_paras.data:
            # Check if this paragraph references others
            refs = db.records.find({
                "labels": ["PARAGRAPH"],
                "where": {
                    "PARAGRAPH": {
                        "$relation": {"type": "REFERENCES", "direction": "in"},
                        "id": para.id
                    }
                }
            })
            
            if refs.total > 0:
                content = para.data.get("content", "")[:40] + "..."
                print(f"\n  Paragraph: {content}")
                print(f"    References {refs.total} other paragraph(s)")
    
    # ---------------------------------------------------------------------
    # Example: RAG-style retrieval with document context
    # ---------------------------------------------------------------------
    print_subheader("Example: RAG pipeline with context enrichment")
    
    # Simulate finding relevant content chunk
    target_para = db.records.find({
        "labels": ["PARAGRAPH"],
        "where": {"content": {"$contains": "embedding"}}
    })
    
    if target_para.total > 0:
        para = target_para.data[0]
        print(f"Retrieved chunk: {para.data.get('content')[:50]}...")
        
        # Get document context (article + section)
        # Find parent section
        parent_sec = db.records.find({
            "labels": ["SECTION"],
            "where": {
                "PARAGRAPH": {
                    "$relation": {"type": "PART_OF", "direction": "in"},
                    "id": para.id
                }
            }
        })
        
        # Find grandparent article
        if parent_sec.total > 0:
            parent_art = db.records.find({
                "labels": ["ARTICLE"],
                "where": {
                    "SECTION": {
                        "$relation": {"type": "BELONGS_TO", "direction": "in"},
                        "id": parent_sec.data[0].id
                    }
                }
            })
            
            if parent_art.total > 0:
                article = parent_art.data[0]
                print(f"\n[Enriched context]")
                print(f"  Article: {article.data.get('title')}")
                print(f"  Section: {parent_sec.data[0].data.get('title')}")
                print(f"  Author: {article.data.get('author')}")
                print(f"\n  → Use this context to ground LLM response with source attribution")
    
    print("\n✓ Hybrid approach: structure + granularity combined")


# =============================================================================
# COMPARISON SUMMARY
# =============================================================================

def print_comparison():
    """Print a side-by-side comparison of both strategies."""
    print_header("STRATEGY COMPARISON")
    
    comparison = """
    | Aspect              | Document-Level        | Chunk-Level           |
    |---------------------|------------------------|------------------------|
    | Granularity         | Record-level           | Field/segment-level    |
    | Best for            | Navigation, browsing  | RAG, precise retrieval |
    | Query complexity    | Simple                 | Complex                |
    | Relationship count | Fewer                  | Many                   |
    | Storage overhead   | Lower                  | Higher                 |
    | Use when            | Structure matters     | Content matters        |
    | Example use case    | Category → Article     | Article → Paragraph    |
    """
    print(comparison)
    
    print("\n[Recommendation]")
    print("  - Start with document-level for clear hierarchies")
    print("  - Add chunk-level when you need granular retrieval")
    print("  - Use hybrid when you need both navigation and precision")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    print("\n" + "=" * 60)
    print("RushDB TUTORIAL")
    print("Chunk-Level vs Document-Level Linking Strategies")
    print("=" * 60)
    
    # Check for data
    check = db.records.find({"labels": ["ARTICLE"], "limit": 1})
    if check.total == 0:
        print("\n⚠ No data found. Please run 'python seed.py' first.\n")
        return
    
    print(f"\n✓ Found {check.total}+ article(s) in database. Running tutorial...\n")
    
    # Run demonstrations
    demonstrate_document_level()
    demonstrate_chunk_level()
    demonstrate_hybrid_approach()
    print_comparison()
    
    print("\n" + "=" * 60)
    print("Tutorial complete! Explore RushDB further:")
    print("  - Docs: https://docs.rushdb.com")
    print("  - Examples: https://github.com/rush-db/examples")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
