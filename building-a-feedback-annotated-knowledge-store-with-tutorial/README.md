# Building a Feedback-Annotated Knowledge Store with Human-in-the-Loop Corrections

This project demonstrates how to build a knowledge management system with feedback-driven corrections using RushDB. It showcases a complete workflow where knowledge entries can be reviewed, corrected, and improved by human annotators.

## What This Project Demonstrates

- **Creating knowledge entries** with rich metadata (topic, content, source)
- **Recording human feedback** with correction types, severity, and status
- **Tracking feedback history** for each knowledge entry
- **Human-in-the-loop workflow** — submitting, reviewing, and applying corrections
- **Querying feedback patterns** to identify knowledge gaps or common errors
- **Using relationships** to connect corrections to original entries

## Prerequisites

- Python 3.9+
- A RushDB account (free tier works)
- Your RushDB API token

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your RUSHDB_API_TOKEN
```

### 3. Seed the Database

This creates sample knowledge entries and feedback data for demonstration:

```bash
python seed.py
```

The seed script will:
- Create 15 knowledge entries across different topics
- Add 20+ feedback corrections with varying types and statuses
- Establish relationships between feedback and entries

### 4. Run the Demo

```bash
python main.py
```

## Expected Output

The demo will:
1. Show all pending feedback requiring attention
2. Demonstrate applying a correction to a knowledge entry
3. Query entries with the most feedback (quality issues)
4. Display feedback breakdown by type and status
5. Show a workflow example: submit → review → apply correction

## Project Structure

```
.
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py             # Generates mock knowledge + feedback data
└── main.py             # Main demo script
```

## Key RushDB Patterns Used

| Pattern | Description |
|---------|-------------|
| `db.records.create()` | Create knowledge entries and feedback records |
| `db.records.attach()` | Link feedback to knowledge entries |
| `db.records.find()` | Query entries by labels, filters, relationships |
| `db.records.update()` | Apply corrections to knowledge entries |
| Transactions | Batch create feedback + attach in one transaction |

## Understanding the Data Model

```
KNOWLEDGE_ENTRY ──(HAS_FEEDBACK)──> FEEDBACK
     │                            │
     └── topic, content           └── type, correction, status
         source, created_at           reviewer, submitted_at
```

**KNOWLEDGE_ENTRY** — A unit of stored knowledge with content, topic classification, and source attribution.

**FEEDBACK** — Human correction or suggestion attached to a knowledge entry. Types include:
- `correction` — factual error that needs fixing
- `clarification` — content is ambiguous and needs explanation
- `addition` — missing information that should be added
- `outdated` — content is no longer accurate

**FEEDBACK_STATUS** — Workflow state: `pending` → `reviewed` → `applied` / `rejected`

## Customization

To adapt this for your use case:
1. Define your knowledge entry schema (topics, content properties)
2. Extend feedback types to match your review workflow
3. Add automated embedding generation for semantic search
4. Implement notification triggers when new feedback arrives

## Learn More

- [RushDB Documentation](https://docs.rushdb.com)
- [RushDB Python SDK](https://docs.rushdb.com/sdk/python)
- [GitHub Example](https://github.com/rush-db/examples)
