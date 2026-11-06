"""
Mock Legal Document Generator

Generates realistic cross-document legal references for demonstrating
the chunk-boundary problem in RAG systems.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# ============================================================
# MOCK LEGAL DOCUMENTS WITH CROSS-REFERENCES
# ============================================================

DOCUMENTS = {
    "msa": {
        "title": "Master Service Agreement",
        "doc_type": "MSA",
        "body": """
MASTER SERVICE AGREEMENT

This Master Service Agreement ("Agreement") is entered into as of January 15, 2024
("Effective Date") by and between Acme Corporation, a Delaware corporation
("Client"), and TechVendor Inc., a California corporation ("Provider").

ARTICLE 1: DEFINITIONS

1.1 "Confidential Information" means any non-public information disclosed by
either party to the other, including but not limited to technical data, trade
secrets, and business information.

1.2 "Services" means the professional services to be provided by Provider as
described in any Statement of Work ("SOW") attached hereto and governed by
this Agreement.

1.3 "Deliverables" means all work product, documentation, and materials
delivered by Provider under a SOW.

1.4 "Intellectual Property" means all patents, copyrights, trademarks, and
trade secrets related to the Services.

ARTICLE 2: SERVICES AND DELIVERABLES

2.1 Provider shall perform the Services in accordance with the terms of this
Agreement and any applicable SOW. Each SOW shall reference this Agreement
and be governed by its terms.

2.2 All Deliverables shall be subject to Client's written acceptance within
fifteen (15) business days of delivery.

ARTICLE 3: PAYMENT TERMS

3.1 Client shall pay Provider the fees set forth in the applicable Statement
of Work. Payment terms are net thirty (30) days from invoice date.

3.2 All fees are exclusive of applicable taxes. Client shall be responsible
for any sales, use, or similar taxes.

3.3 Late payments shall accrue interest at one and one-half percent (1.5%)
per month or the maximum rate permitted by law, whichever is less.

ARTICLE 4: LIABILITY AND INDEMNIFICATION

4.1 Each party's total cumulative liability under this Agreement shall not
exceed the greater of (a) one million dollars ($1,000,000) or (b) the total
fees paid or payable under this Agreement during the twelve (12) months
preceding the claim.

4.2 NEITHER PARTY SHALL BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL,
CONSEQUENTIAL, OR PUNITIVE DAMAGES, REGARDLESS OF THE CAUSE OF ACTION.

4.3 Provider shall indemnify, defend, and hold harmless Client from any
third-party claims arising from Provider's gross negligence or willful misconduct.

ARTICLE 5: CONFIDENTIALITY

5.1 Each party agrees to maintain the confidentiality of the other party's
Confidential Information and to use such information only for purposes of
this Agreement.

5.2 Confidentiality obligations shall survive termination of this Agreement
for a period of three (3) years.

ARTICLE 6: TERM AND TERMINATION

6.1 This Agreement shall commence on the Effective Date and continue for
three (3) years unless terminated earlier in accordance with this Article.

6.2 Either party may terminate this Agreement upon sixty (60) days written
notice to the other party.

6.3 Upon termination, Client shall pay for all Services performed and
Deliverables accepted prior to the termination date.
"""
    },
    "sow_project_alpha": {
        "title": "Statement of Work - Project Alpha",
        "doc_type": "SOW",
        "body": """
STATEMENT OF WORK - PROJECT ALPHA

This Statement of Work ("SOW") is entered into pursuant to the Master Service
Agreement dated January 15, 2024 ("MSA") between Acme Corporation ("Client")
and TechVendor Inc. ("Provider"). This SOW is governed by the terms of the MSA.

1. PROJECT OVERVIEW

1.1 Provider shall design and implement a cloud migration solution for
Client's legacy infrastructure.

1.2 The project shall be completed in three (3) phases over a twelve (12)
month period.


2. SCOPE OF SERVICES

2.1 Phase 1: Assessment and Planning (Months 1-3)
    - Infrastructure audit and documentation
    - Migration strategy development
    - Risk assessment and mitigation planning

2.2 Phase 2: Implementation (Months 4-9)
    - Cloud environment setup and configuration
    - Data migration and validation
    - Application migration and testing

2.3 Phase 3: Optimization and Handover (Months 10-12)
    - Performance optimization
    - Documentation and knowledge transfer
    - Training and support during transition

3. FEES AND PAYMENT

3.1 Client shall pay Provider a fixed fee of five hundred thousand dollars
($500,000) for the Services described herein, payable in quarterly
installments of $125,000.

3.2 The payment schedule shall align with milestone completion as follows:
    - Q1 Milestone: Phase 1 completion - $125,000
    - Q2 Milestone: Phase 2 completion - $150,000
    - Q3 Milestone: Phase 3 completion - $225,000

3.3 All payments are subject to the payment terms set forth in Article 3
of the MSA (net 30 days from invoice).

3.4 Provider shall submit invoices monthly, detailing Services performed
and applicable rates per the attached Pricing Schedule.

4. CHANGE MANAGEMENT

4.1 Any changes to the scope of Services must be documented in a written
change order signed by both parties.

4.2 Change orders may affect the project timeline and fees, which shall
be negotiated in good faith.

5. ACCEPTANCE CRITERIA

5.1 All Deliverables shall be subject to Client's acceptance testing per
Section 2.2 of the MSA.

5.2 Phase completion shall be determined by sign-off from Client's
designated project manager.

6. TERM

6.1 This SOW shall commence on February 1, 2024, and be completed by
January 31, 2025.

6.2 The term of this SOW is subject to the termination provisions of
Article 6 of the MSA.
"""
    },
    "pricing_schedule": {
        "title": "Pricing Schedule",
        "doc_type": "Pricing Schedule",
        "body": """
PRICING SCHEDULE

This Pricing Schedule is attached to and incorporated by reference into
the Master Service Agreement dated January 15, 2024 ("MSA") between
Acme Corporation ("Client") and TechVendor Inc. ("Provider").

This schedule establishes the rates and fees applicable to Services
performed under any Statement of Work.

1. PROFESSIONAL SERVICES RATES

1.1 Engineering Services
    - Senior Cloud Architect: $350/hour
    - Cloud Engineer: $250/hour
    - DevOps Specialist: $225/hour
    - Technical Writer: $150/hour

1.2 Management Services
    - Project Manager: $200/hour
    - Technical Lead: $300/hour

2. FIXED PRICING TIERS

2.1 Assessment and Planning: $150,000 - $200,000
2.2 Implementation Services: $200,000 - $400,000
2.3 Optimization and Training: $75,000 - $150,000

3. REIMBURSABLE EXPENSES

3.1 Travel expenses shall be reimbursed at cost, subject to Client
prior approval.

3.2 Cloud infrastructure costs shall be billed at cost plus five percent
(5%) management fee.

4. PRICING ADJUSTMENTS

4.1 Rates may be adjusted annually upon sixty (60) days written notice.

4.2 Adjustments shall not exceed five percent (5%) per year without
mutual written agreement.

5. PAYMENT APPLICATION

5.1 For time-and-materials SOWs, Provider shall track hours against
the rate categories above.

5.2 The cumulative liability cap referenced in Section 4.1 of the MSA
applies to total fees across all SOWs under this Agreement.
"""
    },
    "sow_project_beta": {
        "title": "Statement of Work - Project Beta",
        "doc_type": "SOW",
        "body": """
STATEMENT OF WORK - PROJECT BETA

This Statement of Work ("SOW") is entered into pursuant to the Master Service
Agreement dated January 15, 2024 ("MSA") between Acme Corporation ("Client")
and TechVendor Inc. ("Provider"). This SOW is governed by the terms of the MSA.


1. PROJECT OVERVIEW

1.1 Provider shall implement a security audit and compliance framework
for Client's cloud infrastructure.

1.2 The project duration is six (6) months.

2. SCOPE OF SERVICES

2.1 Security Assessment (Months 1-2)
    - Vulnerability scanning and analysis
    - Compliance gap assessment against SOC 2 Type II requirements
    - Risk classification and prioritization

2.2 Remediation Planning (Months 3-4)
    - Security control implementation
    - Policy documentation and updates
    - Incident response procedure development

2.3 Validation and Certification (Months 5-6)
    - Control testing and validation
    - Audit preparation and support
    - Certification documentation

3. FEES AND PAYMENT

3.1 Client shall pay Provider a fixed fee of three hundred thousand dollars
($300,000) for the Services described herein.

3.2 Payment terms follow Article 3 of the MSA (net 30 days) and the
rate structure in the attached Pricing Schedule.

3.3 Hourly work outside fixed scope shall be billed at rates established
in the Pricing Schedule.

4. CONFIDENTIALITY

4.1 All security findings and assessments are considered Confidential
Information under Article 5 of the MSA.

4.2 Provider shall maintain audit logs and documentation in accordance
with Client's security policies.

5. LIABILITY

5.1 This SOW's fees contribute to the overall liability cap established
in Section 4.1 of the MSA.

5.2 Provider's indemnification obligations under Section 4.3 of the MSA
apply to this engagement.
"""
    },
    "amendment_1": {
        "title": "Amendment No. 1 to MSA",
        "doc_type": "Amendment",
        "body": """
AMENDMENT NO. 1 TO MASTER SERVICE AGREEMENT

This Amendment ("Amendment") is made to the Master Service Agreement dated
January 15, 2024 ("Agreement") between Acme Corporation ("Client") and
TechVendor Inc. ("Provider").

RECITALS

WHEREAS, the parties desire to amend certain terms of the Agreement;
WHEREAS, the parties acknowledge that the terms of the original Agreement
remain in full force except as specifically modified herein;

NOW, THEREFORE, the parties agree as follows:

1. AMENDMENT TO ARTICLE 4 (LIABILITY)


1.1 Section 4.1 is hereby amended to read:

"Each party's total cumulative liability under this Agreement shall not
exceed the greater of (a) two million dollars ($2,000,000) or (b) the total
fees paid or payable under this Agreement during the twelve (12) months
preceding the claim."

2. ADDITION OF NEW ARTICLE 7: DATA PROTECTION


7.1 Provider shall comply with all applicable data protection regulations,
including but not limited to GDPR and CCPA.

7.2 Provider shall maintain SOC 2 Type II certification throughout the
term of this Agreement.

7.3 Data processing activities shall be documented in a Data Processing
Agreement ("DPA") to be attached as an exhibit.

3. AMENDMENT TO ARTICLE 5 (CONFIDENTIALITY)

3.1 Section 5.2 is hereby amended to extend the confidentiality survival
period from three (3) years to five (5) years for:
    - Customer data and PII
    - Security audit findings
    - Proprietary source code

4. EFFECTIVE DATE

4.1 This Amendment shall be effective as of April 1, 2024.

4.2 All other terms of the Agreement remain unchanged.
"""
    }
}

# ============================================================
# CROSS-REFERENCE RELATIONSHIPS (Graph Edges)
# ============================================================

RELATIONSHIPS = [
    # SOW references the MSA as governing document
    {"source": "sow_project_alpha", "target": "msa", "type": "GOVERNS", "description": "SOW governed by MSA terms"},
    {"source": "sow_project_beta", "target": "msa", "type": "GOVERNS", "description": "SOW governed by MSA terms"},
    
    # Pricing Schedule is attached to MSA
    {"source": "pricing_schedule", "target": "msa", "type": "ATTACHED_TO", "description": "Establishes rates and fees"},
    
    # SOWs reference Pricing Schedule for rates
    {"source": "sow_project_alpha", "target": "pricing_schedule", "type": "REFERENCES", "description": "Contains rate information"},
    {"source": "sow_project_beta", "target": "pricing_schedule", "type": "REFERENCES", "description": "Contains rate information"},
    
    # Amendment modifies MSA
    {"source": "amendment_1", "target": "msa", "type": "MODIFIES", "description": "Amends liability cap and adds data protection"},
    
    # Amendment references liability provisions
    {"source": "amendment_1", "target": "msa", "type": "REFERENCES", "description": "Amends Section 4.1 on liability"},
    
    # SOWs link back to MSA for termination provisions
    {"source": "sow_project_alpha", "target": "msa", "type": "REFERENCES", "description": "Termination per Article 6"},
    {"source": "sow_project_beta", "target": "msa", "type": "REFERENCES", "description": "Termination per Article 6"},
    
    # Both SOWs reference the liability cap
    {"source": "sow_project_beta", "target": "msa", "type": "ESTABLISHES", "description": "Contributes to liability cap per Section 4.1"},
    {"source": "pricing_schedule", "target": "msa", "type": "ESTABLISHES", "description": "Rates subject to liability cap per Section 4.1"},
]

# ============================================================
# MULTI-HOP TEST QUESTIONS
# ============================================================


BENCHMARK_QUESTIONS = [
    {
        "question": "What are the payment terms and how do they relate to the liability cap?",
        "requires_hops": ["sow_project_alpha", "msa", "pricing_schedule"],
        "key_concepts": ["payment terms", "liability cap", "net 30 days"],
        "answerable_with_vector_only": False,
        "answerable_with_graph": True,
        "expected_references": ["sow_project_alpha", "msa", "pricing_schedule"]
    },
    {
        "question": "How do the rates in the pricing schedule apply to Project Alpha?",
        "requires_hops": ["sow_project_alpha", "pricing_schedule"],
        "key_concepts": ["rates", "pricing schedule", "project alpha"],
        "answerable_with_vector_only": False,
        "answerable_with_graph": True,
        "expected_references": ["sow_project_alpha", "pricing_schedule"]
    },
    {
        "question": "What happens to payments upon early termination of Project Beta?",
        "requires_hops": ["sow_project_beta", "msa"],
        "key_concepts": ["termination", "payment", "survive"],
        "answerable_with_vector_only": False,
        "answerable_with_graph": True,
        "expected_references": ["sow_project_beta", "msa"]
    },
    {
        "question": "What is the updated liability cap after the amendment?",
        "requires_hops": ["amendment_1", "msa"],
        "key_concepts": ["liability cap", "amendment", "$2,000,000"],
        "answerable_with_vector_only": True,
        "answerable_with_graph": True,
        "expected_references": ["amendment_1", "msa"]
    },
    {
        "question": "What confidentiality obligations apply to the security audit findings?",
        "requires_hops": ["sow_project_beta", "msa"],
        "key_concepts": ["confidentiality", "security audit", "survive"],
        "answerable_with_vector_only": False,
        "answerable_with_graph": True,
        "expected_references": ["sow_project_beta", "msa"]
    }
]


def check_existing_data(db: RushDB) -> bool:
    """Check if seed data already exists."""
    try:
        result = db.records.find({"labels": ["DOCUMENT"], "limit": 1})
        return len(result.data) > 0
    except Exception:
        return False


def generate_embeddings():
    """Generate embeddings for documents using sentence-transformers."""
    from sentence_transformers import SentenceTransformer
    
    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    embeddings = {}
    for doc_id, doc in DOCUMENTS.items():
        text = doc["title"] + " " + doc["body"]
        vector = model.encode(text).tolist()
        embeddings[doc_id] = vector
        print(f"Generated embedding for: {doc['title']}")
    
    return embeddings



def seed_database():
    """Seed the database with legal documents and relationships."""
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment")
        print("Please copy .env.example to .env and add your API key")
        return False
    
    db = RushDB(api_key)
    
    # Check for existing data
    if check_existing_data(db):
        print("Seed data already exists. Skipping seed.")
        print("To re-seed, delete existing records first.")
        return True
    
    print("\n=== Seeding Database ===")
    
    # Generate embeddings
    embeddings = generate_embeddings()
    
    # Create vector index first
    print("\nCreating vector index for documents...")
    try:
        index = db.ai.indexes.create({
            "label": "DOCUMENT",
            "propertyName": "body",
            "sourceType": "external",
            "dimensions": 384,
            "similarityFunction": "cosine"
        })
        index_id = index.data.get("__id") or index.data.get("id")
        print(f"Vector index created: {index_id}")
    except Exception as e:
        print(f"Vector index may already exist: {e}")
        index_id = None
    
    # Create documents with embeddings
    print("\nCreating documents...")
    created_docs = {}
    
    for i, (doc_id, doc) in enumerate(DOCUMENTS.items()):
        # Create document record with embedding
        record = db.records.create(
            label="DOCUMENT",
            data={
                "slug": doc_id,
                "title": doc["title"],
                "doc_type": doc["doc_type"],
                "body": doc["body"].strip()
            },
            vectors=[{
                "propertyName": "body",
                "vector": embeddings[doc_id]
            }]
        )
        created_docs[doc_id] = record
        print(f"  [{i+1}/{len(DOCUMENTS)}] Created: {doc['title']}")
        
        # Rate limiting
        time.sleep(0.1)
    
    # Create relationships
    print("\nCreating cross-document relationships...")
    
    for i, rel in enumerate(RELATIONSHIPS):
        source = created_docs.get(rel["source"])
        target = created_docs.get(rel["target"])
        
        if source and target:
            db.records.attach(
                source=source,
                target=target,
                options={"type": rel["type"]}
            )
            print(f"  [{i+1}/{len(RELATIONSHIPS)}] {rel['source']} --[{rel['type']}]--> {rel['target']}")
        
        time.sleep(0.05)
    
    print("\n=== Seed Complete ===")
    print(f"Created {len(DOCUMENTS)} documents with {len(RELATIONSHIPS)} cross-references")
    
    return True


def main():
    """Main entry point for seed script."""
    print("Cross-Document Relationship Extraction - Seed Script")
    print("=" * 60)
    
    success = seed_database()
    
    if success:
        print("\nSeed data is ready. Run main.py to execute the benchmark.")
    else:
        print("\nSeed failed. Check your API key and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
