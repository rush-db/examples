"""
Seed script for conversation memory chains demonstration.

Generates realistic conversation history across multiple users and channels,
with messages spanning several days to demonstrate time-decay weighting.

Run this script once to populate your RushDB instance with sample data.
Safe to run multiple times - detects existing data and skips seeding.
"""

import os
import sys
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

from rushdb import RushDB

# Initialize RushDB client
api_token = os.getenv("RUSHDB_API_TOKEN")
if not api_token:
    print("Error: RUSHDB_API_TOKEN not found in environment")
    print("Please add your API key to .env or export RUSHDB_API_TOKEN")
    sys.exit(1)

api_url = os.getenv("RUSHDB_URL")
db = RushDB(api_token, url=api_url) if api_url else RushDB(api_token)

# Sample data for realistic conversations
USERS = [
    "alice@example.com",
    "bob@example.com",
    "charlie@example.com",
    "diana@example.com",
]

CHANNELS = [
    ("engineering", "Project discussions and technical decisions"),
    ("design", "UI/UX and product design reviews"),
    ("general", "Team-wide announcements and social"),
    ("support", "Customer issues and bug reports"),
]

MESSAGE_TEMPLATES = {
    "engineering": [
        "I've reviewed the architecture proposal and have a few concerns about scalability",
        "Can we schedule a code review for the authentication module?",
        "The new caching layer is causing unexpected behavior in production",
        "Just pushed the database migration script to the repository",
        "Need to discuss the API versioning strategy before we ship",
        "Performance benchmarks look good - 40% improvement on query response times",
        "I'm seeing memory leaks in the worker process after ~2 hours of runtime",
        "The webhook integration with the payment provider needs testing",
        "Let's refactor the data access layer to use the repository pattern",
        "Documentation for the new endpoints is ready for review",
        "The load balancer configuration needs adjustment for the new service",
        "I've implemented the rate limiting middleware as discussed",
        "Unit test coverage dropped to 72% after the recent refactor - we should address this",
        "The GraphQL schema changes are backwards compatible",
        "Error rates spiked after the deployment - investigating now",
    ],
    "design": [
        "Here's the mockup for the new dashboard layout",
        "The color palette needs to meet WCAG AA contrast requirements",
        "User testing showed confusion around the navigation structure",
        "Let's align on the icon style before we proceed with implementation",
        "Animation prototypes are ready in Figma - link in thread",
        "The responsive breakpoints need adjustment for tablet views",
        "Typography hierarchy changes approved - will update the design system",
        "Mobile-first approach agreed - starting with the core flows",
        "Can we reduce the number of form fields to improve conversion?",
        "Dark mode support adds complexity to the component library",
    ],
    "general": [
        "Welcome to the team, everyone! Quick intro session tomorrow at 10am",
        "Office hours changed - now Fridays 2-4pm for async questions",
        "Sprint retrospective moved to Thursday due to conflict",
        "New team member joining next week - looking forward to having you!",
        "Reminder: submit your timesheets by end of day Friday",
        "The team lunch is confirmed for next Wednesday at noon",
        "Parking validation available at reception desk",
        "Q3 goals are due by end of month - check the wiki for template",
        "Thanks everyone for the great work on the release!",
        "All hands meeting rescheduled to Friday morning",
    ],
    "support": [
        "Customer reported issues with bulk export functionality",
        "The payment processing error has been identified and fix deployed",
        "User unable to reset password - investigating SSO configuration",
        "Dashboard loading slowly for accounts with large datasets",
        "Export to CSV feature produces malformed file for special characters",
        "Customer asking about data retention policy and GDPR compliance",
        "API rate limiting affecting their integration - need to discuss limits",
        "Mobile app crashes on Android 14 - reproducible issue",
        "The email notification system missed several alerts overnight",
        "User feedback: the new interface is confusing - need better onboarding",
    ],
}


def check_existing_data():
    """Check if conversations already exist to avoid duplicate seeding."""
    existing = db.records.find({"labels": ["CONVERSATION"], "limit": 1})
    return len(existing.data) > 0


def create_conversation(title, channel, description):
    """Create a conversation record."""
    return db.records.create(
        label="CONVERSATION",
        data={
            "title": title,
            "channel": channel,
            "description": description,
        }
    )


def create_message(content, author, timestamp, conversation):
    """Create a message record and attach to conversation."""
    message = db.records.create(
        label="MESSAGE",
        data={
            "content": content,
            "author": author,
            "timestamp": timestamp.isoformat() + "Z",
            "word_count": len(content.split()),
        }
    )
    
    # Link message to conversation
    db.records.attach(
        source=message,
        target=conversation,
        options={"type": "PART_OF"}
    )
    
    return message


def link_context(messages, base_time, days_back, weight, weight_desc):
    """Link a past message as context for the most recent message."""
    recent_idx = len(messages) - 1
    past_idx = recent_idx - days_back
    
    if past_idx >= 0:
        db.records.attach(
            source=messages[recent_idx],
            target=messages[past_idx],
            options={
                "type": "CONTEXTUALLY_LINKED",
                "properties": {
                    "weight": weight,
                    "weight_description": weight_desc,
                    "days_elapsed": days_back,
                    "calculated_at": datetime.utcnow().isoformat() + "Z",
                }
            }
        )


def generate_conversation_concept(channel_name):
    """Generate a plausible conversation title and sequence."""
    concepts = {
        "engineering": [
            ("API Gateway Migration", [
                "Starting the API gateway migration to the new infrastructure",
                "Health checks are passing for the new gateway",
                "SSL certificates validated and installed",
                "Rollback plan documented in the wiki",
                "Traffic cutover scheduled for maintenance window",
                "Monitoring dashboards updated with new metrics",
                "Performance baseline captured for comparison",
                "Edge cases identified and handled",
                "Documentation updates pushed to docs site",
                "Team briefed on new deployment process",
            ]),
            ("Database Performance Optimization", [
                "Query performance degraded after the schema change",
                "Analyzing slow query logs from production",
                "Index strategy needs to be revisited",
                "Partitioning the large tables would help",
                "Connection pooling settings need tuning",
                "Read replicas can offload some queries",
                "Caching layer would benefit the reporting queries",
                "The ORM eager loading is causing N+1 issues",
                "Batch processing for bulk operations",
                "Summary of proposed optimizations attached",
            ]),
        ],
        "design": [
            ("Mobile App Redesign", [
                "User research completed - key insights in attached deck",
                "Navigation patterns need simplification",
                "Tab bar design updated based on feedback",
                "Onboarding flow redesigned to reduce friction",
                "Dark mode color palette finalized",
                "Component library update in progress",
                "Accessibility audit scheduled for next week",
                "Final mockups ready for stakeholder review",
            ]),
        ],
        "general": [
            ("Q1 Planning Kickoff", [
                "Excited to start Q1 planning with everyone",
                "Goals from last quarter achieved - great team effort!",
                "Focus areas for this quarter: growth, reliability, UX",
                "Individual OKRs will be drafted by end of week",
                "Budget allocation for tooling discussed",
                "Hiring pipeline status update next Monday",
                "Team capacity planning needed",
                "All hands recording linked in thread",
            ]),
        ],
        "support": [
            ("Enterprise Customer Escalation", [
                "Customer reported critical issue affecting their workflow",
                "Issue reproducible in staging environment",
                "Root cause identified - fix in code review",
                "Hotfix deployed to production",
                "Customer confirmed issue resolved",
                "Post-mortem scheduled to prevent recurrence",
            ]),
        ],
    }
    
    return random.choice(concepts.get(channel_name, concepts["general"]))


def seed_conversations(days_back=14):
    """Generate realistic conversation history across multiple days."""
    print("\n[Seed] Generating conversation history...")
    
    # Track all messages created for context linking
    all_messages = []
    now = datetime.utcnow()
    
    # Create conversations across different channels
    for channel_name, channel_desc in CHANNELS:
        # Create 2-3 conversation concepts per channel
        for _ in range(random.randint(2, 3)):
            title, content_templates = generate_conversation_concept(channel_name)
            
            # Occasionally add some variation to the title
            if random.random() > 0.5:
                title = f"{title} - {random.choice(['v2', 'follow-up', 'iteration', 'review'])}"
            
            # Create conversation
            conversation = create_conversation(title, channel_name, channel_desc)
            if conversation.id:
                print(f"  [+] Created conversation: {title}")
            
            # Create messages spanning across multiple days
            messages = []
            
            # Vary the number of days this conversation spans
            span_days = random.randint(3, min(days_back, 10))
            messages_per_day = random.randint(3, 8)
            
            for day_offset in range(span_days, -1, -1):
                messages_today = random.randint(
                    max(1, messages_per_day - 2), 
                    messages_per_day + 2
                )
                
                for msg_num in range(messages_today):
                    # Calculate timestamp
                    day_start = now - timedelta(days=day_offset)
                    msg_hour = random.randint(9, 17)
                    msg_minute = random.randint(0, 59)
                    timestamp = day_start.replace(
 hour=msg_hour, minute=msg_minute)
                    
                    # Select content (with some variation)
                    if day_offset == 0 and msg_num == len([1 for _ in range(messages_today)]) - 1:
                        # Most recent message - use a follow-up template
                        content = "Thanks for the update! I'll review and get back to you."
                    else:
                        content = random.choice(MESSAGE_TEMPLATES[channel_name])
                    
                    author = random.choice(USERS)
                    
                    message = create_message(content, author, timestamp, conversation)
                    messages.append(message)
                    all_messages.append(message)
                    
            # Add context links between recent and relevant past messages
            if len(messages) >= 3:
                # Link day-old message to week-old message
                link_context(messages, now, min(7, len(messages) - 1), 0.50, "one_week")
                
                # Link day-old message to two-days-ago message
                link_context(messages, now, min(2, len(messages) - 1), 0.81, "two_days")
                
            if len(messages) % 100 == 0:
                print(f"    ... {len(all_messages)} messages created")
    
    print(f"\n[Seed] Complete: {len(all_messages)} messages across {len(CHANNELS) * 3} conversations")
    return all_messages


def main():
    """Main seeding function."""
    print("=" * 60)
    print("CONVERSATION MEMORY CHAINS - DATA SEEDING")
    print("=" * 60)
    
    # Check for existing data
    if check_existing_data():
        print("\n[!] Existing conversations found. Skipping seed to avoid duplicates.")
        print("    To reseed, delete existing CONVERSATION records first.")
        return
    
    # Generate conversation history
    seed_conversations(days_back=14)
    
    print("\n[Seed] Data seeded successfully!")
    print("    Run `python main.py` to see the time-decay demonstration.")


if __name__ == "__main__":
    main()
