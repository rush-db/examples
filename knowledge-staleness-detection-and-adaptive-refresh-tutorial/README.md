# Knowledge Staleness Detection and Adaptive Refresh Triggers

A practical tutorial demonstrating how to build a knowledge staleness detection system using RushDB's property graph capabilities.

## What This Tutorial Demonstrates

- **Staleness scoring**: Calculate how outdated knowledge base entries are based on time, access patterns, and modification history
- **Adaptive refresh triggers**: Automatically flag or refresh content based on configurable staleness thresholds
- **Graph-based tracking**: Leverage RushDB's relationship model to track content relationships and refresh dependencies
- **Real-time knowledge management**: Implement a system that intelligently prioritizes which documents need attention

## Use Case: Technical Documentation Knowledge Base

Imagine a technical documentation system where:
- Articles have an initial freshness score that decays over time
- Access frequency affects how urgently content needs updating (frequently accessed outdated content is more critical)
- Related articles form dependency chains (refreshing one may require refreshing others)
- Different categories have different staleness tolerance levels

## Prerequisites

- Python 3.9+
- A RushDB account (Free tier works perfectly)
- `rushdb>=2.0.0` Python SDK

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your RushDB credentials:

```bash
cp .env.example .env
```

Required variables:
- `RUSHDB_API_KEY` — Your RushDB API token

### 3. Seed the Database (Optional)

The seed script creates sample knowledge articles with realistic metadata. Run it once to populate test data:

```bash
python seed.py
```

Expected output:
```
✓ Created article: Building REST APIs with FastAPI
✓ Created article: Database Design Patterns
✓ Created article: Microservices Communication
✓ Created article: Authentication Best Practices
✓ Created article: Kubernetes Deployment Guide
✓ Created article: Graph Database Fundamentals
✓ Created article: API Rate Limiting Strategies
✓ Created article: Caching Layer Architecture
✓ Created article: Testing Best Practices
✓ Created article: Security Vulnerability Checklist
✓ Created article: Performance Optimization Techniques
✓ Created article: CI/CD Pipeline Setup
✓ Created 12 articles with access patterns
✓ Created 11 category relationships
✓ Created 8 refresh links
✓ Seeding complete! 12 articles ready for staleness analysis
```

## Running the Tutorial

```bash
python main.py
```

### Expected Output

The tutorial runs in three phases:

**Phase 1: Staleness Analysis**
```
=== Knowledge Staleness Detection ===

Article: Building REST APIs with FastAPI
  Category: backend    Views: 45     Days since update: 45
  Staleness Score: 6.45 (MEDIUM - consider updating)

Article: Database Design Patterns
  Category: backend    Views: 12     Days since update: 180
  Staleness Score: 15.20 (CRITICAL - update immediately)
  ⚠️  HIGH PRIORITY: 1 articles need immediate attention
```

**Phase 2: Adaptive Refresh Triggers**
```
=== Adaptive Refresh Trigger System ===

Configuration:
  CRITICAL threshold: >= 10.0
  HIGH threshold: >= 5.0
  MEDIUM threshold: >= 2.5

Refresh Queue (sorted by priority):
  1. Database Design Patterns [score: 15.20] - CRITICAL
  2. Kubernetes Deployment Guide [score: 7.85] - HIGH
  3. Building REST APIs with FastAPI [score: 6.45] - HIGH
```

**Phase 3: Dependency-Aware Refresh**
```
=== Dependency-Aware Refresh Chains ===

Refresh: "Authentication Best Practices" requires refreshing:
  → "Microservices Communication"
  → "Testing Best Practices"
```

## Key Implementation Patterns

### Staleness Score Calculation

```sdk
# Python — 4-space indentation for every nested level
def calculate_staleness(record):
    import math
    from datetime import datetime, timedelta

    days_since_update = (datetime.now() - datetime.fromisoformat(record["lastUpdated"])).days
    view_count = record.get("viewCount", 0)
    category_weight = {"security": 2.0, "backend": 1.5, "devops": 1.2, "general": 1.0}.get(record["category"], 1.0)

    time_component = math.sqrt(days_since_update) * 2.0
    access_component = math.log1p(view_count) * 0.5
    base_score = (time_component + access_component) * category_weight

    return round(base_score, 2)
___SPLIT___
// TypeScript — 2-space indentation for every nested level
function calculateStaleness(record: ArticleRecord): number {
  const daysSinceUpdate = Math.floor(
    (Date.now() - new Date(record.lastUpdated).getTime()) / (1000 * 60 * 60 * 24)
  );
  const viewCount = record.viewCount ?? 0;
  const categoryWeight: Record<string, number> = {
    security: 2.0,
    backend: 1.5,
    devops: 1.2,
    general: 1.0,
  };
  const weight = categoryWeight[record.category] ?? 1.0;

  const timeComponent = Math.sqrt(daysSinceUpdate) * 2.0;
  const accessComponent = Math.log1p(viewCount) * 0.5;

  return Math.round((timeComponent + accessComponent) * weight * 100) / 100;
}
```

### Refresh Trigger Logic

```sdk
# Python — 4-space indentation for every nested level
def get_refresh_priority(score):
    if score >= 10.0:
        return "CRITICAL"
    elif score >= 5.0:
        return "HIGH"
    elif score >= 2.5:
        return "MEDIUM"
    else:
        return "LOW"

def should_trigger_refresh(record, threshold=5.0):
    score = calculate_staleness(record)
    return score >= threshold
___SPLIT___
// TypeScript — 2-space indentation for every nested level
function getRefreshPriority(score: number): 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' {
  if (score >= 10.0) return 'CRITICAL';
  if (score >= 5.0) return 'HIGH';
  if (score >= 2.5) return 'MEDIUM';
  return 'LOW';
}

function shouldTriggerRefresh(record: ArticleRecord, threshold = 5.0): boolean {
  const score = calculateStaleness(record);
  return score >= threshold;
}
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Knowledge Base                            │
├─────────────────────────────────────────────────────────────┤
│  Article                                                     │
│  ├── title, content, category                               │
│  ├── lastUpdated, viewCount, author                         │
│  └── stalenessScore (computed)                              │
├─────────────────────────────────────────────────────────────┤
│  Relationships                                               │
│  ├── BELONGS_TO → Category                                  │
│  ├── REQUIRES_REFRESH → Article (dependency chain)          │
│  └── WRITTEN_BY → Author                                     │
├─────────────────────────────────────────────────────────────┤
│  Refresh Triggers                                           │
│  ├── CRITICAL (score ≥ 10): Immediate action                 │
│  ├── HIGH (score ≥ 5): Update within 48 hours               │
│  ├── MEDIUM (score ≥ 2.5): Schedule for next sprint         │
│  └── LOW (score < 2.5): Monitor                             │
└─────────────────────────────────────────────────────────────┘
```

## Extending the Example

### Adding Custom Staleness Factors

```python
# Consider content change velocity
change_frequency = record.get("editFrequency", 1)  # edits per month
velocity_penalty = 1.0 / (1.0 + change_frequency)

# Factor in dependency criticality
dependent_count = len(get_dependents(record))
criticality_bonus = dependent_count * 0.5
```

### Implementing Automatic Refresh Suggestions

```python
def suggest_refresh_actions(articles):
    """Generate actionable refresh recommendations."""
    suggestions = []
    for article in articles:
        score = calculate_staleness(article)
        priority = get_refresh_priority(score)
        dependencies = get_refresh_dependencies(article)
        
        suggestions.append({
            "article": article["title"],
            "priority": priority,
            "score": score,
            "refresh_dependencies": dependencies,
            "estimated_effort": estimate_refresh_effort(article),
        })
    
    return sorted(suggestions, key=lambda x: x["score"], reverse=True)
```

## References

- [RushDB Documentation](https://docs.rushdb.com)
- [GitHub Repository](https://github.com/rush-db/examples/tree/main/knowledge-staleness-detection-and-adaptive-refresh-tutorial)
