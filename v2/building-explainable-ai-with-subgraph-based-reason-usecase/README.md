# Building Explainable AI with Subgraph-Based Reasoning Traces

A complete medical diagnosis support system using RushDB's property graph + vector search to provide explainable AI recommendations. This project demonstrates how to retrieve relevant case studies and trace exactly which patient similarity paths led to a suggested diagnosis.

## What This Demonstrates

- **Schema Design**: How to model medical records as a property graph with nodes for Patients, Symptoms, MedicalCases, ResearchPapers, and Diagnoses
- **Vector Embedding**: Using semantic search on research papers to find relevant clinical literature
- **Subgraph Reasoning**: Building complete reasoning chains that explain AI recommendations
- **Explainability**: Contrasting black-box approaches with full transparency for regulated industries
- **Performance**: Measuring the latency cost of explainable reasoning vs. simple results

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Explainable Diagnosis System                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Patient    │───▶│   Medical   │◀──▶│  Research    │       │
│  │    Node      │    │    Case     │    │   Paper      │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Symptom   │◀───│    Has       │    │   Supports   │       │
│  │    Node     │    │   Symptom    │    │              │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                          │                                      │
│                          ▼                                      │
│                   ┌──────────────┐                               │
│                   │  Diagnosis  │                               │
│                   │    Node      │                               │
│                   └──────────────┘                               │
│                          │                                      │
│                          ▼                                      │
│                   ┌──────────────┐                               │
│                   │ Similarity   │                               │
│                   │   Edge       │                               │
│                   │(Vector-based)│                               │
│                   └──────────────┘                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Python 3.9+
- A RushDB account ([sign up free](https://app.rushdb.com))
- `sentence-transformers` for embeddings (or OpenAI if preferred)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# RushDB API credentials
RUSHDB_API_KEY=your_api_key_here

# Optional: OpenAI for embeddings (uses sentence-transformers by default)
# OPENAI_API_KEY=your_openai_key_here

# Embedding model
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 3. Seed the Database

This project includes a medical case dataset. Run the seed script to populate the database:

```bash
python seed.py
```

The seed script will create:
- 15 historical medical cases with diagnoses
- 20 symptoms linked to cases
- 10 research papers with vector embeddings
- Similarity edges between cases

### 4. Run the Demo

```bash
python main.py
```

## Project Structure

```
building-explainable-ai-with-subgraph-based-reason-usecase/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── seed.py            # Mock medical data generator
└── main.py            # Main demonstration script
```

## How It Works

### The Explainable Diagnosis Flow

1. **New Patient Intake**: System receives a new patient with presenting symptoms
2. **Vector Search**: Finds similar historical cases using embedded symptom descriptions
3. **Subgraph Construction**: Builds the complete reasoning trace showing:
   - Which historical cases were similar
   - Which specific symptoms matched
   - What outcomes those cases had
   - Which research papers support the diagnosis
4. **Transparent Output**: Returns diagnosis with full explanation chain

### Developer View vs. Clinician View

**Developer View** (full graph):
```
Reasoning Trace:
├── Similar Case #12 (score: 0.87)
│   ├── Patient: 58M, Hypertension
│   ├── Symptoms matched: ["chest pain", "shortness of breath", "fatigue"]
│   └── Outcome: Acute MI → Recovered after stenting
├── Similar Case #7 (score: 0.82)
│   ├── Patient: 62F, Diabetes
│   ├── Symptoms matched: ["chest pain", "shortness of breath"]
│   └── Outcome: Unstable Angina → Medication management
└── Supporting Research: "Early Intervention in ACS" (relevance: 0.91)
```

**Clinician View** (summarized):
```
SUGGESTED DIAGNOSIS: Acute Coronary Syndrome (ACS)
CONFIDENCE: 78%
KEY EVIDENCE:
  • 2 highly similar cases with same diagnosis
  • Symptom profile matches in 85% of features
  • Supported by current clinical guidelines
RECOMMENDED ACTIONS:
  • ECG within 10 minutes
  • Troponin levels
  • Cardiology consult
```

## RushDB Schema

### Labels

| Label | Description |
|-------|-------------|
| `PATIENT` | Patient demographic records |
| `MEDICAL_CASE` | Historical case records with outcomes |
| `SYMPTOM` | Individual symptom descriptors |
| `DIAGNOSIS` | Possible diagnoses |
| `RESEARCH_PAPER` | Clinical research with vector embeddings |

### Relationship Types

| Type | From → To | Description |
|------|-----------|-------------|
| `HAS_SYMPTOM` | PATIENT/MEDICAL_CASE → SYMPTOM | Links symptoms to records |
| `SIMILAR_TO` | MEDICAL_CASE → MEDICAL_CASE | Vector-similarity connections |
| `RESULTED_IN` | MEDICAL_CASE → DIAGNOSIS | Case outcome |
| `SUPPORTS` | RESEARCH_PAPER → DIAGNOSIS | Literature support |
| `ASSOCIATED_WITH` | SYMPTOM → DIAGNOSIS | Symptom-diagnosis correlation |

## Performance Considerations

| Approach | Latency | Explainability |
|----------|---------|----------------|
| Simple vector search | ~50ms | None (black box) |
| + Subgraph traversal | ~150ms | Full trace |
| + Research paper search | ~250ms | + Literature support |


The subgraph approach adds ~100ms latency but provides complete transparency — essential for regulated industries like healthcare where every AI decision must be explainable.

## Key Code Patterns

### Creating a Patient with Symptoms

```sdk
from rushdb import RushDB

db = RushDB(os.getenv("RUSHDB_API_KEY"))

# Create patient
patient = db.records.create(
    label="PATIENT",
    data={
        "name": "John Doe",
        "age": 65,
        "sex": "M",
        "medicalHistory": ["hypertension", "hyperlipidemia"]
    }
)

# Create and link symptoms
with db.transactions.begin() as tx:
    for symptom_name in ["chest pain", "diaphoresis", "nausea"]:
        symptom = db.records.create(
            label="SYMPTOM",
            data={"name": symptom_name, "severity": "moderate"},
            transaction=tx
        )
        db.records.attach(
            source=patient,
            target=symptom,
            options={"type": "MANIFESTS"},
            transaction=tx
        )
```

### Vector Search for Similar Cases

```sdk
# Find cases with similar symptom presentations
similar_cases = db.ai.search({
    "propertyName": "symptomDescription",
    "query": "chest pain radiating to left arm with shortness of breath",
    "labels": ["MEDICAL_CASE"],
    "limit": 5
})

for case in similar_cases.data:
    print(f"Similarity: {case.score:.2f}")
    print(f"Case: {case.data['summary']}")
```


### Building the Reasoning Subgraph

```sdk
def explain_diagnosis(patient, db):
    """Build complete reasoning subgraph for a diagnosis."""
    
    # 1. Find similar historical cases
    symptom_text = " ".join([s.data["name"] for s in get_patient_symptoms(patient, db)])
    similar_cases = db.ai.search({
        "propertyName": "symptomDescription",
        "query": symptom_text,
        "labels": ["MEDICAL_CASE"],
        "limit": 3
    })
    
    # 2. Get diagnoses from similar cases
    diagnoses = db.records.find({
        "labels": ["DIAGNOSIS"],
        "where": {
            "MEDICAL_CASE": {"$relation": {"type": "RESULTED_IN", "direction": "in"}}
        }
    })
    
    # 3. Find supporting research
    top_diagnosis = get_most_common_diagnosis(diagnoses)
    supporting_papers = db.ai.search({
        "propertyName": "abstract",
        "query": top_diagnosis.data["name"],
        "labels": ["RESEARCH_PAPER"],
        "limit": 2
    })
    
    return build_explanation_subgraph(patient, similar_cases, top_diagnosis, supporting_papers)
```


## In Regulated Industries

This pattern is essential for:

- **Healthcare**: FDA requires explainability for AI-assisted diagnosis
- **Finance**: Regulators need to audit credit/insurance decisions
- **Legal**: Every algorithmic decision must be defensible
- **Insurance**: Audit trails for claims decisions

RushDB's graph model naturally captures the reasoning chain as first-class data, making compliance straightforward.

## Further Reading

- [RushDB Documentation](https://docs.rushdb.com)
- [Property Graphs for Explainable AI](https://rushdb.com/docs)
- [Vector Search Best Practices](https://rushdb.com/docs)

## License

MIT - See LICENSE file for details.
