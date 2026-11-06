# Building a Multi-Turn Dialogue Manager with RushDB State Tracking

A comprehensive tutorial demonstrating how to build a production-ready multi-turn dialogue manager using RushDB as a stateful memory layer. This example shows how to track conversation context, maintain session state, and retrieve relevant history across multiple turns.

## What This Project Demonstrates

- **Session Management**: Creating and tracking conversation sessions with metadata
- **Message History**: Storing user/assistant exchanges with full context
- **State Tracking**: Maintaining conversation state (intents, entities, flags)
- **Context Retrieval**: Loading relevant history for multi-turn understanding
- **Relationship Traversal**: Using RushDB's graph relationships for conversation threads
- **Transaction Safety**: ACID-compliant multi-record operations

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    User     │────▶│   Session   │────▶│   Message   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Context   │     │   Context   │
                    └─────────────┘     └─────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account (free tier at https://rushdb.com)
- `pip` for package management

## Setup

1. **Clone and navigate to the project**:
   ```bash
   cd building-a-multi-turn-dialogue-manager-with-rushdb-tutorial
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your RUSHDB_API_KEY
   ```

4. **Seed the database (optional but recommended)**:
   ```bash
   python seed.py
   ```

## Running the Demo

```bash
python main.py
```

## Expected Output

The demo will:
1. Initialize a new dialogue session
2. Add multiple conversation turns
3. Track conversation state (detected intents, extracted entities)
4. Demonstrate context retrieval for follow-up questions
5. Show relationship-based queries for conversation history

## Project Structure

```
├── main.py          # Main demo script
├── seed.py           # Generates sample conversation data
├── requirements.txt  # Python dependencies
├── .env.example      # Environment template
└── README.md         # This file
```

## Key RushDB Patterns Used

- **Records as Sessions/Messages**: Each conversation component is a typed record
- **Relationships**: Sessions link to Messages; Messages link to Context
- **Transactions**: Atomic creation of session + initial message pairs
- **Graph Queries**: Using label-based filtering for conversation retrieval

## API Reference

- RushDB Python SDK: https://docs.rushdb.com/sdk/python
- Full API docs: https://docs.rushdb.com

## License

MIT
