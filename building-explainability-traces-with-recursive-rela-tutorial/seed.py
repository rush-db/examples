"""
Seed script for building explainability traces demo.

Generates a set of AI decisions with nested reasoning chains, evidence links,
and intermediate results. Safe to run multiple times - checks for existing data.
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

from rushdb import RushDB

load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(API_KEY)

# Sample data for realistic explainability traces
DOMAINS = [
    {
        "name": "credit_approval",
        "model": "CreditScorer-v3",
        "outcomes": ["approved", "denied", "manual_review"],
        "reasoning_templates": [
            {
                "description": "Income verification",
                "evidence_types": ["payslip", "bank_statement", "employment_letter"],
                "confidence_range": (0.85, 0.98),
                "sub_steps": [
                    {
                        "description": "Employment status validation",
                        "evidence_types": ["employer_contact", "contract_copy"],
                        "confidence_range": (0.75, 0.95)
                    },
                    {
                        "description": "Income consistency check",
                        "evidence_types": ["monthly_income_history", "bonus_inclusions"],
                        "confidence_range": (0.80, 0.92)
                    }
                ]
            },
            {
                "description": "Risk assessment",
                "evidence_types": ["credit_report", "debt_records"],
                "confidence_range": (0.78, 0.95),
                "sub_steps": [
                    {
                        "description": "Credit score evaluation",
                        "evidence_types": [" FICO_score", "payment_history"],
                        "confidence_range": (0.82, 0.99)
                    },
                    {
                        "description": "Debt-to-income ratio analysis",
                        "evidence_types": ["existing_debts", "monthly_obligations"],
                        "confidence_range": (0.70, 0.88)
                    }
                ]
            },
            {
                "description": "Collateral evaluation",
                "evidence_types": ["property_appraisal", "vehicle_registration"],
                "confidence_range": (0.88, 0.98),
                "sub_steps": []
            }
        ]
    },
    {
        "name": "fraud_detection",
        "model": "FraudNet-2.1",
        "outcomes": ["legitimate", "suspicious", "blocked"],
        "reasoning_templates": [
            {
                "description": "Transaction pattern analysis",
                "evidence_types": ["transaction_history", "merchant_category"],
                "confidence_range": (0.80, 0.95),
                "sub_steps": [
                    {
                        "description": "Historical spending pattern comparison",
                        "evidence_types": ["avg_transaction_amount", "purchase_frequency"],
                        "confidence_range": (0.76, 0.90)
                    },
                    {
                        "description": "Geographic anomaly detection",
                        "evidence_types": ["location_history", "device_fingerprint"],
                        "confidence_range": (0.68, 0.85)
                    }
                ]
            },
            {
                "description": "Velocity check",
                "evidence_types": ["transaction_count", "time_window"],
                "confidence_range": (0.85, 0.98),
                "sub_steps": [
                    {
                        "description": "Transaction frequency analysis",
                        "evidence_types": ["attempts_per_hour", "failure_rate"],
                        "confidence_range": (0.82, 0.96)
                    }
                ]
            },
            {
                "description": "Device reputation scoring",
                "evidence_types": ["device_id", "ip_reputation"],
                "confidence_range": (0.72, 0.92),
                "sub_steps": []
            }
        ]
    },
    {
        "name": "loan_default_prediction",
        "model": "DefaultPredictor-XL",
        "outcomes": ["low_risk", "medium_risk", "high_risk"],
        "reasoning_templates": [
            {
                "description": "Payment history analysis",
                "evidence_types": ["past_loans", "payment_timing"],
                "confidence_range": (0.88, 0.99),
                "sub_steps": [
                    {
                        "description": "On-time payment ratio",
                        "evidence_types": ["months_on_time", "total_payments"],
                        "confidence_range": (0.85, 0.98)
                    },
                    {
                        "description": "Late payment pattern analysis",
                        "evidence_types": ["late_frequency", "days_overdue"],
                        "confidence_range": (0.78, 0.92)
                    }
                ]
            },
            {
                "description": "Employment stability assessment",
                "evidence_types": ["job_tenure", "industry_type"],
                "confidence_range": (0.75, 0.90),
                "sub_steps": []
            },
            {
                "description": "Financial stress testing",
                "evidence_types": ["expense_ratio", "savings_buffer"],
                "confidence_range": (0.70, 0.88),
                "sub_steps": []
            }
        ]
    }
]


def check_already_seeded():
    """Check if data already exists to avoid duplicate seeding."""
    result = db.records.find({"labels": ["AI_DECISION"], "limit": 1})
    return result.total > 0


def generate_decision_id(domain: str, index: int) -> str:
    """Generate a unique decision ID."""
    return f"{domain}-{index:03d}"


def create_reasoning_chain(templates: list, depth: int = 0, parent_step: dict = None) -> list:
    """Recursively create reasoning step chains from templates."""
    steps = []
    
    for template in templates:
        step = {
            "description": template["description"],
            "confidence": round(random.uniform(*template["confidence_range"]), 2),
            "depth": depth,
            "evidence_types": template["evidence_types"],
            "sub_steps": []
        }
        
        # Create evidence for this step
        for ev_type in template["evidence_types"]:
            evidence = {
                "type": ev_type,
                "value": f"{ev_type}-validated",
                "source": f"automated-{random.choice(['api', 'database', 'verification_service'])}"
            }
            step.setdefault("evidence", []).append(evidence)
        
        # Create intermediate results
        intermediate = {
            "metric": f"{template['description'].lower().replace(' ', '_')}_score",
            "value": round(random.uniform(0.6, 0.99), 3),
            "thresholds": {"low": 0.5, "medium": 0.7, "high": 0.85}
        }
        step["intermediate_result"] = intermediate
        
        # Recursively create sub-steps
        if template.get("sub_steps"):
            step["sub_steps"] = create_reasoning_chain(
                template["sub_steps"], 
                depth + 1,
                step
            )
        
        steps.append(step)
    
    return steps


def seed_decisions(count: int = 15):
    """Seed AI decisions with complete explainability traces."""
    print(f"\n{'='*60}")
    print("SEEDING EXPLAINABILITY TRACES")
    print(f"{'='*60}\n")
    
    # Check if already seeded
    if check_already_seeded():
        print("Data already exists. Skipping seed (or delete all AI_DECISION records to re-seed).")
        print("Run 'python seed.py --force' to re-seed anyway.\n")
        return
    
    decision_count = 0
    
    for domain in DOMAINS:
        # Create 5 decisions per domain
        for i in range(5):
            decision_id = generate_decision_id(domain["name"], i + 1)
            
            # Create the AI decision
            decision = db.records.create(
                label="AI_DECISION",
                data={
                    "decisionId": decision_id,
                    "model": domain["model"],
                    "outcome": random.choice(domain["outcomes"]),
                    "confidence": round(random.uniform(0.75, 0.95), 2),
                    "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                    "domain": domain["name"]
                }
            )
            decision_count += 1
            
            if decision_count % 5 == 0:
                print(f"  Created {decision_count} decisions... ({domain['name']})")
            
            # Create reasoning chain
            reasoning_chain = create_reasoning_chain(domain["reasoning_templates"])
            
            # Store created steps for linking
            previous_steps = []
            
            for step_data in reasoning_chain:
                # Extract evidence and intermediate result before processing sub_steps
                evidence_list = step_data.pop("evidence", [])
                intermediate_result = step_data.pop("intermediate_result")
                sub_steps_data = step_data.pop("sub_steps", [])
                
                # Create the reasoning step
                step = db.records.create(
                    label="REASONING_STEP",
                    data=step_data
                )
                
                # Link decision to reasoning step
                db.records.attach(
                    source=decision,
                    target=step,
                    options={"type": "HAS_REASONING_STEP"}
                )
                
                # Link to previous step if exists (sequential reasoning)
                if previous_steps:
                    for prev_step in previous_steps:
                        db.records.attach(
                            source=prev_step,
                            target=step,
                            options={"type": "LEADS_TO"}
                        )
                
                # Create evidence records and attach
                for ev_data in evidence_list:
                    evidence = db.records.create(
                        label="EVIDENCE",
                        data={
                            "evidenceId": f"{decision_id}-ev-{step.data['description'][:10]}",
                            **ev_data
                        }
                    )
                    db.records.attach(
                        source=step,
                        target=evidence,
                        options={"type": "SUPPORTS"}
                    )
                
                # Create intermediate result and attach
                result = db.records.create(
                    label="INTERMEDIATE_RESULT",
                    data={
                        "resultId": f"{decision_id}-res-{step.data['description'][:10]}",
                        **intermediate_result
                    }
                )
                db.records.attach(
                    source=step,
                    target=result,
                    options={"type": "GENERATED"}
                )
                
                # Collect sub-steps recursively
                current_depth_steps = [step]
                
                def process_sub_steps(parent_step, sub_steps):
                    """Recursively process sub-steps."""
                    nonlocal current_depth_steps
                    
                    for sub_step_data in sub_steps:
                        evidence_list = sub_step_data.pop("evidence", [])
                        intermediate_result = sub_step_data.pop("intermediate_result")
                        grandchild_steps = sub_step_data.pop("sub_steps", [])
                        
                        sub_step = db.records.create(
                            label="REASONING_STEP",
                            data=sub_step_data
                        )
                        
                        # Link to parent step
                        db.records.attach(
                            source=parent_step,
                            target=sub_step,
                            options={"type": "LEADS_TO"}
                        )
                        
                        # Create evidence for sub-step
                        for ev_data in evidence_list:
                            evidence = db.records.create(
                                label="EVIDENCE",
                                data={
                                    "evidenceId": f"{decision_id}-ev-{sub_step.data['description'][:10]}",
                                    **ev_data
                                }
                            )
                            db.records.attach(
                                source=sub_step,
                                target=evidence,
                                options={"type": "SUPPORTS"}
                            )
                        
                        # Create intermediate result for sub-step
                        result = db.records.create(
                            label="INTERMEDIATE_RESULT",
                            data={
                                "resultId": f"{decision_id}-res-{sub_step.data['description'][:10]}",
                                **intermediate_result
                            }
                        )
                        db.records.attach(
                            source=sub_step,
                            target=result,
                            options={"type": "GENERATED"}
                        )
                        
                        # Process grandchildren
                        if grandchild_steps:
                            process_sub_steps(sub_step, grandchild_steps)
                
                if sub_steps_data:
                    process_sub_steps(step, sub_steps_data)
                
                previous_steps = current_depth_steps.copy()
    
    print(f"\n✓ Successfully seeded {decision_count} AI decisions with complete explainability traces.")
    print("\nEach decision includes:")
    print("  - Multiple reasoning steps (depth 0-2)")
    print("  - Evidence links for each step")
    print("  - Intermediate results")
    print("  - Nested sub-steps demonstrating recursive chains\n")


if __name__ == "__main__":
    import sys
    
    force = "--force" in sys.argv
    
    if force:
        # Delete existing data first
        print("Force re-seed: deleting existing AI_DECISION records...")
        db.records.delete_many({"labels": ["AI_DECISION"]})
        print("Deleted existing records.\n")
    
    seed_decisions()
