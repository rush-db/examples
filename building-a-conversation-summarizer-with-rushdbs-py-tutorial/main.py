"""
Conversation Summarizer with RushDB.

Demonstrates:
- Graph relationships (participants ↔ conversations ↔ messages)
- Filtering by related records
- Vector search for semantic queries
- Conversation summarization via graph traversal

Run seed.py first to populate sample data.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Initialize RushDB client
api_token = os.getenv("RUSHDBSDK_API_TOKEN")
if not api_token:
    raise ValueError(
        "RUSHDBSDK_API_TOKEN not found. "
        "Copy .env.example to .env and add your API token."
    )

db = RushDB(api_token)

# Initialize embedding model (local, no API key needed)
print("Loading embedding model (this may take a moment on first run)...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
EMBEDDING_DIMENSIONS = 384  # all-MiniLM-L6-v2 produces 384-dim vectors


def find_conversations_by_participant(email: str):
    """
    Find all conversations a participant is involved in.
    Uses RushDB's relationship filtering to query by related record properties.
    """
    results = db.records.find({
        "labels": ["CONVERSATION"],
        "where": {
            "PARTICIPANT": {
                "$relation": {"type": "PARTICIPANT_IN", "direction": "in"},
                "email": email
            }
        }
    })
    return results.data


def get_conversation_messages(conversation_id: str):
    """
    Get all messages in a conversation using relationship traversal.
    """
    results = db.records.find({
        "labels": ["MESSAGE"],
        "where": {
            "CONVERSATION": {
                "$relation": {"type": "CONTAINS", "direction": "in"},
                "$id": {"$in": [conversation_id]}
            }
        },
        "orderBy": {"timestamp": "asc"}
    })
    return results.data


def get_conversation_participants(conversation_id: str):
    """
    Get all participants in a conversation.
    """
    results = db.records.find({
        "labels": ["PARTICIPANT"],
        "where": {
            "CONVERSATION": {
                "$relation": {"type": "PARTICIPANT_IN", "direction": "out"},
                "$id": {"$in": [conversation_id]}
            }
        }
    })
    return results.data


def ensure_vector_index_exists():
    """
    Ensure a vector index exists for message content.
    Creates it if it doesn't exist.
    """
    # Check for existing indexes
    existing = db.ai.indexes.find()
    for idx in existing.data:
        if idx.get('label') == 'MESSAGE' and idx.get('propertyName') == 'content':
            return idx
    
    # Create new external index
    print("Creating vector index for MESSAGE.content...")
    index = db.ai.indexes.create({
        "label": "MESSAGE",
        "propertyName": "content",
        "sourceType": "external",
        "dimensions": EMBEDDING_DIMENSIONS,
        "similarityFunction": "cosine"
    })
    return index.data


def index_messages_with_embeddings():
    """
    Index all messages with their embeddings for semantic search.
    Uses inline vector writes for cleaner code.
    """
    print("\nIndexing messages with embeddings for semantic search...")
    
    # Get all messages
    all_messages = db.records.find({
        "labels": ["MESSAGE"],
        "limit": 1000
    })
    
    # Check which messages already have vectors
    messages_to_index = []
    for msg in all_messages.data:
        # Messages without embeddings need to be indexed
        if not msg.data.get('__vectors') or 'content' not in msg.data.get('__vectors', {}):
            messages_to_index.append(msg)
    
    if not messages_to_index:
        print("All messages already indexed.")
        return
    
    print(f"Indexing {len(messages_to_index)} messages...")
    
    # Generate embeddings in batch
    contents = [msg['content'] for msg in messages_to_index]
    embeddings = embedding_model.encode(contents).tolist()
    
    # Update records with embeddings using set operation
    # Note: This uses upsert pattern for demo; in production you'd batch this
    for msg, embedding in zip(messages_to_index, embeddings):
        db.records.set(
            target=msg,
            label="MESSAGE",
            data=msg.fields,
            vectors=[{"propertyName": "content", "vector": embedding}]
        )
    
    print(f"Indexed {len(messages_to_index)} messages with embeddings.")


def semantic_search_conversations(query: str, limit: int = 5):
    """
    Find conversations matching a semantic query.
    Searches message content and groups results by conversation.
    """
    # Generate query embedding
    query_vector = embedding_model.encode(query).tolist()
    
    # Search messages
    results = db.ai.search({
        "propertyName": "content",
        "queryVector": query_vector,
        "labels": ["MESSAGE"],
        "limit": limit * 3  # Get more to group by conversation later
    })
    
    return results.data


def group_messages_by_conversation(messages):
    """
    Group search results by conversation ID and aggregate scores.
    """
    conversation_scores = {}
    conversation_messages = {}
    
    for msg in messages:
        # Find the conversation this message belongs to
        conv_results = db.records.find({
            "labels": ["CONVERSATION"],
            "where": {
                "MESSAGE": {
                    "$relation": {"type": "CONTAINS", "direction": "in"},
                    "$id": {"in": [msg.id]}
                }
            }
        })
        
        if conv_results.data:
            conv = conv_results.data[0]
            conv_id = conv.id
            
            if conv_id not in conversation_scores:
                conversation_scores[conv_id] = {
                    'conversation': conv,
                    'score': 0,
                    'count': 0,
                    'messages': []
                }
            
            # Aggregate scores (average them)
            score = msg.score or 0
            conversation_scores[conv_id]['score'] += score
            conversation_scores[conv_id]['count'] += 1
            conversation_scores[conv_id]['messages'].append(msg)
    
    # Average the scores
    for conv_id, data in conversation_scores.items():
        data['score'] /= data['count']
    
    # Sort by score
    sorted_convs = sorted(
        conversation_scores.values(),
        key=lambda x: x['score'],
        reverse=True
    )
    
    return sorted_convs


def generate_conversation_summary(conversation_id: str) -> dict:
    """
    Generate a summary of a conversation by aggregating its messages.
    """
    conversation = db.records.find_by_id(conversation_id)
    if not conversation:
        return {"error": "Conversation not found"}
    
    messages = get_conversation_messages(conversation_id)
    participants = get_conversation_participants(conversation_id)
    
    # Aggregate content for a text summary
    all_content = " ".join([msg['content'] for msg in messages])
    
    # Get unique participant emails
    participant_emails = [p['email'] for p in participants]
    
    # Simple keyword extraction (in production, use NLP)
    keywords = extract_keywords_from_messages(messages)
    
    return {
        "title": conversation['title'],
        "topic": conversation.get('topic', 'Unknown'),
        "message_count": len(messages),
        "participant_count": len(participants),
        "participants": participant_emails,
        "keywords": keywords,
        "preview": messages[0]['content'][:100] + "..." if messages else ""
    }


def extract_keywords_from_messages(messages, top_n: int = 5):
    """
    Simple keyword extraction from message content.
    In production, use NLP libraries like spaCy or KeyBERT.
    """
    # Common stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
        'those', 'i', 'we', 'you', 'he', 'she', 'it', 'they', 'them', 'their',
        'my', 'our', 'your', 'his', 'her', 'its', 'what', 'which', 'who',
        'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
        'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also'
    }
    
    # Collect all words
    all_words = []
    for msg in messages:
        words = msg['content'].lower().split()
        words = [w.strip('.,!?;:()[]{}') for w in words]
        words = [w for w in words if len(w) > 3 and w not in stop_words]
        all_words.extend(words)
    
    # Count frequencies
    word_freq = {}
    for word in all_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get top N by frequency
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]


def main():
    """Main demonstration function."""
    print("=" * 60)
    print("Conversation Summarizer Demo with RushDB")
    print("=" * 60)
    
    # Ensure vector index exists and index messages
    ensure_vector_index_exists()
    index_messages_with_embeddings()
    
    # Demo 1: Find conversations by participant
    print("\n" + "-" * 40)
    print("1. Finding conversations by participant")
    print("-" * 40)
    
    email = "alice@example.com"
    conversations = find_conversations_by_participant(email)
    print(f"\nConversations involving {email}:")
    
    for conv in conversations:
        messages = get_conversation_messages(conv.id)
        print(f"  - '{conv['title']}' ({len(messages)} messages)")
    
    # Demo 2: Semantic search
    print("\n" + "-" * 40)
    print("2. Semantic search: 'database migration strategies'")
    print("-" * 40)
    
    query = "database migration strategies"
    results = semantic_search_conversations(query, limit=5)
    grouped = group_messages_by_conversation(results)
    
    print(f"\nTop matching conversations:")
    for item in grouped[:3]:
        conv = item['conversation']
        participants = get_conversation_participants(conv.id)
        participant_emails = [p['email'] for p in participants]
        print(f"\n  '{conv['title']}' (score: {item['score']:.3f})")
        print(f"    Participants: {', '.join(participant_emails)}")
        print(f"    Keywords: {', '.join(extract_keywords_from_messages(item['messages'][:3]))}")
    
    # Demo 3: Find similar conversations
    print("\n" + "-" * 40)
    print("3. Finding similar conversations")
    print("-" * 40)
    
    query = "frontend testing approaches"
    results = semantic_search_conversations(query, limit=3)
    grouped = group_messages_by_conversation(results)
    
    if grouped:
        top_match = grouped[0]
        print(f"\nMost similar to '{query}':")
        print(f"  '{top_match['conversation']['title']}' (score: {top_match['score']:.3f})")
    else:
        print("\nNo similar conversations found.")
    
    # Demo 4: Generate comprehensive summary
    print("\n" + "-" * 40)
    print("4. Generating conversation summary")
    print("-" * 40)
    
    if conversations:
        summary = generate_conversation_summary(conversations[0].id)
        print(f"\nSummary for '{summary['title']}':")
        print(f"  Topic: {summary['topic']}")
        print(f"  Messages: {summary['message_count']}")
        print(f"  Participants: {', '.join(summary['participants'])}")
        print(f"  Key themes: {', '.join(summary['keywords'])}")
        print(f"  First message: \"{summary['preview']}\"")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
