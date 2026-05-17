"""
Multi-Agent Tool Orchestrator with RushDB Execution Tracing

This demo shows how to:
1. Store tool definitions with vector embeddings for semantic search
2. Record execution traces as graph nodes linked to tools and agents
3. Build execution chains (CHILD_OF) and parallel branches (PARALLEL_OF)
4. Traverse from failed executions to find root triggers and affected branches
5. Use semantic search to find similar available tools
"""

import os
import sys
import time
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from rushdb import RushDB

# Load seed data
from data.seed_data import AGENTS, TOOLS, EXECUTION_SCENARIOS

# Load environment
load_dotenv()

# Initialize embedding model (all-MiniLM-L6-v2 is fast and good quality)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def generate_embedding(text: str, model: SentenceTransformer) -> list:
    """Generate a vector embedding for text using sentence-transformers."""
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def get_or_create_index(db: RushDB, label: str, property_name: str, dimensions: int = 384) -> dict:
    """Get existing index or create a new one for vector search."""
    existing_indexes = db.ai.indexes.find()
    for idx in existing_indexes.data:
        if idx["label"] == label and idx["propertyName"] == property_name:
            return idx

    # Create new index
    index = db.ai.indexes.create({
        "label": label,
        "propertyName": property_name,
        "sourceType": "external",
        "dimensions": dimensions,
        "similarityFunction": "cosine"
    })
    return index.data


def seed_agents(db: RushDB) -> dict:
    """Create agent records in RushDB."""
    print("\n[1] Seeding agents...")
    agents = {}

    for agent_data in AGENTS:
        # Check if agent already exists
        existing = db.records.find({
            "labels": ["AGENT"],
            "where": {"name": agent_data["name"]}
        })


        if existing.data:
            agents[agent_data["name"]] = existing.data[0]
            print(f"  Found existing agent: {agent_data['name']}")
        else:
            agent = db.records.create(
                label="AGENT",
                data=agent_data
            )
            agents[agent_data["name"]] = agent
            print(f"  Created agent: {agent_data['name']}")

    print(f"  Total agents: {len(agents)}")
    return agents


def seed_tools(db: RushDB, model: SentenceTransformer) -> dict:
    """Create tool definitions with vector embeddings."""
    print("\n[2] Seeding tool definitions...")
    tools = {}


    for tool_data in TOOLS:
        # Check if tool already exists
        existing = db.records.find({
            "labels": ["TOOL"],
            "where": {"name": tool_data["name"]}
        })

        if existing.data:
            tools[tool_data["name"]] = existing.data[0]
            print(f"  Found existing tool: {tool_data['name']}")
        else:
            # Generate embedding for description
            description = tool_data["description"]
            embedding = generate_embedding(description, model)

            tool = db.records.create(
                label="TOOL",
                data=tool_data,
                vectors=[{"propertyName": "description", "vector": embedding}]
            )
            tools[tool_data["name"]] = tool
            print(f"  Created tool with embedding: {tool_data['name']}")


    print(f"  Total tools: {len(tools)}")
    return tools


def setup_vector_index(db: RushDB) -> None:
    """Set up vector index for semantic tool search."""
    print("\n[3] Creating vector index for semantic search...")

    index = get_or_create_index(db, "TOOL", "description", dimensions=384)
    print(f"  Vector index 'TOOL.description' ready (status: {index.get('status', 'ready')})")

    # Upsert all tool vectors into the index
    tools = db.records.find({"labels": ["TOOL"], "limit": 100})

    if tools.data:
        index_id = index["__id"]
        items = []
        for tool in tools.data:
            # Get embedding from description vector stored in record
            desc_vector = tool.data.get("__vectors", {}).get("description")
            if desc_vector:
                items.append({
                    "recordId": tool.id,
                    "vector": desc_vector
                })


        if items:
            db.ai.indexes.upsert_vectors(index_id, {"items": items})
            print(f"  Indexed {len(items)} tool vectors")


def record_execution(
    db: RushDB,
    agent: dict,
    tool: dict,
    input_data: dict,
    output_data: Optional[dict],
    status: str,
    error_message: Optional[str] = None,
    parent_execution: Optional[dict] = None,
    parallel_execution: Optional[dict] = None,
    is_root_trigger: bool = False
) -> dict:
    """Record a single execution trace with all relationships."""

    # Create execution record
    execution_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "input": input_data,
        "output": output_data,
        "status": status
    }

    if error_message:
        execution_data["error_message"] = error_message

    execution = db.records.create(label="EXECUTION", data=execution_data)

    # Link execution to agent (agent EXECUTED this execution)
    db.records.attach(
        source=agent,
        target=execution,
        options={"type": "EXECUTED"}
    )

    # Link execution to tool (execution USED this tool)
    db.records.attach(
        source=execution,
        target=tool,
        options={"type": "USED"}
    )

    # Chain: link to parent execution if this is a child in a chain
    if parent_execution:
        db.records.attach(
            source=execution,
            target=parent_execution,
            options={"type": "CHILD_OF"}
        )

    # Parallel: link to sibling execution if running in parallel
    if parallel_execution:
        db.records.attach(
            source=execution,
            target=parallel_execution,
            options={"type": "PARALLEL_OF"}
        )

    # Mark as root trigger if this is the first in a chain
    if is_root_trigger:
        db.records.create(
            label="TRIGGER",
            data={"type": "root_initiation", "execution_id": execution.id},
            vectors=[{"propertyName": "type", "vector": [0.0] * 384}]
        )
        db.records.attach(
            source=execution,
            target=db.records.find({"labels": ["TRIGGER"], "where": {"execution_id": execution.id}}).data[0],
            options={"type": "TRIGGERED"}
        )

    return execution


def simulate_agent_decisions(db: RushDB, agents: dict, tools: dict) -> list:
    """Simulate agent tool decisions and record all execution traces."""
    print("\n[4] Simulating Agent Decisions...")
    print("\n--- Decision Chain: User asks about weather ---")

    orchestrator = agents["orchestrator"]
    executions = []

    # Scenario 1: Weather inquiry chain
    for i, exec_spec in enumerate(EXECUTION_SCENARIOS[0]["executions"]):
        tool = tools[exec_spec["tool_name"]]
        is_root = (i == 0)

        parent_exec = executions[-1] if executions else None
        execution = record_execution(
            db=db,
            agent=orchestrator,
            tool=tool,
            input_data=exec_spec["input"],
            output_data=exec_spec["output"],
            status=exec_spec["status"],
            parent_execution=parent_exec,
            is_root_trigger=is_root
        )
        executions.append(execution)
        print(f"  Execution #{len(executions)}: AGENT_USED tool '{exec_spec['tool_name']}'")

        if parent_exec:
            print(f"  Execution #{len(executions)}: CHILD_OF execution #{len(executions)-1} → '{exec_spec['tool_name']}'")

    print("\n--- Parallel Execution: Multi-source data fetch ---")

    # Scenario 2: Parallel executions
    parallel_specs = EXECUTION_SCENARIOS[1]["executions"]
    parallel_exec_1 = record_execution(
        db=db,
        agent=orchestrator,
        tool=tools[parallel_specs[0]["tool_name"]],
        input_data=parallel_specs[0]["input"],
        output_data=parallel_specs[0]["output"],
        status=parallel_specs[0]["status"],
        is_root_trigger=True
    )
    executions.append(parallel_exec_1)

    parallel_exec_2 = record_execution(
        db=db,
        agent=orchestrator,
        tool=tools[parallel_specs[1]["tool_name"]],
        input_data=parallel_specs[1]["input"],
        output_data=parallel_specs[1]["output"],
        status=parallel_specs[1]["status"],
        parallel_execution=parallel_exec_1,
        is_root_trigger=True
    )
    executions.append(parallel_exec_2)

    print(f"  Execution #{len(executions)-1}: PARALLEL_OF execution #{len(executions)} → '{parallel_specs[0]['tool_name']}'")
    print(f"  Execution #{len(executions)}: PARALLEL_OF execution #{len(executions)-1} → '{parallel_specs[1]['tool_name']}'")

    print("\n--- Parallel Execution: Checkout with failure ---")

    # Scenario 3: Parallel with failure (finance agent)
    finance_agent = agents["finance_agent"]
    checkout_specs = EXECUTION_SCENARIOS[2]["executions"]

    # All three run in parallel - first two succeed, third fails
    failed_exec = record_execution(
        db=db,
        agent=finance_agent,
        tool=tools[checkout_specs[2]["tool_name"]],
        input_data=checkout_specs[2]["input"],
        output_data=None,
        status=checkout_specs[2]["status"],
        error_message=checkout_specs[2]["error"],
        is_root_trigger=True
    )
    executions.append(failed_exec)


    # Create sibling executions
    sibling_1 = record_execution(
        db=db,
        agent=finance_agent,
        tool=tools[checkout_specs[0]["tool_name"]],
        input_data=checkout_specs[0]["input"],
        output_data=checkout_specs[0]["output"],
        status=checkout_specs[0]["status"],
        parallel_execution=failed_exec,
        is_root_trigger=True
    )
    executions.append(sibling_1)

    sibling_2 = record_execution(
        db=db,
        agent=finance_agent,
        tool=tools[checkout_specs[1]["tool_name"]],
        input_data=checkout_specs[1]["input"],
        output_data=checkout_specs[1]["output"],
        status=checkout_specs[1]["status"],
        parallel_execution=failed_exec,
        is_root_trigger=True
    )
    executions.append(sibling_2)


    print(f"  Execution #{len(executions)-2}: PARALLEL_OF failed execution → '{checkout_specs[0]['tool_name']}' (SUCCESS)")
    print(f"  Execution #{len(executions)-1}: PARALLEL_OF failed execution → '{checkout_specs[1]['tool_name']}' (SUCCESS)")
    print(f"  Execution #{len(executions)}: FAILED tool '{checkout_specs[2]['tool_name']}'")

    print("\n--- Notification Discovery: Send email ---")

    # Scenario 4: Notification discovery
    notification_agent = agents["notification_agent"]
    notif_spec = EXECUTION_SCENARIOS[3]["executions"][0]

    email_exec = record_execution(
        db=db,
        agent=notification_agent,
        tool=tools[notif_spec["tool_name"]],
        input_data=notif_spec["input"],
        output_data=notif_spec["output"],
        status=notif_spec["status"],
        is_root_trigger=True
    )
    executions.append(email_exec)
    print(f"  Execution #{len(executions)}: AGENT_USED tool '{notif_spec['tool_name']}' (SUCCESS)")

    print(f"\n  Total executions recorded: {len(executions)}")
    return executions


def find_failure_root_cause(db: RushDB, failed_execution: dict) -> list:
    """Traverse up the CHILD_OF chain to find the root trigger."""
    root_causes = []
    current = failed_execution

    while current:
        root_causes.append(current)

        # Find parent execution (CHILD_OF relationship - we're the child)
        parents = db.records.find({
            "labels": ["EXECUTION"],
            "where": {
                "EXECUTION": {
                    "$relation": {"type": "CHILD_OF", "direction": "in"},
                    "id": current.id
                }
            }
        })

        if not parents.data:
            break

        current = parents.data[0]

    return root_causes


def find_affected_parallel_branches(db: RushDB, execution: dict) -> list:
    """Traverse PARALLEL_OF relationships to find sibling executions."""
    siblings = db.records.find({
        "labels": ["EXECUTION"],
        "where": {
            "EXECUTION": {
                "$relation": {"type": "PARALLEL_OF", "direction": "out"},
                "id": execution.id
            }
        }
    })


    incoming_siblings = db.records.find({
        "labels": ["EXECUTION"],
        "where": {
            "EXECUTION": {
                "$relation": {"type": "PARALLEL_OF", "direction": "in"},
                "id": execution.id
            }
        }
    })

    all_siblings = list(siblings.data) + list(incoming_siblings.data)
    # Filter out the execution itself
    return [s for s in all_siblings if s.id != execution.id]



def get_tool_name_for_execution(db: RushDB, execution: dict) -> str:
    """Get the tool name used in an execution."""
    tool_result = db.records.find({
        "labels": ["TOOL"],
        "where": {
            "EXECUTION": {
                "$relation": {"type": "USED", "direction": "in"},
                "id": execution.id
            }
        }
    })

    if tool_result.data:
        return tool_result.data[0].data.get("name", "unknown")
    return "unknown"


def query_failed_execution_chain(db: RushDB) -> None:
    """Query and display failure root cause analysis."""
    print("\n[5] Traversal Query: Finding failure root cause ===")

    # Find all failed executions
    failed_execs = db.records.find({
        "labels": ["EXECUTION"],
        "where": {"status": "failed"}
    })


    if not failed_execs.data:
        print("  No failed executions found.")
        return

    for failed_exec in failed_execs.data:
        tool_name = get_tool_name_for_execution(db, failed_exec)
        print(f"\n  Failed execution: {tool_name}")

        # Find root cause chain
        root_chain = find_failure_root_cause(db, failed_exec)
        root_chain.reverse()  # Put root first


        print("  Parent chain:")
        for i, exec in enumerate(root_chain):
            exec_tool = get_tool_name_for_execution(db, exec)
            status = exec.data.get("status", "unknown")
            marker = " - ROOT TRIGGER" if i == 0 else ""
            print(f"    - {exec_tool} ({status.upper()}{marker})")

        # Find affected parallel branches
        siblings = find_affected_parallel_branches(db, failed_exec)

        print("  Affected parallel branches:")
        if siblings:
            for sibling in siblings:
                sibling_tool = get_tool_name_for_execution(db, sibling)
                sibling_status = sibling.data.get("status", "unknown")
                print(f"    - {sibling_tool} ({sibling_status.upper()})")
        else:
            print("    (none)")


def find_similar_available_tools(db: RushDB, tools: dict) -> None:
    """Semantic search for tools similar to ones that were used."""
    print("\n[6] Semantic Search: Finding unused similar tools ===")

    # Find executions that used send_email
    email_executions = db.records.find({
        "labels": ["EXECUTION"],
        "where": {
            "TOOL": {"name": "send_email"}
        }
    })

    if not email_executions.data:
        print("  No send_email executions found.")
        return

    # Get the email tool for its description
    email_tool = tools.get("send_email")
    if not email_tool:
        print("  send_email tool not found.")
        return

    print("\n  Query: \"send notification to user\"")
    print("  Used tool: send_email")

    # Semantic search for similar communication tools
    similar_tools = db.ai.search({
        "propertyName": "description",
        "query": "send notification to user",
        "labels": ["TOOL"],
        "limit": 5
    })

    print("\n  Similar tools that were available but not used:")
    for result in similar_tools.data:
        tool_name = result.data.get("name", "unknown")
        # Skip the tool that was actually used
        if tool_name == "send_email":
            continue

        score = result.score or 0.0
        description = result.data.get("description", "")
        print(f"    - {tool_name}: {score:.2f} similarity - \"{description}\"")


def query_agent_executions(db: RushDB, agents: dict) -> None:
    """Query all executions for a specific agent."""
    print("\n[7] Querying all execution traces for 'orchestrator' agent ===")

    orchestrator = agents.get("orchestrator")
    if not orchestrator:
        print("  Orchestrator agent not found.")
        return

    # Find all executions by this agent
    agent_executions = db.records.find({
        "labels": ["EXECUTION"],
        "where": {
            "AGENT": {
                "$relation": {"type": "EXECUTED", "direction": "out"},
                "id": orchestrator.id
            }
        },
        "limit": 50
    })

    print(f"\n  Found {agent_executions.total} executions by orchestrator agent")

    for execution in agent_executions.data[:5]:  # Show first 5
        tool_name = get_tool_name_for_execution(db, execution)
        status = execution.data.get("status", "unknown")
        print(f"    - {tool_name} ({status.upper()})")

    if agent_executions.total > 5:
        print(f"    ... and {agent_executions.total - 5} more")


def main():
    """Main entry point for the demo."""
    print("=" * 50)
    print("  Tool Definition & Execution Trace Demo")
    print("=" * 50)

    # Initialize RushDB client
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY environment variable not set")
        print("Get your API key at https://rushdb.com")
        sys.exit(1)

    db = RushDB(api_key)
    print("\nConnected to RushDB")

    # Initialize embedding model
    print(f"\nLoading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("Embedding model ready")

    # Seed data
    agents = seed_agents(db)
    tools = seed_tools(db, model)

    # Set up vector index
    setup_vector_index(db)


    # Simulate agent decisions and record traces
    executions = simulate_agent_decisions(db, agents, tools)

    # Query: Find failure root cause
    query_failed_execution_chain(db)

    # Semantic search: Find similar available tools
    find_similar_available_tools(db, tools)

    # Query: Agent's execution history
    query_agent_executions(db, agents)

    print("\n" + "=" * 50)
    print("  Demo completed successfully!")
    print("=" * 50)
    print("\nExplore the graph at: https://app.rushdb.com")


if __name__ == "__main__":
    main()
