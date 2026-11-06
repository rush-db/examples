"""
Streaming Token Generation with Graph-Traced Citations

This tutorial demonstrates how to build a streaming token generator that:
1. Stores documents and citations as a property graph in RushDB
2. Uses graph traversal to build citation context
3. Streams tokens with inline citation markers
4. Resolves citations back to graph nodes

Run `python seed.py` first to populate the knowledge graph.
"""

import os
import re
import time
import asyncio
from typing import Iterator, List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from rushdb import RushDB
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Citation:
    """Represents a citation reference in a streaming response."""
    index: int
    document_id: str
    title: str
    authors: List[str]
    year: int
    key_claims: List[str] = field(default_factory=list)
    
    @property
    def short_citation(self) -> str:
        """Generate a short citation string."""
        first_author = self.authors[0] if self.authors else "Unknown"
        return f"{first_author} et al. {self.year}"
    
    @property
    def full_citation(self) -> str:
        """Generate a full citation string."""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " et al."
        return f"{authors_str}. ({self.year}). {self.title}"


@dataclass
class Token:
    """Represents a single streamed token."""
    text: str
    is_citation_marker: bool = False
    citation: Optional[Citation] = None
    timestamp: float = field(default_factory=time.time)


class GraphCitationTracer:
    """
    Traces citations through the RushDB property graph.
    
    This class handles:
    - Finding relevant documents via graph traversal
    - Building citation context from related documents
    - Resolving citation markers to graph nodes
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self._citation_cache: Dict[str, Citation] = {}
    
    def find_relevant_documents(self, query: str, limit: int = 5) -> List:
        """
        Find documents relevant to a query using graph traversal.
        
        In a real implementation, this would use semantic search.
        For this tutorial, we use keyword matching.
        """
        # Find all documents
        all_docs = self.db.records.find({
            "labels": ["DOCUMENT"],
            "limit": 100
        })
        
        # Score by relevance (simple keyword matching)
        query_words = set(query.lower().split())
        scored_docs = []
        
        for doc in all_docs.data:
            score = 0
            title = doc.data.get("title", "").lower()
            abstract = doc.data.get("abstract", "").lower()
            key_claims = " ".join(doc.data.get("key_claims", [])).lower()
            
            # Count matching words
            for word in query_words:
                if word in title:
                    score += 3
                if word in abstract:
                    score += 2
                if word in key_claims:
                    score += 1
            
            if score > 0:
                scored_docs.append((score, doc))
        
        # Sort by score and return top results
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:limit]]
    
    def get_citation_chain(self, document_id: str, depth: int = 2) -> List[Dict]:
        """
        Traverse the citation graph to build a citation chain.
        
        Args:
            document_id: The document to trace citations for
            depth: How many levels of citations to retrieve
            
        Returns:
            List of citation chain dictionaries
        """
        chain = []
        visited = set()
        
        def traverse(doc_id: str, current_depth: int):
            if current_depth > depth or doc_id in visited:
                return
            visited.add(doc_id)
            
            # Find this document
            doc = self.db.records.find_by_id(doc_id)
            if not doc:
                return
            
            doc_info = {
                "id": doc.id,
                "title": doc.data.get("title", "Unknown"),
                "depth": current_depth,
                "cited_by": [],
                "cites": []
            }
            
            # Find documents that cite this one
            cited_by = self.db.records.find({
                "labels": ["DOCUMENT"],
                "where": {
                    "CITES": {
                        "$relation": {"type": "CITES", "direction": "in"},
                        "id": doc_id
                    }
                }
            })
            
            for citing_doc in cited_by.data:
                doc_info["cited_by"].append({
                    "id": citing_doc.id,
                    "title": citing_doc.data.get("title", "Unknown")
                })
                traverse(citing_doc.id, current_depth + 1)
            
            # Find documents this one cites
            cites = self.db.records.find({
                "labels": ["DOCUMENT"],
                "where": {
                    "CITES": {
                        "$relation": {"type": "CITES", "direction": "out"},
                        "id": doc_id
                    }
                }
            })
            
            for cited_doc in cites.data:
                doc_info["cites"].append({
                    "id": cited_doc.id,
                    "title": cited_doc.data.get("title", "Unknown")
                })
            
            chain.append(doc_info)
        
        traverse(document_id, 0)
        return chain
    
    def resolve_citation(self, citation_marker: str) -> Optional[Citation]:
        """
        Resolve a citation marker (e.g., [1], [2]) to a Citation object.
        
        Uses cached citations for efficiency.
        """
        # Check cache
        if citation_marker in self._citation_cache:
            return self._citation_cache[citation_marker]
        
        return None
    
    def build_citation_context(self, document) -> Citation:
        """
        Build a Citation object from a document record.
        
        This extracts all relevant metadata for citation formatting.
        """
        citation = Citation(
            index=len(self._citation_cache) + 1,
            document_id=document.id,
            title=document.data.get("title", "Unknown"),
            authors=document.data.get("authors", []),
            year=document.data.get("year", 0),
            key_claims=document.data.get("key_claims", [])
        )
        
        # Cache it
        self._citation_cache[f"[{citation.index}]"] = citation
        
        return citation


class StreamingTokenGenerator:
    """
    Simulates streaming token generation with inline citation markers.
    
    In a production system, this would connect to an LLM API that supports
    streaming responses with structured output.
    """
    
    def __init__(self, citation_tracer: GraphCitationTracer):
        self.citation_tracer = citation_tracer
    
    def generate_response(
        self,
        query: str,
        relevant_docs: List,
        stream: bool = True
    ) -> Iterator[Token]:
        """
        Generate a streaming response with citations.
        
        Args:
            query: The user's query
            relevant_docs: Documents found via graph search
            stream: Whether to stream tokens (True) or return all at once (False)
            
        Yields:
            Token objects representing streamed content
        """
        # Build citations for relevant documents
        citations = []
        for doc in relevant_docs:
            citation = self.citation_tracer.build_citation_context(doc)
            citations.append(citation)
        
        # Generate response template with citation markers
        response_template = self._build_response_template(query, citations)
        
        # Stream tokens
        for token_text in response_template:
            # Check if this is a citation marker
            if re.match(r'\[' + '|'.join(str(c.index) for c in citations) + '\]', token_text):
                citation = self.citation_tracer.resolve_citation(token_text)
                yield Token(
                    text=token_text,
                    is_citation_marker=True,
                    citation=citations[0] if not citation and citations else citation
                )
            else:
                yield Token(text=token_text, is_citation_marker=False)
    
    def _build_response_template(
        self,
        query: str,
        citations: List[Citation]
    ) -> List[str]:
        """
        Build a response template with citation markers.
        
        This simulates what an LLM would generate when citing sources.
        """
        if not citations:
            return ["I couldn't find relevant sources to answer your query."]
        
        # Simple response template
        primary_citation = citations[0]
        secondary_citation = citations[1] if len(citations) > 1 else None
        
        response_parts = [
            f"The {self._extract_topic(query)} mechanism, ",
            f"as described in [{primary_citation.index}: {primary_citation.short_citation}], ",
            "is a fundamental concept in modern AI systems. ",
            "It enables models to process sequential data efficiently.",
        ]
        
        if secondary_citation:
            response_parts.extend([
                " ",
                f"Building on this foundation, [{secondary_citation.index}: {secondary_citation.short_citation}] ",
                "demonstrates how these concepts scale to larger models."
            ])
        
        # Add some more context
        response_parts.extend([
            " ",
            f"Key innovations include: ",
            ", ".join(primary_citation.key_claims[:2]),
            ".",
            " These approaches have become foundational to modern language models."
        ])
        
        return response_parts
    
    def _extract_topic(self, query: str) -> str:
        """Extract the main topic from a query."""
        # Simple extraction - in production, use NLP
        query_lower = query.lower()
        if "attention" in query_lower:
            return "attention"
        elif "transformer" in query_lower:
            return "transformer"
        elif "language model" in query_lower:
            return "language model"
        else:
            return "neural network"


async def main():
    """Main tutorial demonstration."""
    
    print("=" * 60)
    print("Streaming Token Generation with Graph-Traced Citations")
    print("=" * 60)
    print()
    
    # Initialize RushDB
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment")
        print("Please add it to your .env file or set the environment variable.")
        return
    
    db = RushDB(api_key)
    print("[✓] Connected to RushDB")
    
    # Check for data
    existing_docs = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
    if not existing_docs.data:
        print("\n[✗] No documents found in the database.")
        print("Please run `python seed.py` first to populate the knowledge graph.")
        return
    
    print(f"[✓] Found {len(existing_docs.data)} documents in the graph")
    print()
    
    # Initialize components
    tracer = GraphCitationTracer(db)
    generator = StreamingTokenGenerator(tracer)
    
    # Example query
    query = "How does attention mechanism work in transformers?"
    
    print("-" * 60)
    print("QUERY:", query)
    print("-" * 60)
    print()
    
    # Step 1: Find relevant documents via graph traversal
    print("[1] Searching knowledge graph for relevant documents...")
    relevant_docs = tracer.find_relevant_documents(query, limit=3)
    print(f"    Found {len(relevant_docs)} relevant documents:")
    for i, doc in enumerate(relevant_docs, 1):
        title = doc.data.get("title", "Unknown")
        year = doc.data.get("year", "Unknown")
        print(f"    {i}. {title} ({year})")
    print()
    
    # Step 2: Build citations
    print("[2] Building citation metadata from graph...")
    citations = []
    for doc in relevant_docs:
        citation = tracer.build_citation_context(doc)
        citations.append(citation)
        print(f"    Citation [{citation.index}]: {citation.title}")
        print(f"      Authors: {', '.join(citation.authors[:2])}")
        print(f"      Key Claims: {', '.join(citation.key_claims[:2])}")
    print()
    
    # Step 3: Stream tokens with citations
    print("[3] Streaming tokens with inline citations...")
    print("    " + "-" * 50)
    
    streamed_tokens = []
    streamed_text = ""
    
    for token in generator.generate_response(query, relevant_docs):
        # Print token without newline
        print(token.text, end="", flush=True)
        streamed_tokens.append(token)
        streamed_text += token.text
        
        # Simulate async streaming delay
        await asyncio.sleep(0.02)
    
    print()
    print("    " + "-" * 50)
    print(f"    Streamed {len(streamed_tokens)} tokens")
    print()
    
    # Step 4: Demonstrate citation chain tracing
    if relevant_docs:
        print("[4] Tracing citation chains through the graph...")
        primary_doc = relevant_docs[0]
        print(f"    Starting from: {primary_doc.data.get('title')}")
        
        chain = tracer.get_citation_chain(primary_doc.id, depth=2)
        for i, item in enumerate(chain[:3], 1):
            indent = "    " + "  " * item["depth"]
            print(f"{indent}└─ {item['title']}")
            
            if item["cited_by"]:
                for cb in item["cited_by"][:2]:
                    print(f"{indent}  └──▶ {cb['title']}")
        print()
    
    # Step 5: Display resolved citations
    print("[5] Resolved Citations:")
    print("    " + "-" * 50)
    for citation in citations:
        print(f"    [{citation.index}] {citation.full_citation}")
        print(f"        Citations: {len(citation.key_claims)} claims traced")
    print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  Query: {query}")
    print(f"  Documents referenced: {len(citations)}")
    print(f"  Tokens streamed: {len(streamed_tokens)}")
    print(f"  Graph depth traversed: 2")
    print()
    print("  This demonstration showed:")
    print("    • Storing documents as graph nodes in RushDB")
    print("    • Creating citation relationships as directed edges")
    print("    • Graph traversal to find relevant context")
    print("    • Streaming tokens with inline citation markers")
    print("    • Citation chain resolution back to graph nodes")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
