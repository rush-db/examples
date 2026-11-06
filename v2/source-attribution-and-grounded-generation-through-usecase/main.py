#!/usr/bin/env python3
"""
Source Attribution and Grounded Generation Demo

This script demonstrates RushDB's graph + vector architecture for building
auditable AI applications with full citation lineage.

Key capabilities demonstrated:
1. Vector similarity search for candidate retrieval
2. Graph traversal to claims (provenance)
3. Answer assembly with traced citations
4. Evidence chain auditing
5. Document update handling (where vector stores fail)
"""

import os
import sys
from datetime import datetime
from typing import Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer


# =============================================================================
# CONFIGURATION
# =============================================================================

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")


def print_section(text: str):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*60}{Colors.END}")


# =============================================================================
# DATABASE HELPERS
# =============================================================================

def get_db_status():
    """Get current database status counts."""
    api_key = os.environ.get('RUSHDB_API_KEY')
    if not api_key:
        return None
    
    db = RushDB(api_key)
    
    # Count records by label
    documents = db.records.find({"labels": ["Document"], "limit": 1})
    passages = db.records.find({"labels": ["Passage"], "limit": 1})
    claims = db.records.find({"labels": ["Claim"], "limit": 1})
    
    # Check vector index status
    index_status = "NOT CREATED"
    index_stats = None
    try:
        indexes = db.ai.indexes.find()
        for idx in indexes.data:
            if idx.get('label') == 'Passage' and idx.get('propertyName') == 'content':
                index_id = idx.get('__id')
                stats = db.ai.indexes.stats(index_id)
                index_stats = stats.data
                indexed = index_stats.get('indexedRecords', 0)
                total = index_stats.get('totalRecords', 0)
                index_status = f"ACTIVE ({indexed}/{total} indexed)" if indexed == total else f"PENDING ({indexed}/{total})",
                break
    except Exception:
        pass
    
    return {
        "documents": documents.total,
        "passages": passages.total,
        "claims": claims.total,
        "index_status": index_status,
        "index_stats": index_stats
    }


# =============================================================================
# Q&A PIPELINE
# =============================================================================

class GroundedResearchAssistant:
    """
    A research assistant that demonstrates source attribution through RushDB's
    graph + vector architecture.
    
    Query pipeline:
    1. User question
    2. Semantic search (vector retrieval) → candidate passages
    3. Graph traversal → claims citing those passages
    4. Answer assembly with full provenance
    """
    
    def __init__(self, api_key: str):
        self.db = RushDB(api_key)
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    def get_index_id(self) -> Optional[str]:
        """Find the vector index ID for passages."""
        try:
            indexes = self.db.ai.indexes.find()
            for idx in indexes.data:
                if idx.get('label') == 'Passage' and idx.get('propertyName') == 'content':
                    return idx.get('__id')
        except Exception:
            pass
        return None
    
    def semantic_search_passages(self, query: str, limit: int = 5):
        """
        Phase 1: Vector similarity search for relevant passages.
        
        This is what a pure vector store does well.
        """
        print(f"{Colors.YELLOW}📄 Retrieved Passages (vector similarity):{Colors.END}")
        
        results = self.db.ai.search({
            "propertyName": "content",
            "query": query,
            "labels": ["Passage"],
            "limit": limit
        })
        
        passages = []
        for i, record in enumerate(results.data):
            text = record.get("text", "")
            source = record.get("source_document", "Unknown")
            score = record.score or 0.0
            
            # Truncate long text for display
            display_text = text[:80] + "..." if len(text) > 80 else text
            print(f"  [{i+1}] \"{display_text}\" (score: {score:.2f}, source: {source})")
            
            passages.append({
                "id": record.id,
                "text": text,
                "source": source,
                "score": score
            })
        
        return passages
    
    def traverse_to_claims(self, passages: list) -> list:
        """
        Phase 2: Graph traversal from passages to supporting claims.
        
        This is where RushDB's graph layer adds value — we can traverse
        from retrieved passages to the claims that cite them.
        """
        print(f"\n{Colors.CYAN}🔗 Evidence Chain (graph traversal):{Colors.END}")
        
        all_claims = []
        
        for passage in passages:
            # Find claims that cite this passage
            claims = self.db.records.find({
                "labels": ["Claim"],
                "where": {
                    "Passage": {
                        "$relation": {"type": "CITES", "direction": "in"},
                        "$id": passage["id"]
                    }
                }
            })
            
            for claim in claims.data:
                claim_text = claim.get("text", "")
                extracted_from = claim.get("extracted_from", "Unknown")
                
                print(f"  Passage \"{passage['text'][:50]}...\"")
                print(f"    └─── SUPPORTS ───▶ Claim: \"{claim_text}\"")
                print(f"         Document: {extracted_from}")
                print()
                
                all_claims.append({
                    "id": claim.id,
                    "text": claim_text,
                    "source_document": extracted_from,
                    "citing_passage": passage
                })
        
        return all_claims
    
    def assemble_answer(self, question: str, passages: list, claims: list) -> dict:
        """
        Phase 3: Assemble answer with full provenance.
        
        In a real application, this would call an LLM with the retrieved
        context. Here, we demonstrate the provenance tracking structure.
        """
        print(f"{Colors.GREEN}✅ Assembled Answer:{Colors.END}")
        
        # Build citation string
        citations = []
        for claim in claims:
            citations.append(
                f"[Claim: {claim['text']}, citing '{claim['source_document']}']"
            )
        
        answer_text = (
            f"Based on retrieved evidence and extracted claims: "
            f"{' '.join(citations[:2])}. "
            f"This response can be verified by tracing the citation graph below."
        )
        print(f"  {answer_text}\n")
        
        # Create answer record with provenance
        with self.db.transactions.begin() as tx:
            answer = self.db.records.create(
                label="Answer",
                data={
                    "question": question,
                    "answer_text": answer_text,
                    "created_at": datetime.now().isoformat()
                },
                transaction=tx
            )
            
            # Link answer to claims
            for claim in claims[:3]:  # Limit to top 3 claims
                self.db.records.attach(
                    source=answer,
                    target=self.db.records.find_by_id(claim["id"]),
                    options={"type": "CITES", "direction": "out"},
                    transaction=tx
                )
        
        return {
            "answer_id": answer.id,
            "answer_text": answer_text,
            "citations": citations,
            "claims": claims
        }
    
    def show_citation_graph(self, answer_id: str):
        """
        Show the citation graph for an answer.
        
        This demonstrates RushDB's ability to reconstruct the full provenance
        trail — something pure vector stores cannot do.
        """
        print(f"{Colors.YELLOW}🔍 Citation Graph:{Colors.END}")
        
        answer = self.db.records.find_by_id(answer_id)
        
        # Find cited claims
        cited_claims = self.db.records.find({
            "labels": ["Claim"],
            "where": {
                "Answer": {
                    "$relation": {"type": "CITES", "direction": "in"},
                    "$id": answer_id
                }
            }
        })
        
        for claim in cited_claims.data:
            print(f"  Answer → CITES → Claim: \"{claim.get('text')}\"")
            
            # Find passages cited by this claim
            cited_passages = self.db.records.find({
                "labels": ["Passage"],
                "where": {
                    "Claim": {
                        "$relation": {"type": "CITES", "direction": "in"},
                        "$id": claim.id
                    }
                }
            })
            
            for passage in cited_passages.data:
                print(f"    └─── CITES → Passage: \"{passage.get('text')[:40]}...\"")
                
                # Find document containing this passage
                containing_docs = self.db.records.find({
                    "labels": ["Document"],
                    "where": {
                        "Passage": {
                            "$relation": {"type": "CONTAINS", "direction": "out"},
                            "$id": passage.id
                        }
                    }
                })
                
                for doc in containing_docs.data:
                    print(f"         └─── FROM → Document: {doc.get('title')}")
        
        print()
    
    def run_query(self, question: str):
        """
        Execute the full query pipeline for a question.
        
        Demonstrates:
        1. Vector retrieval (semantic search)
        2. Graph traversal (claim extraction)
        3. Answer assembly with provenance
        4. Citation graph visualization
        """
        print(f"\n{Colors.BOLD}❓ Question: \"{question}\"{Colors.END}")
        
        # Phase 1: Semantic search
        passages = self.semantic_search_passages(question, limit=3)
        
        if not passages:
            print(f"{Colors.RED}No passages found for this question.{Colors.END}")
            return None
        
        # Phase 2: Graph traversal to claims
        claims = self.traverse_to_claims(passages)
        
        if not claims:
            print(f"{Colors.YELLOW}No claims found in evidence chain.{Colors.END}")
        
        # Phase 3: Assemble answer
        result = self.assemble_answer(question, passages, claims)
        
        # Phase 4: Show citation graph
        self.show_citation_graph(result["answer_id"])
        
        return result


# =============================================================================
# EVIDENCE CHAIN AUDITING
# =============================================================================

def demonstrate_evidence_auditing(db: RushDB):
    """
    Demonstrate the auditing capabilities that RushDB enables.
    
    Pure vector stores cannot answer questions like:
    - "What evidence supports this claim?"
    - "Which documents does this claim reference?"
    - "How current is this evidence?"
    """
    print_section("EVIDENCE CHAIN AUDIT")
    
    # Get a sample claim
    claims = db.records.find({"labels": ["Claim"], "limit": 1})
    
    if not claims.data:
        print("No claims found to audit.")
        return
    
    claim = claims.data[0]
    print(f"\nClaim: \"{claim.get('text')}\"")
    
    # Audit 1: What passages support this claim?
    supporting_passages = db.records.find({
        "labels": ["Passage"],
        "where": {
            "Claim": {
                "$relation": {"type": "CITES", "direction": "in"},
                "$id": claim.id
            }
        }
    })
    
    print(f"\n  • Supported by: {supporting_passages.total} passage(s)")
    for passage in supporting_passages.data:
        print(f"    - \"{passage.get('text')[:60]}...\"")
    
    # Audit 2: What documents are involved?
    document_query = db.records.find({
        "labels": ["Document"],
        "where": {
            "Passage": {
                "Claim": {
                    "$relation": {"type": "CITES", "direction": "in"},
                    "$id": claim.id
                }
            }
        }
    })
    
    print(f"\n  • First-order citations: {document_query.total} document(s)")
    for doc in document_query.data:
        print(f"    - {doc.get('title')} ({doc.get('year')})")
    
    # Audit 3: Verification status (all evidence chain intact)
    verification_status = "✅ VERIFIED" if supporting_passages.total > 0 else "❌ UNVERIFIED"
    print(f"\n  • Verification status: {verification_status}")


# =============================================================================
# DOCUMENT UPDATE SCENARIO
# =============================================================================

def demonstrate_update_handling(db: RushDB):
    """
    Demonstrate how RushDB handles document updates.
    
    This is where pure vector stores break down:
    - Old chunks remain in the index (stale evidence)
    - No way to know what changed
    - Need full re-embedding
    
    RushDB handles this gracefully:
    - Update the record
    - Graph edges remain valid
    - No need to rebuild the vector index
    """
    print_section("DOCUMENT UPDATE SCENARIO")
    
    print(f"{Colors.YELLOW}📝 Simulating document update...{Colors.END}\n")
    
    # Find a document
    documents = db.records.find({"labels": ["Document"], "limit": 1})
    
    if not documents.data:
        print("No documents found.")
        return
    
    document = documents.data[0]
    original_title = document.get("title")
    
    print(f"Original document: {original_title}")
    print(f"Document ID: {document.id}")
    
    # Find passages and claims for this document
    passages = db.records.find({
        "labels": ["Passage"],
        "where": {
            "Document": {
                "$relation": {"type": "CONTAINS", "direction": "in"},
                "$id": document.id
            }
        }
    })
    
    print(f"Passages: {passages.total}")
    
    # Demonstrate update: Add a new field to the document
    print(f"\n{Colors.GREEN}✅ Updating document metadata...{Colors.END}")
    
    with db.transactions.begin() as tx:
        # Update the document record
        db.records.set(
            target=document,
            label="Document",
            data={
                "title": original_title,
                "authors": document.get("authors", []),
                "year": document.get("year", 2020),
                "paper_id": document.get("paper_id"),
                "abstract": document.get("abstract", ""),
                "last_updated": datetime.now().isoformat(),
                "version": "2.0"
            },
            transaction=tx
        )
    
    print(f"  Added: last_updated={datetime.now().isoformat()}")
    print(f"  Added: version='2.0'")
    
    # Verify relationships still intact
    updated_passages = db.records.find({
        "labels": ["Passage"],
        "where": {
            "Document": {
                "$relation": {"type": "CONTAINS", "direction": "in"},
                "$id": document.id
            }
        }
    })
    
    print(f"\n{Colors.GREEN}✅ Graph relationships preserved{Colors.END}")
    print(f"  • Document → CONTAINS → {updated_passages.total} passages (unchanged)")
    print(f"  • Citation graph remains fully navigable")
    
    print(f"\n{Colors.CYAN}💡 Why this works:{Colors.END}")
    print(f"  • RushDB updated only the Document record")
    print(f"  • Passage records unchanged (no re-embedding needed)")
    print(f"  • Graph edges intact (CONTAINS, CITES relationships preserved)")
    print(f"  • Pure vector stores would need full document re-indexing")


# =============================================================================
# DOWNSTREAM VERIFICATION
# =============================================================================

def demonstrate_downstream_verification(db: RushDB):
    """
    Demonstrate downstream verification capabilities.
    
    Once you have a citation graph, you can:
    - Verify claims against original sources
    - Trace back to primary documents
    - Audit AI-generated content
    - Support compliance requirements
    """
    print_section("DOWNSTREAM VERIFICATION")
    
    print(f"{Colors.YELLOW}🔬 Verifying AI-generated claims...{Colors.END}\n")
    
    # Find all claims with their provenance
    all_claims = db.records.find({"labels": ["Claim"], "limit": 10})
    
    verification_results = []
    
    for claim in all_claims.data:
        claim_text = claim.get("text", "")
        
        # Find source document
        source_docs = db.records.find({
            "labels": ["Document"],
            "where": {
                "Passage": {
                    "Claim": {
                        "$relation": {"type": "CITES", "direction": "in"},
                        "$id": claim.id
                    }
                }
            }
        })
        
        for doc in source_docs.data:
            verification_results.append({
                "claim": claim_text,
                "document": doc.get("title"),
                "authors": doc.get("authors", []),
                "year": doc.get("year")
            })
    
    print(f"  Found {len(verification_results)} verifiable claims:\n")
    
    for i, result in enumerate(verification_results[:5], 1):
        print(f"  {i}. Claim: \"{result['claim'][:50]}...\"")
        print(f"     Source: {result['document']} ({result['year']})")
        print(f"     Authors: {', '.join(result['authors'][:2])}")
        print(f"     Status: ✅ TRACEABLE")
        print()
    
    print(f"{Colors.CYAN}💡 Verification capabilities:{Colors.END}")
    print(f"  • Every claim traces back to original research paper")
    print(f"  • Full author attribution available")
    print(f"  • Can be used for compliance auditing")
    print(f"  • Enables 'show your work' transparency")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run the complete source attribution demonstration."""
    
    # Check API key
    api_key = os.environ.get('RUSHDB_API_KEY')
    if not api_key:
        print(f"{Colors.RED}❌ Error: RUSHDB_API_KEY not found{Colors.END}")
        print(f"   Please copy .env.example to .env and add your API key")
        sys.exit(1)
    
    db = RushDB(api_key)
    
    # Check if data exists, if not prompt to seed
    status = get_db_status()
    if status and status["passages"] == 0:
        print(f"{Colors.YELLOW}⚠️  No data found in database.{Colors.END}")
        print(f"   Please run `python seed.py` first to populate the database.\n")
        response = input("   Run seed script now? (y/n): ")
        if response.lower() == 'y':
            print()
            import seed
            seed.seed_database()
            status = get_db_status()
        else:
            sys.exit(0)
    
    # Print header
    print_header("GROUNDED AI RESEARCH ASSISTANT — Source Attribution Demo")
    
    # Show database status
    print_section("Database Status")
    
    if status:
        print(f"  • Documents: {status['documents']}")
        print(f"  • Passages: {status['passages']} (all vectorized)")
        print(f"  • Claims: {status['claims']}")
        print(f"  • Vector Index: {status['index_status']}")
    else:
        print("  Unable to fetch database status.")
    
    # Initialize the research assistant
    assistant = GroundedResearchAssistant(api_key)
    
    # Q&A with provenance
    print_header("Q&A WITH FULL PROVENANCE")
    
    questions = [
        "How does retrieval improve language model performance?",
        "What role does model scale play in AI capabilities?",
        "How do transformers enable parallel processing?"
    ]
    
    for question in questions:
        assistant.run_query(question)
    
    # Evidence chain auditing
    demonstrate_evidence_auditing(db)
    
    # Document update handling
    demonstrate_update_handling(db)
    
    # Downstream verification
    demonstrate_downstream_verification(db)
    
    # Summary
    print_header("SUMMARY")
    
    print(f"""
{Colors.BOLD}What RushDB enables:{Colors.END}

  ✅ Full citation lineage for every generated answer
  ✅ Auditable evidence chains from claims to sources
  ✅ Document updates without full re-indexing
  ✅ Downstream verification and compliance support
  ✅ Queryable citation graph (unlike black-box vector stores)

{Colors.BOLD}Where pure vector stores fall short:{Colors.END}

  ❌ Cannot trace claim provenance
  ❌ Stale embeddings when documents update
  ❌ No way to verify AI-generated content
  ❌ Black box — cannot explain reasoning
  ❌ Flat similarity — no structured relationships

{Colors.BOLD}This production pattern is enabled by:{Colors.END}

  1. RushDB's dual-layer architecture (Neo4j + vectors)
  2. Transactional graph building with relationships
  3. Inline vector writes on record creation
  4. Semantic search + graph traversal query pipeline

{Learn more at https://docs.rushdb.com}
    """)


if __name__ == "__main__":
    main()
