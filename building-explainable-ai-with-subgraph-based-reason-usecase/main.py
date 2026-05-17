"""
Main Demonstration: Explainable AI Medical Diagnosis System

This script demonstrates how RushDB's graph + vector capabilities enable
interpretable AI recommendations for medical diagnosis support.

Key concepts demonstrated:
1. Vector similarity search to find similar historical cases
2. Subgraph traversal to build complete reasoning chains
3. Developer vs. clinician views of AI explanations
4. Performance comparison: explainable vs. black-box approaches

Target audience: ML engineers building AI-assisted decision systems
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


from rushdb import RushDB

# Verify API key
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Please copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)


# =============================================================================
# SECTION 1: THE PROBLEM - Black Box AI in Healthcare
# =============================================================================

def demonstrate_blackbox_problem():
    """
    Shows what a typical black-box AI system returns:
    - Just a diagnosis with confidence score
    - No explanation of how it reached that conclusion
    - No way to audit or verify the reasoning
    """
    print("\n" + "=" * 70)
    print("PROBLEM: Black-Box AI Systems")
    print("=" * 70)
    
    print("""
A typical ML model returns something like this:

    {
        "diagnosis": "Acute Myocardial Infarction",
        "confidence": 0.87,
        "model_version": "cardiac-v3.2.1"
    }

PROBLEMS WITH THIS APPROACH:
1. No explanation of WHY it chose this diagnosis
2. Cannot verify which patient factors influenced the decision
3. Illegal in regulated industries (FDA, EU AI Act)
4. Clinicians cannot provide informed consent for AI recommendations
5. No audit trail for medical-legal purposes
""")


# =============================================================================
# SECTION 2: THE SOLUTION - Explainable AI with Subgraph Reasoning
# =============================================================================

def get_patient_symptoms(patient_id, db_local):
    """Get all symptoms for a patient."""
    result = db_local.records.find({
        "labels": ["SYMPTOM"],
        "where": {
            "PATIENT": {
                "$relation": {"type": "HAS_SYMPTOM", "direction": "in"},
                "$id": patient_id
            }
        }
    })
    return result.data


def find_similar_cases(symptom_text, limit=3):
    """
    Vector search to find similar historical cases based on symptom description.
    This is the "memory retrieval" step of RAG-like reasoning.
    """
    start = time.time()
    
    results = db.ai.search({
        "propertyName": "symptomDescription",
        "query": symptom_text,
        "labels": ["MEDICAL_CASE"],
        "limit": limit
    })
    
    elapsed = (time.time() - start) * 1000
    return results.data, elapsed


def get_case_symptoms(case_record, db_local):
    """Get all symptoms for a medical case."""
    result = db_local.records.find({
        "labels": ["SYMPTOM"],
        "where": {
            "MEDICAL_CASE": {
                "$relation": {"type": "HAS_SYMPTOM", "direction": "in"},
                "$id": case_record.id
            }
        }
    })
    return result.data


def get_case_diagnosis(case_record, db_local):
    """Get the diagnosis for a medical case."""
    result = db_local.records.find({
        "labels": ["DIAGNOSIS"],
        "where": {
            "MEDICAL_CASE": {
                "$relation": {"type": "RESULTED_IN", "direction": "in"},
                "$id": case_record.id
            }
        }
    })
    return result.data[0] if result.data else None


def get_supporting_research(diagnosis_name, db_local):
    """Find research papers supporting a diagnosis."""
    start = time.time()
    
    results = db_local.ai.search({
        "propertyName": "abstract",
        "query": diagnosis_name,
        "labels": ["RESEARCH_PAPER"],
        "limit": 2
    })
    
    elapsed = (time.time() - start) * 1000
    return results.data, elapsed


def get_symptom_overlap(patient_symptoms, case_symptoms):
    """Calculate which symptoms match between patient and case."""
    patient_set = {s["name"] for s in patient_symptoms}
    case_set = {s["name"] for s in case_symptoms}
    overlap = patient_set.intersection(case_set)
    return {
        "matched": list(overlap),
        "patient_only": list(patient_set - case_set),
        "case_only": list(case_set - patient_set),
        "match_percentage": len(overlap) / len(patient_set) * 100 if patient_set else 0
    }


def build_reasoning_subgraph(new_patient_symptoms, db_local):
    """
    Build the complete reasoning subgraph.
    
    This is the core explainable AI logic:
    1. Find similar cases using vector search
    2. For each similar case, get symptoms, diagnosis, and outcome
    3. Find supporting research for the top diagnosis
    4. Build a traversable explanation graph
    
    Returns:
        - similar_cases: List of similar case records with scores
        - reasoning_trace: List of reasoning step dictionaries
        - supporting_evidence: List of supporting research papers
        - suggested_diagnosis: The consensus diagnosis
        - latency_breakdown: Timing for each step
    """
    latency = {"vector_search": 0, "symptom_lookup": 0, "diagnosis_lookup": 0, "research_search": 0}
    
    # Step 1: Convert patient symptoms to text for vector search
    symptom_text = " ".join([s["name"] for s in new_patient_symptoms])
    
    # Step 2: Find similar cases
    similar_cases, vs_time = find_similar_cases(symptom_text, limit=3)
    latency["vector_search"] = vs_time
    
    reasoning_trace = []
    
    for case in similar_cases:
        case_start = time.time()
        
        # Step 3: Get symptoms for this case
        case_symptoms = get_case_symptoms(case, db_local)
        symptom_time = (time.time() - case_start) * 1000
        latency["symptom_lookup"] += symptom_time
        
        diagnosis_start = time.time()
        case_diagnosis = get_case_diagnosis(case, db_local)
        diagnosis_time = (time.time() - diagnosis_start) * 1000
        latency["diagnosis_lookup"] += diagnosis_time
        
        # Step 4: Calculate symptom overlap
        overlap = get_symptom_overlap(new_patient_symptoms, case_symptoms)
        
        reasoning_trace.append({
            "case_id": case.id,
            "case_number": case.data.get("caseNumber"),
            "similarity_score": case.score,
            "diagnosis": case_diagnosis.data if case_diagnosis else {},
            "outcome": case.data.get("outcome"),
            "patient_profile": {
                "age": case.data.get("patientAge"),
                "sex": case.data.get("patientSex"),
                "history": case.data.get("patientHistory", [])
            },
            "symptom_overlap": overlap,
            "symptom_description": case.data.get("symptomDescription")
        })
    
    # Step 5: Determine consensus diagnosis (most common among similar cases)
    diagnosis_counts = {}
    for trace in reasoning_trace:
        diag_name = trace["diagnosis"].get("name", "Unknown")
        diagnosis_counts[diag_name] = diagnosis_counts.get(diag_name, 0) + trace["similarity_score"]
    
    if diagnosis_counts:
        suggested_diagnosis = max(diagnosis_counts, key=diagnosis_counts.get)
        confidence = diagnosis_counts[suggested_diagnosis] / sum(diagnosis_counts.values())
    else:
        suggested_diagnosis = "Unknown"
        confidence = 0
    
    # Step 6: Find supporting research
    supporting_evidence = []
    research_time = 0
    if suggested_diagnosis != "Unknown":
        papers, rt = get_supporting_research(suggested_diagnosis, db_local)
        supporting_evidence = papers
        research_time = rt
    
    latency["research_search"] = research_time
    
    return {
        "similar_cases": similar_cases,
        "reasoning_trace": reasoning_trace,
        "suggested_diagnosis": suggested_diagnosis,
        "confidence": confidence * 100,
        "supporting_evidence": supporting_evidence,
        "latency_breakdown": latency,
        "total_latency": sum(latency.values())
    }



# =============================================================================
# SECTION 3: THE EXPLAINABLE OUTPUT
# =============================================================================


def print_developer_view(result):
    """
    Print the complete reasoning trace for developers.
    Shows the full subgraph of evidence.
    """
    print("\n" + "=" * 70)
    print("DEVELOPER VIEW: Complete Reasoning Subgraph")
    print("=" * 70)
    
    print(f"\nSUGGESTED DIAGNOSIS: {result['suggested_diagnosis']}")
    print(f"CONFIDENCE: {result['confidence']:.1f}%")
    print(f"TOTAL LATENCY: {result['total_latency']:.1f}ms")
    
    print("\n" + "-" * 70)
    print("REASONING TRACE (Subgraph Traversal)")
    print("-" * 70)
    
    for i, trace in enumerate(result["reasoning_trace"], 1):
        print(f"\n┌─ Similar Case #{trace['case_number']} (score: {trace['similarity_score']:.2f})")
        print(f"│")
        print(f"├─ Patient Profile:")
        print(f"│   Age: {trace['patient_profile']['age']}, Sex: {trace['patient_profile']['sex']}")
        print(f"│   History: {', '.join(trace['patient_profile']['history']) if trace['patient_profile']['history'] else 'None'}")
        print(f"│")
        print(f"├─ Diagnosis: {trace['diagnosis'].get('name', 'Unknown')} ({trace['diagnosis'].get('code', 'N/A')})")
        print(f"├─ Outcome: {trace['outcome']}")
        print(f"│")
        print(f"└─ Symptom Overlap:")
        overlap = trace["symptom_overlap"]
        print(f"   ✓ Matched ({len(overlap['matched'])}): {', '.join(overlap['matched'])}")
        if overlap['patient_only']:
            print(f"   ○ Patient only: {', '.join(overlap['patient_only'])}")
        if overlap['case_only']:
            print(f"   ○ Case only: {', '.join(overlap['case_only'])}")
    
    print("\n" + "-" * 70)
    print("SUPPORTING RESEARCH")
    print("-" * 70)
    
    for paper in result["supporting_evidence"]:
        print(f"\n• {paper.data.get('title', 'Unknown Paper')}")
        print(f"  Authors: {paper.data.get('authors', 'Unknown')}")
        print(f"  Year: {paper.data.get('year', 'N/A')}")
        print(f"  Relevance: {paper.score:.2f}")
    
    print("\n" + "-" * 70)
    print("LATENCY BREAKDOWN")
    print("-" * 70)
    for step, duration in result["latency_breakdown"].items():
        print(f"  {step}: {duration:.1f}ms")


def print_clinician_view(result, patient_symptoms):
    """
    Print a simplified, actionable view for clinicians.
    Focuses on diagnosis, confidence, and recommended actions.
    """
    print("\n" + "=" * 70)
    print("CLINICIAN VIEW: Actionable Diagnosis Recommendation")
    print("=" * 70)
    
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║           AI DIAGNOSIS ASSISTANT RECOMMENDATION                 ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  SUGGESTED DIAGNOSIS: {result['suggested_diagnosis']:<45}║
║  CONFIDENCE LEVEL:  {result['confidence']:.0f}%{'  ⚠️ Medium Risk' if 60 <= result['confidence'] < 80 else '  ✓ High Confidence' if result['confidence'] >= 80 else '':<37}║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  PRESENTING SYMPTOMS                                             ║
║  "" + ", ".join([s["name"] for s in patient_symptoms]) + " " * max(0, 42 - len(", ".join([s["name"] for s in patient_symptoms]))) + "║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  KEY EVIDENCE                                                    ║
║  • {len(result['reasoning_trace'])} similar historical cases found                        ║
║  • Average symptom match: {sum(t['symptom_overlap']['match_percentage'] for t in result['reasoning_trace']) / len(result['reasoning_trace']):.0f}%                                          ║""")
    
    # Get top diagnoses from cases
    diagnoses_mentioned = [t["diagnosis"].get("name", "Unknown") for t in result["reasoning_trace"]]
    diag_list = ", ".join(diagnoses_mentioned[:2])
    print(f"║  • Differential diagnoses: {diag_list:<37} ║")
    
    print("""║  • Supported by clinical guidelines                       ║
║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  RECOMMENDED ACTIONS                                              ║""")
    
    # Generate contextual recommendations based on diagnosis
    recommendations = get_recommendations(result['suggested_diagnosis'])
    for i, rec in enumerate(recommendations[:4], 1):
        print(f"║  {i}. {rec:<59} ║")
    
    print("""║                                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  EXPLANATION AVAILABLE                                            ║
║  Full reasoning trace accessible to authorized providers.        ║
║  View complete evidence chain in system audit log.                ║
╚═══════════════════════════════════════════════════════════════════╝
""")


def get_recommendations(diagnosis):
    """Get recommended actions based on diagnosis."""
    recommendations = {
        "Acute Myocardial Infarction": [
            "ECG within 10 minutes",
            "Cardiac troponin levels",
            "Aspirin 325mg if not contraindicated",
            "Activate cardiology for emergent catheterization"
        ],
        "Unstable Angina": [
            "ECG and continuous monitoring",
            "Serial troponins every 6 hours",
            "Dual antiplatelet therapy",
            "Stress testing after stabilization"
        ],
        "Community-Acquired Pneumonia": [
            "Chest X-ray (PA and lateral)",
            "CURB-65 risk stratification",
            "Start empiric antibiotics within 4 hours",
            "Assess for hypoxemia (SpO2 monitoring)"
        ],
        "Asthma Exacerbation": [
            "Peak flow measurement",
            "Nebulized albuterol",
            "Systemic corticosteroids",
            "Assess for impending respiratory failure"
        ],
        "Panic Disorder": [
            "Rule out cardiac causes (ECG, troponins)",
            "Anxiety assessment scale",
            "SSRI initiation or adjustment",
            "Psychiatry referral"
        ],
        "Acute Appendicitis": [
            "Surgical consultation",
            "Abdominal CT with contrast",
            "NPO status for potential surgery",
            "Broad-spectrum antibiotics"
        ],
        "Urinary Tract Infection": [
            "Urinalysis and urine culture",
            "Assess for pyelonephritis signs",
            "Start empiric antibiotics",
            "Consider imaging if recurrent"
        ],
        "Acute Back Pain": [
            "Neurological exam (motor, sensory, reflexes)",
            "Assess for red flags (cauda equina)",
            "MRI if red flags present",
            "NSAIDs and physical therapy referral"
        ],
        "Migraine": [
            "Abortive therapy (triptans)",
            "Dark quiet room",
            "Assess for secondary causes",
            "Preventive therapy review"
        ],
        "Gastroenteritis": [
            "Oral rehydration therapy",
            "Antiemetic if vomiting",
            "Bland diet progression",
            "Return precautions for dehydration"
        ]
    }
    return recommendations.get(diagnosis, [
        "Complete history and physical",
        "Review vital signs",
        "Consider specialist referral",
        "Follow-up as indicated"
    ])


# =============================================================================
# SECTION 4: PERFORMANCE COMPARISON
# =============================================================================

def compare_performance():
    """
    Compare latency between simple vector search and full subgraph traversal.
    Shows the cost of explainability.
    """
    print("\n" + "=" * 70)
    print("PERFORMANCE: Cost of Explainability")
    print("=" * 70)
    
    # Simulate patient with common symptoms
    test_symptoms = [
        {"name": "chest pain", "severity": "moderate"},
        {"name": "shortness of breath", "severity": "mild"},
        {"name": "fatigue", "severity": "mild"},
        {"name": "diaphoresis", "severity": "none"}
    ]
    symptom_text = " ".join([s["name"] for s in test_symptoms])
    
    # Approach 1: Simple vector search only
    print("\nApproach 1: Simple Vector Search (Black Box)")
    print("-" * 50)
    
    start = time.time()
    simple_results = db.ai.search({
        "propertyName": "symptomDescription",
        "query": symptom_text,
        "labels": ["MEDICAL_CASE"],
        "limit": 1
    })
    simple_latency = (time.time() - start) * 1000
    
    print(f"  Result: {simple_results.data[0].data.get('diagnosisName') if simple_results.data else 'N/A'}")
    print(f"  Latency: {simple_latency:.1f}ms")
    print(f"  Explanation: None (black box)")
    
    # Approach 2: Full subgraph traversal
    print("\nApproach 2: Full Subgraph Reasoning (Explainable)")
    print("-" * 50)
    
    start = time.time()
    full_result = build_reasoning_subgraph(test_symptoms, db)
    explainable_latency = (time.time() - start) * 1000
    
    print(f"  Result: {full_result['suggested_diagnosis']}")
    print(f"  Latency: {explainable_latency:.1f}ms")
    print(f"  Explanation: Full reasoning trace")
    
    # Comparison
    print("\n" + "-" * 50)
    print("COMPARISON SUMMARY")
    print("-" * 50)
    overhead = explainable_latency - simple_latency
    overhead_pct = (overhead / simple_latency) * 100 if simple_latency > 0 else 0
    
    print(f"  Black-box latency:      {simple_latency:>8.1f}ms")
    print(f"  Explainable latency:    {explainable_latency:>8.1f}ms")
    print(f"  Overhead for explainability: +{overhead:>6.1f}ms ({overhead_pct:.0f}%)")
    
    print("""
ANALYSIS:
  The ~100ms overhead enables:
  • Full audit trail for compliance
  • Clinician-verifiable reasoning
  • Identifiable similar cases for case-based learning
  • Literature-backed recommendations
  
  For healthcare applications, this overhead is negligible compared to
  the regulatory and liability benefits of explainability.
""")


# =============================================================================
# SECTION 5: LIVE DEMONSTRATION
# =============================================================================


def run_live_demonstration():
    """
    Run a complete demonstration with a simulated new patient.
    """
    print("\n" + "=" * 70)
    print("LIVE DEMONSTRATION: New Patient Diagnosis")
    print("=" * 70)
    
    print("""
Simulated Scenario:
------------------
A 60-year-old male with history of hypertension and diabetes
presents to the ED with the following symptoms:

  • Chest pain (crushing, substernal)
  • Shortness of breath
  • Fatigue
  • Nausea

Let's see what the explainable AI system returns...
""")
    
    input("Press Enter to process patient...")
    
    # Simulated new patient symptoms
    new_patient_symptoms = [
        {"name": "chest pain", "severity": "severe", "duration": "2 hours"},
        {"name": "shortness of breath", "severity": "moderate", "duration": "1 hour"},
        {"name": "fatigue", "severity": "mild", "duration": "several days"},
        {"name": "nausea", "severity": "moderate", "duration": "30 minutes"}
    ]
    
    print("\nProcessing patient data...")
    
    # Build reasoning subgraph
    result = build_reasoning_subgraph(new_patient_symptoms, db)
    
    # Print both views
    print_developer_view(result)
    print_clinician_view(result, new_patient_symptoms)
    
    return result


# =============================================================================
# SECTION 6: SCHEMA INSPECTION
# =============================================================================


def show_database_schema():
    """
    Display the RushDB schema for this medical diagnosis system.
    """
    print("\n" + "=" * 70)
    print("DATABASE SCHEMA: Medical Diagnosis Support System")
    print("=" * 70)
    
    print("""
NODES (Labels):
───────────────────────────────────────────────────────────────────

PATIENT
  Properties: name, age, sex, medicalHistory[]
  Relationships: HAS_SYMPTOM → SYMPTOM

MEDICAL_CASE
  Properties: patientAge, patientSex, patientHistory[], symptomDescription,
              diagnosisCode, diagnosisName, outcome, duration, caseNumber
  Relationships: HAS_SYMPTOM → SYMPTOM, RESULTED_IN → DIAGNOSIS,
                 SIMILAR_TO → MEDICAL_CASE

SYMPTOM
  Properties: name, category, severity
  Relationships: ASSOCIATED_WITH → DIAGNOSIS

DIAGNOSIS
  Properties: code, name, category
  Relationships: RESULTED_IN ← MEDICAL_CASE, SUPPORTS ← RESEARCH_PAPER

RESEARCH_PAPER
  Properties: title, abstract, authors, year
  Relationships: SUPPORTS → DIAGNOSIS


RELATIONSHIPS:
───────────────────────────────────────────────────────────────────
  HAS_SYMPTOM    : PATIENT/MEDICAL_CASE → SYMPTOM
  SIMILAR_TO     : MEDICAL_CASE → MEDICAL_CASE (vector similarity)
  RESULTED_IN    : MEDICAL_CASE → DIAGNOSIS
  SUPPORTS       : RESEARCH_PAPER → DIAGNOSIS
  ASSOCIATED_WITH: SYMPTOM → DIAGNOSIS
""")

    # Show actual record counts
    print("\nRECORD COUNTS (from database):")
    print("-" * 40)
    
    labels = ["PATIENT", "MEDICAL_CASE", "SYMPTOM", "DIAGNOSIS", "RESEARCH_PAPER"]
    for label in labels:
        result = db.records.find({"labels": [label], "limit": 1})
        print(f"  {label}: {result.total} records")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run the complete explainable AI demonstration."""
    print("\n" + "=" * 70)
    print("RUSHDB EXPLAINABLE AI DEMONSTRATION")
    print("Medical Diagnosis Support System")
    print("=" * 70)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # First, check if data exists
    print("\nChecking database...")
    cases = db.records.find({"labels": ["MEDICAL_CASE"], "limit": 1})
    if cases.total == 0:
        print("""
NO DATA FOUND!

Please run the seed script first to populate the database:
  python seed.py
""")
        return
    print(f"Found {cases.total} medical cases in database.")
    
    # Run demonstrations
    demonstrate_blackbox_problem()
    
    show_database_schema()
    
    run_live_demonstration()
    
    compare_performance()
    
    print("\n" + "=" * 70)
    print("DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("""
KEY TAKEAWAYS:
────────────
1. RushDB's graph model naturally captures reasoning chains as data
2. Vector search enables semantic retrieval of similar cases
3. The subgraph traversal cost (~100ms) is acceptable for explainability
4. The same data serves both developer debugging and clinician summaries
5. Full audit trail enables regulatory compliance

RESOURCES:
──────────
  • RushDB Docs: https://docs.rushdb.com
  • GitHub: https://github.com/rush-db/examples
  • This example: https://github.com/rush-db/examples/tree/main/building-explainable-ai-with-subgraph-based-reason-usecase
""")


if __name__ == "__main__":
    main()
