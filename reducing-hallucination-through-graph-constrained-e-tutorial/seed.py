#!/usr/bin/env python3
"""
Seed script: Populates the knowledge graph with claims, sources, verifications, and concepts.

This demonstrates a realistic knowledge graph for ML interpretability research.
All data is programmatically generated — no external downloads required.
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env and fill in your key.")

db = RushDB(API_KEY)

# Seed data: Sources (authoritative documents)
SOURCES = [
    {
        "id": "src-001",
        "title": "A Unified Approach to Interpreting Model Predictions",
        "authors": ["Lundberg & Lee"],
        "publication": "NeurIPS 2017",
        "url": "arxiv.org/papers/1705.07874",
        "year": 2017,
        "reliability_score": 0.95,
        "type": "peer_reviewed",
        "abstract": "We present SHAP (SHapley Additive exPlanations), a unified approach to explaining predictions."
    },
    {
        "id": "src-002",
        "title": "Why Should I Trust You?: Explaining the Predictions of Any Classifier",
        "authors": ["Ribeiro, Singh & Guestrin"],
        "publication": "KDD 2016",
        "url": "arxiv.org/papers/1602.04938",
        "year": 2016,
        "reliability_score": 0.93,
        "type": "peer_reviewed",
        "abstract": "While various explanation methods have been proposed, it remains unclear which method provides the most trustworthy explanations."
    },
    {
        "id": "src-003",
        "title": "Neural Network Verification: A Practical Guide",
        "authors": ["Katz et al."],
        "publication": "ACM Computing Surveys",
        "url": "arxiv.org/papers/2108.07817",
        "year": 2021,
        "reliability_score": 0.91,
        "type": "peer_reviewed",
        "abstract": "Techniques for formally verifying neural network properties."
    },
    {
        "id": "src-004",
        "title": "On the Faithfulness of Attention Explanations",
        "authors": ["Jain & Wallace"],
        "publication": "NAACL 2019",
        "url": "arxiv.org/papers/1906.03752",
        "year": 2019,
        "reliability_score": 0.88,
        "type": "peer_reviewed",
        "abstract": "We investigate the relationship between attention weights and feature importance."
    },
    {
        "id": "src-005",
        "title": "Benchmarking Neural Network Interpretability",
        "authors": ["Yang et al."],
        "publication": "ICML 2021 Workshop",
        "url": "openreview.net/forum?id=benchmark-2021",
        "year": 2021,
        "reliability_score": 0.86,
        "type": "workshop",
        "abstract": "Standardized benchmarks for comparing interpretability methods."
    }
]

# Seed data: Claims (factual statements from sources)
CLAIMS = [
    {
        "id": "clm-001",
        "text": "SHAP values provide theoretically sound and consistent feature attributions",
        "subject": "SHAP",
        "predicate": "provides consistent feature attribution",
        "source_ref": "src-001",
        "verified": True,
        "confidence": 0.95
    },
    {
        "id": "clm-002",
        "text": "SHAP is the only explanation method that satisfies local accuracy, missingness, and consistency axioms",
        "subject": "SHAP",
        "predicate": "satisfies all three axioms",
        "source_ref": "src-001",
        "verified": True,
        "confidence": 0.92
    },
    {
        "id": "clm-003",
        "text": "LIME explanations are locally faithful but may be unstable across perturbations",
        "subject": "LIME",
        "predicate": "has unstable perturbations",
        "source_ref": "src-002",
        "verified": True,
        "confidence": 0.88
    },
    {
        "id": "clm-004",
        "text": "Attention weights do not directly correspond to feature importance in Transformers",
        "subject": "Attention weights",
        "predicate": "not feature importance",
        "source_ref": "src-004",
        "verified": True,
        "confidence": 0.85
    },
    {
        "id": "clm-005",
        "text": "Formal verification methods can prove neural network robustness properties",
        "subject": "Formal verification",
        "predicate": "proves robustness",
        "source_ref": "src-003",
        "verified": True,
        "confidence": 0.90
    },
    {
        "id": "clm-006",
        "text": "Gradient-based explanations scale well to large models but miss input-level interactions",
        "subject": "Gradient-based methods",
        "predicate": "miss input interactions",
        "source_ref": "src-005",
        "verified": True,
        "confidence": 0.82
    },
    {
        "id": "clm-007",
        "text": "SHAP KernelExplainer provides model-agnostic interpretation for any function",
        "subject": "SHAP KernelExplainer",
        "predicate": "model-agnostic",
        "source_ref": "src-001",
        "verified": True,
        "confidence": 0.94
    },
    {
        "id": "clm-008",
        "text": "Perturbation-based explanations like LIME are computationally expensive for large inputs",
        "subject": "LIME",
        "predicate": "computationally expensive",
        "source_ref": "src-002",
        "verified": True,
        "confidence": 0.87
    },
    {
        "id": "clm-009",
        "text": "Global feature importance can be derived by aggregating local SHAP values",
        "subject": "SHAP",
        "predicate": "aggregates to global importance",
        "source_ref": "src-001",
        "verified": True,
        "confidence": 0.93
    },
    {
        "id": "clm-010",
        "text": "There exists no universally best interpretability method across all model types",
        "subject": "Interpretability methods",
        "predicate": "no universal best",
        "source_ref": "src-005",
        "verified": True,
        "confidence": 0.89
    },
    {
        "id": "clm-011",
        "text": "Attention mechanisms in Transformers primarily capture positional relationships",
        "subject": "Attention mechanisms",
        "predicate": "positional relationships",
        "source_ref": "src-004",
        "verified": False,  # This claim is intentionally unverified for demo
        "confidence": 0.71
    },
    {
        "id": "clm-012",
        "text": "Counterfactual explanations help users understand model decision boundaries",
        "subject": "Counterfactual explanations",
        "predicate": "explain decision boundaries",
        "source_ref": "src-002",
        "verified": True,
        "confidence": 0.86
    },
    {
        "id": "clm-013",
        "text": "SMV (SmoothMax) regularization improves verification tractability",
        "subject": "SMV regularization",
        "predicate": "improves tractability",
        "source_ref": "src-003",
        "verified": True,
        "confidence": 0.78
    },
    {
        "id": "clm-014",
        "text": "SHAP TreeExplainer runs in O(TL) time where T is tree depth and L is number of features",
        "subject": "SHAP TreeExplainer",
        "predicate": "O(TL) complexity",
        "source_ref": "src-001",
        "verified": True,
        "confidence": 0.91
    },
    {
        "id": "clm-015",
        "text": "Feature attribution methods outperform activation-based methods on benchmark datasets",
        "subject": "Feature attribution",
        "predicate": "outperforms activation methods",
        "source_ref": "src-005",
        "verified": True,
        "confidence": 0.84
    }
]

# Seed data: Concepts (topic entities)
CONCEPTS = [
    {"id": "con-001", "name": "SHAP", "category": "method", "description": "SHapley Additive exPlanations"},
    {"id": "con-002", "name": "LIME", "category": "method", "description": "Local Interpretable Model-agnostic Explanations"},
    {"id": "con-003", "name": "Feature Attribution", "category": "technique", "description": "Methods that assign importance to input features"},
    {"id": "con-004", "name": "Model Interpretability", "category": "field", "description": "The study of making model decisions understandable"},
    {"id": "con-005", "name": "Attention Mechanisms", "category": "technique", "description": "Neural network components that focus on relevant input parts"},
    {"id": "con-006", "name": "Formal Verification", "category": "technique", "description": "Mathematical proof of neural network properties"},
    {"id": "con-007", "name": "Local Explanations", "category": "scope", "description": "Explanations for individual predictions"},
    {"id": "con-008", "name": "Global Explanations", "category": "scope", "description": "Explanations for overall model behavior"}
]

# Seed data: Verifications (trust assessments)
VERIFICATIONS = [
    {
        "id": "ver-001",
        "assessor": "automated",
        "method": "axiomatic_verification",
        "result": "passed",
        "confidence_score": 0.95,
        "claim_ref": "clm-001",
        "source_ref": "src-001"
    },
    {
        "id": "ver-002",
        "assessor": "human_expert",
        "method": "peer_review",
        "result": "confirmed",
        "confidence_score": 0.92,
        "claim_ref": "clm-002",
        "source_ref": "src-001"
    },
    {
        "id": "ver-003",
        "assessor": "replication",
        "method": "experiment",
        "result": "confirmed",
        "confidence_score": 0.88,
        "claim_ref": "clm-003",
        "source_ref": "src-002"
    },
    {
        "id": "ver-004",
        "assessor": "peer_review",
        "method": "citation_analysis",
        "result": "contested",
        "confidence_score": 0.72,
        "claim_ref": "clm-004",
        "source_ref": "src-004"
    },
    {
        "id": "ver-005",
        "assessor": "formal_proof",
        "method": "smt_solver",
        "result": "proven",
        "confidence_score": 0.97,
        "claim_ref": "clm-005",
        "source_ref": "src-003"
    },
    {
        "id": "ver-006",
        "assessor": "benchmarking",
        "method": "quantitative_eval",
        "result": "confirmed",
        "confidence_score": 0.85,
        "claim_ref": "clm-006",
        "source_ref": "src-005"
    },
    {
        "id": "ver-007",
        "assessor": "automated",
        "method": "theoretical_proof",
        "result": "confirmed",
        "confidence_score": 0.94,
        "claim_ref": "clm-007",
        "source_ref": "src-001"
    },
    {
        "id": "ver-008",
        "assessor": "replication",
        "method": "experiment",
        "result": "confirmed",
        "confidence_score": 0.87,
        "claim_ref": "clm-008",
        "source_ref": "src-002"
    },
    {
        "id": "ver-009",
        "assessor": "mathematical",
        "method": "derivation",
        "result": "confirmed",
        "confidence_score": 0.93,
        "claim_ref": "clm-009",
        "source_ref": "src-001"
    },
    {
        "id": "ver-010",
        "assessor": "meta_analysis",
        "method": "benchmark_comparison",
        "result": "confirmed",
        "confidence_score": 0.89,
        "claim_ref": "clm-010",
        "source_ref": "src-005"
    },
    {
        "id": "ver-011",
        "assessor": "replication",
        "method": "experiment",
        "result": "inconclusive",
        "confidence_score": 0.65,
        "claim_ref": "clm-011",
        "source_ref": "src-004"
    },
    {
        "id": "ver-012",
        "assessor": "expert_panel",
        "method": "qualitative_review",
        "result": "confirmed",
        "confidence_score": 0.86,
        "claim_ref": "clm-012",
        "source_ref": "src-002"
    }
]


def clear_existing_data():
    """Remove all existing records of our seed types (idempotent cleanup)."""
    print("[1] Clearing existing seed data...")
    
    labels_to_clear = ["SOURCE", "CLAIM", "CONCEPT", "VERIFICATION"]
    
    for label in labels_to_clear:
        try:
            result = db.records.find({"labels": [label], "limit": 100})
            if result.total > 0:
                ids = [r.id for r in result.data]
                for bid in ids:
                    db.records.delete(record_id=bid)
                print(f"    - Cleared {len(ids)} {label} records")
        except Exception as e:
            print(f"    - {label}: no records to clear (or error: {e})")
    
    print("    ✓ Cleanup complete\n")


def seed_sources():
    """Create SOURCE records for authoritative documents."""
    print("[2] Seeding SOURCE records...")
    created = {}
    
    for source in SOURCES:
        record = db.records.create(
            label="SOURCE",
            data={
                "external_id": source["id"],
                "title": source["title"],
                "authors": source["authors"],
                "publication": source["publication"],
                "url": source["url"],
                "year": source["year"],
                "reliability_score": source["reliability_score"],
                "type": source["type"],
                "abstract": source["abstract"]
            }
        )
        created[source["id"]] = record
        print(f"    - Created SOURCE: {source['title'][:50]}...")
    
    print(f"    ✓ Created {len(created)} sources\n")
    return created


def seed_claims(sources_map):
    """Create CLAIM records linked to sources."""
    print("[3] Seeding CLAIM records...")
    created = {}
    
    for claim in CLAIMS:
        # Create the claim record
        record = db.records.create(
            label="CLAIM",
            data={
                "external_id": claim["id"],
                "text": claim["text"],
                "subject": claim["subject"],
                "predicate": claim["predicate"],
                "verified": claim["verified"],
                "confidence": claim["confidence"]
            }
        )
        created[claim["id"]] = record
        
        # Link claim to source via MAKES_CLAIM relationship
        source_record = sources_map.get(claim["source_ref"])
        if source_record:
            db.records.attach(
                source=source_record,
                target=record,
                options={"type": "MAKES_CLAIM"}
            )
        
        print(f"    - Created CLAIM: {claim['text'][:50]}...")
    
    print(f"    ✓ Created {len(created)} claims\n")
    return created


def seed_concepts():
    """Create CONCEPT records for topic organization."""
    print("[4] Seeding CONCEPT records...")
    created = {}
    
    for concept in CONCEPTS:
        record = db.records.create(
            label="CONCEPT",
            data={
                "external_id": concept["id"],
                "name": concept["name"],
                "category": concept["category"],
                "description": concept["description"]
            }
        )
        created[concept["id"]] = record
        print(f"    - Created CONCEPT: {concept['name']}")
    
    print(f"    ✓ Created {len(created)} concepts\n")
    return created


def seed_verifications(claims_map, sources_map):
    """Create VERIFICATION records linking claims to sources."""
    print("[5] Seeding VERIFICATION records...")
    created = {}
    
    for verification in VERIFICATIONS:
        claim_record = claims_map.get(verification["claim_ref"])
        source_record = sources_map.get(verification["source_ref"])
        
        if not claim_record or not source_record:
            print(f"    ! Skipping {verification['id']}: missing claim or source")
            continue
        
        record = db.records.create(
            label="VERIFICATION",
            data={
                "external_id": verification["id"],
                "assessor": verification["assessor"],
                "method": verification["method"],
                "result": verification["result"],
                "confidence_score": verification["confidence_score"]
            }
        )
        created[verification["id"]] = record
        
        # Link VERIFICATION to CLAIM via SUPPORTS
        db.records.attach(
            source=record,
            target=claim_record,
            options={"type": "SUPPORTS"}
        )
        
        # Link SOURCE to VERIFICATION via ATTESTS
        db.records.attach(
            source=source_record,
            target=record,
            options={"type": "ATTESTS"}
        )
        
        print(f"    - Created VERIFICATION: {verification['method']} -> {verification['result']}")
    
    print(f"    ✓ Created {len(created)} verifications\n")
    return created


def create_semantic_relationships(claims_map, concepts_map):
    """Link claims to concepts they address."""
    print("[6] Creating semantic relationships (CLAIM -> CONCEPT)...")
    
    # Map concepts by name for matching
    concept_by_name = {c["name"]: cid for c, cid in 
                       zip([c for c in CONCEPTS], concepts_map.values())}
    
    claim_concept_links = [
        ("clm-001", "con-001"), ("clm-001", "con-003"),  # SHAP -> SHAP, Feature Attribution
        ("clm-002", "con-001"),  # SHAP axioms
        ("clm-003", "con-002"), ("clm-003", "con-003"),  # LIME -> LIME, Feature Attribution
        ("clm-004", "con-005"),  # Attention weights
        ("clm-005", "con-006"),  # Formal verification
        ("clm-006", "con-003"), ("clm-006", "con-007"),  # Gradient methods
        ("clm-007", "con-001"), ("clm-007", "con-003"),  # SHAP KernelExplainer
        ("clm-008", "con-002"), ("clm-008", "con-007"),  # LIME efficiency
        ("clm-009", "con-001"), ("clm-009", "con-008"),  # SHAP global
        ("clm-010", "con-004"),  # Universal interpretability
        ("clm-011", "con-005"),  # Attention mechanisms
        ("clm-012", "con-007"),  # Counterfactual local
        ("clm-013", "con-006"),  # SMV verification
        ("clm-014", "con-001"),  # SHAP complexity
        ("clm-015", "con-003"),  # Feature attribution benchmark
    ]
    
    links_created = 0
    for claim_id, concept_id in claim_concept_links:
        claim_rec = claims_map.get(claim_id)
        concept_rec = concepts_map.get(concept_id)
        if claim_rec and concept_rec:
            db.records.attach(
                source=claim_rec,
                target=concept_rec,
                options={"type": "ADDRESSES"}
            )
            links_created += 1
    
    print(f"    ✓ Created {links_created} claim-concept links\n")


def create_dependency_relationships(claims_map):
    """Create DEPENDS_ON relationships between claims."""
    print("[7] Creating dependency relationships (CLAIM -> CLAIM)...")
    
    # Some claims depend on others for logical chains
    dependencies = [
        ("clm-002", "clm-001"),  # Axioms claim depends on consistency claim
        ("clm-009", "clm-001"),  # Global SHAP depends on local SHAP
        ("clm-007", "clm-001"),  # KernelExplainer depends on SHAP theory
    ]
    
    links_created = 0
    for dependent_id, prerequisite_id in dependencies:
        dependent = claims_map.get(dependent_id)
        prerequisite = claims_map.get(prerequisite_id)
        if dependent and prerequisite:
            db.records.attach(
                source=dependent,
                target=prerequisite,
                options={"type": "DEPENDS_ON"}
            )
            links_created += 1
    
    print(f"    ✓ Created {links_created} dependency links\n")


def print_summary():
    """Print a summary of seeded data."""
    print("[8] Seeding Complete - Summary:\n")
    
    result = db.labels.find({})
    for label_result in result:
        print(f"    - {label_result.name}: {label_result.count} records")
    
    print("\n✓ Knowledge graph ready for graph-constrained retrieval!\n")


def main():
    """Run the complete seed process."""
    print("\n" + "=" * 60)
    print("KNOWLEDGE GRAPH SEEDING SCRIPT")
    print("=" * 60 + "\n")
    
    try:
        # Clear any existing seed data (idempotent)
        clear_existing_data()
        
        # Seed all record types
        sources_map = seed_sources()
        claims_map = seed_claims(sources_map)
        concepts_map = seed_concepts()
        seed_verifications(claims_map, sources_map)
        
        # Create relationships
        create_semantic_relationships(claims_map, concepts_map)
        create_dependency_relationships(claims_map)
        
        # Print summary
        print_summary()
        
        return True
        
    except Exception as e:
        print(f"\n✗ Seeding failed: {e}")
        raise


if __name__ == "__main__":
    main()
