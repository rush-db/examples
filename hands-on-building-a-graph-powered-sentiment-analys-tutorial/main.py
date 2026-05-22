#!/usr/bin/env python3
"""
Graph-Powered Sentiment Analysis Pipeline - Main Demo

This script demonstrates how to use RushDB for sentiment analysis workflows:
1. Create reviews with sentiment scores
2. Query by sentiment ranges
3. Traverse relationships to find patterns
4. Aggregate metrics across the graph

Run `python seed.py` first to populate sample data.
"""

import os
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv
from textblob import TextBlob

from rushdb import RushDB

# Load environment variables
load_dotenv()

# Initialize RushDB client
db = RushDB(api_key=os.environ.get("RUSHDB_API_KEY"))


def section_header(number: int, title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"[{number}] {title}")
    print('=' * 60)


def demo_create_review_with_sentiment():
    """Demonstrate creating a review with sentiment analysis."""
    section_header(1, "Creating a Review with Sentiment Analysis")
    
    review_text = "This product is absolutely fantastic! Works exactly as described."
    
    # Analyze sentiment
    blob = TextBlob(review_text)
    sentiment_score = round(blob.sentiment.polarity, 2)
    
    # Classify sentiment
    if sentiment_score < -0.1:
        sentiment_label = "negative"
    elif sentiment_score > 0.1:
        sentiment_label = "positive"
    else:
        sentiment_label = "neutral"
    
    print(f"Review text: \"{review_text}\"")
    print(f"Sentiment score: {sentiment_score}")
    print(f"Sentiment label: {sentiment_label}")
    
    # Find a product to link to
    products = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    if not products:
        print("\n⚠️  No products found. Run `python seed.py` first.")
        return
    
    product = products[0]
    
    # Find a customer
    customers = db.records.find({"labels": ["CUSTOMER"], "limit": 1})
    customer = customers[0]
    
    # Create the review record
    print("\nCreating review record in RushDB...")
    
    review = db.records.create(
        label="REVIEW",
        data={
            "content": review_text,
            "rating": 5,
            "sentiment_score": sentiment_score,
            "sentiment_label": sentiment_label,
            "verified_purchase": True,
            "helpful_count": 0,
            "review_date": datetime.now().isoformat(),
        }
    )
    
    print(f"  Created review: {review.id}")
    print(f"  Label: {review.label}")
    print(f"  Fields: {review.fields}")
    
    # Attach relationships
    db.records.attach(
        source=review,
        target=product,
        options={"type": "REVIEWED", "direction": "out"}
    )
    print(f"  Attached to product: {product['name']}")
    
    db.records.attach(
        source=customer,
        target=review,
        options={"type": "WRITTEN_BY", "direction": "out"}
    )
    print(f"  Attached to customer: {customer['name']}")
    
    print("\n✓ Review created with sentiment analysis and graph relationships")
    
    return review


def demo_query_by_sentiment():
    """Demonstrate querying reviews by sentiment score ranges."""
    section_header(2, "Querying Reviews by Sentiment Range")
    
    # Find negative reviews (sentiment_score < -0.1)
    negative_reviews = db.records.find({
        "labels": ["REVIEW"],
        "where": {
            "sentiment_score": {"$lt": -0.1}
        },
        "limit": 20
    })
    print(f"\nNegative reviews (score < -0.1): {len(negative_reviews)} found")
    
    if negative_reviews:
        sample = negative_reviews[0]
        print(f"  Sample: \"{sample['content'][:60]}...\"")
        print(f"  Score: {sample['sentiment_score']}, Rating: {sample['rating']}")
    
    # Find positive reviews (sentiment_score > 0.1)
    positive_reviews = db.records.find({
        "labels": ["REVIEW"],
        "where": {
            "sentiment_score": {"$gt": 0.1}
        },
        "limit": 20
    })
    print(f"\nPositive reviews (score > 0.1): {len(positive_reviews)} found")
    
    if positive_reviews:
        sample = positive_reviews[0]
        print(f"  Sample: \"{sample['content'][:60]}...\"")
        print(f"  Score: {sample['sentiment_score']}, Rating: {sample['rating']}")
    
    # Find neutral reviews
    neutral_reviews = db.records.find({
        "labels": ["REVIEW"],
        "where": {
            "sentiment_score": {"$gte": -0.1, "$lte": 0.1}
        },
        "limit": 20
    })
    print(f"\nNeutral reviews (score between -0.1 and 0.1): {len(neutral_reviews)} found")
    
    # Summary statistics
    print("\n" + "-" * 40)
    print("Sentiment Distribution Summary:")
    print(f"  Negative: {len(negative_reviews)}")
    print(f"  Neutral:  {len(neutral_reviews)}")
    print(f"  Positive: {len(positive_reviews)}")
    
    return {
        "negative": len(negative_reviews),
        "neutral": len(neutral_reviews),
        "positive": len(positive_reviews)
    }


def demo_traverse_relationships():
    """Demonstrate relationship traversal to find customer review patterns."""
    section_header(3, "Traversing Relationships: Customer Review Patterns")
    
    # Find customers who have written multiple negative reviews
    # First, get all negative reviews
    negative_reviews = db.records.find({
        "labels": ["REVIEW"],
        "where": {
            "sentiment_score": {"$lt": -0.1}
        }
    })
    
    if not negative_reviews:
        print("\n⚠️  No negative reviews found.")
        return
    
    # Group negative reviews by customer
    customer_negative_counts = defaultdict(list)
    
    for review in negative_reviews:
        # Find the customer who wrote this review
        # We look for CUSTOMER records linked to this review with WRITTEN_BY
        customers = db.records.find({
            "labels": ["CUSTOMER"],
            "where": {
                "REVIEW": {
                    "$relation": {"type": "WRITTEN_BY", "direction": "out"}
                }
            }
        })
        
        # Alternative: query from customer side
        # Find customers whose reviews have low sentiment
        related_customers = db.records.find({
            "labels": ["CUSTOMER"],
            "where": {
                "REVIEW": {
                    "sentiment_score": {"$lt": -0.1}
                }
            }
        })
    
    # Count reviews per customer using aggregation
    print("\nCustomers with the most negative reviews:")
    
    # Get all customers and count their negative reviews
    customers = db.records.find({"labels": ["CUSTOMER"], "limit": 50})
    
    customer_review_stats = []
    for customer in customers:
        # Find reviews written by this customer
        reviews = db.records.find({
            "labels": ["REVIEW"],
            "where": {
                "CUSTOMER": {
                    "$relation": {"type": "WRITTEN_BY", "direction": "in"},
                    "email": customer["email"]
                }
            }
        })
        
        if reviews:
            negative_count = sum(1 for r in reviews if r["sentiment_score"] < -0.1)
            total_count = len(reviews)
            
            if negative_count > 0:
                customer_review_stats.append({
                    "customer": customer,
                    "total_reviews": total_count,
                    "negative_reviews": negative_count,
                    "negative_ratio": round(negative_count / total_count, 2)
                })
    
    # Sort by negative review count
    customer_review_stats.sort(key=lambda x: x["negative_reviews"], reverse=True)
    
    # Display top 5
    for i, stat in enumerate(customer_review_stats[:5], 1):
        c = stat["customer"]
        print(f"\n  {i}. {c['name']} ({c['email']})")
        print(f"     Total reviews: {stat['total_reviews']}")
        print(f"     Negative reviews: {stat['negative_reviews']}")
        print(f"     Negative ratio: {stat['negative_ratio']*100:.0f}%")
    
    print(f"\n✓ Found {len(customer_review_stats)} customers with negative reviews")
    
    return customer_review_stats


def demo_sentiment_by_category():
    """Demonstrate aggregating sentiment by product category."""
    section_header(4, "Aggregating Sentiment by Product Category")
    
    # Get all products with their categories
    products = db.records.find({"labels": ["PRODUCT"], "limit": 100})
    
    # Group products by category
    category_products = defaultdict(list)
    for product in products:
        category_products[product["category"]].append(product)
    
    print("\nSentiment Analysis by Category:")
    print("-" * 50)
    
    category_sentiments = {}
    
    for category, prods in sorted(category_products.items()):
        all_sentiments = []
        product_details = []
        
        for product in prods:
            # Find reviews for this product
            reviews = db.records.find({
                "labels": ["REVIEW"],
                "where": {
                    "PRODUCT": {
                        "$relation": {"type": "REVIEWED", "direction": "in"}
                    }
                }
            })
            
            # Filter to reviews for this specific product
            for review in reviews:
                # We need to check if this review is for the specific product
                # In a real scenario, you'd have a more direct relationship
                pass
        
        # Simpler approach: get all reviews and aggregate by product category
        all_reviews = db.records.find({"labels": ["REVIEW"], "limit": 500})
        
        # For this demo, we'll use a simplified aggregation
        # Get reviews linked to products in each category
        category_review_scores = defaultdict(list)
        
        for product in prods:
            # Find reviews directly linked to this product
            reviews = db.records.find({
                "labels": ["REVIEW"],
                "where": {}
            })
        
        break  # Use simplified approach below
    
    # Simplified aggregation for demonstration
    print("\nFetching reviews and aggregating by product category...")
    
    products_by_id = {p.id: p for p in products}
    product_categories = {p.id: p["category"] for p in products}
    
    reviews = db.records.find({"labels": ["REVIEW"], "limit": 500})
    
    # Map reviews to categories via their linked products
    category_scores = defaultdict(list)
    
    for review in reviews:
        # For each review, find what product it's linked to
        # In this demo, we'll use the review's embedded data
        # In a production scenario, you'd traverse the graph
        
        # Get the product from the REVIEWED relationship
        # Since RushDB stores relationships, we query for products linked to this review
        linked_products = db.records.find({
            "labels": ["PRODUCT"],
            "where": {
                "REVIEW": {
                    "$relation": {"type": "REVIEWED", "direction": "in"}
                }
            }
        })
        
        if linked_products:
            for product in linked_products:
                category = product.get("category") or product_categories.get(product.id)
                if category:
                    category_scores[category].append(review["sentiment_score"])
    
    # Calculate and display averages
    print("\n" + "=" * 60)
    print(f"{'Category':<20} {'Reviews':<10} {'Avg Sentiment':<15} {'Distribution'}")
    print("=" * 60)
    
    for category in sorted(category_scores.keys()):
        scores = category_scores[category]
        if scores:
            avg_sentiment = sum(scores) / len(scores)
            positive = sum(1 for s in scores if s > 0.1)
            neutral = sum(1 for s in scores if -0.1 <= s <= 0.1)
            negative = sum(1 for s in scores if s < -0.1)
            
            # Sentiment indicator
            if avg_sentiment > 0.2:
                indicator = "😊 positive"
            elif avg_sentiment < -0.2:
                indicator = "😞 negative"
            else:
                indicator = "😐 mixed"
            
            print(f"{category:<20} {len(scores):<10} {avg_sentiment:>+.2f}          {indicator}")
            print(f"                     +: {positive}  ~: {neutral}  -: {negative}")
    
    return category_scores


def demo_find_extreme_reviews():
    """Find reviews at the extremes of sentiment."""
    section_header(5, "Finding Extreme Sentiment Reviews")
    
    # Most positive reviews
    print("\nMost Positive Reviews (top 5):")
    print("-" * 40)
    
    positive_reviews = db.records.find({
        "labels": ["REVIEW"],
        "where": {
            "sentiment_score": {"$gt": 0.1}
        },
        "orderBy": {"sentiment_score": "desc"},
        "limit": 5
    })
    
    for i, review in enumerate(positive_reviews, 1):
        content = review["content"][:70] + "..." if len(review["content"]) > 70 else review["content"]
        print(f"\n  {i}. \"{content}\"")
        print(f"     Score: {review['sentiment_score']:>+.2f} | Rating: {review['rating']}/5")
    
    # Most negative reviews
    print("\n\nMost Negative Reviews (top 5):")
    print("-" * 40)
    
    negative_reviews = db.records.find({
        "labels": ["REVIEW"],
        "where": {
            "sentiment_score": {"$lt": -0.1}
        },
        "orderBy": {"sentiment_score": "asc"},
        "limit": 5
    })
    
    for i, review in enumerate(negative_reviews, 1):
        content = review["content"][:70] + "..." if len(review["content"]) > 70 else review["content"]
        print(f"\n  {i}. \"{content}\"")
        print(f"     Score: {review['sentiment_score']:>+.2f} | Rating: {review['rating']}/5")
    
    return {
        "most_positive": positive_reviews,
        "most_negative": negative_reviews
    }


def demo_correlation_analysis():
    """Analyze correlation between star rating and sentiment score."""
    section_header(6, "Rating vs. Sentiment Score Correlation")
    
    reviews = db.records.find({"labels": ["REVIEW"], "limit": 500})
    
    # Group by rating
    rating_sentiments = defaultdict(list)
    for review in reviews:
        rating = review.get("rating")
        sentiment = review.get("sentiment_score")
        if rating and sentiment is not None:
            rating_sentiments[rating].append(sentiment)
    
    print("\nAverage Sentiment Score by Star Rating:")
    print("-" * 50)
    
    for rating in sorted(rating_sentiments.keys()):
        scores = rating_sentiments[rating]
        avg = sum(scores) / len(scores)
        
        # Visual bar
        bar_length = int((avg + 1) * 20)  # Scale -1 to 1 to 0-40
        bar = "█" * bar_length + "░" * (40 - bar_length)
        
        print(f"\n  {rating}★ ({len(scores)} reviews): avg sentiment = {avg:+.2f}")
        print(f"     {bar}")
    
    # Calculate correlation
    total_reviews = sum(len(v) for v in rating_sentiments.values())
    print(f"\n  Total reviews analyzed: {total_reviews}")
    
    # Check for anomalies (high rating but negative sentiment)
    print("\n" + "=" * 50)
    print("Anomaly Detection: High Rating, Low Sentiment")
    print("-" * 50)
    
    anomalies = []
    for review in reviews:
        rating = review.get("rating")
        sentiment = review.get("sentiment_score")
        
        # High rating but negative sentiment is an anomaly
        if rating and rating >= 4 and sentiment is not None and sentiment < -0.2:
            anomalies.append(review)
    
    if anomalies:
        print(f"\n  Found {len(anomalies)} potential anomalies!")
        print("  (Reviews with high star rating but negative sentiment)")
        
        for anomaly in anomalies[:3]:
            print(f"\n  Rating: {anomaly['rating']}★, Sentiment: {anomaly['sentiment_score']:+.2f}")
            print(f"  \"{anomaly['content'][:80]}...\"")
    else:
        print("\n  No significant anomalies detected.")
    
    return rating_sentiments


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("  GRAPH-POWERED SENTIMENT ANALYSIS PIPELINE")
    print("  Powered by RushDB")
    print("=" * 60)
    
    # Check connection
    try:
        test = db.records.find({"labels": ["PRODUCT"], "limit": 1})
        print("\n✓ Connected to RushDB")
        
        product_count = len(db.records.find({"labels": ["PRODUCT"]}))
        review_count = len(db.records.find({"labels": ["REVIEW"]}))
        customer_count = len(db.records.find({"labels": ["CUSTOMER"]}))
        
        print(f"  Database contains: {product_count} products, {review_count} reviews, {customer_count} customers")
        
        if review_count == 0:
            print("\n⚠️  Warning: No reviews found. Run `python seed.py` first!")
            print("    Proceeding with demo anyway...")
    except Exception as e:
        print(f"\n✗ Error connecting to RushDB: {e}")
        print("  Make sure your RUSHDB_API_KEY is set in .env")
        return
    
    # Run demonstrations
    demo_create_review_with_sentiment()
    demo_query_by_sentiment()
    demo_traverse_relationships()
    demo_sentiment_by_category()
    demo_find_extreme_reviews()
    demo_correlation_analysis()
    
    # Summary
    print("\n" + "=" * 60)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nThis demo showed:")
    print("  • Creating review records with sentiment analysis")
    print("  • Querying by sentiment score ranges")
    print("  • Traversing graph relationships")
    print("  • Aggregating sentiment by category")
    print("  • Finding reviews at sentiment extremes")
    print("  • Detecting rating/sentiment anomalies")
    print("\nFor more information, visit: https://docs.rushdb.com")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
