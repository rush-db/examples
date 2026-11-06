#!/usr/bin/env python3
"""
Multi-hop Reasoning Chains in Graph-Augmented Generation

This script demonstrates how to:
1. Perform multi-hop graph traversals (2-4 hops) using RushDB
2. Build reasoning chains from traversal results
3. Augment LLM prompts with structured graph context

The example uses a biomedical knowledge graph with:
- Genes, Proteins, Diseases, and Drugs as entity types
- Multi-hop relationships between these entities
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# -----------------------------------------------------------------------------
# Initialize RushDB Client
# -----------------------------------------------------------------------------

api_key = os.environ.get("RUSHDB_API_KEY")
if not api_key:
    print("Error: RUSHDB_API_KEY not found.")
    print("Copy .env.example to .env and add your API key.")
    exit(1)

db = RushDB(api_key)


# -----------------------------------------------------------------------------
# Multi-hop Reasoning Functions
# -----------------------------------------------------------------------------

def find_proteins_for_gene(gene_symbol: str) -> list:
    """
    1-hop traversal: Find proteins encoded by a gene.
    Pattern: GENE -> CODES_FOR -> PROTEIN
    """
    proteins = db.records.find({
        "labels": ["PROTEIN"],
        "where": {
            "GENE": {
                "$relation": {"type": "CODES_FOR", "direction": "in"},
                "symbol": gene_symbol
            }
        }
    })
    return proteins.data


def find_diseases_for_protein(protein_name: str) -> list:
    """
    2-hop traversal: Find diseases involving a protein.
    Pattern: PROTEIN -> INVOLVED_IN -> DISEASE
    """
    diseases = db.records.find({
        "labels": ["DISEASE"],
        "where": {
            "PROTEIN": {
                "$relation": {"type": "INVOLVED_IN", "direction": "in"},
                "name": protein_name
            }
        }
    })
    return diseases.data


def find_diseases_for_gene(gene_symbol: str) -> list:
    """
    2-hop traversal: Find diseases via gene's proteins.
    Pattern: GENE -> CODES_FOR -> PROTEIN -> INVOLVED_IN -> DISEASE
    This demonstrates nested relationship filtering.
    """
    diseases = db.records.find({
        "labels": ["DISEASE"],
        "where": {
            "PROTEIN": {
                "GENE": {
                    "symbol": gene_symbol
                }
            }
        }
    })
    return diseases.data


def find_drugs_for_disease(disease_name: str) -> list:
    """
    1-hop traversal: Find drugs that treat a disease.
    Pattern: DISEASE -> TREATED_BY -> DRUG
    """
    drugs = db.records.find({
        "labels": ["DRUG"],
        "where": {
            "DISEASE": {
                "$relation": {"type": "TREATED_BY", "direction": "in"},
                "name": disease_name
            }
        }
    })
    return drugs.data


def find_drugs_for_gene(gene_symbol: str) -> list:
    """
    3-hop traversal: Find drugs for diseases linked to a gene.
    Pattern: GENE -> CODES_FOR -> PROTEIN -> INVOLVED_IN -> DISEASE -> TREATED_BY -> DRUG
    """
    drugs = db.records.find({
        "labels": ["DRUG"],
        "where": {
            "DISEASE": {
                "PROTEIN": {
                    "GENE": {
                        "symbol": gene_symbol
                    }
                }
            }
        }
    })
    return drugs.data


def find_protein_interactions(protein_name: str) -> list:
    """
    1-hop traversal: Find proteins that interact with a given protein.
    Pattern: PROTEIN -> INTERACTS_WITH -> PROTEIN
    """
    interactions = db.records.find({
        "labels": ["PROTEIN"],
        "where": {
            "PROTEIN": {
                "$relation": {"type": "INTERACTS_WITH", "direction": "in"},
                "name": protein_name
            }
        }
    })
    return interactions.data


# -----------------------------------------------------------------------------
# Reasoning Chain Builder
# -----------------------------------------------------------------------------

def build_reasoning_chain(gene_symbol: str) -> dict:
    """
    Build a complete reasoning chain for a gene:
    1. Find gene's proteins
    2. Find diseases involving those proteins
    3. Find drugs treating those diseases
    4. Generate natural language reasoning
    """
    chain = {
        "query": gene_symbol,
        "hops": [],
        "drugs": [],
        "reasoning": ""
    }
    
    # Hop 1: Gene -> Proteins
    proteins = find_proteins_for_gene(gene_symbol)
    if proteins:
        chain["hops"].append({
            "depth": 1,
            "pattern": "GENE -> PROTEIN",
            "entities": [{"name": p["name"], "function": p.get("function", "Unknown")} for p in proteins]
        })
    
    # Hop 2: Protein -> Disease
    disease_connections = []
    for protein in proteins:
        diseases = find_diseases_for_protein(protein["name"])
        for disease in diseases:
            disease_connections.append({
                "protein": protein["name"],
                "disease": disease["name"]
            })
    
    if disease_connections:
        chain["hops"].append({
            "depth": 2,
            "pattern": "PROTEIN -> DISEASE",
            "connections": disease_connections
        })
    
    # Hop 3: Disease -> Drug
    drug_connections = []
    for conn in disease_connections:
        drugs = find_drugs_for_disease(conn["disease"])
        for drug in drugs:
            drug_connections.append({
                "disease": conn["disease"],
                "protein": conn["protein"],
                "drug": drug["name"],
                "mechanism": drug.get("mechanism", "Unknown")
            })
    
    if drug_connections:
        chain["hops"].append({
            "depth": 3,
            "pattern": "DISEASE -> DRUG",
            "connections": drug_connections
        })
    
    # Aggregate unique drugs
    unique_drugs = {}
    for conn in drug_connections:
        drug_name = conn["drug"]
        if drug_name not in unique_drugs:
            unique_drugs[drug_name] = {
                "name": drug_name,
                "diseases": [],
                "mechanism": conn["mechanism"]
            }
        unique_drugs[drug_name]["diseases"].append(conn["disease"])
    
    chain["drugs"] = list(unique_drugs.values())
    
    # Generate reasoning text
    if chain["drugs"]:
        drug_list = ", ".join([d["name"] for d in chain["drugs"]])
        disease_count = len(set(c["disease"] for c in drug_connections))
        chain["reasoning"] = (
            f"Gene {gene_symbol} encodes {len(proteins)} protein(s). "
            f"These proteins are involved in {disease_count} disease(s). "
            f"{len(chain['drugs'])} drug(s) may be relevant: {drug_list}."
        )
    else:
        chain["reasoning"] = f"No drug connections found for gene {gene_symbol}."
    
    return chain


# -----------------------------------------------------------------------------
# Graph-Augmented Generation Helper
# -----------------------------------------------------------------------------

def build_augmented_prompt(gene_symbol: str, user_question: str) -> str:
    """
    Build an LLM prompt augmented with graph reasoning context.
    
    This demonstrates how multi-hop traversal results can be
    injected into a prompt to give the LLM structured context.
    """
    chain = build_reasoning_chain(gene_symbol)
    
    # Simulate what you'd send to an LLM
    prompt = f"""You are a biomedical research assistant.

CONTEXT FROM KNOWLEDGE GRAPH:
{json.dumps(chain, indent=2)}

USER QUESTION:
{user_question}

Based on the graph data above, provide a detailed answer.
"""
    return prompt


# -----------------------------------------------------------------------------
# Demo
# -----------------------------------------------------------------------------

def run_demo():
    """Run the multi-hop reasoning demonstration."""
    
    print("=" * 60)
    print("Multi-hop Reasoning Chains in Graph-Augmented Generation")
    print("=" * 60)
    print()
    
    # Verify data exists
    genes = db.records.find({"labels": ["GENE"], "limit": 1})
    if genes.total == 0:
        print("No data found. Please run `python seed.py` first.")
        return
    
    # Demo queries
    demo_genes = ["TP53", "BRCA1", "EGFR"]
    
    for gene in demo_genes:
        print(f"\n{'='*60}")
        print(f"Query: {gene}")
        print("="*60)
        
        # Get reasoning chain
        chain = build_reasoning_chain(gene)
        
        # Display hops
        for hop in chain["hops"]:
            print(f"\n[Hop {hop['depth']}] {hop['pattern']}")
            if "entities" in hop:
                for entity in hop["entities"]:
                    print(f"  └─ {entity['name']} (function: {entity['function']})")
            elif "connections" in hop:
                for conn in hop["connections"]:
                    if "drug" in conn:
                        print(f"  └─ {conn.get('protein', '?')} → {conn['disease']} → {conn['drug']}")
                    else:
                        print(f"  └─ {conn['protein']} → {conn['disease']}")
        
        # Display aggregated drugs
        if chain["drugs"]:
            print(f"\n[Aggregated Drug Recommendations]")
            for drug in chain["drugs"]:
                diseases = ", ".join(drug["diseases"])
                print(f"  • {drug['name']} (for: {diseases})")
                print(f"    Mechanism: {drug['mechanism']}")
        
        # Display reasoning text
        print(f"\n[Generated Reasoning]")
        print(f"  {chain['reasoning']}")
    
    # Demonstrate prompt augmentation
    print(f"\n{'='*60}")
    print("Graph-Augmented Prompt Example")
    print("="*60)
    
    prompt = build_augmented_prompt(
        "TP53",
        "What potential therapeutic options exist for a patient with TP53 mutations?"
    )
    print(f"\n[Augmented Prompt for LLM]")
    print("-" * 40)
    print(prompt)
    
    # Show protein interactions as bonus
    print(f"\n{'='*60}")
    print("Bonus: Protein Interaction Network (1-hop)")
    print("="*60)
    
    for gene in ["TP53", "EGFR"]:
        proteins = find_proteins_for_gene(gene)
        if proteins:
            protein_name = proteins[0]["name"]
            interactions = find_protein_interactions(protein_name)
            if interactions:
                print(f"\n{protein_name} interacts with:")
                for interacting in interactions:
                    print(f"  └─ {interacting['name']}")


if __name__ == "__main__":
    run_demo()
