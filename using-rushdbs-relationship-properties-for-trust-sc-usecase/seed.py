"""
Seed script for trust-scored retrieval demo.

Creates a content moderation scenario with:
- Verified users (with varying trust scores)
- Articles with semantic content
- Verification relationships with trust scores stored on edges

The script is idempotent: it checks for existing data before creating.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

load_dotenv()

# Initialize RushDB client
db = RushDB(os.environ["RUSHD_API_TOKEN"])

# Mock data: verified users with trust scores
USERS = [
    {"name": "Dr. Sarah Chen", "trust_score": 0.99, "expertise": "Machine Learning"},
    {"name": "Marcus Johnson", "trust_score": 0.95, "expertise": "Software Engineering"},
    {"name": "Elena Rodriguez", "trust_score": 0.88, "expertise": "Data Science"},
    {"name": "James Wilson", "trust_score": 0.75, "expertise": "Technology"},
    {"name": "Anonymous User", "trust_score": 0.45, "expertise": "General"},
]

# Mock articles with semantic content
ARTICLES = [
    {
        "title": "Understanding Neural Networks: A Practical Guide",
        "category": "tech",
        "body": "Neural networks are computational models inspired by biological neural networks. They consist of layers of interconnected nodes or neurons that process data using connectionist approaches. Deep learning has revolutionized computer vision and natural language processing applications. Machine learning practitioners use frameworks like TensorFlow and PyTorch to build and train these models.",
    },
    {
        "title": "Introduction to Transformer Architecture",
        "category": "tech",
        "body": "Transformers represent a breakthrough in sequence modeling tasks. Unlike recurrent neural networks, transformers use self-attention mechanisms to process input sequences in parallel. BERT and GPT models built on transformer architecture have achieved state-of-the-art results in NLP. The attention mechanism allows models to weigh the importance of different parts of the input.",
    },
    {
        "title": "Python Best Practices for Data Engineering",
        "category": "tech",
        "body": "Data engineering requires robust Python code practices. Use type hints and dataclasses for better code clarity. Implement proper error handling and logging. Consider using Apache Airflow for workflow orchestration. Database connections should use connection pooling to improve performance.",
    },
    {
        "title": "React Performance Optimization Techniques",
        "category": "tech",
        "body": "Building performant React applications requires understanding virtual DOM reconciliation. Use React.memo and useMemo for preventing unnecessary re-renders. Implement code splitting with React.lazy for better initial load times. Profile applications with React DevTools Profiler to identify bottlenecks.",
    },
    {
        "title": "Understanding COVID-19 Vaccines",
        "category": "health",
        "body": "mRNA vaccines represent a breakthrough in immunization technology. These vaccines teach cells how to make proteins that trigger immune responses. The Pfizer and Moderna vaccines demonstrated high efficacy rates in clinical trials. Side effects are generally mild and temporary. Vaccination remains the most effective tool against severe disease.",
    },
    {
        "title": "Mental Health Benefits of Regular Exercise",
        "category": "health",
        "body": "Physical activity has profound effects on mental well-being. Aerobic exercise reduces symptoms of anxiety and depression. Endorphins released during exercise improve mood and energy levels. Regular workout routines establish healthy habits that support overall mental health. Even short walks can make significant differences.",
    },
    {
        "title": "Understanding Heart Disease Risk Factors",
        "category": "health",
        "body": "Cardiovascular disease remains the leading cause of death globally. Risk factors include high blood pressure, cholesterol, and smoking. Lifestyle modifications can significantly reduce risk. Mediterranean diet and regular exercise provide protective benefits. Regular medical checkups help identify risk factors early.",
    },
    {
        "title": "Nutritional Guidelines for Athletes",
        "category": "health",
        "body": "Athletes require optimized nutrition for performance and recovery. Carbohydrate loading before events provides sustained energy. Protein intake supports muscle repair and growth. Hydration affects performance more than any other factor. Micronutrients like iron and vitamin D are commonly deficient in athletes.",
    },
    {
        "title": "Economic Impact of Climate Policy",
        "category": "politics",
        "body": "Climate policy creates complex economic trade-offs. Carbon pricing mechanisms internalize environmental externalities. Green infrastructure investments generate employment in new sectors. Transition costs affect fossil fuel dependent communities. Economists debate optimal policy instruments for emissions reduction.",
    },
    {
        "title": "Understanding Electoral Systems",
        "category": "politics",
        "body": "Different electoral systems produce varied political outcomes. First-past-the-post favors two-party systems. Proportional representation enables broader representation. Mixed systems attempt to balance these considerations. Electoral reform remains politically contentious in established democracies.",
    },
    {
        "title": "Healthcare Policy Comparison",
        "category": "politics",
        "body": "Healthcare systems vary significantly across developed nations. Single-payer systems guarantee universal coverage but may face rationing. Multi-payer systems offer choice but create administrative complexity. Cost control mechanisms include price negotiations and reference pricing. Reform debates continue across political spectrums.",
    },
    {
        "title": "Data Privacy Regulations Explained",
        "category": "politics",
        "body": "GDPR transformed data privacy expectations globally. CCPA gives California residents expanded control over their data. Privacy regulations create compliance burdens for businesses. Enforcement mechanisms vary in effectiveness across jurisdictions. Privacy advocates argue for stronger protections.",
    },
    {
        "title": "Getting Started with Kubernetes",
        "category": "tech",
        "body": "Kubernetes automates deployment and management of containerized applications. Pods represent the smallest deployable units in the Kubernetes model. Services provide stable networking for dynamic pod deployments. Helm charts simplify complex application configurations. GitOps workflows automate infrastructure changes through version control.",
    },
    {
        "title": "Introduction to Graph Databases",
        "category": "tech",
        "body": "Graph databases excel at modeling connected data relationships. Neo4j uses the property graph model with nodes and relationships. Cypher provides expressive query capabilities for graph traversal. Use cases include social networks, recommendation engines, and fraud detection. Graph databases handle relationship-focused queries efficiently.",
    },
    {
        "title": "Understanding Quantum Computing Basics",
        "category": "tech",
        "body": "Quantum computers leverage quantum mechanical phenomena for computation. Qubits can exist in superposition of zero and one states. Quantum entanglement enables correlations impossible in classical systems. Error correction remains a significant challenge for practical quantum computers. Companies like IBM and Google are racing to achieve quantum advantage.",
    },
    {
        "title": "Sleep Science and Optimal Rest",
        "category": "health",
        "body": "Sleep quality significantly impacts cognitive function and health. Circadian rhythms regulate the sleep-wake cycle through melatonin. REM sleep plays crucial roles in memory consolidation. Sleep debt accumulates and affects performance for days. Consistent sleep schedules improve overall sleep quality.",
    },
    {
        "title": "The Science of Meditation",
        "category": "health",
        "body": "Meditation practices demonstrate measurable effects on brain structure. Regular meditation increases gray matter in prefrontal cortex. Mindfulness reduces activity in the default mode network. Studies show benefits for attention, emotional regulation, and stress. Even brief daily practice yields measurable improvements.",
    },
    {
        "title": "Understanding Inflation Economics",
        "category": "politics",
        "body": "Inflation erodes purchasing power of money over time. Central banks target inflation rates around two percent for stability. Demand-pull and cost-push mechanisms drive different inflation types. Unexpected inflation benefits debtors at expense of savers. Monetary policy tools control money supply and interest rates.",
    },
    {
        "title": "Space Exploration Budget Analysis",
        "category": "politics",
        "body": "Space agency budgets spark debates about national priorities. NASA budget represents less than one percent of federal spending. Private companies like SpaceX reduce launch costs dramatically. Mars colonization proposals require unprecedented funding levels. International cooperation on space missions faces geopolitical challenges.",
    },
    {
        "title": "Renewable Energy Transition Economics",
        "category": "politics",
        "body": "Energy transition creates winners and losers across industries. Solar and wind costs declined faster than predicted. Battery storage improvements enable higher renewable penetration. Grid modernization requires substantial investment. Job losses in fossil fuel sectors create political resistance to transition policies.",
    },
]


def check_data_exists():
    """Check if seed data already exists."""
    existing_users = db.records.find({"labels": ["USER"], "limit": 1})
    return len(existing_users.data) > 0


def seed_data():
    """Create users, articles, and verification relationships."""
    print("\n" + "=" * 60)
    print("SEEDING TRUST-SCORED RETRIEVAL DEMO DATA")
    print("=" * 60)

    # Check for existing data
    if check_data_exists():
        print("\n[SKIP] Data already exists. Deleting existing records first...")
        db.records.delete({"labels": ["USER"]})
        db.records.delete({"labels": ["ARTICLE"]})

    # Create users with trust scores
    print("\n[1/3] Creating verified users...")
    user_records = []
    for i, user_data in enumerate(USERS):
        user = db.records.create(
            label="USER",
            data={
                "name": user_data["name"],
                "expertise": user_data["expertise"],
                "trust_score": user_data["trust_score"],
                "verified": True,
            }
        )
        user_records.append(user)
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} users...")
    print(f"  ✓ Created {len(user_records)} users")

    # Create articles with body content (vectors will be indexed)
    print("\n[2/3] Creating articles with vector embeddings...")
    article_records = []
    for i, article_data in enumerate(ARTICLES):
        # Note: For production use, you'd pre-compute embeddings
        # For this demo, we create the records; vector index will be created in main.py
        article = db.records.create(
            label="ARTICLE",
            data={
                "title": article_data["title"],
                "category": article_data["category"],
                "body": article_data["body"],
                "word_count": len(article_data["body"].split()),
            },
            vectors=[{"propertyName": "body", "vector": [0.0] * 768}]  # Placeholder, re-indexed in main.py
        )
        article_records.append(article)
        if (i + 1) % 100 == 0:
            print(f"  Created {i + 1} articles...")
    print(f"  ✓ Created {len(article_records)} articles")

    # Create verification relationships with trust scores
    print("\n[3/3] Creating trust relationships (VERIFIED_BY edges)...")
    verification_count = 0
    for article in article_records:
        # Assign 1-4 random verifiers to each article
        num_verifiers = random.randint(1, 4)
        verifiers = random.sample(user_records, num_verifiers)

        for verifier in verifiers:
            # Create relationship from article to user with trust_score property
            # Lower trust users have lower probability of verification
            if random.random() < (verifier["trust_score"] / 1.0):
                db.records.attach(
                    source=article,
                    target=verifier,
                    options={
                        "type": "VERIFIED_BY",
                        "direction": "out",
                        "properties": {
                            "trust_score": verifier["trust_score"],
                            "verified_at": "2024-01-15T10:30:00Z",
                        }
                    }
                )
                verification_count += 1

    print(f"  ✓ Created {verification_count} verification relationships")
    print("\n" + "=" * 60)
    print("SEEDING COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  - {len(user_records)} users with trust scores")
    print(f"  - {len(article_records)} articles with body content")
    print(f"  - {verification_count} VERIFIED_BY relationships")
    print(f"\nNext: Run `python main.py` to demonstrate trust-scored retrieval\n")


if __name__ == "__main__":
    seed_data()
