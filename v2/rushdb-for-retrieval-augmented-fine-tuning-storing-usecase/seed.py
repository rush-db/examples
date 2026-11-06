#!/usr/bin/env python3
"""
Seed script for generating synthetic training examples.

This script creates:
- Source documents (knowledge base articles, documentation pages)
- Fine-tuning tasks (customer support, code generation, data analysis)
- Training examples linked to source documents and tasks
- Pre-computed vector embeddings for each example

Run once to populate RushDB with demo data. Safe to run multiple times
(idempotent via upsert patterns).
"""

import os
import json
import random
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load environment
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

if not API_KEY:
    raise ValueError("Missing RUSHDB_API_KEY. Copy .env.example to .env and fill in your API key.")


# Initialize RushDB
db = RushDB(API_KEY)

# Initialize embedding model
print(f"Loading embedding model: {EMBEDDING_MODEL}")
model = SentenceTransformer(EMBEDDING_MODEL)
EMBEDDING_DIMENSIONS = model.get_sentence_embedding_dimension()
print(f"Embedding dimensions: {EMBEDDING_DIMENSIONS}")

# Domain-specific training data templates
DOMAINS = {
    "customer_support": {
        "task_name": "Customer Support Response Generation",
        "target_model": "gpt-4-turbo",
        "instructions": [
            "How do I reset my password?",
            "How can I update my billing information?",
            "What are the subscription plans available?",
            "How do I cancel my subscription?",
            "Why is my payment failing?",
            "How do I contact support?",
            "Can I get a refund?",
            "How do I upgrade my plan?",
            "Where can I find my invoice?",
            "How do I change my email address?",
            "My account is locked, what should I do?",
            "How do I delete my account?",
        ],
        "outputs": [
            "To reset your password, go to Settings > Security > Reset Password and follow the instructions sent to your email.",
            "You can update your billing information in Account Settings > Billing > Update Payment Method.",
            "We offer three plans: Starter ($9/mo), Pro ($29/mo), and Enterprise (custom pricing). View all options at our pricing page.",
            "To cancel your subscription, go to Settings > Billing > Cancel Subscription. Your access continues until the end of the billing period.",
            "Payment failures typically occur due to: expired card, insufficient funds, or bank restrictions. Please verify your payment details.",
            "You can contact support via email at support@example.com or use the live chat feature in the bottom right corner.",
            "We offer a 30-day money-back guarantee. Submit a refund request through our support portal with your order ID.",
            "To upgrade your plan, go to Settings > Billing > Upgrade Plan and choose your desired tier. Changes take effect immediately.",
            "Invoices are available in Account Settings > Billing > Invoice History. You can download PDF copies there.",
            "To change your email, go to Settings > Account > Change Email and verify the new address.",
            "Your account may be locked due to multiple failed login attempts. Wait 15 minutes or use 'Forgot Password' to unlock.",
            "To delete your account, go to Settings > Privacy > Delete Account. Note: this action is irreversible and deletes all data.",
        ],
        "source_types": ["knowledge_base", "faq", "documentation", "support_ticket"],
    },
    "code_generation": {
        "task_name": "Code Generation and Refactoring",
        "target_model": "gpt-4-turbo",
        "instructions": [
            "Write a function to validate email addresses in Python",
            "Create a unit test for the user authentication module",
            "Add docstrings to this function that explains the parameters",
            "Refactor this code to use async/await patterns",
            "Write a SQL query to calculate monthly revenue",
            "Create a decorator for caching function results",
            "Implement a rate limiter for API endpoints",
            "Write a regex pattern for phone number validation",
            "Create a context manager for database connections",
            "Implement binary search in JavaScript",
            "Write a function to merge sorted arrays",
            "Create a retry decorator with exponential backoff",
        ],
        "outputs": [
            '```python\nimport re\n\nemail_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"\n\ndef validate_email(email: str) -> bool:\n    return bool(re.match(email_pattern, email))\n```',
            '```python\nimport pytest\nfrom auth import authenticate_user\n\nclass TestAuthentication:\n    def test_valid_credentials(self):\n        assert authenticate_user("user@example.com", "password123") == True\n    \n    def test_invalid_password(self):\n        assert authenticate_user("user@example.com", "wrong") == False\n```',
            '```python\ndef process_data(data: list[dict], options: dict = None) -> list[dict]:\n    """Process raw data with optional transformation settings.\n    \n    Args:\n        data: List of dictionaries containing raw records\n        options: Optional settings for filtering and transformation\n    \n    Returns:\n        List of processed dictionaries\n    """\n    ...\n```',
            '```python\nimport asyncio\n\nasync def fetch_data(url: str) -> dict:\n    async with aiohttp.ClientSession() as session:\n        async with session.get(url) as response:\n            return await response.json()\n\nasync def main():\n    results = await asyncio.gather(*[fetch_data(url) for url in urls])\n```',
            '```sql\nSELECT \n    DATE_TRUNC(\'month\', created_at) as month,\n    SUM(amount) as total_revenue\nFROM orders\nWHERE status = \'completed\'\nGROUP BY DATE_TRUNC(\'month\', created_at)\nORDER BY month DESC;\n```',
            '```python\nfrom functools import wraps\n\ndef cache(func):\n    cache_store = {}\n    \n    @wraps(func)\n    def wrapper(*args, **kwargs):\n        key = str(args) + str(kwargs)\n        if key not in cache_store:\n            cache_store[key] = func(*args, **kwargs)\n        return cache_store[key]\n    return wrapper\n```',
            '```python\nimport time\nfrom functools import wraps\n\ndef rate_limit(max_calls: int, window_seconds: int):\n    def decorator(func):\n        calls = []\n        @wraps(func)\n        def wrapper(*args, **kwargs):\n            now = time.time()\n            calls[:] = [t for t in calls if now - t < window_seconds]\n            if len(calls) >= max_calls:\n                raise Exception("Rate limit exceeded")\n            calls.append(now)\n            return func(*args, **kwargs)\n        return wrapper\n    return decorator\n```',
            '```javascript\nconst phonePattern = /^\\+?[1-9]\\d{1,14}$/;\n\nfunction validatePhone(phone) {\n    return phonePattern.test(phone.replace(/[\\s\\-()]/g, \'\'));\n}\n```',
            '```python\nclass DatabaseConnection:\n    def __init__(self, connection_string):\n        self.connection_string = connection_string\n        self.connection = None\n    \n    def __enter__(self):\n        self.connection = create_connection(self.connection_string)\n        return self.connection\n    \n    def __exit__(self, exc_type, exc_val, exc_tb):\n        if self.connection:\n            self.connection.close()\n```',
            '```javascript\nfunction binarySearch(arr, target) {\n    let left = 0;\n    let right = arr.length - 1;\n    \n    while (left <= right) {\n        const mid = Math.floor((left + right) / 2);\n        if (arr[mid] === target) return mid;\n        if (arr[mid] < target) left = mid + 1;\n        else right = mid - 1;\n    }\n    return -1;\n}\n```',
            '```python\ndef merge_sorted(arr1, arr2):\n    result = []\n    i = j = 0\n    while i < len(arr1) and j < len(arr2):\n        if arr1[i] <= arr2[j]:\n            result.append(arr1[i])\n            i += 1\n        else:\n            result.append(arr2[j])\n            j += 1\n    result.extend(arr1[i:])\n    result.extend(arr2[j:])\n    return result\n```',
            '```python\nimport time\nimport asyncio\n\nclass RetryError(Exception):\n    pass\n\ndef retry(max_attempts=3, delay=1.0, backoff=2.0):\n    def decorator(func):\n        async def wrapper(*args, **kwargs):\n            last_error = None\n            for attempt in range(max_attempts):\n                try:\n                    return await func(*args, **kwargs)\n                except Exception as e:\n                    last_error = e\n                    if attempt < max_attempts - 1:\n                        await asyncio.sleep(delay * (backoff ** attempt))\n            raise RetryError(f"Failed after {max_attempts} attempts") from last_error\n        return wrapper\n    return decorator\n```',
        ],
        "source_types": ["github", "stackoverflow", "documentation", "internal_repo"],
    },
    "data_analysis": {
        "task_name": "Data Analysis and Report Generation",
        "target_model": "gpt-4-turbo",
        "instructions": [
            "Analyze this sales data and identify top-performing products",
            "Generate a monthly summary report from the transaction data",
            "Calculate customer churn rate for the past quarter",
            "Create a visualization showing revenue trends over time",
            "Identify anomalies in the system logs",
            "Calculate average order value by customer segment",
            "Generate a cohort analysis for user retention",
            "Analyze campaign performance and ROI",
            "Create a customer segmentation report",
            "Calculate lifetime value for different customer groups",
            "Identify cross-sell opportunities from purchase history",
            "Generate executive summary from sales metrics",
        ],
        "outputs": [
            "Based on the sales data analysis, the top-performing products are: Product A (42% of revenue), Product B (28%), and Product C (18%). Recommendations: Increase inventory for Product A, consider bundling Product C with slower-moving items.",
            "Monthly Summary: Total transactions: 15,234. Revenue: $892,432. Average order value: $58.54. Peak day: Wednesday. Customer retention rate: 67%. Notable trend: 23% increase in repeat purchases.",
            "Q3 Churn Analysis: Overall churn rate: 5.2%. At-risk segments: Customers aged 25-35 (8.1% churn), New customers within 30 days (12.4% churn). Key predictors: Reduced login frequency, support tickets > 2.",
            "Revenue Trends: Q1: $2.1M, Q2: $2.4M (+14%), Q3: $2.8M (+17%), Q4: $3.2M (+14%). Seasonality: Strong Q4 performance (+45% vs average). Growth rate: 18% YoY.",
            "Log Anomalies Detected: 3 critical error spikes at 02:00 UTC (potential cron job failures), 47 instances of timeout errors from API gateway, Unusual spike in authentication failures from IP range 192.168.x.x.",
            "AOV by Segment: Enterprise: $342, Mid-Market: $156, SMB: $67, Startup: $45. Key insight: Enterprise customers spend 7.6x more per transaction than SMB. Cross-segment opportunity: Upsell mid-market to enterprise tier.",
            "Cohort Analysis: Week 1 retention: 68%, Week 4: 42%, Month 2: 31%, Month 3: 24%. Best performing cohorts: Users acquired via referral (71% week 1 retention). At-risk: Users from paid ads (52% week 1 retention).",
            "Campaign Performance: Holiday Sale - Spend: $45K, Revenue: $312K, ROI: 593%. Email Blast - Spend: $2K, Revenue: $28K, ROI: 1300%. Social Media - Spend: $12K, Revenue: $89K, ROI: 642%.",
            "Customer Segments: Champions (22%): High spend, frequent buyers. Loyalists (31%): Moderate spend, regular engagement. At-Risk (18%): Declining activity. Lost (12%): Churned within 90 days. New (17%): Acquired within 30 days.",
            "Customer Lifetime Value: Enterprise: $4,200 (avg 3.2 year relationship), Mid-Market: $1,850 (avg 2.1 years), SMB: $520 (avg 1.4 years). Key driver: Product adoption score positively correlates with 2.3x LTV increase.",
            "Cross-sell Analysis: Customers who bought Product A: 67% also bought Product B within 90 days. Recommended bundles: A+B (16% discount), Core+Add-on (12% discount). High potential: Enterprise segment shows 89% cross-sell acceptance.",
            "Executive Summary: Revenue grew 18% YoY to $10.5M. Customer base expanded to 45K (12% growth). Churn reduced to 5.2% (from 7.1%). Key wins: Enterprise segment (+34% revenue), international expansion (now 23 countries).",
        ],
        "source_types": ["dashboard", "analytics_report", "internal_metrics", "market_research"],
    },
}


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts."""
    return model.encode(texts, show_progress_bar=False).tolist()


def create_source_document(content: str, source_type: str, title: str) -> dict:
    """Create a source document record."""
    source_doc = db.records.create(
        label="SourceDocument",
        data={
            "content": content,
            "source_type": source_type,
            "title": title,
            "author": random.choice(["Alice Chen", "Bob Martinez", "Carol Smith", "Dan Kim"]),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "url": f"https://example.com/docs/{random.randint(1000, 9999)}",
        }
    )
    return source_doc


def create_fine_tuning_task(domain: str, task_info: dict) -> dict:
    """Create a fine-tuning task record."""
    task = db.records.upsert(
        label="FineTuningTask",
        data={
            "name": task_info["task_name"],
            "domain": domain,
            "target_model": task_info["target_model"],
            "status": "active",
            "description": f"Generate high-quality responses for {domain.replace('_', ' ')} tasks",
        },
        options={"mergeBy": ["name"]}
    )
    return task


def create_category(name: str, domain: str) -> dict:
    """Create a category record for stratified sampling."""
    category = db.records.upsert(
        label="Category",
        data={
            "name": name,
            "domain": domain,
            "description": f"Category for {domain} examples",
        },
        options={"mergeBy": ["name"]}
    )
    return category


def create_training_example(
    instruction: str,
    input_text: str,
    output: str,
    source_doc: dict,
    task: dict,
    category: dict,
    domain: str,
) -> Optional[dict]:
    """"Create a training example with all relationships."""
    # Generate embedding for the instruction
    embedding = generate_embeddings([instruction])[0]
    
    # Confidence based on source type (higher for documentation, lower for tickets)
    source_confidence_map = {
        "documentation": (0.85, 0.98),
        "knowledge_base": (0.80, 0.95),
        "faq": (0.75, 0.92),
        "stackoverflow": (0.70, 0.90),
        "github": (0.78, 0.94),
        "internal_repo": (0.82, 0.96),
        "dashboard": (0.80, 0.93),
        "analytics_report": (0.85, 0.97),
        "support_ticket": (0.60, 0.85),
        "market_research": (0.75, 0.90),
        "internal_metrics": (0.82, 0.95),
    }
    conf_range = source_confidence_map.get(source_doc["source_type"], (0.7, 0.9))
    label_confidence = random.uniform(*conf_range)
    
    # Label quality
    label_options = ["positive", "positive", "positive", "neutral", "needs_review"]
    label = random.choice(label_options)
    
    # User feedback (higher confidence = more likely accepted)
    if label_confidence > 0.9:
        feedback_options = ["accepted", "accepted", "reviewed"]
    elif label_confidence > 0.8:
        feedback_options = ["accepted", "reviewed", "pending"]
    else:
        feedback_options = ["reviewed", "pending", "rejected"]
    user_feedback = random.choice(feedback_options)
    
    # Create the training example with vector embedding
    example = db.records.create(
        label="TrainingExample",
        data={
            "instruction": instruction,
            "input": input_text,
            "output": output,
            "source": source_doc["source_type"],
            "timestamp": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat(),
            "label_confidence": round(label_confidence, 3),
            "label": label,
            "user_feedback": user_feedback,
            "domain": domain,
        },
        vectors=[{"propertyName": "instruction", "vector": embedding}]
    )
    
    # Attach relationships
    db.records.attach(
        source=example,
        target=source_doc,
        options={"type": "DERIVED_FROM", "direction": "out"}
    )
    
    db.records.attach(
        source=example,
        target=task,
        options={"type": "TRAINS_FOR", "direction": "out"}
    )
    
    db.records.attach(
        source=example,
        target=category,
        options={"type": "BELONGS_TO", "direction": "out"}
    )
    
    return example


def main():
    """Main seeding function."""
    print("\n" + "=" * 60)
    print("RushDB Training Examples Seeder")
    print("=" * 60)
    
    # Check if data already exists
    existing = db.records.find({"labels": ["TrainingExample"], "limit": 1})
    if existing:
        print("\n⚠️  Training examples already exist. Skipping seed.")
        print("   To re-seed, delete existing records first.")
        return
    
    print("\n📦 Creating source documents, tasks, and training examples...")
    
    total_examples = 0
    
    for domain, task_info in DOMAINS.items():
        print(f"\n{'─' * 40}")
        print(f"📂 Domain: {domain}")
        print(f"{'─' * 40}")
        
        # Create fine-tuning task
        task = create_fine_tuning_task(domain, task_info)
        print(f"   ✓ Fine-tuning task: {task_info['task_name']}")
        
        # Create category for stratified sampling
        category = create_category(domain, domain)
        print(f"   ✓ Category: {domain}")
        
        # Create training examples for this domain
        domain_examples = 0
        for i, (instruction, output) in enumerate(
            zip(task_info["instructions"], task_info["outputs"])
        ):
            source_type = random.choice(task_info["source_types"])
            
            # Create source document
            source_doc = create_source_document(
                content=output,
                source_type=source_type,
                title=f"{domain.title()} Example {i + 1}",
            )
            
            # Create training example
            example = create_training_example(
                instruction=instruction,
                input_text="",
                output=output,
                source_doc=source_doc,
                task=task,
                category=category,
                domain=domain,
            )
            
            domain_examples += 1
            total_examples += 1
            
            if (i + 1) % 5 == 0:
                print(f"   📝 Created {i + 1}/{len(task_info['instructions'])} examples...")
        
        print(f"   ✅ Domain complete: {domain_examples} examples created")
    
    print("\n" + "=" * 60)
    print(f"✅ Seeding complete!")
    print(f"   Total training examples: {total_examples}")
    print(f"   Total source documents: {total_examples}")
    print(f"   Total tasks: {len(DOMAINS)}")
    print(f"   Total categories: {len(DOMAINS)}")
    print("=" * 60)
    
    # Print index info
    print("\n📊 Vector Index Status:")
    indexes = db.ai.indexes.find()
    if indexes.data:
        for idx in indexes.data:
            stats = db.ai.indexes.stats(idx["__id"])
            print(f"   • {idx['label']}.{idx['propertyName']}: {stats.data.get('indexedRecords', 0)} indexed")
    else:
        print("   (No indexes found - they are created on-demand)")


if __name__ == "__main__":
    main()
