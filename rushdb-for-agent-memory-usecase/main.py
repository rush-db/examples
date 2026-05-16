"""
RushDB for Agent Memory - Complete Implementation

This example demonstrates how to build persistent long-term memory for AI agents
using RushDB's unique combination of property graph relationships and vector 
similarity search.

Key concepts demonstrated:
1. Zero-schema approach: Add memory types without migrations
2. Graph relationships: Link sessions, tasks, and tool executions
3. Vector embeddings: Semantic retrieval of similar past issues
4. Hybrid queries: Combine graph traversal with vector search
5. Full agent loop: From task receipt to memory-enriched response
"""

import os
import time
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from rushdb import RushDB
from sentence_transformers import SentenceTransformer
import numpy as np


class AgentMemory:
    """
    Agent memory system using RushDB for persistent, retrievable context.
    
    This class demonstrates RushDB's dual-layer architecture:
    - Property graph for relationship-based context (sessions, tasks, tools)
    - Vector search for semantic similarity (finding related failures/solutions)
    """

    def __init__(self, db: RushDB, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the agent memory system.
        
        Args:
            db: RushDB instance for persistent storage
            model_name: Name of the sentence-transformer model for embeddings
        """
        self.db = db
        self.model = SentenceTransformer(model_name)
        self.vector_index_id: Optional[str] = None
        
        # Ensure we have a vector index for semantic memory search
        self._ensure_vector_index()

    def _ensure_vector_index(self) -> None:
        """
        Create or verify the vector index for memory episodes.
        
        RushDB's zero-schema approach means we can add properties freely,
        but we still need an index for vector similarity search.
        """
        existing_indexes = self.db.ai.indexes.find()
        
        # Look for an existing index on MemoryEpisode content
        for idx in existing_indexes.data:
            if idx.get('label') == 'MemoryEpisode' and idx.get('propertyName') == 'content':
                self.vector_index_id = idx.get('__id')
                print(f"[Memory] Found existing vector index: {self.vector_index_id}")
                return
        
        # Create a new index if none exists
        # Dimensions: 384 for 'all-MiniLM-L6-v2' model
        index = self.db.ai.indexes.create({
            "label": "MemoryEpisode",
            "propertyName": "content",
            "dimensions": 384,
            "similarityFunction": "cosine"
        })
        self.vector_index_id = index.data.get('__id')
        print(f"[Memory] Created vector index: {self.vector_index_id}")

    def generate_embedding(self, text: str) -> list:
        """
        Generate a vector embedding for the given text.
        
        Using sentence-transformers for high-quality,通用 embeddings
        that capture semantic meaning for similarity search.
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def start_session(self, user_id: str, system_context: str) -> dict:
        """
        Start a new agent session.
        
        Creates a Session record that will track all tasks and context
        for this agent interaction. The session serves as the root node
        for all subsequent memory graph operations.
        
        Args:
            user_id: Identifier for the user requesting assistance
            system_context: Initial context/instructions for the agent
            
        Returns:
                dict with session metadata and RushDB record
        """
        session_id = f"session_{int(time.time() * 1000)}"
        
        # Create the session record
        # RushDB's zero-schema means we can store any properties we want
        session = self.db.records.create(
            label="Session",
            data={
                "session_id": session_id,
                "user_id": user_id,
                "system_context": system_context,
                "started_at": datetime.now().isoformat(),
                "status": "active"
            }
        )
        
        print(f"[Memory] Started new session: {session_id}")
        return {
            "session_id": session_id,
            "session_record": session
        }

    def get_relevant_memory(self, task_id: str, task_description: str = "") -> dict:
        """
        Retrieve relevant memory using hybrid graph + vector search.
        
        This is the core memory retrieval pattern:
        1. Graph traversal: Find tasks that previously failed on the same ID
        2. Vector search: Find semantically similar memory episodes
        3. Combine results for context-enriched responses
        
        Args:
            task_id: Identifier for the current task
            task_description: Natural language description for vector search
            
        Returns:
            dict with past failures, similar issues, and context summary
        """
        context = {
            "past_failures": [],
            "similar_issues": [],
            "executed_tools": [],
            "summary": ""
        }
        
        # ============================================================
        # STEP 1: Graph Traversal - Follow FAILED_ON relationships
        # ============================================================
        # Find all tasks that failed with this task_id and linked memory
        past_failed_tasks = self.db.records.find({
            "labels": ["Task"],
            "where": {
                "MemoryEpisode": {
                    "$relation": {
                        "type": "FAILED_ON",
                        "direction": "out"
                    }
                },
                "task_id": task_id
            }
        })
        
        if past_failed_tasks.data:
            print(f"[Memory] Found {len(past_failed_tasks.data)} past failures for task_id: {task_id}")
            for task in past_failed_tasks.data:
                # Get the linked memory episodes
                linked_memory = self.db.records.find({
                    "labels": ["MemoryEpisode"],
                    "where": {
                        "Task": {
                            "$relation": {
                                "type": "FAILED_ON",
                                "direction": "in"
                            },
                            "$id": task.id
                        }
                    }
                })
                
                for memory in linked_memory.data:
                    context["past_failures"].append({
                        "error": memory.data.get("error_message", ""),
                        "lesson": memory.data.get("lesson", ""),
                        "timestamp": memory.data.get("created_at", "")
                    })
        
        # ============================================================
        # STEP 2: Vector Search - Find semantically similar issues
        # ============================================================
        if task_description:
            query_embedding = self.generate_embedding(task_description)
            
            if self.vector_index_id:
                # Upsert the query vector for search
                # In production, you might pre-compute task embeddings on creation
                try:
                    self.db.ai.indexes.upsert_vectors(
                        self.vector_index_id,
                        {
                            "items": [
                                {
                                    "recordId": f"query_{task_id}",
                                    "vector": query_embedding
                                }
                            ]
                        }
                    )
                except Exception as e:
                    print(f"[Memory] Vector upsert skipped: {e}")
            
            # Search for similar memory episodes
            # The semantic search finds issues with similar descriptions
            similar_results = self.db.ai.search({
                "propertyName": "content",
                "query": task_description,
                "labels": ["MemoryEpisode"],
                "where": {"type": "failure"},
                "limit": 3
            })
            
            for result in similar_results.data:
                if result.data.get("__score", 0) > 0.5:  # Similarity threshold
                    context["similar_issues"].append({
                        "description": result.data.get("description", ""),
                        "error": result.data.get("error_message", ""),
                        "lesson": result.data.get("lesson", ""),
                        "similarity_score": result.data.get("__score", 0)
                    })
        
        # ============================================================
        # STEP 3: Tool execution patterns
        # ============================================================
        # Find what tools have been used for similar tasks
        similar_tool_calls = self.db.records.find({
            "labels": ["ToolExecution"],
            "where": {
                "task_id": {"$contains": task_id.split("_")[0] if "_" in task_id else task_id}
            },
            "limit": 5
        })
        
        for tool in similar_tool_calls.data:
            context["executed_tools"].append({
                "tool": tool.data.get("tool_name", ""),
                "result": tool.data.get("result", {})
            })
        
        # Build summary
        context["summary"] = self._build_context_summary(context)
        
        return context

    def _build_context_summary(self, context: dict) -> str:
        """Build a natural language summary from retrieved context."""
        parts = []
        
        if context["past_failures"]:
            parts.append(f"Found {len(context['past_failures'])} past failures for this task")
            for failure in context["past_failures"][:2]:
                if failure["lesson"]:
                    parts.append(f"Previous lesson: {failure['lesson']}")
        
        if context["similar_issues"]:
            parts.append(f"Found {len(context['similar_issues'])} semantically similar issues")
            for issue in context["similar_issues"][:2]:
                if issue["lesson"]:
                    parts.append(f"Similar issue lesson: {issue['lesson']}")
        
        if context["executed_tools"]:
            tool_names = [t["tool"] for t in context["executed_tools"]]
            parts.append(f"Previously used tools: {', '.join(set(tool_names))}")
        
        return " ".join(parts) if parts else "No prior context found"

    def create_task(self, session_id: str, task_id: str, description: str, 
                    priority: str = "medium") -> dict:
        """
        Create a task record within a session.
        
        RushDB's zero-schema approach means we can add any properties
        to Task records as our agent capabilities evolve.
        """
        # Find the session
        sessions = self.db.records.find({
            "labels": ["Session"],
            "where": {"session_id": session_id}
        })
        
        if not sessions.data:
            raise ValueError(f"Session not found: {session_id}")
        
        session = sessions.data[0]
        
        # Create task with optional embedding for future retrieval
        task = self.db.records.create(
            label="Task",
            data={
                "task_id": task_id,
                "description": description,
                "priority": priority,
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
        )
        
        # Link task to session via graph relationship
        self.db.records.attach(
            source=session,
            target=task,
            options={"type": "CONTAINS", "direction": "out"}
        )
        
        print(f"[Memory] Created task: {task_id}")
        return {
            "task_id": task_id,
            "task_record": task
        }

    def record_tool_execution(self, task_id: str, tool_name: str, 
                              parameters: dict, result: dict) -> dict:
        """
        Record a tool execution for memory and pattern analysis.
        
        Tool execution history is crucial for:
        1. Understanding which tools work for which task types
        2. Debugging when tool combinations fail
        3. Optimizing future tool selection
        """
        # Find the task
        tasks = self.db.records.find({
            "labels": ["Task"],
            "where": {"task_id": task_id}
        })
        
        execution = self.db.records.create(
            label="ToolExecution",
            data={
                "tool_name": tool_name,
                "parameters": parameters,
                "result": result,
                "task_id": task_id,
                "executed_at": datetime.now().isoformat(),
                "success": result.get("success", True)
            }
        )
        
        # Link to task via graph relationship
        if tasks.data:
            self.db.records.attach(
                source=tasks.data[0],
                target=execution,
                options={"type": "EXECUTED", "direction": "out"}
            )
        
        print(f"[Memory] Recorded tool execution: {tool_name}")
        return {
            "tool_name": tool_name,
            "execution_record": execution
        }

    def record_failure(self, task_id: str, tool_name: str, 
                       error_message: str, lesson: str = "") -> dict:
        """
        Record a failure with lessons learned.
        
        This demonstrates RushDB's graph relationship strength:
        1. Create a MemoryEpisode record
        2. Link it via FAILED_ON (from Task)
        3. Link it via LEARNED_FROM (from Task)
        
        This creates a traversable failure history that can be queried:
        - "What tasks failed on 'deploy' recently?"
        - "What lessons were learned from database errors?"
        """
        # Find the task
        tasks = self.db.records.find({
            "labels": ["Task"],
            "where": {"task_id": task_id}
        })
        
        if not tasks.data:
            print(f"[Memory] Task not found for failure recording: {task_id}")
            return {"success": False}
        
        task = tasks.data[0]
        
        # Create memory episode with failure details
        content = f"Task {task_id} failed using {tool_name}. Error: {error_message}. Lesson: {lesson}"
        embedding = self.generate_embedding(content)
        
        memory_episode = self.db.records.create(
            label="MemoryEpisode",
            data={
                "type": "failure",
                "description": f"Failure when executing {tool_name}",
                "content": content,
                "error_message": error_message,
                "tool_name": tool_name,
                "lesson": lesson,
                "created_at": datetime.now().isoformat()
            }
        )
        
        # Link via FAILED_ON relationship (task failed on this memory)
        self.db.records.attach(
            source=task,
            target=memory_episode,
            options={"type": "FAILED_ON", "direction": "out"}
        )
        
        # Also link via LEARNED_FROM (task learned from this memory)
        self.db.records.attach(
            source=task,
            target=memory_episode,
            options={"type": "LEARNED_FROM", "direction": "out"}
        )
        
        # Upsert vector for future semantic search
        if self.vector_index_id:
            try:
                self.db.ai.indexes.upsert_vectors(
                    self.vector_index_id,
                    {
                        "items": [
                            {
                                "recordId": memory_episode.id,
                                "vector": embedding
                            }
                        ]
                    }
                )
            except Exception as e:
                print(f"[Memory] Vector upsert skipped: {e}")
        
        print(f"[Memory] Recorded failure with lesson: {lesson[:50]}...")
        return {
            "task_id": task_id,
            "memory_episode": memory_episode
        }

    def get_session_summary(self, session_id: str) -> dict:
        """
        Get a complete summary of a session's memory.
        
        Demonstrates graph traversal to gather all related records:
        - Session → Tasks (via CONTAINS)
        - Task → ToolExecutions (via EXECUTED)
        - Task → MemoryEpisodes (via FAILED_ON, LEARNED_FROM)
        """
        sessions = self.db.records.find({
            "labels": ["Session"],
            "where": {"session_id": session_id}
        })
        
        if not sessions.data:
            return {"error": "Session not found"}
        
        session = sessions.data[0]
        summary = {
            "session_id": session_id,
            "user_id": session.data.get("user_id", ""),
            "started_at": session.data.get("started_at", ""),
            "tasks": [],
            "total_failures": 0,
            "total_tool_calls": 0
        }
        
        # Get all tasks in this session
        tasks = self.db.records.find({
            "labels": ["Task"],
            "where": {
                "Session": {
                    "$relation": {
                        "type": "CONTAINS",
                        "direction": "in"
                    },
                    "$id": session.id
                }
            }
        })
        
        for task in tasks.data:
            task_info = {
                "task_id": task.data.get("task_id", ""),
                "status": task.data.get("status", ""),
                "tool_executions": [],
                "failures": []
            }
            
            # Get tool executions for this task
            tool_calls = self.db.records.find({
                "labels": ["ToolExecution"],
                "where": {
                    "Task": {
                        "$relation": {
                            "type": "EXECUTED",
                            "direction": "in"
                        },
                        "$id": task.id
                    }
                }
            })
            
            for tool in tool_calls.data:
                task_info["tool_executions"].append(tool.data.get("tool_name", ""))
            
            # Get failures for this task
            failures = self.db.records.find({
                "labels": ["MemoryEpisode"],
                "where": {
                    "Task": {
                        "$relation": {
                            "type": "FAILED_ON",
                            "direction": "in"
                        },
                        "$id": task.id
                    }
                }
            })
            
            for failure in failures.data:
                task_info["failures"].append({
                    "error": failure.data.get("error_message", ""),
                    "lesson": failure.data.get("lesson", "")
                })
            
            summary["tasks"].append(task_info)
            summary["total_failures"] += len(task_info["failures"])
            summary["total_tool_calls"] += len(task_info["tool_executions"])
        
        return summary


def run_agent_loop(agent: AgentMemory):
    """
    Demonstrate the full agent loop with memory integration.
    
    This simulates an agent handling multiple tasks, showing:
    1. Session creation
    2. Context retrieval (hybrid search)
    3. Tool execution with memory
    4. Failure recording
    5. Memory-enabled responses
    """
    print("\n" + "=" * 60)
    print("RUNNING AGENT MEMORY LOOP")
    print("=" * 60)
    
    # Step 1: Start a new session
    session_info = agent.start_session(
        user_id="developer_alice",
        system_context="You are a debugging assistant that remembers past issues"
    )
    session_id = session_info["session_id"]
    
    # Step 2: Define tasks to process
    tasks_to_process = [
        {
            "task_id": "debug_api_timeout",
            "description": "User reports API timeout when fetching user data",
            "priority": "high"
        },
        {
            "task_id": "fix_login_redirect",
            "description": "Login redirect loop after successful authentication",
            "priority": "high"
        },
        {
            "task_id": "optimize_db_query",
            "description": "Slow database query causing dashboard lag",
            "priority": "medium"
        }
    ]
    
    # Step 3: Create tasks and process each one
    for task_info in tasks_to_process:
        print(f"\n--- Processing Task: {task_info['task_id']} ---")
        
        # Create the task in RushDB
        agent.create_task(
            session_id=session_id,
            task_id=task_info["task_id"],
            description=task_info["description"],
            priority=task_info["priority"]
        )
        
        # Retrieve relevant memory BEFORE processing
        # This is the key to memory-enabled responses
        context = agent.get_relevant_memory(
            task_id=task_info["task_id"],
            task_description=task_info["description"]
        )
        
        print(f"  Memory Context: {context['summary']}")
        
        # Simulate agent processing with context
        # In a real implementation, this would call an LLM with the context
        response = f"Processing '{task_info['description']}'"
        if context["past_failures"] or context["similar_issues"]:
            response += " (with memory context)"
        
        print(f"  Agent Response: {response}")
        
        # Record tool executions (simulated)
        tools_used = [
            {
                "tool_name": "code_search",
                "parameters": {"query": task_info["task_id"]},
                "result": {"files_found": 3}
            },
            {
                "tool_name": "git_blame",
                "parameters": {"file": "src/api.py", "line": 42},
                "result": {"author": "alice", "date": "2024-01-15"}
            }
        ]
        
        for tool in tools_used:
            agent.record_tool_execution(
                task_id=task_info["task_id"],
                tool_name=tool["tool_name"],
                parameters=tool["parameters"],
                result=tool["result"]
            )
        
        # Simulate a failure for demonstration
        if task_info["task_id"] == "debug_api_timeout":
            agent.record_failure(
                task_id=task_info["task_id"],
                tool_name="api_fetch",
                error_message="Connection timeout after 30 seconds",
                lesson="Always add retry logic with exponential backoff for external API calls"
            )
    
    # Step 4: Get session summary
    print("\n" + "=" * 60)
    print("SESSION SUMMARY")
    print("=" * 60)
    
    summary = agent.get_session_summary(session_id)
    print(f"Session ID: {summary['session_id']}")
    print(f"User: {summary['user_id']}")
    print(f"Total Tasks: {len(summary['tasks'])}")
    print(f"Total Tool Calls: {summary['total_tool_calls']}")
    print(f"Total Failures: {summary['total_failures']}")
    
    for task in summary["tasks"]:
        print(f"\n  Task: {task['task_id']}")
        print(f"    Status: {task['status']}")
        print(f"    Tools: {', '.join(task['tool_executions'])}")
        if task['failures']:
            for failure in task['failures']:
                print(f"    Failure: {failure['error']}")
                print(f"    Lesson: {failure['lesson']}")
    
    return session_id


def main():
    """Main entry point demonstrating the complete agent memory system."""
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("RUSHDB_API_KEY")
    
    if not api_key:
        print("ERROR: RUSHDB_API_KEY not found in environment")
        print("Please copy .env.example to .env and add your API key")
        print("Get your API key at: https://app.rushdb.com")
        return
    
    # Initialize RushDB connection
    db = RushDB(api_key)
    print("[Init] Connected to RushDB")
    
    # Initialize the agent memory system
    # Using 'all-MiniLM-L6-v2' - a fast, high-quality sentence embedding model
    agent = AgentMemory(db, model_name='all-MiniLM-L6-v2')
    print("[Init] Agent memory system ready")
    
    # Run the complete agent loop
    final_session_id = run_agent_loop(agent)
    
    print("\n" + "=" * 60)
    print("EXAMPLE COMPLETE")
    print("=" * 60)
    print(f"Session with all memory records: {final_session_id}")
    print("\nYou can now:")
    print("  1. Query this session again to get memory-enriched responses")
    print("  2. Start a new session and see past context influence behavior")
    print("  3. Explore the graph relationships in RushDB dashboard")


if __name__ == "__main__":
    main()
