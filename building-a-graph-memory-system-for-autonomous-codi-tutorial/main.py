"""
Building a Graph-Memory System for Autonomous Coding Agents

A complete implementation demonstrating persistent memory for autonomous
coding agents using RushDB's property graph and vector search.

This example shows:
1. Schema setup for code entities and relationships
2. Pushing observations from agent actions into the graph
3. Semantic vector search for context retrieval
4. Memory pruning (forgetting stale nodes)
5. A minimal agent loop that writes to and reads from graph memory

Run: python main.py
Setup: First run python seed.py to populate sample data
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# =============================================================================
# CONFIGURATION
# =============================================================================

api_key = os.getenv("RUSHDB_API_KEY")
if not api_key:
    print("ERROR: RUSHDB_API_KEY not found in environment")
    print("Copy .env.example to .env and add your API key")
    sys.exit(1)

db = RushDB(api_key)

# Initialize embedding model (sentence-transformers/all-MiniLM-L6-v2)
# This is a fast, lightweight model good for code-related text
print("Loading embedding model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def get_embedding(text: str) -> list:
    """Generate embedding for text using the sentence-transformer model."""
    return model.encode(text).tolist()


# =============================================================================
# SCHEMA SETUP
# =============================================================================

def initialize_schema():
    """
    Initialize the graph memory schema.
    
    Creates a simple structure:
    - Agent: The autonomous coding agent
    - Task: A coding task or goal  
    - File: A file being modified
    - Observation: An observation or hypothesis
    - ConfirmedFact: A validated piece of knowledge
    - Decision: A decision made during execution
    """
    print("\n" + "="*60)
    print("STEP 1: Initializing Graph Memory Schema")
    print("="*60)
    
    # Check if schema already exists by looking for Agent label
    existing_agents = db.records.find({"labels": ["Agent"], "limit": 1})
    
    if existing_agents.data:
        print("Schema already initialized. Fetching existing agent...")
        return db.records.find_by_id(existing_agents.data[0].id)
    
    # Create the agent record
    agent = db.records.create(
        label="Agent",
        data={
            "name": "Codi",
            "version": "1.0.0",
            "session_id": f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "session_started": datetime.now().isoformat()
        },
        vectors=[{"propertyName": "description", "vector": get_embedding("Codi is an autonomous coding agent")}]
    )
    
    print(f"Created agent: {agent['name']} (ID: {agent.id})")
    print("\nSchema labels available:")
    print("  - Agent: Represents the autonomous agent")
    print("  - Task: Coding tasks or goals")
    print("  - File: Files being modified")
    print("  - Observation: Observations and hypotheses")
    print("  - ConfirmedFact: Validated knowledge")
    print("  - Decision: Decisions made during execution")
    
    return agent


# =============================================================================
# PUSHING OBSERVATIONS
# =============================================================================

def push_observation(agent, observation_type: str, content: str, importance: int = 2, metadata: dict = None):
    """
    Push an observation from the agent's actions into the graph.
    
    Args:
        agent: The agent record
        observation_type: Type of observation (hypothesis, finding, speculation, etc.)
        content: The observation content
        importance: 1=low, 2=medium, 3=high (high importance = never auto-delete)
        metadata: Additional metadata for the observation
    """
    observation = db.records.create(
        label="Observation",
        data={
            "type": observation_type,
            "content": content,
            "importance": importance,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            **(metadata or {})
        },
        vectors=[{"propertyName": "content", "vector": get_embedding(content)}]
    )
    
    # Link observation to the agent who created it
    db.records.attach(
        source=agent,
        target=observation,
        options={"type": "CREATED"}
    )
    
    return observation


def push_file_change(agent, task, file_path: str, change_type: str, content_summary: str):
    """
    Record a file modification in the graph.
    
    Args:
        agent: The agent record
        task: The task being worked on
        file_path: Path to the modified file
        change_type: Type of change (created, modified, deleted)
        content_summary: Summary of what changed
    """
    file_record = db.records.create(
        label="File",
        data={
            "path": file_path,
            "change_type": change_type,
            "content_summary": content_summary,
            "modified_at": datetime.now().isoformat()
        },
        vectors=[{"propertyName": "description", "vector": get_embedding(f"{file_path}: {content_summary}")}]
    )
    
    # Link file to task
    db.records.attach(
        source=task,
        target=file_record,
        options={"type": "MODIFIES"}
    )
    
    return file_record


def push_confirmed_fact(agent, content: str, source: str = "agent_analysis", related_observation=None):
    """
    Record a confirmed fact in the graph.
    
    Confirmed facts have importance=3 and are never auto-deleted.
    
    Args:
        agent: The agent record
        content: The confirmed fact content
        source: Where this fact was confirmed from
        related_observation: Optional observation that was validated
    """
    fact = db.records.create(
        label="ConfirmedFact",
        data={
            "content": content,
            "source": source,
            "confirmed_at": datetime.now().isoformat(),
            "importance": 3  # High importance - never delete
        },
        vectors=[{"propertyName": "content", "vector": get_embedding(content)}]
    )
    
    # If there's a related observation, link them and update observation status
    if related_observation:
        db.records.attach(
            source=related_observation,
            target=fact,
            options={"type": "VALIDATED_AS"}
        )
        # Update the observation status
        db.records.update(
            record_id=related_observation.id,
            data={"status": "confirmed"}
        )
    
    return fact


def demonstrate_pushing_observations(agent):
    """Demonstrate pushing various types of observations into the graph."""
    print("\n" + "="*60)
    print("STEP 2: Pushing Observations from Agent Actions")
    print("="*60)
    
    # Create a task to work on
    task = db.records.create(
        label="Task",
        data={
            "title": "Add rate limiting to API endpoints",
            "description": "Implement rate limiting middleware to prevent abuse",
            "status": "in_progress",
            "created_at": datetime.now().isoformat()
        },
        vectors=[{"propertyName": "description", "vector": get_embedding("Implement rate limiting middleware to prevent abuse")}]
    )
    
    db.records.attach(source=agent, target=task, options={"type": "WORKING_ON"})
    print(f"Created task: {task['title']} (ID: {task.id})")
    
    # Push various observations
    print("\nPushing observations...")
    
    obs1 = push_observation(
        agent,
        observation_type="hypothesis",
        content="Redis would be ideal for rate limiting due to its atomic INCR operation",
        importance=2,
        metadata={"domain": "infrastructure"}
    )
    print(f"  Created hypothesis: {obs1['content'][:50]}...")
    
    obs2 = push_observation(
        agent,
        observation_type="finding",
        content="The /api/users endpoint is called 10x more than other endpoints",
        importance=2,
        metadata={"endpoint": "/api/users", "call_frequency": "high"}
    )
    print(f"  Created finding: {obs2['content'][:50]}...")
    
    obs3 = push_observation(
        agent,
        observation_type="speculation",
        content="Could use token bucket algorithm for smoother rate limiting",
        importance=1
    )
    print(f"  Created speculation: {obs3['content'][:50]}...")
    
    # Confirm a fact from an observation
    print("\nConfirming a hypothesis...")
    fact = push_confirmed_fact(
        agent,
        content="Token bucket algorithm provides better rate limiting than fixed window",
        source="algorithm_analysis",
        related_observation=obs3
    )
    print(f"  Confirmed fact: {fact['content'][:50]}...")
    print(f"  Observation '{obs3['content'][:30]}...' status updated to: confirmed")
    
    # Record file changes
    print("\nRecording file modifications...")
    file1 = push_file_change(
        agent, task,
        file_path="src/middleware/rate_limiter.py",
        change_type="created",
        content_summary="New rate limiting middleware with token bucket"
    )
    print(f"  Created file: {file1['path']}")
    
    file2 = push_file_change(
        agent, task,
        file_path="src/config/rate_limits.json",
        change_type="created",
        content_summary="Configuration for rate limit thresholds"
    )
    print(f"  Created file: {file2['path']}")
    
    return task, [obs1, obs2, obs3], fact


# =============================================================================
# SEMANTIC CONTEXT RETRIEVAL
# =============================================================================

def retrieve_relevant_context(query: str, labels: list = None, limit: int = 5) -> list:
    """
    Retrieve relevant context using semantic vector search.
    
    This is the key advantage over scanning full history - we can find
    semantically similar past observations without exact keyword matching.
    
    Args:
        query: Natural language query
        labels: Optional list of labels to filter by
        limit: Maximum number of results
        
    Returns:
        List of matching records with similarity scores
    """
    search_params = {
        "propertyName": "content",
        "query": query,
        "limit": limit
    }
    
    if labels:
        search_params["labels"] = labels
    
    results = db.ai.search(search_params)
    
    return [
        {
            "record": record,
            "score": record.score,
            "content": record.get("content", ""),
            "type": record.get("type", record.label)
        }
        for record in results.data
    ]


def demonstrate_semantic_search(agent):
    """Demonstrate semantic context retrieval from the graph."""
    print("\n" + "="*60)
    print("STEP 3: Semantic Context Retrieval")
    print("="*60)
    
    print("\nQuery: 'What do I know about JWT and authentication?'")
    print("-" * 50)
    results = retrieve_relevant_context(
        "JWT authentication security",
        labels=["Observation", "ConfirmedFact"],
        limit=5
    )
    for i, result in enumerate(results, 1):
        print(f"  {i}. [{result['type']}] (score: {result['score']:.3f})")
        print(f"     {result['content'][:80]}...")
    
    print("\nQuery: 'What decisions have been made about security?'")
    print("-" * 50)
    results = retrieve_relevant_context(
        "security architecture decisions",
        labels=["Decision", "ConfirmedFact"],
        limit=5
    )
    for i, result in enumerate(results, 1):
        print(f"  {i}. [{result['type']}] (score: {result['score']:.3f})")
        print(f"     {result['content'][:80]}...")
    
    print("\nQuery: 'What files have been modified recently?'")
    print("-" * 50)
    results = retrieve_relevant_context(
        "file modifications code changes",
        labels=["File"],
        limit=5
    )
    for i, result in enumerate(results, 1):
        print(f"  {i}. [file] (score: {result['score']:.3f})")
        print(f"     {result['record']['path']}")


# =============================================================================
# MEMORY PRUNING (FORGETTING)
# =============================================================================

def get_memory_age_days(record) -> int:
    """Calculate how many days old a memory record is."""
    created_at = record.get("created_at") or record.get("confirmed_at") or record.get("decided_at")
    if not created_at:
        return 0
    
    created = datetime.fromisoformat(created_at)
    age = datetime.now() - created
    return age.days


def prune_stale_observations(agent, max_age_by_importance: dict = None) -> dict:
    """
    Prune (soft-delete) stale observations while preserving important decisions.
    
    Memory pruning strategy:
    - importance=3 (high): Never auto-delete - these are confirmed facts/decisions
    - importance=2 (medium): Delete after 30 days if not confirmed
    - importance=1 (low): Delete after 7 days
    
    Args:
        agent: The agent record (for filtering)
        max_age_by_importance: Dict mapping importance to max age in days
        
    Returns:
        Dict with pruning statistics
    """
    if max_age_by_importance is None:
        max_age_by_importance = {1: 7, 2: 30}  # Low: 7 days, Medium: 30 days
    
    print("\n" + "="*60)
    print("STEP 4: Memory Pruning (Forgetting Stale Observations)")
    print("="*60)
    
    stats = {"checked": 0, "pruned": 0, "preserved": 0, "by_importance": {}}
    
    # Find all observations
    observations = db.records.find({"labels": ["Observation"], "limit": 100})
    
    print(f"\nChecking {len(observations.data)} observations for pruning...")
    print(f"Pruning rules: importance=1 -> {max_age_by_importance.get(1, 7)} days, importance=2 -> {max_age_by_importance.get(2, 30)} days")
    print("Preserved: importance=3 (high) observations are never auto-deleted")
    print()
    
    for obs in observations.data:
        stats["checked"] += 1
        importance = obs.get("importance", 2)
        status = obs.get("status", "pending")
        age_days = get_memory_age_days(obs)
        max_age = max_age_by_importance.get(importance, 30)
        
        # Never delete high-importance (confirmed) observations
        if importance >= 3:
            stats["preserved"] += 1
            stats["by_importance"][importance] = stats["by_importance"].get(importance, 0) + 1
            continue
        
        # Skip if already confirmed (these are valuable)
        if status == "confirmed":
            stats["preserved"] += 1
            continue
        
        # Check if stale
        if age_days > max_age:
            # Soft delete by marking as 'pruned'
            db.records.update(
                record_id=obs.id,
                data={"status": "pruned", "pruned_at": datetime.now().isoformat()}
            )
            stats["pruned"] += 1
            print(f"  Pruned: '{obs['content'][:50]}...' (importance={importance}, age={age_days} days)")
        else:
            stats["preserved"] += 1
    
    print(f"\nPruning complete:")
    print(f"  Checked: {stats['checked']}")
    print(f"  Preserved: {stats['preserved']}")
    print(f"  Pruned: {stats['pruned']}")
    
    return stats


# =============================================================================
# MINIMAL AGENT LOOP
# =============================================================================

def agent_loop(agent, num_iterations: int = 3):
    """
    A minimal agent loop that demonstrates the full memory cycle:
    1. Perceive (get context from memory)
    2. Think (process and decide)
    3. Act (modify files, make observations)
    4. Remember (store in memory)
    
    Args:
        agent: The agent record
        num_iterations: Number of simulated work iterations
    """
    print("\n" + "="*60)
    print("STEP 5: Minimal Agent Loop")
    print("="*60)
    
    tasks_to_work_on = [
        {
            "title": "Implement caching layer",
            "description": "Add Redis caching for frequently accessed data"
        },
        {
            "title": "Add logging middleware",
            "description": "Create structured logging for API requests"
        },
        {
            "title": "Update API documentation",
            "description": "Document new rate limiting endpoints"
        }
    ]
    
    for i, task_template in enumerate(tasks_to_work_on[:num_iterations], 1):
        print(f"\n--- Iteration {i}/{num_iterations} ---")
        
        # Step 1: PERCEIVE - Get relevant context from memory
        print(f"\n1. PERCEIVE: Searching memory for context about '{task_template['title']}'...")
        context = retrieve_relevant_context(
            task_template["description"],
            labels=["Observation", "ConfirmedFact", "Task"],
            limit=3
        )
        if context:
            print(f"   Found {len(context)} relevant memories")
            for c in context[:2]:
                print(f"   - {c['content'][:60]}...")
        else:
            print("   No relevant memories found")
        
        # Step 2: THINK - Create task and make observations
        print(f"\n2. THINK: Processing task '{task_template['title']}'...")
        task = db.records.create(
            label="Task",
            data={
                **task_template,
                "status": "in_progress",
                "created_at": datetime.now().isoformat()
            },
            vectors=[{"propertyName": "description", "vector": get_embedding(task_template["description"])}]
        )
        db.records.attach(source=agent, target=task, options={"type": "WORKING_ON"})
        print(f"   Created task: {task['title']} (ID: {task.id})")
        
        # Make an observation based on the task
        observation_content = f"Consider using decorator pattern for {task_template['title']}"
        obs = push_observation(
            agent,
            observation_type="idea",
            content=observation_content,
            importance=2,
            metadata={"task_id": task.id}
        )
        print(f"   Made observation: {observation_content[:50]}...")
        
        # Step 3: ACT - Simulate making a decision
        print(f"\n3. ACT: Making decision about implementation approach...")
        decision = db.records.create(
            label="Decision",
            data={
                "description": f"Implement {task_template['title']} using dependency injection",
                "rationale": "This approach allows for easier testing and mocking",
                "outcome": "planned",
                "decided_at": datetime.now().isoformat(),
                "importance": 2
            },
            vectors=[{"propertyName": "rationale", "vector": get_embedding("This approach allows for easier testing and mocking")}]
        )
        db.records.attach(source=agent, target=decision, options={"type": "MADE_DECISION"})
        db.records.attach(source=decision, target=task, options={"type": "INFORMS"})
        print(f"   Made decision: {decision['description'][:50]}...")
        
        # Step 4: REMEMBER - Update task status
        print(f"\n4. REMEMBER: Storing results in memory...")
        db.records.update(
            record_id=task.id,
            data={"status": "completed", "completed_at": datetime.now().isoformat()}
        )
        print(f"   Task '{task['title']}' marked as completed")
    
    print("\n" + "="*60)
    print("Agent loop complete!")
    print("="*60)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Run the complete graph-memory demonstration."""
    print("\n" + "#"*60)
    print("# Graph Memory System for Autonomous Coding Agents")
    print("#"*60)
    print("\nThis demonstration shows how to build persistent memory")
    print("for autonomous coding agents using RushDB.")
    print()
    
    # Step 1: Initialize schema
    agent = initialize_schema()
    
    # Step 2: Push observations
    task, observations, fact = demonstrate_pushing_observations(agent)
    
    # Step 3: Semantic search
    demonstrate_semantic_search(agent)
    
    # Step 4: Memory pruning
    prune_stale_observations(agent)
    
    # Step 5: Agent loop
    agent_loop(agent, num_iterations=2)
    
    # Summary
    print("\n" + "#"*60)
    print("# SUMMARY")
    print("#"*60)
    print("""
This tutorial demonstrated:

1. SCHEMA SETUP
   - Created Agent, Task, File, Observation, ConfirmedFact, Decision labels
   - Established relationships: WORKING_ON, MODIFIES, CREATED, MADE_DECISION

2. PUSHING OBSERVATIONS
   - Logged hypotheses, findings, and speculations
   - Recorded file modifications
   - Confirmed facts and linked them to source observations

3. SEMANTIC CONTEXT RETRIEVAL
   - Used vector similarity search to find relevant memories
   - No need to scan full history - semantic search finds context

4. MEMORY PRUNING
   - Implemented importance-based retention policy
   - High importance (3): Never delete
   - Medium importance (2): Delete after 30 days if not confirmed
   - Low importance (1): Delete after 7 days
   - Preserved confirmed facts and decisions

5. AGENT LOOP
   - Demonstrated perceive -> think -> act -> remember cycle
   - Each iteration creates tasks, observations, and decisions
   - All stored persistently in the graph

The total implementation is under 200 lines of core logic,
eliminating the need for manual context management in autonomous agents.
""")

    # Final stats
    print("\nFinal database state:")
    labels = db.labels.find({})
    for label_result in labels:
        print(f"  {label_result.name}: {label_result.count} records")


if __name__ == "__main__":
    main()
