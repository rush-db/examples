"""
Implementing Tool Composition Graphs for Hierarchical Agent Task Decomposition

This example demonstrates how to model tool compositions and task hierarchies
using RushDB as a property graph store. It shows how agents can decompose complex
tasks into simpler sub-tasks by traversing tool composition graphs.
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB


def initialize_rushdb():
    """Initialize the RushDB client."""
    load_dotenv()
    
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        raise ValueError(
            "RUSHDB_API_KEY not found. "
            "Please add it to your .env file or export it as an environment variable."
        )
    
    url = os.getenv("RUSHDB_URL")
    if url:
        return RushDB(api_key, url=url)
    return RushDB(api_key)


def create_primitive_tools(db):
    """
    Create atomic tool capabilities that cannot be decomposed further.
    These are the leaf nodes in the tool composition graph.
    """
    primitive_tools = [
        {
            "name": "auth_user",
            "description": "Authenticate users via OAuth2 with multi-provider support",
            "capability": "authentication",
            "version": "1.0.0",
            "inputs": ["credentials", "provider"],
            "outputs": ["user_id", "session_token"],
        },
        {
            "name": "db_query",
            "description": "Execute parameterized SQL queries against the database",
            "capability": "data_retrieval",
            "version": "2.1.0",
            "inputs": ["query", "parameters"],
            "outputs": ["rows", "affected_count"],
        },
        {
            "name": "send_email",
            "description": "Send transactional emails via SMTP or API",
            "capability": "communication",
            "version": "1.5.0",
            "inputs": ["recipient", "template", "data"],
            "outputs": ["message_id", "status"],
        },
        {
            "name": "generate_pdf",
            "description": "Generate PDF documents from templates with data injection",
            "capability": "document_generation",
            "version": "3.0.0",
            "inputs": ["template", "data"],
            "outputs": ["document_url", "metadata"],
        },
        {
            "name": "log_activity",
            "description": "Log user activities and system events with structured metadata",
            "capability": "observability",
            "version": "1.0.0",
            "inputs": ["event_type", "user_id", "metadata"],
            "outputs": ["log_id", "timestamp"],
        },
    ]
    
    created_tools = []
    for tool_data in primitive_tools:
        tool = db.records.create(label="TOOL", data=tool_data)
        created_tools.append(tool)
    
    return created_tools


def create_composite_tools(db, primitive_tools):
    """
    Create composite tools that are composed of primitive tools.
    These form the edges in the tool composition graph.
    """
    # Create a lookup for primitive tools by name
    tool_lookup = {tool["name"]: tool for tool in primitive_tools}
    
    composite_tools_definitions = [
        {
            "name": "user_onboarding",
            "description": "Complete user onboarding flow with auth, email, and logging",
            "capability": "workflow",
            "version": "1.0.0",
            "sub_tool_names": ["auth_user", "send_email", "log_activity"],
        },
        {
            "name": "report_generation",
            "description": "Generate reports by querying data and producing PDF output",
            "capability": "workflow",
            "version": "2.0.0",
            "sub_tool_names": ["db_query", "generate_pdf", "log_activity"],
        },
        {
            "name": "customer_portal",
            "description": "Full customer portal workflow combining onboarding and reporting",
            "capability": "workflow",
            "version": "1.0.0",
            "sub_tool_names": ["user_onboarding", "report_generation", "log_activity"],
        },
    ]
    
    created_composites = []
    
    for composite_def in composite_tools_definitions:
        # Create the composite tool record
        composite = db.records.create(
            label="COMPOSITE_TOOL",
            data={
                "name": composite_def["name"],
                "description": composite_def["description"],
                "capability": composite_def["capability"],
                "version": composite_def["version"],
                "sub_tool_names": composite_def["sub_tool_names"],
            }
        )
        
        # Create composition relationships using a transaction
        with db.transactions.begin() as tx:
            for sub_tool_name in composite_def["sub_tool_names"]:
                # Handle both primitive tools and composite tool references
                if sub_tool_name in tool_lookup:
                    sub_tool = tool_lookup[sub_tool_name]
                else:
                    # Look up the composite tool by name
                    results = db.records.find({
                        "labels": ["COMPOSITE_TOOL"],
                        "where": {"name": sub_tool_name},
                    })
                    if results.data:
                        sub_tool = results.data[0]
                    else:
                        # Try to find as a primitive tool
                        results = db.records.find({
                            "labels": ["TOOL"],
                            "where": {"name": sub_tool_name},
                        })
                        sub_tool = results.data[0] if results.data else None
                
                if sub_tool:
                    db.records.attach(
                        source=composite,
                        target=sub_tool,
                        options={"type": "COMPOSED_OF", "direction": "out"},
                        transaction=tx,
                    )
        
        created_composites.append(composite)
    
    return created_composites


def create_agent(db, primitive_tools):
    """Create an agent and assign tools it can use."""
    agent = db.records.create(
        label="AGENT",
        data={
            "name": "Senior Engineer Agent",
            "role": "task_decomposer",
            "capabilities": ["planning", "execution", "composition"],
            "max_subtasks": 10,
        }
    )
    
    # Attach tools the agent can use
    for tool in primitive_tools:
        db.records.attach(
            source=agent,
            target=tool,
            options={"type": "USES", "direction": "out"},
        )
    
    return agent


def decompose_task_hierarchically(db, agent, composite_tools):
    """
    Decompose a complex task into a hierarchy of sub-tasks.
    This demonstrates how to use tool compositions for task decomposition.
    """
    # Find the customer_portal composite tool
    customer_portal = next(
        ct for ct in composite_tools if ct["name"] == "customer_portal"
    )
    
    # Create the root task
    root_task = db.records.create(
        label="TASK",
        data={
            "title": "Build Customer Portal",
            "description": "Build a complete customer portal with authentication and reporting",
            "priority": "high",
            "status": "decomposing",
        }
    )
    
    # Attach the agent and composite tool to the root task
    db.records.attach(
        source=agent,
        target=root_task,
        options={"type": "ASSIGNED_TO", "direction": "out"},
    )
    db.records.attach(
        source=root_task,
        target=customer_portal,
        options={"type": "REQUIRES_TOOL", "direction": "out"},
    )
    
    # Define sub-tasks based on the tool composition
    sub_tasks_definitions = [
        {
            "title": "Setup User Authentication",
            "description": "Configure OAuth2 authentication with multi-provider support",
            "tool_name": "auth_user",
            "is_primitive": True,
        },
        {
            "title": "Create User Dashboard",
            "description": "Build the user dashboard with reporting capabilities",
            "tool_name": "report_generation",
            "is_primitive": False,
        },
        {
            "title": "Send Welcome Email",
            "description": "Send welcome email to new users after account creation",
            "tool_name": "send_email",
            "is_primitive": True,
        },
        {
            "title": "Generate Privacy Report",
            "description": "Generate GDPR-compliant privacy report for users",
            "tool_name": "report_generation",
            "is_primitive": False,
        },
        {
            "title": "Log Portal Creation",
            "description": "Log all portal creation activities for audit trail",
            "tool_name": "log_activity",
            "is_primitive": True,
        },
    ]
    
    # Create sub-tasks and link them to the root task
    created_subtasks = []
    
    for idx, subtask_def in enumerate(sub_tasks_definitions):
        # Find the required tool
        tool_results = db.records.find({
            "labels": ["COMPOSITE_TOOL"],
            "where": {"name": subtask_def["tool_name"]},
        })
        
        if not tool_results.data:
            tool_results = db.records.find({
                "labels": ["TOOL"],
                "where": {"name": subtask_def["tool_name"]},
            })
        
        tool = tool_results.data[0] if tool_results.data else None
        
        # Create the sub-task
        sub_task = db.records.create(
            label="SUBTASK",
            data={
                "title": subtask_def["title"],
                "description": subtask_def["description"],
                "status": "pending",
                "order": idx + 1,
                "is_primitive": subtask_def["is_primitive"],
            }
        )
        
        # Link sub-task to root task (decomposition relationship)
        db.records.attach(
            source=root_task,
            target=sub_task,
            options={"type": "DECOMPOSES_INTO", "direction": "out"},
        )
        
        # Link sub-task to its required tool
        if tool:
            db.records.attach(
                source=sub_task,
                target=tool,
                options={"type": "EXECUTES_TOOL", "direction": "out"},
            )
        
        created_subtasks.append(sub_task)
    
    return root_task, created_subtasks


def query_composition_graph(db):
    """
    Query the tool composition graph to demonstrate graph traversal.
    """
    # Find all composite tools and their components
    composite_tools = db.records.find({
        "labels": ["COMPOSITE_TOOL"],
        "select": ["name", "description", "version"],
    })
    
    return composite_tools.data


def query_task_hierarchy(db, root_task):
    """
    Query the task hierarchy by finding all sub-tasks linked to a root task.
    """
    # Use label-based filtering to find sub-tasks of the root task
    sub_tasks = db.records.find({
        "labels": ["SUBTASK"],
        "where": {
            "TASK": {"$relation": {"type": "DECOMPOSES_INTO", "direction": "in"}}
        },
        "orderBy": {"order": "asc"},
    })
    
    return sub_tasks.data


def traverse_tool_composition(db, composite_tool, depth=0):
    """
    Recursively traverse the tool composition graph to show all components.
    """
    # Find all components of this composite tool
    components = db.records.find({
        "labels": ["TOOL", "COMPOSITE_TOOL"],
        "where": {
            composite_tool.label: {
                "$relation": {"type": "COMPOSED_OF", "direction": "in"}
            }
        },
    })
    
    results = []
    indent = "  " * depth
    
    for component in components.data:
        results.append({
            "depth": depth,
            "name": component["name"],
            "label": component.label,
            "is_composite": component.label == "COMPOSITE_TOOL",
        })
        
        # Recursively traverse if this is also a composite tool
        if component.label == "COMPOSITE_TOOL":
            nested = traverse_tool_composition(db, component, depth + 1)
            results.extend(nested)
    
    return results


def print_tool_composition_tree(db, composite_tool, depth=0):
    """"Print a formatted tree of tool compositions."""
    indent = "  " * depth
    prefix = "└── " if depth > 0 else ""
    marker = "[COMPOSITE]" if composite_tool.label == "COMPOSITE_TOOL" else "[PRIMITIVE]"
    
    print(f"{indent}{prefix}{composite_tool['name']} {marker}")
    
    # Find components
    components = db.records.find({
        "labels": ["TOOL", "COMPOSITE_TOOL"],
        "where": {
            composite_tool.label: {
                "$relation": {"type": "COMPOSED_OF", "direction": "in"}
            }
        },
    })
    
    for component in components.data:
        print_tool_composition_tree(db, component, depth + 1)


def main():
    """Main entry point for the tool composition graph demo."""
    print("=== Tool Composition Graph Demo ===\n")
    
    # Initialize RushDB
    print("[1] Initializing RushDB connection...")
    db = initialize_rushdb()
    print("    Connected successfully!\n")
    
    # Create primitive tools
    print("[2] Creating primitive tool capabilities...")
    primitive_tools = create_primitive_tools(db)
    print(f"    Created {len(primitive_tools)} primitive tools")
    for tool in primitive_tools:
        print(f"    - {tool['name']}: {tool['description'][:50]}...")
    print()
    
    # Create composite tools with composition relationships
    print("[3] Creating composite tools with compositions...")
    composite_tools = create_composite_tools(db, primitive_tools)
    print(f"    Created {len(composite_tools)} composite tools")
    for tool in composite_tools:
        print(f"    - {tool['name']}: {tool['description'][:50]}...")
    print()
    
    # Create agent and assign tools
    print("[4] Creating agent with tool assignments...")
    agent = create_agent(db, primitive_tools)
    print(f"    Agent: {agent['name']}")
    print(f"    Role: {agent['role']}")
    print(f"    Capabilities: {', '.join(agent['capabilities'])}")
    print()
    
    # Decompose a complex task hierarchically
    print("[5] Decomposing complex task into sub-tasks...")
    root_task, sub_tasks = decompose_task_hierarchically(db, agent, composite_tools)
    print(f"    Root Task: {root_task['title']}")
    print(f"    Decomposed into {len(sub_tasks)} sub-tasks:")
    for idx, subtask in enumerate(sub_tasks, 1):
        primitive_marker = "(primitive)" if subtask["is_primitive"] else "(composite)"
        print(f"    {idx}. {subtask['title']} {primitive_marker}")
    print()
    
    # Query the composition graph
    print("[6] Querying composition graph...")
    composites = query_composition_graph(db)
    print(f"    Found {len(composites)} composite tools in the graph")
    print()
    
    # Traverse the task hierarchy
    print("[7] Traversing task hierarchy...")
    hierarchy = query_task_hierarchy(db, root_task)
    print(f"    Found {len(hierarchy)} sub-tasks linked to root task")
    print()
    
    # Print full tool composition tree
    print("[8] Tool Composition Tree:")
    customer_portal = next(
        ct for ct in composite_tools if ct["name"] == "customer_portal"
    )
    print_tool_composition_tree(db, customer_portal)
    print()
    
    # Demonstrate recursive traversal
    print("[9] Recursive Composition Traversal:")
    traversal = traverse_tool_composition(db, customer_portal)
    for item in traversal:
        indent = "  " * item["depth"]
        label_type = "[COMPOSITE]" if item["is_composite"] else "[PRIMITIVE]"
        print(f"{indent}{item['name']} {label_type}")
    print()
    
    print("=== Demo Complete ===")
    print("\nThe tool composition graph is now persisted in RushDB.")
    print("You can query it anytime using the RushDB SDK or API.")


if __name__ == "__main__":
    main()
