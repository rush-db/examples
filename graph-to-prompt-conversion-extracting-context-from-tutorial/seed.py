#!/usr/bin/env python3
"""
Seed script for the tutorial knowledge graph.
Creates a rich graph with semantic relationships for context extraction demo.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB


def get_db():
    """Initialize RushDB connection."""
    api_key = os.getenv("RUSHDB_API_KEY")
    url = os.getenv("RUSHDB_URL")
    
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Get your API key at https://app.rushdb.com/settings/api-keys")
        sys.exit(1)
    
    if url:
        return RushDB(api_key, url=url)
    return RushDB(api_key)


def seed_tutorial_graph(db: RushDB):
    """
    Create a knowledge graph about software development tutorials.
    
    Graph structure:
    - TUTORIAL (root nodes)
      - CHAPTER (CONTAINS)
        - CONCEPT (EXPLAINS)
          - EXAMPLE (DEMONSTRATES)
    - Cross-references via RELATED_TO, PREREQUISITE, EXTENDS
    """
    print("Seeding tutorial knowledge graph...\n")
    
    # Check if data already exists
    existing = db.records.find({"labels": ["TUTORIAL"], "limit": 1})
    if existing:
        print("Graph already exists. Run 'python main.py' to see the demo.")
        return
    
    # ========== TUTORIALS ==========
    tutorials_data = [
        {
            "title": "Introduction to Graph Databases",
            "slug": "intro-graph-databases",
            "difficulty": "beginner",
            "duration_minutes": 45,
            "tags": ["databases", "graph-theory", "nosql"]
        },
        {
            "title": "Property Graph Modeling",
            "slug": "property-graph-modeling",
            "difficulty": "intermediate",
            "duration_minutes": 60,
            "tags": ["databases", "modeling", "design"]
        },
        {
            "title": "Graph Traversal Algorithms",
            "slug": "graph-traversal-algorithms",
            "difficulty": "advanced",
            "duration_minutes": 90,
            "tags": ["algorithms", "bfs", "dfs", "performance"]
        },
        {
            "title": "Building RAG Systems with Graphs",
            "slug": "rag-systems-graphs",
            "difficulty": "intermediate",
            "duration_minutes": 75,
            "tags": ["ai", "rag", "llm", "embeddings"]
        },
        {
            "title": "Graph Databases in Production",
            "slug": "graphs-production",
            "difficulty": "advanced",
            "duration_minutes": 120,
            "tags": ["devops", "scaling", "monitoring"]
        },
    ]
    
    tutorials = []
    for i, data in enumerate(tutorials_data):
        tutorial = db.records.create(label="TUTORIAL", data=data)
        tutorials.append(tutorial)
        if (i + 1) % 5 == 0:
            print(f"  ✓ Created {i + 1}/5 TUTORIAL records")
    print(f"  ✓ Created {len(tutorials)} TUTORIAL records")
    
    # ========== CHAPTERS ==========
    chapters_data = [
        # Graph Databases chapters
        {"tutorial_idx": 0, "title": "What is a Graph Database?", "order": 1, "summary": "Understanding the fundamentals of graph data structures"},
        {"tutorial_idx": 0, "title": "Nodes and Edges", "order": 2, "summary": "Core building blocks of graph databases"},
        {"tutorial_idx": 0, "title": "Query Languages", "order": 3, "summary": "Cypher, Gremlin, and graph query fundamentals"},
        # Property Graph Modeling chapters
        {"tutorial_idx": 1, "title": "Schema Design Principles", "order": 1, "summary": "Designing effective graph schemas"},
        {"tutorial_idx": 1, "title": "Relationship Cardinality", "order": 2, "summary": "One-to-many, many-to-many patterns in graphs"},
        {"tutorial_idx": 1, "title": "Anti-patterns", "order": 3, "summary": "Common mistakes in graph modeling"},
        # Graph Traversal chapters
        {"tutorial_idx": 2, "title": "Breadth-First Search", "order": 1, "summary": "Level-by-level graph exploration"},
        {"tutorial_idx": 2, "title": "Depth-First Search", "order": 2, "summary": "Deep path exploration techniques"},
        {"tutorial_idx": 2, "title": "Shortest Path Algorithms", "order": 3, "summary": "Dijkstra, A* and pathfinding"},
        # RAG Systems chapters
        {"tutorial_idx": 3, "title": "Context Windows and Token Limits", "order": 1, "summary": "Understanding LLM context constraints"},
        {"tutorial_idx": 3, "title": "Knowledge Graph Construction", "order": 2, "summary": "Building graphs from unstructured data"},
        {"tutorial_idx": 3, "title": "Graph-Enhanced Retrieval", "order": 3, "summary": "Using graphs to improve RAG accuracy"},
        # Production chapters
        {"tutorial_idx": 4, "title": "Query Optimization", "order": 1, "summary": "Optimizing graph queries for performance"},
        {"tutorial_idx": 4, "title": "Indexing Strategies", "order": 2, "summary": "Creating effective indexes on graph properties"},
        {"tutorial_idx": 4, "title": "Monitoring and Observability", "order": 3, "summary": "Tracking graph database health"},
    ]
    
    chapters = []
    for i, data in enumerate(chapters_data):
        chapter = db.records.create(
            label="CHAPTER",
            data={
                "title": data["title"],
                "order": data["order"],
                "summary": data["summary"]
            }
        )
        chapters.append((chapter, data["tutorial_idx"]))
        if (i + 1) % 5 == 0:
            print(f"  ✓ Created {i + 1}/{len(chapters_data)} CHAPTER records")
    print(f"  ✓ Created {len(chapters)} CHAPTER records")
    
    # Attach chapters to tutorials
    with db.transactions.begin() as tx:
        for chapter, tut_idx in chapters:
            db.records.attach(
                source=tutorials[tut_idx],
                target=chapter,
                options={"type": "CONTAINS", "direction": "out"},
                transaction=tx
            )
    print(f"  ✓ Attached {len(chapters)} CHAPTERs to TUTORIALs")
    
    # ========== CONCEPTS ==========
    concepts_data = [
        # Database fundamentals
        {"name": "Property Graph", "category": "fundamentals", "description": "A graph structure where nodes and edges can have properties"},
        {"name": "Directed Edge", "category": "fundamentals", "description": "An edge with a directional relationship between nodes"},
        {"name": "Node Label", "category": "fundamentals", "description": "Type classification for graph nodes"},
        {"name": "Relationship Type", "category": "fundamentals", "description": "Semantic meaning of connections between nodes"},
        # Modeling concepts
        {"name": "Schema Design", "category": "modeling", "description": "Process of defining node types and relationships"},
        {"name": "Cardinality Patterns", "category": "modeling", "description": "Patterns for one-to-one, one-to-many, many-to-many relationships"},
        {"name": "Normalization", "category": "modeling", "description": "Reducing redundancy in graph design"},
        {"name": "Traversal Efficiency", "category": "modeling", "description": "Designing for fast graph traversals"},
        # Algorithm concepts
        {"name": "Breadth-First Search (BFS)", "category": "algorithms", "description": "Level-order graph traversal algorithm"},
        {"name": "Depth-First Search (DFS)", "category": "algorithms", "description": "Deep-path-first graph traversal algorithm"},
        {"name": "Shortest Path", "category": "algorithms", "description": "Finding minimum-cost paths between nodes"},
        {"name": "PageRank", "category": "algorithms", "description": "Algorithm for measuring node importance"},
        # RAG concepts
        {"name": "Context Window", "category": "rag", "description": "Maximum input size for LLM processing"},
        {"name": "Token Budget", "category": "rag", "description": "Limiting context to fit within token limits"},
        {"name": "Knowledge Extraction", "category": "rag", "description": "Extracting structured knowledge from text"},
        {"name": "Semantic Search", "category": "rag", "description": "Vector-based similarity search over content"},
        {"name": "Context Prioritization", "category": "rag", "description": "Ranking retrieved content by relevance"},
        # Production concepts
        {"name": "Query Optimization", "category": "production", "description": "Improving query performance through planning"},
        {"name": "Index Strategies", "category": "production", "description": "Using indexes to speed up graph lookups"},
        {"name": "Performance Monitoring", "category": "production", "description": "Tracking query latency and throughput"},
    ]
    
    concepts = []
    for i, data in enumerate(concepts_data):
        concept = db.records.create(
            label="CONCEPT",
            data={
                "name": data["name"],
                "category": data["category"],
                "description": data["description"]
            }
        )
        concepts.append(concept)
        if (i + 1) % 10 == 0:
            print(f"  ✓ Created {i + 1}/{len(concepts_data)} CONCEPT records")
    print(f"  ✓ Created {len(concepts)} CONCEPT records")
    
    # Attach concepts to chapters
    chapter_to_concepts = {
        0: [0, 1, 2],       # What is a Graph DB: Property Graph, Directed Edge, Node Label
        1: [0, 2, 3],       # Nodes and Edges: Property Graph, Directed Edge, Relationship Type
        2: [3],             # Query Languages: Relationship Type
        3: [4, 5, 6],       # Schema Design: Schema Design, Cardinality, Normalization
        4: [5, 6, 7],       # Relationship Cardinality: Cardinality, Normalization, Traversal
        5: [7],             # Anti-patterns: Traversal Efficiency
        6: [8, 9],          # BFS: BFS, DFS
        7: [9, 10],         # DFS: DFS, Shortest Path
        8: [10, 11],        # Shortest Path: Shortest Path, PageRank
        9: [12, 13],        # Context Windows: Context Window, Token Budget
        10: [14, 15],       # Knowledge Graph: Knowledge Extraction, Semantic Search
        11: [15, 16],       # Graph-Enhanced Retrieval: Semantic Search, Context Prioritization
        12: [17, 18],       # Query Optimization: Query Optimization, Index Strategies
        13: [18, 19],       # Indexing: Index Strategies, Performance Monitoring
        14: [19],           # Monitoring: Performance Monitoring
    }
    
    with db.transactions.begin() as tx:
        for chapter_idx, concept_indices in chapter_to_concepts.items():
            chapter = chapters[chapter_idx][0]
            for concept_idx in concept_indices:
                db.records.attach(
                    source=chapter,
                    target=concepts[concept_idx],
                    options={"type": "EXPLAINS", "direction": "out"},
                    transaction=tx
                )
    print("  ✓ Attached CONCEPTs to CHAPTERs via EXPLAINs")
    
    # ========== EXAMPLES ==========
    examples_data = [
        {"title": "Creating a Simple Property Graph", "language": "python", "code": "nodes = ['User', 'Post', 'Comment']\nrelationships = [('User', 'CREATED', 'Post'), ('User', 'WRITING', 'Post')]"},
        {"title": "Directed vs Undirected Edges", "language": "python", "code": "# Directed: User -> followed_by -> Follower\n# Undirected: User <-> friends <-> User"},
        {"title": "Labeling Nodes by Type", "language": "cypher", "code": "MATCH (n) WHERE n:User OR n:Admin RETURN n"},
        {"title": "Schema for Social Network", "language": "python", "code": "schema = {\n  'User': {'name', 'email'},\n  'FOLLOWS': {'since'}\n}"},
        {"title": "One-to-Many Pattern", "language": "cypher", "code": "MATCH (u:User)-[:HAS_ADDRESS]->(a:Address)\nWHERE u.id = $userId"},
        {"title": "Many-to-Many Pattern", "language": "cypher", "code": "MATCH (u:User)-[:INTERESTED_IN]->(t:Topic)<-[:WORKS_ON]-(p:Project)"},
        {"title": "BFS Implementation", "language": "python", "code": "from collections import deque\ndef bfs(start):\n  queue = deque([start])\n  while queue:\n    node = queue.popleft()\n    yield node\n    queue.extend(node.neighbors)"},
        {"title": "DFS with Recursion", "language": "python", "code": "def dfs(node, visited=None):\n  if visited is None: visited = set()\n  if node in visited: return\n  visited.add(node)\n  for neighbor in node.neighbors:\n    dfs(neighbor, visited)"},
        {"title": "Dijkstra's Algorithm", "language": "python", "code": "import heapq\ndef dijkstra(graph, start):\n  dist = {start: 0}\n  pq = [(0, start)]\n  while pq:\n    d, u = heapq.heappop(pq)\n    if d > dist.get(u, inf): continue\n    # process edges\n  return dist"},
        {"title": "Token Budget Calculator", "language": "python", "code": "import tiktoken\ndef count_tokens(text, model='gpt-4'):\n  enc = tiktoken.encoding_for_model(model)\n  return len(enc.encode(text))"},
        {"title": "Priority-based Context Pruning", "language": "python", "code": "def prune_context(items, max_tokens):\n  # Sort by priority descending\n  sorted_items = sorted(items, key=lambda x: x.priority, reverse=True)\n  selected = []\n  current_tokens = 0\n  for item in sorted_items:\n    if current_tokens + item.tokens <= max_tokens:\n      selected.append(item)\n      current_tokens += item.tokens\n  return selected"},
        {"title": "Entity Extraction Pipeline", "language": "python", "code": "from openai import OpenAI\n\ndef extract_entities(text):\n  client = OpenAI()\n  response = client.chat.completions.create(\n    model='gpt-4',\n    messages=[{'role': 'system', 'content': 'Extract entities...'}, {'role': 'user', 'content': text}]\n  )\n  return parse_response(response)"},
    ]
    
    examples = []
    for i, data in enumerate(examples_data):
        example = db.records.create(
            label="EXAMPLE",
            data={
                "title": data["title"],
                "language": data["language"],
                "code_snippet": data["code"]
            }
        )
        examples.append(example)
        if (i + 1) % 6 == 0:
            print(f"  ✓ Created {i + 1}/{len(examples_data)} EXAMPLE records")
    print(f"  ✓ Created {len(examples)} EXAMPLE records")
    
    # Attach examples to concepts
    concept_to_examples = {
        0: [0],      # Property Graph example
        1: [1],      # Directed Edge example
        2: [2],      # Node Label example
        3: [2, 3],   # Relationship Type examples
        4: [3],      # Schema Design example
        5: [4, 5],   # Cardinality examples
        8: [6],      # BFS example
        9: [7],      # DFS example
        10: [8],     # Shortest Path example
        12: [9],     # Context Window example
        13: [9],     # Token Budget example
        16: [10],    # Context Prioritization example
        14: [11],    # Knowledge Extraction example
        17: [8],     # Query Optimization uses Dijkstra
    }
    
    with db.transactions.begin() as tx:
        for concept_idx, example_indices in concept_to_examples.items():
            concept = concepts[concept_idx]
            for example_idx in example_indices:
                db.records.attach(
                    source=concept,
                    target=examples[example_idx],
                    options={"type": "DEMONSTRATES", "direction": "out"},
                    transaction=tx
                )
    print("  ✓ Attached EXAMPLEs to CONCEPTs via DEMONSTRATES")
    
    # ========== CROSS-RELATIONSHIPS ==========
    
    # Prerequisites between tutorials
    with db.transactions.begin() as tx:
        # Graph Traversal requires Graph Databases knowledge
        db.records.attach(
            source=tutorials[2],  # Graph Traversal
            target=tutorials[0],  # Intro to Graph DBs
            options={"type": "PREREQUISITE", "direction": "in"},
            transaction=tx
        )
        # RAG Systems requires Property Graph Modeling
        db.records.attach(
            source=tutorials[3],  # RAG Systems
            target=tutorials[1],  # Property Graph Modeling
            options={"type": "PREREQUISITE", "direction": "in"},
            transaction=tx
        )
        # Production requires Traversal knowledge
        db.records.attach(
            source=tutorials[4],  # Production
            target=tutorials[2],  # Graph Traversal
            options={"type": "PREREQUISITE", "direction": "in"},
            transaction=tx
        )
    print("  ✓ Created PREREQUISITE relationships between TUTORIALs")
    
    # Related concepts (cross-links for richer context)
    with db.transactions.begin() as tx:
        # Traversal relates to Query Optimization
        db.records.attach(
            source=concepts[7],   # Traversal Efficiency
            target=concepts[17],  # Query Optimization
            options={"type": "RELATED_TO", "direction": "out"},
            transaction=tx
        )
        # Token Budget relates to Context Prioritization
        db.records.attach(
            source=concepts[13],  # Token Budget
            target=concepts[16],  # Context Prioritization
            options={"type": "RELATED_TO", "direction": "out"},
            transaction=tx
        )
        # Semantic Search relates to Knowledge Extraction
        db.records.attach(
            source=concepts[15],  # Semantic Search
            target=concepts[14],  # Knowledge Extraction
            options={"type": "RELATED_TO", "direction": "out"},
            transaction=tx
        )
    print("  ✓ Created RELATED_TO relationships between CONCEPTs")
    
    # Example extends (building on previous concepts)
    with db.transactions.begin() as tx:
        db.records.attach(
            source=examples[7],  # DFS example
            target=examples[6],   # BFS example
            options={"type": "EXTENDS", "direction": "out"},
            transaction=tx
        )
        db.records.attach(
            source=examples[10],  # Priority pruning
            target=examples[9],   # Token budget
            options={"type": "EXTENDS", "direction": "out"},
            transaction=tx
        )
    print("  ✓ Created EXTENDS relationships between EXAMPLEs")
    
    print("\n=== Seeding Complete ===")
    print(f"  Total TUTORIALs: {len(tutorials)}")
    print(f"  Total CHAPTERs: {len(chapters)}")
    print(f"  Total CONCEPTs: {len(concepts)}")
    print(f"  Total EXAMPLEs: {len(examples)}")
    print(f"  Relationship types: CONTAINS, EXPLAINs, DEMONSTRATES,")
    print(f"                      PREREQUISITE, RELATED_TO, EXTENDS")


if __name__ == "__main__":
    db = get_db()
    seed_tutorial_graph(db)
