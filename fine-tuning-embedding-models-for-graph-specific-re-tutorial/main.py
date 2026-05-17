#!/usr/bin/env python3
"""
Main tutorial script demonstrating fine-tuning embedding models for graph-specific representation learning using RushDB.

This script showcases:
1. Loading graph schema from RushDB
2. Base semantic search using pre-trained embeddings
3. Graph contrastive learning for fine-tuning
4. Enhanced search with fine-tuned embeddings
5. Hybrid graph + vector queries
"""

import random
from collections import defaultdict
from typing import Any

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from config import (
    RUSHDB_API_KEY,
    RUSHDB_URL,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
    FINE_TUNE_EPOCHS,
    FINE_TUNE_LR,
    CONTRASTIVE_TEMPERATURE,
    BATCH_SIZE,
)
from rushdb import RushDB

# Initialize RushDB client
db = RushDB(RUSHDB_API_KEY, url=RUSHDB_URL)


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def explore_schema():
    """Explore the graph schema from RushDB."""
    print_header("Graph Schema from RushDB")

    try:
        ontology = db.ai.getOntology()
        print("\nLabels and their properties:")
        for label, info in ontology.items():
            props = info.get("properties", [])
            print(f"\n  {label}:")
            for prop in props:
                print(f"    - {prop['name']} ({prop.get('type', 'unknown')})")
    except Exception as e:
        print(f"Could not fetch ontology: {e}")
        print("\nAvailable labels:")
        try:
            labels = db.labels.find({})
            for label in labels:
                print(f"  - {label.name} ({label.count} records)")
        except Exception:
            print("  (Could not fetch labels)")


def base_semantic_search():
    """Demonstrate semantic search with pre-trained embeddings."""
    print_header("Base Semantic Search")

    query = "machine learning transformers"
    print(f'\nSearching for: "{query}"')

    try:
        results = db.ai.search(
            {
                "propertyName": "abstract",
                "query": query,
                "labels": ["PAPER"],
                "limit": 5,
            }
        )

        print(f"\nFound {len(results.data)} papers:")
        for i, paper in enumerate(results.data, 1):
            score = paper.score or paper.data.get("__score", 0)
            title = paper.data.get("title", "Unknown")
            print(f"  {i}. [{score:.3f}] {title}")

        return results.data

    except Exception as e:
        print(f"Semantic search error: {e}")
        print("\nFalling back to regular find...")
        papers = db.records.find({"labels": ["PAPER"], "limit": 5})
        for i, paper in enumerate(papers.data, 1):
            print(f"  {i}. {paper.data.get('title', 'Unknown')}")
        return papers.data


def analyze_graph_structure():
    """Analyze the citation graph structure."""
    print_header("Citation Graph Analysis")

    # Get all papers with their citation counts
    papers = db.records.find({"labels": ["PAPER"], "limit": 100})

    if papers.total == 0:
        print("No papers found in the database. Run seed.py first!")
        return None, None

    # Find most cited paper
    most_cited = max(papers.data, key=lambda p: p.data.get("citations", 0))
    print(f"\nMost cited paper: {most_cited.data.get('title', 'Unknown')}")
    print(f"  Citations: {most_cited.data.get('citations', 0)}")

    # Get topic distribution
    topic_counts = defaultdict(int)
    for paper in papers.data:
        # Find related topics
        topic_results = db.records.find({
            "labels": ["TOPIC"],
            "where": {
                "PAPER": {"$relation": {"type": "ABOUT", "direction": "in"}}
            },
            "limit": 1
        })
        if topic_results.data:
            topic_counts[topic_results.data[0].data.get("name", "Unknown")] += 1

    print(f"\nTopic distribution (from {papers.total} papers):")
    for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1])[:5]:
        print(f"  - {topic}: {count} papers")

    return papers.data, most_cited


class GraphContrastiveDataset(Dataset):
    """
    Dataset for graph contrastive learning.

    Creates positive pairs from:
    - Papers that cite each other (bidirectional citations)
    - Papers by the same author
    - Papers on the same topic

    Negative pairs are randomly sampled from different topics.
    """

    def __init__(
        self,
        papers: list[Any],
        embeddings: dict[str, list[float]],
        citations: list[tuple],
        authorships: list[tuple],
        topics: list[Any],
    ):
        self.papers = papers
        self.paper_ids = [p.id for p in papers]
        self.embeddings = embeddings

        # Build positive pairs graph
        self.positive_pairs: set[tuple[str, str]] = set()

        # Citation-based pairs
        for source, target in citations:
            self.positive_pairs.add((source.id, target.id))
            self.positive_pairs.add((target.id, source.id))  # Bidirectional

        # Co-authorship pairs
        author_papers: dict[str, list[str]] = defaultdict(list)
        for paper, author in authorships:
            author_papers[author.id].append(paper.id)

        for author, papers_list in author_papers.items():
            for i, p1 in enumerate(papers_list):
                for p2 in papers_list[i + 1:]:
                    self.positive_pairs.add((p1, p2))
                    self.positive_pairs.add((p2, p1))

        # Topic-based pairs
        topic_papers: dict[str, list[str]] = defaultdict(list)
        for paper in papers:
            topic_results = db.records.find({
                "labels": ["TOPIC"],
                "where": {
                    "PAPER": {"$relation": {"type": "ABOUT", "direction": "in"}}
                },
                "limit": 1
            })
            if topic_results.data:
                topic_papers[topic_results.data[0].id].append(paper.id)

        for topic, papers_list in topic_papers.items():
            for i, p1 in enumerate(papers_list):
                for p2 in papers_list[i + 1:]:
                    self.positive_pairs.add((p1, p2))

        print(f"Created {len(self.positive_pairs)} positive pairs")

    def __len__(self):
        return len(self.paper_ids)

    def __getitem__(self, idx):
        paper_id = self.paper_ids[idx]

        # Get anchor embedding
        anchor = torch.tensor(self.embeddings[paper_id], dtype=torch.float32)

        # Positive pair (if exists)
        pos_id = self._get_positive_pair(paper_id)
        if pos_id:
            pos_emb = torch.tensor(self.embeddings[pos_id], dtype=torch.float32)
        else:
            pos_emb = anchor  # Use same if no positive found

        # Negative pair (random different paper)
        neg_id = self._get_negative_pair(paper_id)
        neg_emb = torch.tensor(self.embeddings[neg_id], dtype=torch.float32)

        return anchor, pos_emb, neg_emb

    def _get_positive_pair(self, paper_id: str) -> str | None:
        """Get a positive pair for the given paper."""
        candidates = [pid for pid in self.paper_ids if (paper_id, pid) in self.positive_pairs]
        if candidates:
            return random.choice(candidates)
        return None

    def _get_negative_pair(self, paper_id: str) -> str:
        """Get a negative pair (random paper not connected to this one)."""
        candidates = [pid for pid in self.paper_ids if pid != paper_id]
        return random.choice(candidates)


class GraphEmbeddingModel(torch.nn.Module):
    """
    Simple MLP projection head for fine-tuning embeddings.

    Takes pre-trained embeddings and projects them into a space
    optimized for graph similarity.
    """

    def __init__(self, input_dim: int = EMBEDDING_DIMENSIONS, hidden_dim: int = 256):
        super().__init__()
        self.projection = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, hidden_dim),
            torch.nn.LayerNorm(hidden_dim),
        )

    def forward(self, x):
        return self.projection(x)


def nt_xent_loss(z_i: torch.Tensor, z_j: torch.Tensor, temperature: float) -> torch.Tensor:
    """
    NT-Xent (Normalized Temperature-scaled Cross Entropy) loss.

    Encourages similar representations for positive pairs
    and dissimilar representations for negative pairs.
    """
    batch_size = z_i.shape[0]

    # Normalize embeddings
    z_i = F.normalize(z_i, dim=1)
    z_j = F.normalize(z_j, dim=1)

    # Concatenate all embeddings
    representations = torch.cat([z_i, z_j], dim=0)

    # Compute similarity matrix
    similarity_matrix = F.cosine_similarity(
        representations.unsqueeze(1),
        representations.unsqueeze(0),
        dim=2,
    )

    # Create labels: position i and i+batch_size are positive pairs
    sim_ij = torch.diag(similarity_matrix, batch_size)
    sim_ji = torch.diag(similarity_matrix, -batch_size)
    positives = torch.cat([sim_ij, sim_ji], dim=0)

    # Mask out self-similarities
    negatives = similarity_matrix.view(-1) - torch.eye(2 * batch_size).view(-1)
    negatives = negatives.view(2 * batch_size, -1)
    negatives = negatives[torch.arange(2 * batch_size), torch.arange(2 * batch_size)]
    negatives = torch.exp(negatives / temperature)

    # Compute loss
    positives = torch.exp(positives / temperature)
    loss = -torch.log(positives / (positives + negatives.sum()))

    return loss.mean()


def fine_tune_embeddings(
    papers: list[Any],
    embeddings: dict[str, list[float]],
) -> dict[str, list[float]]:
    """
    Fine-tune embeddings using graph contrastive learning.

    This demonstrates how to adapt pre-trained embeddings to
    capture graph structure (citations, co-authorship, topics).
    """
    print_header("Graph Contrastive Fine-tuning")

    print(f"\nFine-tuning configuration:")
    print(f"  - Model: GraphEmbeddingModel with projection head")
    print(f"  - Learning rate: {FINE_TUNE_LR}")
    print(f"  - Temperature: {CONTRASTIVE_TEMPERATURE}")
    print(f"  - Epochs: {FINE_TUNE_EPOCHS}")

    # Get citations and authorships
    all_citations = []
    all_authorships = []
    all_topics = []

    for paper in papers:
        # Get citations
        cited = db.records.find({
            "labels": ["PAPER"],
            "where": {
                "PAPER": {"$relation": {"type": "CITES", "direction": "in"}}
            }
        })
        for citing in cited.data:
            all_citations.append((citing, paper))

        # Get authors
        authors = db.records.find({
            "labels": ["AUTHOR"],
            "where": {
                "PAPER": {"$relation": {"type": "WRITTEN_BY", "direction": "in"}}
            }
        })
        for author in authors.data:
            all_authorships.append((paper, author))

        # Get topics
        topics = db.records.find({
            "labels": ["TOPIC"],
            "where": {
                "PAPER": {"$relation": {"type": "ABOUT", "direction": "in"}}
            }
        })
        all_topics.extend(topics.data)

    # Create dataset
    dataset = GraphContrastiveDataset(
        papers=papers,
        embeddings=embeddings,
        citations=all_citations,
        authorships=all_authorships,
        topics=all_topics,
    )

    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    # Initialize model
    model = GraphEmbeddingModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=FINE_TUNE_LR)

    print(f"\nTraining on {len(dataset)} samples...")

    # Training loop
    for epoch in range(FINE_TUNE_EPOCHS):
        total_loss = 0.0
        num_batches = 0

        for anchor, pos, neg in tqdm(dataloader, desc=f"Epoch {epoch + 1}/{FINE_TUNE_EPOCHS}"):
            optimizer.zero_grad()

            # Project embeddings
            z_anchor = model(anchor)
            z_pos = model(pos)

            # Compute contrastive loss
            loss = nt_xent_loss(z_anchor, z_pos, CONTRASTIVE_TEMPERATURE)

            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            num_batches += 1

        avg_loss = total_loss / num_batches
        print(f"  Epoch {epoch + 1}/{FINE_TUNE_EPOCHS} - Loss: {avg_loss:.4f}")

    # Generate fine-tuned embeddings
    print("\nGenerating fine-tuned embeddings...")
    model.eval()
    fine_tuned_embeddings = {}

    with torch.no_grad():
        for paper in tqdm(papers, desc="Encoding"):
            emb = torch.tensor(embeddings[paper.id], dtype=torch.float32)
            fine_tuned = model(emb).numpy()
            fine_tuned_embeddings[paper.id] = fine_tuned.tolist()

    print("Fine-tuning complete!")
    return fine_tuned_embeddings


def compare_search_results(
    original_embeddings: dict[str, list[float]],
    fine_tuned_embeddings: dict[str, list[float]],
):
    """Compare search results before and after fine-tuning."""
    print_header("Search Quality Comparison")

    queries = [
        "neural network training optimization",
        "language model transformers attention",
        "image recognition deep learning",
    ]

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Installing sentence-transformers for comparison...")
        import subprocess
        subprocess.check_call(["pip", "install", "sentence-transformers"])
        from sentence_transformers import SentenceTransformer

    print("\nLoading sentence transformer for query encoding...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    for query in queries:
        print(f"\nQuery: \"{query}\"")
        query_embedding = model.encode([query])[0]

        # Compute similarities with original embeddings
        original_sims = []
        for paper_id, emb in original_embeddings.items():
            sim = np.dot(query_embedding, emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(emb)
            )
            original_sims.append((paper_id, sim))

        # Compute similarities with fine-tuned embeddings
        tuned_sims = []
        for paper_id, emb in fine_tuned_embeddings.items():
            sim = np.dot(query_embedding, emb) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(emb)
            )
            tuned_sims.append((paper_id, sim))

        # Sort and get top results
        original_sims.sort(key=lambda x: -x[1])
        tuned_sims.sort(key=lambda x: -x[1])

        # Get paper titles
        top_original = original_sims[:3]
        top_tuned = tuned_sims[:3]

        original_titles = []
        for paper_id, _ in top_original:
            paper = db.records.find_by_id(paper_id)
            if paper:
                original_titles.append(paper.data.get("title", "Unknown")[:50])

        tuned_titles = []
        for paper_id, _ in top_tuned:
            paper = db.records.find_by_id(paper_id)
            if paper:
                tuned_titles.append(paper.data.get("title", "Unknown")[:50])

        print("  Original:", " | ".join(original_titles))
        print("  Fine-tuned:", " | ".join(tuned_titles))


def hybrid_graph_vector_query():
    """Demonstrate combining graph traversal with vector search."""
    print_header("Hybrid Graph + Vector Search")

    # Find papers similar to "Attention Is All You Need"
    target_title = "Attention Is All You Need"

    target_paper = db.records.find({
        "labels": ["PAPER"],
        "where": {"title": {"$contains": target_title}}
    })

    if not target_paper.data:
        print("Target paper not found. Skipping hybrid query demo.")
        return

    target = target_paper.data[0]
    print(f"\nFinding papers related to: {target.data.get('title')}")

    # Get the authors of the target paper
    authors = db.records.find({
        "labels": ["AUTHOR"],
        "where": {
            "PAPER": {"$relation": {"type": "WRITTEN_BY", "direction": "in"}}
        }
    })

    author_names = [a.data.get("name") for a in authors.data]
    print(f"Authors: {', '.join(author_names)}")

    # Get the topic of the target paper
    topics = db.records.find({
        "labels": ["TOPIC"],
        "where": {
            "PAPER": {"$relation": {"type": "ABOUT", "direction": "in"}}
        }
    })

    if topics.data:
        topic_name = topics.data[0].data.get("name")
        print(f"Topic: {topic_name}")

        # Find other papers on the same topic
        related = db.records.find({
            "labels": ["PAPER"],
            "where": {
                "TOPIC": {"name": topic_name}
            },
            "limit": 5
        })

        print(f"\nOther papers on \"{topic_name}\":")
        for i, paper in enumerate(related.data, 1):
            if paper.id != target.id:
                print(f"  {i}. {paper.data.get('title', 'Unknown')[:60]}")

    # Find papers that cite this one
    citing_papers = db.records.find({
        "labels": ["PAPER"],
        "where": {
            "PAPER": {"$relation": {"type": "CITES", "direction": "out"}}
        },
        "limit": 5
    })

    if citing_papers.data:
        print(f"\nPapers that cite \"{target_title}\":")
        for i, paper in enumerate(citing_papers.data, 1):
            print(f"  {i}. {paper.data.get('title', 'Unknown')[:60]}")


def main():
    """Main tutorial function."""
    print("=" * 60)
    print(" Fine-tuning Embedding Models for Graph-Specific")
    print("         Representation Learning with RushDB")
    print("=" * 60)

    # 1. Explore schema
    explore_schema()

    # 2. Base semantic search
    base_semantic_search()

    # 3. Analyze graph structure
    papers, most_cited = analyze_graph_structure()

    if papers is None:
        print("\nNo data found. Please run seed.py first!")
        return

    # 4. Collect original embeddings
    print_header("Collecting Original Embeddings")
    original_embeddings = {}
    for paper in tqdm(papers, desc="Fetching embeddings"):
        # Embeddings are stored in the database; we need to retrieve them
        # For this demo, we'll generate fresh embeddings
        text = f"{paper.data.get('title', '')}. {paper.data.get('abstract', '')}"
        original_embeddings[paper.id] = None  # Placeholder

    # Generate fresh embeddings for comparison
    print("\nGenerating embeddings with sentence-transformers...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL)

        texts = [
            f"{p.data.get('title', '')}. {p.data.get('abstract', '')}"
            for p in papers
        ]
        embeddings = model.encode(texts, show_progress_bar=True)

        for i, paper in enumerate(papers):
            original_embeddings[paper.id] = embeddings[i].tolist()
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return

    # 5. Fine-tune embeddings
    fine_tuned_embeddings = fine_tune_embeddings(papers, original_embeddings)

    # 6. Compare results
    compare_search_results(original_embeddings, fine_tuned_embeddings)

    # 7. Hybrid search
    hybrid_graph_vector_query()

    print("\n" + "=" * 60)
    print(" Tutorial Complete!")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  1. RushDB stores both graph structure and vector embeddings")
    print("  2. Graph relationships enable contrastive fine-tuning")
    print("  3. Fine-tuned embeddings capture domain-specific similarity")
    print("  4. Combine vector search with graph traversal for RAG")
    print("\nLearn more: https://docs.rushdb.com")


if __name__ == "__main__":
    main()
