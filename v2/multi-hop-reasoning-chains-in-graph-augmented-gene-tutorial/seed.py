#!/usr/bin/env python3
"""
Seed script for the Multi-hop Reasoning Chains tutorial.

Creates a biomedical knowledge graph with:
- 12 GENE records (oncogenes and tumor suppressors)
- 10 PROTEIN records (gene products)
- 8 DISEASE records (cancer types)
- 6 DRUG records (cancer treatments)
- 25 relationships across 4 relationship types

Run this once before main.py to populate the graph.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Verify API key is configured
api_key = os.environ.get("RUSHDB_API_KEY")
if not api_key:
    print("Error: RUSHDB_API_KEY not found in environment.")
    print("Copy .env.example to .env and add your API key.")
    exit(1)

db = RushDB(api_key)

# -----------------------------------------------------------------------------
# Seed Data
# -----------------------------------------------------------------------------

# Cancer-related genes
genes_data = [
    {"symbol": "TP53", "name": "Tumor Protein P53", "organism": "Homo sapiens", "type": "Tumor Suppressor"},
    {"symbol": "BRCA1", "name": "BRCA1 DNA Repair Associated", "organism": "Homo sapiens", "type": "Tumor Suppressor"},
    {"symbol": "BRCA2", "name": "BRCA2 DNA Repair Associated", "organism": "Homo sapiens", "type": "Tumor Suppressor"},
    {"symbol": "EGFR", "name": "Epidermal Growth Factor Receptor", "organism": "Homo sapiens", "type": "Oncogene"},
    {"symbol": "KRAS", "name": "KRAS Proto-Oncogene", "organism": "Homo sapiens", "type": "Oncogene"},
    {"symbol": "MYC", "name": "MYC Proto-Oncogene", "organism": "Homo sapiens", "type": "Oncogene"},
    {"symbol": "BRAF", "name": "B-Raf Proto-Oncogene", "organism": "Homo sapiens", "type": "Oncogene"},
    {"symbol": "ERBB2", "name": "ERBB2 Receptor Tyrosine Kinase 2", "organism": "Homo sapiens", "type": "Oncogene"},
    {"symbol": "PTEN", "name": "Phosphatase and Tensin Homolog", "organism": "Homo sapiens", "type": "Tumor Suppressor"},
    {"symbol": "RB1", "name": "RB Transcriptional Corepressor 1", "organism": "Homo sapiens", "type": "Tumor Suppressor"},
    {"symbol": "CDK4", "name": "Cyclin Dependent Kinase 4", "organism": "Homo sapiens", "type": "Oncogene"},
    {"symbol": "CDK6", "name": "Cyclin Dependent Kinase 6", "organism": "Homo sapiens", "type": "Oncogene"},
]

# Proteins encoded by these genes
proteins_data = [
    {"name": "p53", "fullName": "Cellular tumor antigen p53", "function": "DNA repair, cell cycle arrest, apoptosis", "length": 393},
    {"name": "BRCA1", "fullName": "Breast Cancer Type 1 Susceptibility Protein", "function": "DNA damage repair, genome stability", "length": 1863},
    {"name": "BRCA2", "fullName": "Breast Cancer Type 2 Susceptibility Protein", "function": "Homologous recombination repair", "length": 3418},
    {"name": "EGFR", "fullName": "Epidermal Growth Factor Receptor", "function": "Cell proliferation, survival signaling", "length": 1210},
    {"name": "K-Ras", "fullName": "GTPase KRas", "function": "Signal transduction, cell growth", "length": 189},
    {"name": "c-Myc", "fullName": "Myc Proto-Oncogene Protein", "function": "Transcription factor, cell growth", "length": 439},
    {"name": "B-Raf", "fullName": "Serine/Threonine-Protein Kinase B-Raf", "function": "Cell division, differentiation signaling", "length": 766},
    {"name": "HER2", "fullName": "Receptor Tyrosine-Protein Kinase erbB-2", "function": "Cell growth and differentiation", "length": 1255},
    {"name": "PTEN", "fullName": "Phosphatidylinositol 3,4,5-trisphosphate 3-phosphatase", "function": "Tumor suppression, cell survival regulation", "length": 403},
    {"name": "Rb", "fullName": "Retinoblastoma-associated Protein", "function": "Cell cycle regulation, tumor suppression", "length": 928},
]

# Cancer diseases
diseases_data = [
    {"name": "Breast Cancer", "category": "Carcinoma", "omimId": "114550", "prevalence": "High"},
    {"name": "Lung Cancer", "category": "Carcinoma", "omimId": "211980", "prevalence": "High"},
    {"name": "Colorectal Cancer", "category": "Carcinoma", "omimId": "114500", "prevalence": "High"},
    {"name": "Melanoma", "category": "Skin Cancer", "omimId": "155600", "prevalence": "Medium"},
    {"name": "Pancreatic Cancer", "category": "Carcinoma", "omimId": "260350", "prevalence": "Medium"},
    {"name": "Prostate Cancer", "category": "Carcinoma", "omimId": "176807", "prevalence": "High"},
    {"name": "Glioblastoma", "category": "Brain Tumor", "omimId": "137800", "prevalence": "Low"},
    {"name": "Ovarian Cancer", "category": "Gynecological", "omimId": "167000", "prevalence": "Medium"},
]

# Cancer drugs
drugs_data = [
    {"name": "Tamoxifen", "drugType": "Hormonal Therapy", "mechanism": "Estrogen receptor modulator", "status": "Approved"},
    {"name": "Trastuzumab", "drugType": "Monoclonal Antibody", "mechanism": "HER2 targeting", "status": "Approved"},
    {"name": "Gefitinib", "drugType": "Tyrosine Kinase Inhibitor", "mechanism": "EGFR inhibitor", "status": "Approved"},
    {"name": "Ribociclib", "drugType": "Kinase Inhibitor", "mechanism": "CDK4/6 inhibitor", "status": "Approved"},
    {"name": "Vemurafenib", "drugType": "Kinase Inhibitor", "mechanism": "B-Raf inhibitor", "status": "Approved"},
    {"name": "Olaparib", "drugType": "PARP Inhibitor", "mechanism": "DNA repair pathway inhibition", "status": "Approved"},
]

# Relationship mappings
# Format: (from_label, from_identifier, to_label, to_identifier, rel_type)
relationships = [
    # Gene -> Protein (CODES_FOR)
    ("GENE", "TP53", "PROTEIN", "p53"),
    ("GENE", "BRCA1", "PROTEIN", "BRCA1"),
    ("GENE", "BRCA2", "PROTEIN", "BRCA2"),
    ("GENE", "EGFR", "PROTEIN", "EGFR"),
    ("GENE", "KRAS", "PROTEIN", "K-Ras"),
    ("GENE", "MYC", "PROTEIN", "c-Myc"),
    ("GENE", "BRAF", "PROTEIN", "B-Raf"),
    ("GENE", "ERBB2", "PROTEIN", "HER2"),
    ("GENE", "PTEN", "PROTEIN", "PTEN"),
    ("GENE", "RB1", "PROTEIN", "Rb"),
    ("GENE", "CDK4", "PROTEIN", "Rb"),
    ("GENE", "CDK6", "PROTEIN", "Rb"),
    
    # Protein -> Disease (INVOLVED_IN)
    ("PROTEIN", "p53", "DISEASE", "Breast Cancer"),
    ("PROTEIN", "p53", "DISEASE", "Lung Cancer"),
    ("PROTEIN", "p53", "DISEASE", "Colorectal Cancer"),
    ("PROTEIN", "BRCA1", "DISEASE", "Breast Cancer"),
    ("PROTEIN", "BRCA2", "DISEASE", "Breast Cancer"),
    ("PROTEIN", "EGFR", "DISEASE", "Lung Cancer"),
    ("PROTEIN", "HER2", "DISEASE", "Breast Cancer"),
    ("PROTEIN", "B-Raf", "DISEASE", "Melanoma"),
    ("PROTEIN", "K-Ras", "DISEASE", "Pancreatic Cancer"),
    ("PROTEIN", "PTEN", "DISEASE", "Glioblastoma"),
    
    # Disease -> Drug (TREATED_BY)
    ("DISEASE", "Breast Cancer", "DRUG", "Tamoxifen"),
    ("DISEASE", "Breast Cancer", "DRUG", "Trastuzumab"),
    ("DISEASE", "Breast Cancer", "DRUG", "Ribociclib"),
    ("DISEASE", "Lung Cancer", "DRUG", "Gefitinib"),
    ("DISEASE", "Melanoma", "DRUG", "Vemurafenib"),
    ("DISEASE", "Breast Cancer", "DRUG", "Olaparib"),
    ("DISEASE", "Ovarian Cancer", "DRUG", "Olaparib"),
    ("DISEASE", "Breast Cancer", "DRUG", "Ribociclib"),
]

# Protein -> Protein interactions (INTERACTS_WITH)
protein_interactions = [
    ("PROTEIN", "p53", "PROTEIN", "HER2"),
    ("PROTEIN", "EGFR", "PROTEIN", "HER2"),
    ("PROTEIN", "K-Ras", "PROTEIN", "B-Raf"),
    ("PROTEIN", "BRCA1", "PROTEIN", "BRCA2"),
    ("PROTEIN", "p53", "PROTEIN", "Rb"),
    ("PROTEIN", "Rb", "PROTEIN", "CDK4"),
    ("PROTEIN", "Rb", "PROTEIN", "CDK6"),
]


def check_already_seeded():
    """Check if data already exists to prevent duplicates."""
    result = db.records.find({"labels": ["GENE"], "limit": 1})
    return result.total > 0


def seed():
    """Seed the knowledge graph with biomedical data."""
    
    # Check for existing data
    if check_already_seeded():
        print("Data already exists. Skipping seed. Delete existing records to re-seed.")
        return
    
    print("Seeding knowledge graph...")
    
    with db.transactions.begin() as tx:
        # Create genes
        gene_map = {}
        for i, gene_data in enumerate(genes_data):
            gene = db.records.create(label="GENE", data=gene_data, transaction=tx)
            gene_map[gene_data["symbol"]] = gene
            if (i + 1) % 4 == 0:
                print(f"[1/5] Created {i + 1} GENE records")
        
        # Create proteins
        protein_map = {}
        for i, protein_data in enumerate(proteins_data):
            protein = db.records.create(label="PROTEIN", data=protein_data, transaction=tx)
            protein_map[protein_data["name"]] = protein
            if (i + 1) % 5 == 0:
                print(f"[2/5] Created {i + 1} PROTEIN records")
        
        # Create diseases
        disease_map = {}
        for i, disease_data in enumerate(diseases_data):
            disease = db.records.create(label="DISEASE", data=disease_data, transaction=tx)
            disease_map[disease_data["name"]] = disease
            if (i + 1) % 4 == 0:
                print(f"[3/5] Created {i + 1} DISEASE records")
        
        # Create drugs
        drug_map = {}
        for i, drug_data in enumerate(drugs_data):
            drug = db.records.create(label="DRUG", data=drug_data, transaction=tx)
            drug_map[drug_data["name"]] = drug
            if (i + 1) % 3 == 0:
                print(f"[4/5] Created {i + 1} DRUG records")
        
        # Create relationships (Gene -> Protein)
        for i, (from_label, from_id, to_label, to_id) in enumerate(relationships):
            if from_label == "GENE":
                source = gene_map.get(from_id)
            elif from_label == "PROTEIN":
                source = protein_map.get(from_id)
            
            if to_label == "PROTEIN":
                target = protein_map.get(to_id)
            elif to_label == "DISEASE":
                target = disease_map.get(to_id)
            elif to_label == "DRUG":
                target = drug_map.get(to_id)
            
            if source and target:
                rel_type = "CODES_FOR" if from_label == "GENE" else (
                    "INVOLVED_IN" if from_label == "PROTEIN" else "TREATED_BY"
                )
                db.records.attach(source=source, target=target, options={"type": rel_type}, transaction=tx)
        
        # Create protein-protein interactions
        for from_label, from_id, to_label, to_id in protein_interactions:
            source = protein_map.get(from_id)
            target = protein_map.get(to_id)
            if source and target:
                db.records.attach(source=source, target=target, options={"type": "INTERACTS_WITH"}, transaction=tx)
        
        print(f"[5/5] Created {len(relationships)} primary + {len(protein_interactions)} interaction relationships")
    
    # Get final counts
    gene_count = db.records.find({"labels": ["GENE"]}).total
    protein_count = db.records.find({"labels": ["PROTEIN"]}).total
    disease_count = db.records.find({"labels": ["DISEASE"]}).total
    drug_count = db.records.find({"labels": ["DRUG"]}).total
    
    print(f"\nDone! Graph contains {gene_count + protein_count + disease_count + drug_count} records and {len(relationships) + len(protein_interactions)} relationships.")


if __name__ == "__main__":
    seed()
