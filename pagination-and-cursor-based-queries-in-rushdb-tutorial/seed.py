#!/usr/bin/env python3
"""
Seed script for pagination tutorial.
Creates 100 mock articles across 5 categories for pagination demos.

Run this once before main.py to populate the database.
Safe to run multiple times - checks for existing data.
"""

import os
import random
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

db = RushDB(API_KEY)

# Categories for articles
CATEGORIES = ["technology", "science", "business", "health", "general"]

# Article titles by category
ARTICLE_TITLES = {
    "technology": [
        "The Future of AI in Software Development",
        "Cloud Computing Trends for 2025",
        "Cybersecurity Best Practices",
        "Machine Learning Model Optimization",
        "DevOps Automation Strategies",
    ],
    "science": [
        "Breakthroughs in Quantum Computing",
        "Climate Change Research Update",
        "Space Exploration Missions",
        "Genomics and Personalized Medicine",
        "Renewable Energy Innovations",
    ],
    "business": [
        "Startup Funding Strategies",
        "Remote Work Management Tips",
        "Digital Marketing Trends",
        "Supply Chain Optimization",
        "Leadership in Uncertain Times",
    ],
    "health": [
        "Mental Health in the Workplace",
        "Nutrition Science Update",
        "Exercise and Longevity Research",
        "Sleep Quality Studies",
        "Preventive Healthcare Tips",
    ],
    "general": [
        "Time Management Techniques",
        "Productivity Hacks for Professionals",
        "Work-Life Balance Strategies",
        "Communication Skills Development",
        "Critical Thinking Exercises",
    ],
}


def check_existing_data() -> bool:
    """Check if articles already exist in the database."""
    result = db.records.find({"labels": ["ARTICLE"], "limit": 1})
    return result.total > 0


def clean_existing_data():
    """Remove existing tutorial articles for a fresh start."""
    print("Cleaning existing tutorial data...")
    db.records.delete({"labels": ["ARTICLE"], "where": {"tutorial_seed": True}})
    print("Existing data cleaned.")


def generate_articles() -> list[dict]:
    """Generate 100 mock articles with realistic content."""
    articles = []
    
    for i in range(100):
        # Distribute across categories
        category = CATEGORIES[i % len(CATEGORIES)]
        base_title = random.choice(ARTICLE_TITLES[category])
        
        # Create unique article data
        article = {
            "slug": f"article-{i}",
            "title": f"{base_title} #{i}",
            "category": category,
            "content": f"This is the content for article {i}. It contains detailed information about {category} topics.",
            "views": random.randint(10, 10000),
            "rating": round(random.uniform(3.0, 5.0), 1),
            "published": random.choice([True, False]),
            "tutorial_seed": True,  # Marker for cleanup
        }
        articles.append(article)
        
        if (i + 1) % 20 == 0:
            print(f"  Generated {i + 1}/100 articles...")
    
    return articles


def seed_database():
    """Main seeding function."""
    print("\n=== RushDB Pagination Tutorial - Data Seeder ===\n")
    
    # Check for existing data
    if check_existing_data():
        print("Found existing tutorial data.")
        response = input("Do you want to reset? (y/N): ").strip().lower()
        if response == "y":
            clean_existing_data()
        else:
            print("Keeping existing data. Run main.py to continue.")
            return
    
    # Generate articles
    print("Generating 100 mock articles...")
    articles = generate_articles()
    
    # Batch create in chunks of 25
    print("\nImporting articles to RushDB...")
    for i in range(0, len(articles), 25):
        chunk = articles[i:i + 25]
        db.records.create_many(label="ARTICLE", data=chunk)
        print(f"  Imported {min(i + 25, len(articles))}/{len(articles)} articles...")
    
    print(f"\n✓ Successfully seeded {len(articles)} articles")
    print("\nRun 'python main.py' to see pagination demos.")


if __name__ == "__main__":
    seed_database()
