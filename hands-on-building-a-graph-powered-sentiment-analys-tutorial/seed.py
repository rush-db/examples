#!/usr/bin/env python3
"""
Seed script for the Graph-Powered Sentiment Analysis Pipeline.

Generates realistic mock data (products, customers, reviews with sentiment scores)
and imports it into RushDB. Idempotent—safe to run multiple times.

Usage:
    python seed.py
"""

import os
import random
from datetime import datetime, timedelta
from textblob import TextBlob

from dotenv import load_dotenv
from faker import Faker

from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
db = RushDB(api_key=os.environ.get("RUSHDB_API_KEY"))

# Initialize Faker for realistic data
fake = Faker()
Faker.seed(42)
random.seed(42)

# Product categories with sample products
PRODUCT_CATALOG = {
    "Electronics": [
        ("Wireless Bluetooth Headphones", 79.99, "SoundWave Audio"),
        ("Smartphone Stand with USB Charging", 29.99, "DeskMate"),
        ("4K Webcam with Microphone", 89.99, "VisionTech"),
        ("Mechanical Keyboard RGB", 119.99, "KeyMaster Pro"),
        ("Portable SSD 1TB", 109.99, "DataFast"),
        ("Noise Cancelling Earbuds", 149.99, "SoundWave Audio"),
        ("Smart Watch Fitness Tracker", 199.99, "TechFit"),
        ("USB-C Hub 7-in-1", 49.99, "DeskMate"),
        ("Laptop Cooling Pad", 34.99, "CoolTech"),
        ("Wireless Mouse Ergonomic", 44.99, "ErgoWorks"),
    ],
    "Clothing": [
        ("Cotton T-Shirt Classic Fit", 24.99, "BasicWear"),
        ("Denim Jeans Relaxed Fit", 59.99, "JeanCo"),
        ("Running Shoes Lightweight", 89.99, "SpeedStep"),
        ("Wool Sweater Crew Neck", 79.99, "WarmAndSoft"),
        ("Waterproof Rain Jacket", 99.99, "WeatherPro"),
        ("Athletic Shorts Quick-Dry", 34.99, "SpeedStep"),
        ("Casual Button-Down Shirt", 44.99, "BasicWear"),
        ("Winter Boots Insulated", 129.99, "WeatherPro"),
        ("Canvas Sneakers Low-Top", 54.99, "StreetStyle"),
        ("Performance Hoodie", 49.99, "SpeedStep"),
    ],
    "Home & Garden": [
        ("Indoor Plant Pot Ceramic", 19.99, "GreenThumb"),
        ("LED Desk Lamp Adjustable", 39.99, "BrightLight"),
        ("Memory Foam Pillow", 34.99, "ComfortSleep"),
        ("Stainless Steel Water Bottle", 24.99, "EcoDrink"),
        ("Bamboo Cutting Board Set", 29.99, "KitchenPro"),
        ("Scented Candle Collection", 22.99, "CozyHome"),
        ("Storage Basket Woven", 18.99, "HomeStyle"),
        ("Garden Tool Set 5-Piece", 49.99, "GreenThumb"),
        ("Blackout Curtains 84 inch", 44.99, "WindowTreat"),
        ("Electric Kettle 1.7L", 39.99, "BrewMaster"),
    ],
}

# Review templates for sentiment generation
POSITIVE_REVIEW_TEMPLATES = [
    "Absolutely love this product! Exceeded all my expectations. Highly recommend to anyone looking for quality.",
    "Best purchase I've made in a while. The build quality is excellent and it works perfectly.",
    "Fantastic value for money. Does exactly what it's supposed to do and more.",
    "Very impressed with the performance. Customer service was also outstanding when I had questions.",
    "Five stars all around! This has become an essential part of my daily routine.",
    "Great product, great price. Shipping was fast and everything arrived in perfect condition.",
    "Outstanding quality and craftsmanship. You can tell a lot of thought went into the design.",
    "This exceeded my expectations! Will definitely be buying again.",
    "Reliable and well-made. Works flawlessly. Couldn't be happier with this purchase.",
    "Perfect for my needs. The attention to detail is remarkable.",
]

NEGATIVE_REVIEW_TEMPLATES = [
    "Terrible quality. Broke after just a few uses. Do not recommend.",
    "Disappointed with this purchase. The product doesn't match the description at all.",
    "Poor build quality and the performance is subpar. Save your money.",
    "Not worth the price. There are much better alternatives available.",
    "Arrived damaged and customer support was unhelpful. Very frustrated with this experience.",
    "Completely unusable. Returned it immediately. Worst purchase ever.",
    "Falls apart easily. Should have read the negative reviews before buying.",
    "Defective product received. The quality control seems nonexistent.",
    "Overpriced for what you get. Definitely look elsewhere.",
    "Stopped working after one week. Very disappointed.",
]

NEUTRAL_REVIEW_TEMPLATES = [
    "It's okay. Does the job but nothing special. Average quality.",
    "Decent product for the price. Some pros and some cons.",
    "Works as expected. Nothing to complain about but nothing impressive either.",
    "Basic functionality is there. Might be worth it on sale.",
    "Average product overall. Gets the job done but has some room for improvement.",
    "Not bad, not great. Just an average product in its category.",
    "Mixed feelings about this. Some features work well, others are lacking.",
    "It's fine for occasional use but I wouldn't rely on it daily.",
    "Acceptable quality for the price point. Meets basic expectations.",
    "Standard product. Does what it says without fanfare.",
]


def analyze_sentiment(text: str) -> tuple[float, str]:
    """
    Analyze text sentiment using TextBlob.
    Returns tuple of (polarity_score, sentiment_label).
    """
    blob = TextBlob(text)
    score = blob.sentiment.polarity
    
    if score < -0.1:
        label = "negative"
    elif score > 0.1:
        label = "positive"
    else:
        label = "neutral"
    
    return round(score, 2), label


def generate_review_sentiment() -> tuple[str, float, str, int]:
    """
    Generate a review with sentiment analysis.
    Returns (review_text, sentiment_score, sentiment_label, rating).
    """
    # Weighted distribution: 40% positive, 35% neutral, 25% negative
    rand = random.random()
    
    if rand < 0.40:
        templates = POSITIVE_REVIEW_TEMPLATES
        rating = random.randint(4, 5)
    elif rand < 0.65:
        templates = NEUTRAL_REVIEW_TEMPLATES
        rating = 3
    else:
        templates = NEGATIVE_REVIEW_TEMPLATES
        rating = random.randint(1, 2)
    
    # Add some variation to reviews
    base_text = random.choice(templates)
    
    # Sometimes add extra sentences
    if random.random() > 0.5:
        extra_sentences = [
            " Would buy again.",
            " Delivery was quick too.",
            " Easy to set up.",
            " Matches the photos exactly.",
            " Packaging was secure.",
        ]
        if rating >= 4:
            base_text += random.choice(extra_sentences)
        else:
            base_text += " Not impressed."
    
    score, label = analyze_sentiment(base_text)
    return base_text, score, label, rating


def seed_database():
    """Seed RushDB with products, customers, and reviews."""
    print("\n" + "=" * 60)
    print("Seeding RushDB with sentiment analysis data...")
    print("=" * 60)
    
    # Check if data already exists
    existing_products = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    if existing_products:
        print("\n⚠️  Data already exists in the database.")
        print("   Run cleanup first or skip seeding.")
        print("   To re-seed, delete existing records first.")
        return {
            "products_created": 0,
            "customers_created": 0,
            "reviews_created": 0
        }
    
    products_created = 0
    customers_created = 0
    reviews_created = 0
    
    # Create products
    print("\n[1/3] Creating products...")
    product_records = {}
    
    with db.transactions.begin() as tx:
        for category, items in PRODUCT_CATALOG.items():
            for name, price, brand in items:
                product = db.records.create(
                    label="PRODUCT",
                    data={
                        "name": name,
                        "category": category,
                        "brand": brand,
                        "price": round(price, 2),
                    },
                    transaction=tx
                )
                product_records[name] = product
                products_created += 1
                
                if products_created % 10 == 0:
                    print(f"   Created {products_created} products...")
    
    print(f"   ✓ Created {products_created} products")
    
    # Create customers
    print("\n[2/3] Creating customers...")
    membership_tiers = ["basic", "silver", "gold", "platinum"]
    customer_records = []
    
    with db.transactions.begin() as tx:
        for i in range(30):
            customer = db.records.create(
                label="CUSTOMER",
                data={
                    "name": fake.name(),
                    "email": fake.email(),
                    "membership_tier": random.choice(membership_tiers),
                    "join_date": fake.date_between(start_date="-2y", end_date="today").isoformat(),
                },
                transaction=tx
            )
            customer_records.append(customer)
            customers_created += 1
            
            if customers_created % 10 == 0:
                print(f"   Created {customers_created} customers...")
    
    print(f"   ✓ Created {customers_created} customers")
    
    # Create reviews with sentiment analysis
    print("\n[3/3] Creating reviews with sentiment analysis...")
    
    review_count = 0
    reviews_per_product = 5  # Each product gets ~5 reviews
    
    for product_name, product in product_records.items():
        # Number of reviews per product (2-8, with clustering)
        num_reviews = random.randint(2, 8)
        
        batch_reviews = []
        for _ in range(num_reviews):
            customer = random.choice(customer_records)
            review_text, sentiment_score, sentiment_label, rating = generate_review_sentiment()
            
            # Generate review date
            days_ago = random.randint(1, 365)
            review_date = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            review_data = {
                "content": review_text,
                "rating": rating,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "verified_purchase": random.random() > 0.2,  # 80% verified
                "helpful_count": random.randint(0, 50),
                "review_date": review_date,
            }
            batch_reviews.append((review_data, customer, product))
        
        # Batch create reviews in a transaction
        with db.transactions.begin() as tx:
            for review_data, customer, product in batch_reviews:
                review = db.records.create(
                    label="REVIEW",
                    data=review_data,
                    transaction=tx
                )
                
                # Attach relationships
                db.records.attach(
                    source=review,
                    target=product,
                    options={"type": "REVIEWED", "direction": "out"},
                    transaction=tx
                )
                
                db.records.attach(
                    source=customer,
                    target=review,
                    options={"type": "WRITTEN_BY", "direction": "out"},
                    transaction=tx
                )
                
                reviews_created += 1
                review_count += 1
                
                if review_count % 50 == 0:
                    print(f"   Created {review_count} reviews...")
    
    print(f"   ✓ Created {reviews_created} reviews with sentiment scores")
    
    # Summary
    print("\n" + "=" * 60)
    print("Seeding complete!")
    print("=" * 60)
    print(f"  Products:  {products_created}")
    print(f"  Customers: {customers_created}")
    print(f"  Reviews:   {reviews_created}")
    print("\nRun `python main.py` to analyze the data.")
    
    return {
        "products_created": products_created,
        "customers_created": customers_created,
        "reviews_created": reviews_created,
    }


if __name__ == "__main__":
    seed_database()
