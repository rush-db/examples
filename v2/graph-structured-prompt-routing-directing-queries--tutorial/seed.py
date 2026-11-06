"""
Seed script: Creates the knowledge graph for prompt routing demo.

This generates:
- 5 topic domains as graph nodes
- Query patterns linked to domains via relationships
- Knowledge entries within each domain subgraph
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()
API_KEY = os.getenv("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment")

db = RushDB(API_KEY)

# Domain definitions with their patterns and knowledge
DOMAINS = {
    "CODING": {
        "description": "Software development, programming languages, APIs, debugging",
        "patterns": [
            "how do I fix this error",
            "debug null pointer exception",
            "python list comprehension tutorial",
            "REST API best practices",
            "TypeScript generics explained",
            "Git merge vs rebase",
            "async/await in JavaScript",
            "database connection pooling",
            "Docker container optimization",
            "unit testing strategies",
            "error handling patterns",
            "memory leak diagnosis",
            "API rate limiting implementation",
            "microservices communication",
            "cache invalidation strategies",
        ],
        "knowledge": [
            {"title": "Python Exception Handling", "body": "Use try-except blocks with specific exception types. Always log the full traceback for debugging.", "tags": ["python", "errors", "best-practices"]},
            {"title": "Null Pointer Prevention", "body": "Initialize variables at declaration. Use optional chaining (?.) in TypeScript. Add null checks before method calls.", "tags": ["debugging", "null-safety", "typescript"]},
            {"title": "REST API Design Guide", "body": "Use nouns for endpoints. Support filtering with query params. Return appropriate HTTP status codes. Version your API from day one.", "tags": ["api", "rest", "design"]},
            {"title": "Git Workflow Strategies", "body": "Feature branches for all changes. Rebase before merge to keep history clean. Use squash commits for messy feature branch histories.", "tags": ["git", "workflow", "version-control"]},
            {"title": "Async Programming Patterns", "body": "Wrap async calls in try-catch. Use Promise.all for parallel operations. Handle timeouts explicitly. Avoid callback hell with async/await.", "tags": ["async", "javascript", "patterns"]},
        ],
    },
    "DESIGN": {
        "description": "UI/UX design, color theory, typography, design systems",
        "patterns": [
            "design a landing page",
            "color palette for mobile app",
            "typography best practices",
            "user interface components",
            "responsive design grid",
            "design system documentation",
            "accessibility guidelines WCAG",
            "icon design principles",
            "logo design inspiration",
            "wireframing tools comparison",
            "prototype animations",
            "design token system",
            "dark mode color scheme",
            "dashboard layout patterns",
            "mobile-first design approach",
        ],
        "knowledge": [
            {"title": "Color Theory for UI", "body": "Use 60-30-10 rule: 60% neutral, 30% secondary, 10% accent. Ensure 4.5:1 contrast ratio for accessibility. Test with color blindness simulators.", "tags": ["color", "ui", "accessibility"]},
            {"title": "Typography Scale System", "body": "Use modular scale (1.25 or 1.333 ratio) for harmonious sizing. Minimum 16px for body text. Line height 1.5 for readability.", "tags": ["typography", "fonts", "hierarchy"]},
            {"title": "Design System Components", "body": "Build atoms (buttons, inputs) first. Compose molecules (form fields). Assemble organisms (navbars, cards). Document with usage guidelines.", "tags": ["design-system", "components", "documentation"]},
            {"title": "Responsive Grid Patterns", "body": "12-column grid for desktop. Collapse to 6 at tablet, 4 at mobile. Use CSS Grid with minmax() for fluid layouts. Test with real devices.", "tags": ["responsive", "css", "grid"]},
            {"title": "Dark Mode Implementation", "body": "Use CSS custom properties for theming. Test all color combinations. Avoid pure black (#000) — use gray tones. Consider auto dark mode at night.", "tags": ["dark-mode", "theming", "css"]},
        ],
    },
    "MARKETING": {
        "description": "Content marketing, SEO, social media, campaigns",
        "patterns": [
            "SEO keyword research",
            "content marketing strategy",
            "social media engagement",
            "email campaign optimization",
            "conversion rate improvement",
            "brand voice guidelines",
            "influencer partnership",
            "analytics dashboard setup",
            "lead nurturing sequence",
            "viral content creation",
            "advertising budget allocation",
            "customer persona development",
            "market competitive analysis",
            "launch strategy planning",
            "community building tactics",
        ],
        "knowledge": [
            {"title": "SEO Keyword Strategy", "body": "Focus on search intent, not just volume. Target long-tail keywords. Create content clusters around pillar pages. Update old content monthly.", "tags": ["seo", "keywords", "content"]},
            {"title": "Email Campaign Metrics", "body": "Target 25%+ open rate with subject line optimization. Click-through should be 3-5%. Unsubscribe under 0.5%. A/B test everything.", "tags": ["email", "metrics", "optimization"]},
            {"title": "Social Media Content Calendar", "body": "Post consistently (daily for Twitter, 3x/week for LinkedIn). Use content batching. Mix promotional (20%) with educational (80%).", "tags": ["social-media", "content", "planning"]},
            {"title": "Conversion Funnel Analysis", "body": "Map customer journey stages. Identify drop-off points with analytics. A/B test landing pages. Personalize CTAs based on referral source.", "tags": ["conversion", "funnel", "analytics"]},
            {"title": "Brand Voice Development", "body": "Define 3-5 personality traits. Create vocabulary lists (words to use/avoid). Document tone adjustments for context. Train all content creators.", "tags": ["brand", "voice", "content"]},
        ],
    },
    "FINANCE": {
        "description": "Pricing, billing, invoices, payment processing, budgeting",
        "patterns": [
            "subscription pricing model",
            "invoice payment terms",
            " Stripe integration setup",
            "expense tracking system",
            "revenue forecasting",
            "tax compliance checklist",
            "consulting rate calculation",
            "budget allocation strategy",
            "financial dashboard metrics",
            "ROI calculation method",
            "cash flow management",
            "pricing page optimization",
            "payment failed retry logic",
            "fiscal year planning",
            "investment decision framework",
        ],
        "knowledge": [
            {"title": "SaaS Pricing Strategies", "body": "Start with value-based pricing. Offer annual discounts (15-20%). Test price points with value metrics. Include tier migration paths.", "tags": ["pricing", "saas", "strategy"]},
            {"title": "Payment Retry Logic", "body": "Retry failed payments 3x over 7 days. Add exponential backoff. Email reminder before retry. Offer alternative payment methods.", "tags": ["payments", "billing", "retention"]},
            {"title": "Consulting Rate Calculator", "body": "Annual goal ÷ billable hours (typically 1200) × risk multiplier (1.5-2x). Include overhead, taxes, and desired profit margin.", "tags": ["consulting", "rates", "pricing"]},
            {"title": "Financial KPIs Dashboard", "body": "Track MRR, churn rate, LTV, CAC, and burn rate monthly. Set thresholds for warning (red) and target (green) values.", "tags": ["metrics", "dashboard", "kpis"]},
            {"title": "Cash Flow Forecasting", "body": "Use rolling 13-week forecast. Track receivables aging. Maintain 3-month runway buffer. Scenario plan for best/worst case.", "tags": ["cashflow", "forecast", "planning"]},
        ],
    },
    "SUPPORT": {
        "description": "Customer support, troubleshooting, FAQs, documentation",
        "patterns": [
            "reset password not working",
            "account access issues",
            "billing inquiry",
            "feature request submission",
            "bug report format",
            "refund request process",
            "subscription cancellation",
            "data export tutorial",
            "two-factor authentication help",
            "integration setup guide",
            "permissions troubleshooting",
            "notification settings",
            "mobile app sync issues",
            "api key regeneration",
            "contact support escalation",
        ],
        "knowledge": [
            {"title": "Password Reset Troubleshooting", "body": "Check spam/junk folder. Verify email domain is correct. Clear browser cache. Try incognito mode. Check corporate email restrictions.", "tags": ["password", "account", "troubleshooting"]},
            {"title": "2FA Setup Guide", "body": "Download authenticator app. Scan QR code within 30 seconds. Save backup codes securely. Test before disabling SMS fallback.", "tags": ["2fa", "security", "setup"]},
            {"title": "Refund Policy Process", "body": "Verify purchase date (< 30 days for full refund). Check payment method. Process via original transaction. Send confirmation email.", "tags": ["refund", "billing", "process"]},
            {"title": "API Key Management", "body": "Generate with descriptive name. Set expiration date. Restrict to required scopes. Rotate quarterly. Revoke immediately if compromised.", "tags": ["api", "security", "keys"]},
            {"title": "Bug Report Template", "body": "Include: steps to reproduce, expected behavior, actual result, browser/OS version, screenshot/video, urgency level.", "tags": ["bugs", "reporting", "template"]},
        ],
    },
}


def check_data_exists():
    """Check if routing graph is already seeded."""
    result = db.labels.find({})
    return any(label.name == "DOMAIN" for label in result)


def seed_domain(tx, domain_id: str, domain_data: dict):
    """Create a domain node with its patterns and knowledge."""
    # Create domain node
    domain = db.records.create(
        label="DOMAIN",
        data={
            "id": domain_id,
            "name": domain_id,
            "description": domain_data["description"],
            "entry_count": len(domain_data["knowledge"]),
        },
        transaction=tx,
    )

    # Create pattern nodes and link to domain
    for pattern_text in domain_data["patterns"]:
        pattern = db.records.create(
            label="PATTERN",
            data={
                "text": pattern_text,
                "domain_id": domain_id,
            },
            transaction=tx,
        )
        db.records.attach(
            source=pattern,
            target=domain,
            options={"type": "ROUTES_TO", "direction": "out"},
            transaction=tx,
        )

    # Create knowledge entries and link to domain
    for entry in domain_data["knowledge"]:
        knowledge = db.records.create(
            label="KNOWLEDGE",
            data={
                "title": entry["title"],
                "body": entry["body"],
                "tags": entry["tags"],
                "domain_id": domain_id,
            },
            transaction=tx,
        )
        db.records.attach(
            source=knowledge,
            target=domain,
            options={"type": "BELONGS_TO", "direction": "out"},
            transaction=tx,
        )

    return domain


def main():
    print("=== Seeding Graph-Structured Prompt Routing Data ===\n")

    # Check if already seeded
    if check_data_exists():
        print("✓ Routing graph already exists. Skipping seed.")
        print("  To re-seed, delete existing DOMAIN records first.\n")
        return

    print("Creating domain subgraphs...")

    with db.transactions.begin() as tx:
        domain_count = 0
        pattern_count = 0
        knowledge_count = 0

        for domain_id, domain_data in DOMAINS.items():
            domain = seed_domain(tx, domain_id, domain_data)
            domain_count += 1
            pattern_count += len(domain_data["patterns"])
            knowledge_count += len(domain_data["knowledge"])
            print(f"  ✓ {domain_id}: {len(domain_data['patterns'])} patterns, {len(domain_data['knowledge'])} knowledge entries")

    print(f"\n✓ Graph seeded successfully!")
    print(f"  {domain_count} domains")
    print(f"  {pattern_count} routing patterns")
    print(f"  {knowledge_count} knowledge entries\n")


if __name__ == "__main__":
    main()
