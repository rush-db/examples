# Query Decomposition: Splitting Complex Questions via Graph Exploration

A practical tutorial demonstrating how to decompose complex questions into simpler sub-queries using RushDB's property graph model. This technique is essential for building intelligent Q&A systems, chatbots, and AI agents that need to answer multi-part questions.

## What is Query Decomposition?

Query decomposition is the technique of breaking down a complex question into simpler, atomic sub-questions that can be answered independently, then combining the results. In a graph database context, this maps naturally to:

1. **Identifying entities** in the question
2. **Finding relevant graph patterns** for each sub-question
3. **Traversing relationships** to collect related data
4. **Aggregating results** to form a complete answer

## Why RushDB?

RushDB's property graph model makes query decomposition elegant:
- **Records** represent entities (actors, movies, directors)
- **Relationships** represent connections (ACTED_IN, DIRECTED, BELONGS_TO)
- **Property indexing** enables fast lookups by entity attributes
- **Graph traversal** via relationship filtering answers multi-hop questions

## Project Structure

```
query-decomposition-splitting-complex-questions-vi-tutorial/
├── README.md           # This file
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── seed.py              # Generate and import graph data
└── main.py              # Tutorial code demonstrating query decomposition
```

## Prerequisites

- Python 3.9+
- A RushDB account ([sign up free](https://app.rushdb.com))
- RushDB API key

## Setup

1. **Clone and navigate to the project:**
   ```bash
   cd query-decomposition-splitting-complex-questions-vi-tutorial
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

4. **Generate sample graph data:**
   ```bash
   python seed.py
   ```
   This creates a movie knowledge graph with ~30 records including:
   - 8 Movies
   - 10 Actors
   - 4 Directors
   - 4 Genres
   - Various relationships (ACTED_IN, DIRECTED, BELONGS_TO, AWARDED)

5. **Run the tutorial:**
   ```bash
   python main.py
   ```

## Expected Output

```
========================================
QUERY DECOMPOSITION TUTORIAL
========================================

--- Example 1: Simple Entity Lookup ---
Question: "Who is Tom Hanks?"
Decomposition: Identify the entity and fetch basic properties
Result: Tom Hanks is an American actor born on 1956-07-09

--- Example 2: Relationship Traversal ---
Question: "What movies has Tom Hanks acted in?"
Decomposition: Find all movies connected via ACTED_IN relationship
Result: 3 movies found: Forrest Gump, The Green Mile, Cast Away

--- Example 3: Multi-Hop Traversal ---
Question: "Who directed Tom Hanks' movies?"
Decomposition:
  Step 1: Find Tom Hanks' movies
  Step 2: Find directors of those movies
Result: Robert Zemeckis directed 2 of his movies, Frank Darabont directed 1

--- Example 4: Complex Decomposition ---
Question: "Which actors have won awards for drama movies from the 90s?"
Decomposition:
  Step 1: Find drama movies from the 90s
  Step 2: Find actors in those movies
  Step 3: Check which actors have awards
Result: 4 actors found matching criteria

--- Example 5: Aggregating Multi-Source Data ---
Question: "Compare the movies directed by Robert Zemeckis"
Decomposition:
  Step 1: Find movies directed by Zemeckis
  Step 2: Fetch all actors in those movies
  Step 3: Aggregate ratings and awards
Result: 2 movies compared with 4 unique actors

--- Example 6: Chain Decomposition ---
Question: "Find co-actors who have also worked with directors of Tom Hanks' movies"
Decomposition:
  Step 1: Get Tom Hanks' movies
  Step 2: Get directors of those movies
  Step 3: Find other movies by those directors
  Step 4: Get actors in those other movies
Result: 6 co-actors found across director collaborations
```

## Key Concepts Demonstrated

### 1. Entity Identification
Using `db.records.find()` with simple `where` clauses to locate specific entities.

### 2. Direct Relationship Traversal
Using relationship-based filtering in the `where` clause to find connected records:
```python
{"where": {"ACTOR": {"name": "Tom Hanks"}}}
```

### 3. Multi-Step Decomposition
Breaking complex questions into sequential queries, using results from one query as input to the next.

### 4. Result Aggregation
Collecting and summarizing results from multiple sub-queries.

## The Graph Model

```
    ACTOR ──ACTED_IN──> MOVIE <──DIRECTED── DIRECTOR
       │                                        │
       │                BELONGS_TO              │
       v                        v               v
    AWARD ───────────> GENRE    MOVIE ──AWARDED
```

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB GitHub Examples](https://github.com/rush-db/examples)
- [Property Graph Concepts](https://docs.rushdb.com/concepts)

## License

MIT License - feel free to use and modify for your projects.
