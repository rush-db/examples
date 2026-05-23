"""
Knowledge Staleness Detection and Adaptive Refresh Triggers

A comprehensive tutorial demonstrating how to build an intelligent knowledge
management system using RushDB's property graph capabilities.

This example implements:
1. Staleness scoring based on time decay, access frequency, and category priority
2. Adaptive refresh triggers with configurable thresholds
3. Dependency-aware refresh chains using graph relationships
4. Real-time priority queue generation for content maintenance
"""

import os
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from rushdb import RushDB

# Load environment variables
load_dotenv()

# =============================================================================
# Configuration
# =============================================================================

# Staleness scoring weights by category (higher = more critical)
CATEGORY_WEIGHTS = {
    "security": 2.0,
    "backend": 1.5,
    "devops": 1.2,
    "testing": 1.0,
    "general": 1.0,
}

# Refresh priority thresholds
REFRESH_THRESHOLDS = {
    "CRITICAL": 10.0,
    "HIGH": 5.0,
    "MEDIUM": 2.5,
    "LOW": 0.0,
}


# =============================================================================
# Staleness Detection
# =============================================================================

def calculate_staleness_score(article: Dict[str, Any]) -> float:
    """
    Calculate a staleness score for a knowledge article.
    
    The score combines:
    - Time decay: Articles become more stale over time (sqrt scaling)
    - Access frequency: Popular articles have higher urgency when stale
    - Category priority: Security content decays faster than general content
    
    Args:
        article: Article record with lastUpdated, viewCount, and category
    
    Returns:
        Staleness score (higher = more stale)
    """
    # Parse last update timestamp
    last_updated_str = article.get("lastUpdated", "")
    if not last_updated_str:
        return 0.0
    
    try:
        last_updated = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))
        days_since_update = (datetime.now() - last_updated).days
    except (ValueError, TypeError):
        days_since_update = 0
    
    # Get article metadata
    view_count = article.get("viewCount", 0)
    category = article.get("category", "general")
    
    # Get category weight
    category_weight = CATEGORY_WEIGHTS.get(category, 1.0)
    
    # Calculate components
    # Time component: sqrt decay - captures diminishing urgency over time
    time_component = math.sqrt(days_since_update) * 2.0
    
    # Access component: log scale - popular content has higher refresh urgency
    access_component = math.log1p(view_count) * 0.5
    
    # Combine with category weight
    base_score = (time_component + access_component) * category_weight
    
    return round(base_score, 2)


def get_refresh_priority(score: float) -> str:
    """
    Determine refresh priority based on staleness score.
    
    Args:
        score: Staleness score from calculate_staleness_score
    
    Returns:
        Priority level: CRITICAL, HIGH, MEDIUM, or LOW
    """
    if score >= REFRESH_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"
    elif score >= REFRESH_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif score >= REFRESH_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    else:
        return "LOW"


def analyze_article_staleness(article: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform comprehensive staleness analysis on an article.
    
    Args:
        article: Article record from RushDB
    
    Returns:
        Analysis result with score, priority, and recommendations
    """
    score = calculate_staleness_score(article)
    priority = get_refresh_priority(score)
    
    # Calculate days since update for display
    last_updated_str = article.get("lastUpdated", "")
    try:
        last_updated = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))
        days_since_update = (datetime.now() - last_updated).days
    except (ValueError, TypeError):
        days_since_update = 0
    
    # Generate recommendation based on priority
    recommendations = {
        "CRITICAL": "Update immediately - content is outdated and actively accessed",
        "HIGH": "Schedule update within 48 hours",
        "MEDIUM": "Consider updating in next sprint cycle",
        "LOW": "Monitor - content is reasonably current",
    }
    
    return {
        "title": article.get("title", "Untitled"),
        "category": article.get("category", "unknown"),
        "viewCount": article.get("viewCount", 0),
        "daysSinceUpdate": days_since_update,
        "stalenessScore": score,
        "priority": priority,
        "recommendation": recommendations.get(priority, "Unknown"),
    }


# =============================================================================
# Adaptive Refresh Triggers
# =============================================================================

class RefreshTriggerSystem:
    """
    Manages adaptive refresh triggers for knowledge articles.
    
    This system:
    - Monitors article staleness in real-time
    - Generates prioritized refresh queues
    - Respects configurable thresholds
    - Accounts for dependency chains
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        self.thresholds = REFRESH_THRESHOLDS.copy()
    
    def set_threshold(self, priority: str, value: float):
        """Update threshold for a specific priority level."""
        if priority in self.thresholds:
            self.thresholds[priority] = value
    
    def should_trigger_refresh(self, article: Dict[str, Any], min_priority: str = "HIGH") -> bool:
        """
        Determine if an article should trigger a refresh.
        
        Args:
            article: Article record
            min_priority: Minimum priority level to trigger (default: HIGH)
        
        Returns:
            True if refresh should be triggered
        """
        score = calculate_staleness_score(article)
        priority = get_refresh_priority(score)
        
        priority_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        return priority_order.index(priority) >= priority_order.index(min_priority)
    
    def generate_refresh_queue(self) -> List[Dict[str, Any]]:
        """
        Generate a prioritized refresh queue for all articles.
        
        Returns:
            Sorted list of articles requiring refresh, highest priority first
        """
        # Fetch all articles
        articles_result = self.db.records.find({
            "labels": ["Article"]
        })
        
        queue = []
        for article in articles_result.data:
            analysis = analyze_article_staleness(article)
            if analysis["priority"] != "LOW":
                queue.append(analysis)
        
        # Sort by staleness score (descending)
        queue.sort(key=lambda x: x["stalenessScore"], reverse=True)
        
        return queue
    
    def get_priority_counts(self) -> Dict[str, int]:
        """Get counts of articles by priority level."""
        articles_result = self.db.records.find({"labels": ["Article"]})
        
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for article in articles_result.data:
            score = calculate_staleness_score(article)
            priority = get_refresh_priority(score)
            counts[priority] += 1
        
        return counts


# =============================================================================
# Dependency-Aware Refresh
# =============================================================================

class DependencyRefreshManager:
    """
    Manages dependency chains for knowledge refresh operations.
    
    When one article needs refreshing, this system identifies
    and chains together all related articles that may also need updates.
    """
    
    def __init__(self, db: RushDB):
        self.db = db
    
    def get_refresh_dependencies(self, article_id: str) -> List[Dict[str, Any]]:
        """
        Find all articles that should be refreshed along with the given article.
        
        Args:
            article_id: ID of the primary article to refresh
        
        Returns:
            List of dependent articles that should be refreshed together
        """
        # Find RefreshLink records connected to this article
        refresh_links = self.db.records.find({
            "labels": ["RefreshLink"],
            "where": {
                "REQUIRES": {"$id": article_id}
            }
        })
        
        dependencies = []
        for link in refresh_links.data:
            # Find articles triggered by this link
            triggered = self.db.records.find({
                "labels": ["Article"],
                "where": {
                    "TRIGGERS": {"$id": link.id}
                }
            })
            for article in triggered.data:
                dependencies.append({
                    "title": article.get("title", "Unknown"),
                    "id": article.id,
                    "reason": "dependency_chain",
                })
        
        return dependencies
    
    def generate_refresh_plan(self, article_title: str) -> Dict[str, Any]:
        """
        Generate a complete refresh plan including dependencies.
        
        Args:
            article_title: Title of the article to refresh
        
        Returns:
            Refresh plan with primary article and all dependencies
        """
        # Find the article
        articles = self.db.records.find({
            "labels": ["Article"],
            "where": {
                "title": article_title
            }
        })
        
        if not articles.data:
            return {"error": f"Article not found: {article_title}"}
        
        primary = articles.data[0]
        dependencies = self.get_refresh_dependencies(primary.id)
        
        return {
            "primary": {
                "title": primary.get("title"),
                "id": primary.id,
                "stalenessScore": calculate_staleness_score(primary),
                "priority": get_refresh_priority(calculate_staleness_score(primary)),
            },
            "dependencies": dependencies,
            "totalArticles": 1 + len(dependencies),
        }


# =============================================================================
# Main Tutorial Execution
# =============================================================================

def get_db() -> RushDB:
    """Initialize RushDB connection."""
    api_key = os.environ.get("RUSHDB_API_KEY")
    if not api_key:
        print("Error: RUSHDB_API_KEY not found in environment")
        print("Copy .env.example to .env and add your API key")
        sys.exit(1)
    return RushDB(api_key)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def main():
    """Run the knowledge staleness detection tutorial."""
    print_section("Knowledge Staleness Detection and Adaptive Refresh")
    print("\nThis tutorial demonstrates:")
    print("  1. Staleness scoring for knowledge articles")
    print("  2. Adaptive refresh trigger configuration")
    print("  3. Dependency-aware refresh chains")
    
    # Initialize RushDB connection
    db = get_db()
    
    # Check if data exists, if not suggest running seed.py
    articles_result = db.records.find({"labels": ["Article"]})
    if not articles_result.data:
        print("\n⚠️  No articles found in database.")
        print("   Run 'python seed.py' first to populate test data.")
        sys.exit(1)
    
    print(f"\n✓ Connected to RushDB - Found {len(articles_result.data)} articles\n")
    
    # ========================================================================
    # Phase 1: Staleness Analysis
    # ========================================================================
    print_section("Phase 1: Staleness Analysis")
    
    print("\nCalculating staleness scores based on:")
    print("  • Time since last update (sqrt decay)")
    print("  • Access frequency (log scale)")
    print("  • Category priority weights")
    
    # Analyze each article
    analyses = []
    for article in articles_result.data:
        analysis = analyze_article_staleness(article)
        analyses.append(analysis)
        
        # Display article analysis
        print_subsection(analysis["title"])
        print(f"  Category: {analysis['category']}")
        print(f"  Views: {analysis['viewCount']} | Days since update: {analysis['daysSinceUpdate']}")
        print(f"  Staleness Score: {analysis['stalenessScore']} ({analysis['priority']})")
        
        if analysis["priority"] != "LOW":
            print(f"  → {analysis['recommendation']}")
    
    # Summary statistics
    print_section("Staleness Summary")
    
    priority_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for analysis in analyses:
        priority_counts[analysis["priority"]] += 1
    
    print("\nArticles by priority:")
    for priority, count in priority_counts.items():
        indicator = "🔴" if priority == "CRITICAL" else "🟠" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
        print(f"  {indicator} {priority}: {count} articles")
    
    critical_articles = [a for a in analyses if a["priority"] == "CRITICAL"]
    if critical_articles:
        print(f"\n⚠️  HIGH PRIORITY: {len(critical_articles)} articles need immediate attention")
    
    # ========================================================================
    # Phase 2: Adaptive Refresh Triggers
    # ========================================================================
    print_section("Phase 2: Adaptive Refresh Trigger System")
    
    # Initialize trigger system
    trigger_system = RefreshTriggerSystem(db)
    
    print("\nConfiguration:")
    for priority, threshold in REFRESH_THRESHOLDS.items():
        print(f"  {priority} threshold: >= {threshold}")
    
    # Generate refresh queue
    refresh_queue = trigger_system.generate_refresh_queue()
    
    if refresh_queue:
        print_subsection("Refresh Queue (sorted by priority)")
        for idx, item in enumerate(refresh_queue, 1):
            priority_icon = "🔴" if item["priority"] == "CRITICAL" else "🟠"
            print(f"  {idx}. {item['title']} [score: {item['stalenessScore']}] - {priority_icon} {item['priority']}")
    else:
        print("\n✓ No articles require immediate refresh")
    
    # Demonstrate threshold adjustment
    print_subsection("Dynamic Threshold Adjustment")
    print("\nSimulating stricter security policy (lowered HIGH threshold to 3.0):")
    trigger_system.set_threshold("HIGH", 3.0)
    
    strict_queue = []
    for article in articles_result.data:
        if trigger_system.should_trigger_refresh(article, min_priority="HIGH"):
            analysis = analyze_article_staleness(article)
            strict_queue.append(analysis)
    
    strict_queue.sort(key=lambda x: x["stalenessScore"], reverse=True)
    print(f"  With stricter thresholds: {len(strict_queue)} articles flagged for HIGH priority")
    
    # Reset threshold
    trigger_system.set_threshold("HIGH", 5.0)
    
    # ========================================================================
    # Phase 3: Dependency-Aware Refresh
    # ========================================================================
    print_section("Phase 3: Dependency-Aware Refresh Chains")
    
    # Initialize dependency manager
    dep_manager = DependencyRefreshManager(db)
    
    # Check for articles with refresh dependencies
    refresh_links = db.records.find({"labels": ["RefreshLink"]})
    
    if refresh_links.data:
        print(f"\nFound {len(refresh_links.data)} refresh dependency chains")
        
        # Pick an article with dependencies to demonstrate
        demo_article = "Authentication Best Practices"
        
        print_subsection(f"Refresh Plan: {demo_article}")
        
        refresh_plan = dep_manager.generate_refresh_plan(demo_article)
        
        if "error" not in refresh_plan:
            print(f"\nPrimary article: {refresh_plan['primary']['title']}")
            print(f"  Priority: {refresh_plan['primary']['priority']}")
            print(f"  Staleness Score: {refresh_plan['primary']['stalenessScore']}")
            
            if refresh_plan["dependencies"]:
                print(f"\nRefreshing this article requires updating {len(refresh_plan['dependencies'])} dependent articles:")
                for dep in refresh_plan["dependencies"]:
                    print(f"  → {dep['title']}")
                print(f"\nTotal articles in refresh chain: {refresh_plan['totalArticles']}")
            else:
                print("\n  ✓ No dependencies - can be refreshed independently")
    else:
        print("\nNo refresh dependency chains found.")
        print("  (Run seed.py to create test dependencies)")
    
    # ========================================================================
    # Phase 4: Interactive Staleness Check
    # ========================================================================
    print_section("Phase 4: On-Demand Staleness Check")
    
    print("\nDemonstrating on-demand staleness calculation for a specific article:\n")
    
    # Get a random article for demonstration
    import random
    sample_article = random.choice(articles_result.data)
    
    print(f"Article: {sample_article.get('title')}")
    print("\nDynamic staleness calculation:")
    
    # Simulate different scenarios
    scenarios = [
        {"days": 10, "views": 10},
        {"days": 60, "views": 50},
        {"days": 180, "views": 200},
    ]
    
    for scenario in scenarios:
        # Create a modified copy for simulation
        test_article = {
            **sample_article,
            "lastUpdated": (datetime.now() - timedelta(days=scenario["days"])).isoformat(),
            "viewCount": scenario["views"],
        }
        
        score = calculate_staleness_score(test_article)
        priority = get_refresh_priority(score)
        
        print(f"  Scenario: {scenario['days']} days old, {scenario['views']} views → Score: {score} ({priority})")
    
    # ========================================================================
    # Conclusion
    # ========================================================================
    print_section("Tutorial Complete!")
    
    print("\nWhat we demonstrated:")
    print("  ✓ Staleness scoring with configurable weights")
    print("  ✓ Priority classification based on thresholds")
    print("  ✓ Adaptive refresh trigger system")
    print("  ✓ Dependency-aware refresh chains")
    print("  ✓ Dynamic threshold adjustment")
    
    print("\nNext steps to extend this example:")
    print("  • Add automatic refresh scheduling")
    print("  • Integrate with CMS/webhook triggers")
    print("  • Implement ML-based staleness prediction")
    print("  • Add user feedback loops for accuracy")
    
    print("\n" + "=" * 60)
    print("\n📚 For more RushDB examples, visit:")
    print("   https://github.com/rush-db/examples")
    print("\n📖 RushDB Documentation:")
    print("   https://docs.rushdb.com")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
