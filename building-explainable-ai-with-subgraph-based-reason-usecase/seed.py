"""
Medical Case Seed Script

Generates realistic mock medical data for the explainable AI diagnosis system.
Creates historical cases, symptoms, diagnoses, and research papers.

This script is idempotent - safe to run multiple times. Run with --reset to clear existing data.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


from rushdb import RushDB

# Verify API key is configured
api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Please copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)

# Medical data definitions
SYMPTOMS = [
    "chest pain", "shortness of breath", "fatigue", "dizziness",
    "nausea", "diaphoresis", "palpitations", "syncope", "cough",
    "abdominal pain", "headache", "fever", "weakness", "anxiety",
    "leg swelling", "wheezing", "back pain", "joint pain", "rash"
]

DIAGNOSES = [
    {"code": "I21", "name": "Acute Myocardial Infarction", "category": "Cardiac"},
    {"code": "I20", "name": "Unstable Angina", "category": "Cardiac"},
    {"code": "J18", "name": "Community-Acquired Pneumonia", "category": "Pulmonary"},
    {"code": "J45", "name": "Asthma Exacerbation", "category": "Pulmonary"},
    {"code": "K35", "name": "Acute Appendicitis", "category": "GI"},
    {"code": "N39", "name": "Urinary Tract Infection", "category": "GU"},
    {"code": "M54", "name": "Acute Back Pain", "category": "Musculoskeletal"},
    {"code": "G43", "name": "Migraine", "category": "Neurological"},
    {"code": "F41", "name": "Panic Disorder", "category": "Psychiatric"},
    {"code": "R10", "name": "Gastroenteritis", "category": "GI"}
]

MEDICAL_CASES = [
    {
        "patientAge": 58, "patientSex": "M", "patientHistory": ["hypertension", "hyperlipidemia"],
        "symptoms": ["chest pain", "shortness of breath", "fatigue", "diaphoresis"],
        "diagnosisCode": "I21", "diagnosisName": "Acute Myocardial Infarction",
        "outcome": "STEMI - emergency stenting - full recovery", "duration": "5 days",
        "symptomDescription": "Crushing substernal chest pain radiating to left arm, associated with diaphoresis and dyspnea. Patient presented with elevated troponins and ST elevation on ECG."
    },
    {
        "patientAge": 62, "patientSex": "F", "patientHistory": ["diabetes", "obesity"],
        "symptoms": ["chest pain", "shortness of breath", "nausea", "fatigue"],
        "diagnosisCode": "I20", "diagnosisName": "Unstable Angina",
        "outcome": "Non-STEMI - medical management with antiplatelet therapy", "duration": "3 days",
        "symptomDescription": "Intermittent chest discomfort with exertion, relieved by rest. Troponin borderline elevated. No ST changes on ECG."
    },
    {
        "patientAge": 45, "patientSex": "M", "patientHistory": ["asthma"],
        "symptoms": ["cough", "wheezing", "shortness of breath", "fatigue"],
        "diagnosisCode": "J45", "diagnosisName": "Asthma Exacerbation",
        "outcome": "Acute exacerbation - bronchodilators and steroids - discharged next day", "duration": "2 days",
        "symptomDescription": "Progressive dyspnea and wheezing over 3 days, not responding to home inhaler. Physical exam showed bilateral expiratory wheezes."
    },
    {
        "patientAge": 71, "patientSex": "M", "patientHistory": ["COPD", "smoking history"],
        "symptoms": ["cough", "shortness of breath", "fever", "fatigue"],
        "diagnosisCode": "J18", "diagnosisName": "Community-Acquired Pneumonia",
        "outcome": "Bacterial pneumonia - antibiotics - chest X-ray cleared at follow-up", "duration": "7 days",
        "symptomDescription": "Productive cough with purulent sputum, fever of 102F, pleuritic chest pain. Chest X-ray showed right lower lobe infiltrate."
    },
    {
        "patientAge": 28, "patientSex": "F", "patientHistory": ["anxiety disorder"],
        "symptoms": ["chest pain", "palpitations", "dizziness", "anxiety"],
        "diagnosisCode": "F41", "diagnosisName": "Panic Disorder",
        "outcome": "Panic attack - cognitive behavioral therapy referral - PRN alprazolam", "duration": "6 hours",
        "symptomDescription": "Sudden onset palpitations, feeling of impending doom, chest tightness, hyperventilation. Normal cardiac workup including ECG and troponins."
    },
    {
        "patientAge": 34, "patientSex": "M", "patientHistory": [] as list,
        "symptoms": ["abdominal pain", "nausea", "fever", "weakness"],
        "diagnosisCode": "K35", "diagnosisName": "Acute Appendicitis",
        "outcome": "Acute appendicitis - laparoscopic appendectomy - uneventful recovery", "duration": "2 days",
        "symptomDescription": "Periumbilical pain migrating to RLQ, anorexia, nausea, low-grade fever. Positive McBurney point tenderness with rebound."
    },
    {
        "patientAge": 55, "patientSex": "F", "patientHistory": ["UTI history", "diabetes"],
        "symptoms": ["abdominal pain", "fever", "weakness", "fatigue"],
        "diagnosisCode": "N39", "diagnosisName": "Urinary Tract Infection",
        "outcome": "Complicated UTI - IV antibiotics - symptoms resolved", "duration": "4 days",
        "symptomDescription": "Suprapubic pain, dysuria, frequency, fever. Urinalysis showed pyuria and bacteriuria. Blood cultures negative."
    },
    {
        "patientAge": 42, "patientSex": "M", "patientHistory": ["mechanical work"],
        "symptoms": ["back pain", "leg pain", "weakness", "numbness"],
        "diagnosisCode": "M54", "diagnosisName": "Acute Back Pain",
        "outcome": "Lumbar disc herniation - physical therapy - MRI scheduled", "duration": "Outpatient",
        "symptomDescription": "Acute onset LBP after lifting, radiating pain down posterior thigh to knee. Positive straight leg raise. No bowel/bladder symptoms."
    },
    {
        "patientAge": 38, "patientSex": "F", "patientHistory": ["migraine history"],
        "symptoms": ["headache", "nausea", "dizziness", "sensitivity to light"],
        "diagnosisCode": "G43", "diagnosisName": "Migraine",
        "outcome": "Migraine with aura - sumatriptan - headache resolved in 2 hours", "duration": "4 hours",
        "symptomDescription": "Throbbing unilateral headache preceded by visual aura (scintillating scotoma). Phonophobia and photophobia. History of similar episodes."
    },
    {
        "patientAge": 52, "patientSex": "M", "patientHistory": ["food allergies"],
        "symptoms": ["abdominal pain", "nausea", "vomiting", "diarrhea"],
        "diagnosisCode": "R10", "diagnosisName": "Gastroenteritis",
        "outcome": "Viral gastroenteritis - supportive care - symptoms resolved in 48 hours", "duration": "2 days",
        "symptomDescription": "Acute onset nausea, vomiting, watery diarrhea after eating at restaurant. Low-grade fever, mild abdominal cramping. No bloody stool."
    },
    {
        "patientAge": 65, "patientSex": "F", "patientHistory": ["hypertension", "coronary artery disease"],
        "symptoms": ["chest pain", "fatigue", "leg swelling", "shortness of breath"],
        "diagnosisCode": "I21", "diagnosisName": "Acute Myocardial Infarction",
        "outcome": "NSTEMI - cardiac catheterization - triple vessel disease, medical management", "duration": "6 days",
        "symptomDescription": "Subacute chest discomfort over 48 hours, worsening dyspnea on exertion, bilateral ankle edema. Elevated troponins, EF 35% on echo."
    },
    {
        "patientAge": 29, "patientSex": "M", "patientHistory": ["healthy"],
        "symptoms": ["fever", "cough", "headache", "fatigue"],
        "diagnosisCode": "J18", "diagnosisName": "Community-Acquired Pneumonia",
        "outcome": "Viral pneumonia - supportive care - chest X-ray improved at follow-up", "duration": "10 days",
        "symptomDescription": "Upper respiratory prodrome followed by dry cough and fever. Mild hypoxemia. CT chest showed bilateral ground-glass opacities."
    },
    {
        "patientAge": 48, "patientSex": "F", "patientHistory": ["hypothyroidism"],
        "symptoms": ["fatigue", "weakness", "dizziness", "palpitations"],
        "diagnosisCode": "I20", "diagnosisName": "Unstable Angina",
        "outcome": "Stress test positive - medical management with ranolazine", "duration": "3 days",
        "symptomDescription": "Exertional chest discomfort, dyspnea, and fatigue for 2 weeks. Normal resting ECG. Positive exercise stress test with ST depression."
    },
    {
        "patientAge": 33, "patientSex": "F", "patientHistory": ["anxiety"],
        "symptoms": ["dizziness", "palpitations", "shortness of breath", "chest pain"],
        "diagnosisCode": "F41", "diagnosisName": "Panic Disorder",
        "outcome": "Panic disorder with agoraphobia - SSRI started - therapy referral", "duration": "Ongoing",
        "symptomDescription": "Recurrent episodes of intense fear with chest tightness, palpitations, tingling in extremities. Episodes occur without trigger, including at night."
    },
    {
        "patientAge": 67, "patientSex": "M", "patientHistory": ["atrial fibrillation", "heart failure"],
        "symptoms": ["shortness of breath", "leg swelling", "fatigue", "cough"],
        "diagnosisCode": "I21", "diagnosisName": "Acute Myocardial Infarction",
        "outcome": "Acute decompensated heart failure secondary to NSTEMI - diuresis and revascularization", "duration": "8 days",
        "symptomDescription": "Rapidly worsening dyspnea, orthopnea, paroxysmal nocturnal dyspnea, bilateral edema. Elevated BNP, rising troponins, new atrial fibrillation."
    }
]

RESEARCH_PAPERS = [
    {
        "title": "2023 ESC Guidelines for Acute Coronary Syndromes",
        "abstract": "These guidelines provide evidence-based recommendations for the management of acute coronary syndromes including STEMI, NSTEMI, and unstable angina. Key recommendations include early aspirin and P2Y12 inhibition, risk stratification using GRACE score, and urgent revascularization strategies.",
        "authors": "European Society of Cardiology",
        "year": 2023
    },
    {
        "title": "Management of Community-Acquired Pneumonia in Adults",
        "abstract": "Evidence-based guidelines for diagnosing and treating CAP, including risk stratification using CURB-65 score, appropriate antibiotic selection based on severity and local resistance patterns, and criteria for hospitalization versus outpatient management.",
        "authors": "American Thoracic Society",
        "year": 2019
    },
    {
        "title": "GINA 2023 Asthma Management Recommendations",
        "abstract": "Global Initiative for Asthma guidelines covering asthma diagnosis, assessment, and treatment. Emphasizes stepwise approach to therapy, importance of inhaler technique, and action plan for acute exacerbations.",
        "authors": "GINA Board",
        "year": 2023
    },
    {
        "title": "Diagnosis and Treatment of Panic Disorder",
        "abstract": "Clinical guidelines for panic disorder including DSM-5 criteria, differential diagnosis considerations (ruling out cardiac and pulmonary causes), first-line treatments (SSRIs and CBT), and management of refractory cases.",
        "authors": "American Psychiatric Association",
        "year": 2021
    },
    {
        "title": "SAGES Guidelines for Appendicitis",
        "abstract": "Evidence-based recommendations for the diagnosis and management of acute appendicitis, including imaging criteria, timing of surgery, role of antibiotics-first approach for uncomplicated cases, and management of complicated appendicitis.",
        "authors": "Society of American Gastrointestinal and Endoscopic Surgeons",
        "year": 2020
    },
    {
        "title": "ACEP Clinical Policy on Acute Back Pain",
        "abstract": "Emergency department management of acute back pain focusing on red flag identification, appropriate imaging criteria, opioid-sparing pain management strategies, and indications for emergent surgical intervention.",
        "authors": "American College of Emergency Physicians",
        "year": 2022
    },
    {
        "title": "IDSA Guidelines for Urinary Tract Infections",
        "abstract": "Infectious Diseases Society of America guidelines covering diagnosis and treatment of uncomplicated and complicated UTIs, including antimicrobial resistance considerations, duration of therapy, and management of recurrent infections.",
        "authors": "Infectious Diseases Society of America",
        "year": 2022
    },
    {
        "title": "AHA/ASA Migraine Prevention Guidelines",
        "abstract": "American Heart Association guidelines for migraine management including acute treatment algorithms, preventive therapy options (beta-blockers, anticonvulsants, CGRP antagonists), and lifestyle modifications.",
        "authors": "American Heart Association",
        "year": 2021
    },
    {
        "title": "AGA Clinical Practice Update on Gastroenteritis",
        "abstract": "American Gastroenterological Association recommendations for managing acute gastroenteritis including oral rehydration strategies, antiemetic use, antidiarrheal considerations, and diet recommendations.",
        "authors": "American Gastroenterological Association",
        "year": 2020
    },
    {
        "title": "Heart Failure Society of America Guidelines",
        "abstract": "Comprehensive guidelines for heart failure management including diagnosis with BNP and echocardiography, GDMT medications, device therapy indications, and acute decompensation management.",
        "authors": "Heart Failure Society of America",
        "year": 2022
    }
]


def clear_existing_data():
    """Clear all medical-related records."""
    labels = ["PATIENT", "MEDICAL_CASE", "SYMPTOM", "DIAGNOSIS", "RESEARCH_PAPER"]
    print("Clearing existing data...")
    for label in labels:
        result = db.records.delete_many({"labels": [label]})
        print(f"  Cleared {label} records")



def create_symptoms(tx=None):
    """Create all symptom records."""
    print("Creating symptoms...")
    symptom_records = {}
    for symptom_name in SYMPTOMS:
        symptom = db.records.create(
            label="SYMPTOM",
            data={
                "name": symptom_name,
                "category": get_symptom_category(symptom_name)
            },
            transaction=tx
        )
        symptom_records[symptom_name] = symptom
        if SYMPTOMS.index(symptom_name) % 5 == 0:
            print(f"  Created {len(symptom_records)} symptoms...")
    print(f"  Total: {len(symptom_records)} symptoms created")
    return symptom_records



def get_symptom_category(symptom):
    """Categorize symptoms."""
    cardiac_symptoms = ["chest pain", "palpitations", "syncope", "diaphoresis"]
    respiratory_symptoms = ["shortness of breath", "cough", "wheezing"]
    gi_symptoms = ["abdominal pain", "nausea", "diarrhea", "vomiting"]
    neurological_symptoms = ["dizziness", "headache", "weakness", "numbness"]
    
    if symptom in cardiac_symptoms:
        return "Cardiovascular"
    elif symptom in respiratory_symptoms:
        return "Respiratory"
    elif symptom in gi_symptoms:
        return "Gastrointestinal"
    elif symptom in neurological_symptoms:
        return "Neurological"
    else:
        return "General"



def create_diagnoses(tx=None):
    """Create all diagnosis records."""
    print("Creating diagnoses...")
    diagnosis_records = {}
    for diag in DIAGNOSES:
        diagnosis = db.records.create(
            label="DIAGNOSIS",
            data={
                "code": diag["code"],
                "name": diag["name"],
                "category": diag["category"]
            },
            transaction=tx
        )
        diagnosis_records[diag["code"]] = diagnosis
    print(f"  Total: {len(diagnosis_records)} diagnoses created")
    return diagnosis_records


def create_medical_cases(symptom_records, diagnosis_records, tx=None):
    """Create all medical case records."""
    print("Creating medical cases...")
    case_records = []
    for i, case in enumerate(MEDICAL_CASES):
        case_record = db.records.create(
            label="MEDICAL_CASE",
            data={
                "patientAge": case["patientAge"],
                "patientSex": case["patientSex"],
                "patientHistory": case["patientHistory"],
                "diagnosisCode": case["diagnosisCode"],
                "diagnosisName": case["diagnosisName"],
                "outcome": case["outcome"],
                "duration": case["duration"],
                "symptomDescription": case["symptomDescription"],
                "caseNumber": i + 1
            },
            transaction=tx
        )
        case_records.append(case_record)
        
        # Link symptoms to case
        for symptom_name in case["symptoms"]:
            if symptom_name in symptom_records:
                db.records.attach(
                    source=case_record,
                    target=symptom_records[symptom_name],
                    options={"type": "HAS_SYMPTOM"},
                    transaction=tx
                )
        
        # Link diagnosis to case
        if case["diagnosisCode"] in diagnosis_records:
            db.records.attach(
                source=case_record,
                target=diagnosis_records[case["diagnosisCode"]],
                options={"type": "RESULTED_IN"},
                transaction=tx
            )
        
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1} cases...")
    
    print(f"  Total: {len(case_records)} medical cases created")
    return case_records


def create_research_papers(diagnosis_records, tx=None):
    """Create all research paper records."""
    print("Creating research papers...")
    paper_records = []
    for paper in RESEARCH_PAPERS:
        paper_record = db.records.create(
            label="RESEARCH_PAPER",
            data={
                "title": paper["title"],
                "abstract": paper["abstract"],
                "authors": paper["authors"],
                "year": paper["year"]
            },
            transaction=tx
        )
        paper_records.append(paper_record)
    
    print(f"  Total: {len(paper_records)} research papers created")
    return paper_records


def create_similarity_edges(case_records, db_local, tx=None):
    """Create similarity edges between cases based on shared symptoms."""
    print("Creating similarity edges...")
    similarity_count = 0
    
    for i, case_a in enumerate(case_records):
        for case_b in case_records[i + 1:]:
            # Calculate symptom overlap
            shared_symptoms = calculate_shared_symptoms(case_a, case_b)
            if shared_symptoms >= 2:
                # Create SIMILAR_TO relationship
                similarity_score = shared_symptoms / 4.0  # Normalize
                db_local.records.attach(
                    source=case_a,
                    target=case_b,
                    options={"type": "SIMILAR_TO"},
                    transaction=tx
                )
                similarity_count += 1
    
    print(f"  Total: {similarity_count} similarity edges created")


def calculate_shared_symptoms(case_a, case_b):
    """Calculate number of shared symptoms between two cases."""
    symptoms_a = set(case_a.data.get("symptoms", []))
    symptoms_b = set(case_b.data.get("symptoms", []))
    return len(symptoms_a.intersection(symptoms_b))



def main():
    """Main seeding function."""
    print("=" * 60)
    print("Medical Case Database Seeding")
    print("=" * 60)
    
    # Check if reset is requested
    reset = "--reset" in sys.argv
    
    if reset:
        clear_existing_data()
    else:
        # Check if data already exists
        existing = db.records.find({"labels": ["MEDICAL_CASE"], "limit": 1})
        if existing.total > 0:
            print(f"\nFound {existing.total} existing medical cases.")
            print("Run with --reset to clear and reseed, or skip this script.")
            response = input("\nContinue seeding anyway? (y/N): ")
            if response.lower() != 'y':
                print("Seeding cancelled.")
                return

    print("\nStarting database seeding...")
    print("-" * 60)
    
    start_time = datetime.now()
    
    with db.transactions.begin() as tx:
        # Create all base records
        symptom_records = create_symptoms(tx)
        diagnosis_records = create_diagnoses(tx)
        case_records = create_medical_cases(symptom_records, diagnosis_records, tx)
        paper_records = create_research_papers(diagnosis_records, tx)
        
        # Create similarity edges (separate transaction to avoid long hold)
        create_similarity_edges(case_records, db, tx)
        
        tx.commit()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("-" * 60)
    print(f"\nSeeding completed in {duration:.2f} seconds")
    print("\nDatabase summary:")
    print(f"  - {len(SYMPTOMS)} symptom records")
    print(f"  - {len(DIAGNOSES)} diagnosis records")
    print(f"  - {len(MEDICAL_CASES)} medical case records")
    print(f"  - {len(RESEARCH_PAPERS)} research paper records")
    print("=" * 60)


if __name__ == "__main__":
    main()
