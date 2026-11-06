#!/usr/bin/env python3
"""
Seed script for Trust Scoring Agents example.
Creates mock data: agents, responses, evidence, claims, and sources.
Idempotent: checks for existing data before creating new records.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

API_KEY = os.environ.get("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

db = RushDB(API_KEY)

# Seed data constants
AGENTS = [
    {"name": "Dr. Elena Vasquez", "specialty": "climate_science", "base_trust": 0.95},
    {"name": "Marcus Chen", "specialty": "machine_learning", "base_trust": 0.88},
    {"name": "Sarah Mitchell", "specialty": "cybersecurity", "base_trust": 0.85},
    {"name": "James Okonkwo", "specialty": "quantum_computing", "base_trust": 0.82},
    {"name": "Dr. Yuki Tanaka", "specialty": "bioinformatics", "base_trust": 0.89},
    {"name": "Alex Rodriguez", "specialty": "neuroscience", "base_trust": 0.78},
    {"name": "Dr. Priya Sharma", "specialty": "materials_science", "base_trust": 0.91},
    {"name": "Michael Thompson", "specialty": "astrophysics", "base_trust": 0.84},
]

SOURCES = [
    {"name": "Nature Journal", "type": "peer_reviewed", "base_reliability": 0.95},
    {"name": "Science Magazine", "type": "peer_reviewed", "base_reliability": 0.94},
    {"name": "arXiv Preprint", "type": "preprint", "base_reliability": 0.75},
    {"name": "IPCC Official Report", "type": "government", "base_reliability": 0.95},
    {"name": "NIST Guidelines", "type": "government", "base_reliability": 0.92},
    {"name": "TechCrunch", "type": "news", "base_reliability": 0.65},
    {"name": "Wikipedia", "type": "encyclopedia", "base_reliability": 0.60},
    {"name": "World Economic Forum", "type": "organization", "base_reliability": 0.70},
    {"name": "MIT Technology Review", "type": "news", "base_reliability": 0.78},
    {"name": "Stanford AI Report", "type": "academic", "base_reliability": 0.88},
    {"name": "Reuters Science", "type": "news", "base_reliability": 0.80},
    {"name": "Google Research", "type": "corporate", "base_reliability": 0.82},
    {"name": "Bloomberg Tech", "type": "news", "base_reliability": 0.72},
    {"name": "Harvard Medical Review", "type": "academic", "base_reliability": 0.90},
    {"name": "Defense One", "type": "news", "base_reliability": 0.74},
]

RESPONSES = [
    {"text": "Climate change is accelerating faster than predicted models suggest.", "topic": "climate"},
    {"text": "Machine learning models can now outperform traditional algorithms in protein folding.", "topic": "ml"},
    {"text": "Quantum computing will break current encryption standards within 10 years.", "topic": "quantum"},
    {"text": "The human brain can store approximately 2.5 petabytes of data.", "topic": "neuroscience"},
    {"text": "Graphene-based batteries could increase energy density by 500%.", "topic": "materials"},
    {"text": "Dark matter comprises approximately 27% of the universe.", "topic": "astrophysics"},
    {"text": "CRISPR gene editing has a 15% off-target mutation rate in clinical trials.", "topic": "bioinformatics"},
    {"text": "Zero-trust security models reduce breach risk by 60%.", "topic": "security"},
    {"text": "The global AI market will reach $500 billion by 2027.", "topic": "ai_market"},
    {"text": "Neural interfaces could enable direct brain-to-computer communication by 2030.", "topic": "neural"},
    {"text": "Quantum error correction has reached 99.9% accuracy in recent experiments.", "topic": "quantum"},
    {"text": "Global sea levels could rise 0.3 meters by 2050 under current trajectories.", "topic": "climate"},
    {"text": "Transformer architectures have revolutionized NLP tasks.", "topic": "ml"},
    {"text": "室温超导体可能改变能源传输效率。", "topic": "materials"},
    {"text": "脑机接口的延迟已降至5毫秒以下。", "topic": "neural"},
    {"text": "机器学习在药物发现中的应用正在快速增长。", "topic": "ml"},
    {"text": "网络安全威胁数量同比增长了35%。", "topic": "security"},
    {"text": "量子计算机的量子比特数已达到1000个。", "topic": "quantum"},
    {"text": "气候变化导致极端天气事件频率增加了40%。", "topic": "climate"},
    {"text": "新材料科学正在推动电池技术革命。", "topic": "materials"},
    {"text": "人工智能伦理问题成为全球关注焦点。", "topic": "ai_ethics"},
    {"text": "神经科学揭示了记忆形成的分子机制。", "topic": "neuroscience"},
    {"text": "天体物理学家发现了新的系外行星。", "topic": "astrophysics"},
    {"text": "量子通信网络已开始商业化部署。", "topic": "quantum"},
    {"text": "生物信息学工具加速了基因组测序分析。", "topic": "bioinformatics"},
]

EVIDENCE_TEMPLATES = [
    {"description": "A peer-reviewed study published in {source}", "weight": 0.85},
    {"description": "Government report from {source}", "weight": 0.80},
    {"description": "Industry whitepaper by {source}", "weight": 0.70},
    {"description": "Preprint research from {source}", "weight": 0.60},
    {"description": "News report citing {source}", "weight": 0.55},
    {"description": "Academic conference presentation at {source}", "weight": 0.75},
    {"description": "Meta-analysis covering data from {source}", "weight": 0.90},
    {"description": "Expert interview published in {source}", "weight": 0.65},
]

CLAIM_TEMPLATES = [
    "Based on empirical data collected over {years} years",
    "Verified through replication by {verifiers} independent teams",
    "Supported by {count} separate studies",
    "Statistical analysis shows p-value < {pvalue}",
    "Cross-referenced with {count} authoritative sources",
    "Validated against {dataset} benchmark dataset",
    "Consistent with findings from {source} 2023 report",
    "Contradicted by newer evidence from {source}",
]


def check_existing_data():
    """Check if data already exists to make seed idempotent."""
    existing = db.records.find({"labels": ["AGENT"], "limit": 1})
    return existing.total > 0


def seed_sources():
    """Create all sources."""
    print("Creating sources...")
    sources = []
    for i, src in enumerate(SOURCES):
        source = db.records.create(
            label="SOURCE",
            data={
                "name": src["name"],
                "type": src["type"],
                "base_reliability": src["base_reliability"],
                "total_citations": random.randint(10, 500),
                "accuracy_score": src["base_reliability"] + random.uniform(-0.05, 0.05),
            }
        )
        sources.append(source)
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(SOURCES)} sources")
    return sources


def seed_agents():
    """Create all agents."""
    print("Creating agents...")
    agents = []
    for i, agent_data in enumerate(AGENTS):
        agent = db.records.create(
            label="AGENT",
            data={
                "name": agent_data["name"],
                "specialty": agent_data["specialty"],
                "base_trust": agent_data["base_trust"],
                "total_responses": random.randint(50, 500),
                "successful_verifications": random.randint(30, 400),
                "reliability_score": agent_data["base_trust"] + random.uniform(-0.05, 0.05),
            }
        )
        agents.append(agent)
        if (i + 1) % 4 == 0:
            print(f"  Created {i + 1}/{len(AGENTS)} agents")
    return agents


def seed_responses(agents):
    """Create all responses with links to agents."""
    print("Creating responses...")
    responses = []
    for i, resp_data in enumerate(RESPONSES):
        agent = random.choice(agents)
        response = db.records.create(
            label="RESPONSE",
            data={
                "text": resp_data["text"],
                "topic": resp_data["topic"],
                "generated_at": "2024-01-15T10:30:00Z",
                "confidence": random.uniform(0.5, 0.95),
            }
        )
        # Attach response to agent
        db.records.attach(
            source=agent,
            target=response,
            options={"type": "GENERATED", "direction": "out"}
        )
        responses.append(response)
        if (i + 1) % 5 == 0:
            print(f"  Created {i + 1}/{len(RESPONSES)} responses")
    return responses


def seed_evidence_and_claims(responses, sources):
    """Create evidence with claims linked to sources."""
    print("Creating evidence and claims...")
    evidence_count = 0
    total_evidence = 40
    
    evidence_list = []
    
    for i in range(total_evidence):
        response = random.choice(responses)
        source = random.choice(sources)
        template = random.choice(EVIDENCE_TEMPLATES)
        
        # Determine if supporting or contradicting
        is_supporting = random.random() > 0.2  # 80% supporting, 20% contradicting
        relationship_type = "SUPPORTS" if is_supporting else "CONTRADICTS"
        
        # Create evidence
        evidence = db.records.create(
            label="EVIDENCE",
            data={
                "description": template["description"].format(source=source["name"]),
                "weight": template["weight"],
                "type": relationship_type,
                "veracity_score": template["weight"] * source.data["base_reliability"],
                "created_at": "2024-01-10T08:00:00Z",
            }
        )
        evidence_list.append(evidence)
        
        # Attach evidence to response
        db.records.attach(
            source=evidence,
            target=response,
            options={"type": relationship_type, "direction": "out"}
        )
        
        # Create claim
        claim_template = random.choice(CLAIM_TEMPLATES)
        claim = db.records.create(
            label="CLAIM",
            data={
                "statement": claim_template.format(
                    years=random.randint(3, 20),
                    verifiers=random.randint(2, 10),
                    count=random.randint(3, 20),
                    pvalue=random.choice(["0.01", "0.05", "0.001", "0.0001"]),
                    source=random.choice(["Nature", "Science", "arXiv"]),
                    dataset=random.choice(["ImageNet", "GLUE", "SQuAD"]),
                ),
                "confidence": random.uniform(0.6, 0.95),
            }
        )
        
        # Link claim to evidence
        db.records.attach(
            source=claim,
            target=evidence,
            options={"type": "MAKES", "direction": "out"}
        )
        
        # Link claim to source
        db.records.attach(
            source=claim,
            target=source,
            options={"type": "CITES", "direction": "out"}
        )
        
        evidence_count += 1
        if (evidence_count) % 10 == 0:
            print(f"  Created {evidence_count}/{total_evidence} evidence pieces")
    
    return evidence_list


def seed_vouching_relationships(agents):
    """Create agent vouching relationships."""
    print("Creating agent vouching relationships...")
    vouch_count = 0
    
    for agent in agents:
        # Each agent vouches for 1-2 other agents
        vouches_for = random.sample([a for a in agents if a.id != agent.id], k=random.randint(1, 2))
        for vouched in vouches_for:
            db.records.attach(
                source=agent,
                target=vouched,
                options={"type": "VOUCHES_FOR", "direction": "out"}
            )
            vouch_count += 1
    
    print(f"  Created {vouch_count} vouching relationships")


def main():
    print("\n" + "=" * 50)
    print("Trust Scoring Agents - Data Seeding")
    print("=" * 50 + "\n")
    
    # Check for existing data
    if check_existing_data():
        print("Data already exists. Skipping seed to maintain idempotency.")
        print("Delete existing records to re-seed.\n")
        
        # Count existing records
        agents = db.records.find({"labels": ["AGENT"], "limit": 100})
        responses = db.records.find({"labels": ["RESPONSE"], "limit": 100})
        evidence = db.records.find({"labels": ["EVIDENCE"], "limit": 100})
        sources = db.records.find({"labels": ["SOURCE"], "limit": 100})
        
        print(f"Existing data: {agents.total} agents, {responses.total} responses, "
              f"{evidence.total} evidence, {sources.total} sources")
        return
    
    # Seed all data
    sources = seed_sources()
    print()
    
    agents = seed_agents()
    print()
    
    responses = seed_responses(agents)
    print()
    
    evidence = seed_evidence_and_claims(responses, sources)
    print()
    
    seed_vouching_relationships(agents)
    print()
    
    print("\n" + "=" * 50)
    print("Seeding complete!")
    print(f"  Created {len(AGENTS)} agents")
    print(f"  Created {len(RESPONSES)} responses")
    print(f"  Created {len(evidence)} evidence pieces")
    print(f"  Created {len(SOURCES)} sources")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
