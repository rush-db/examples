"""
Event source simulator for agent interaction logs.

This module simulates a streaming event source that generates
realistic agent interaction events in real-time.

In a production environment, this would be replaced by:
- WebSocket connections to agent services
- Message queue consumers (Kafka, RabbitMQ, SQS)
- HTTP webhook endpoints
- Database change data capture (CDC)
"""
import time
import random
from datetime import datetime, timedelta
from typing import Generator, List, Dict, Any
from dataclasses import asdict

from models import (
    EventType,
    SessionEvent,
    MessageEvent,
    ToolCallEvent,
    ToolResultEvent,
    Agent,
    Session,
)


# Realistic tool registry for simulation
AVAILABLE_TOOLS = [
    {"name": "web_search", "description": "Search the web for information"},
    {"name": "database_query", "description": "Query a database"},
    {"name": "file_read", "description": "Read content from a file"},
    {"name": "file_write", "description": "Write content to a file"},
    {"name": "email_send", "description": "Send an email"},
    {"name": "calendar_create", "description": "Create a calendar event"},
    {"name": "code_execute", "description": "Execute code in sandbox"},
    {"name": "image_generate", "description": "Generate an image"},
]

# Sample user messages for realistic simulation
USER_MESSAGES = [
    "Can you help me analyze this dataset?",
    "What's the weather like in Tokyo?",
    "Write a Python function to calculate fibonacci numbers",
    "Send an email to the team about the meeting",
    "Find all users who signed up this week",
    "Create a report summarizing Q4 sales",
    "Help me debug this error: stack trace attached",
    "Schedule a call with the design team for next week",
    "What are the trending topics in AI this month?",
    "Generate sample data for our test environment",
]

# Sample assistant responses
ASSISTANT_RESPONSES = [
    "Based on my analysis, here are the key findings...",
    "I'll help you with that. Let me access the necessary tools.",
    "Here's a comprehensive solution to your request.",
    "I've completed the task. Here's the summary:",
    "Let me search for the relevant information for you.",
    "I've processed your data and generated the following output:",
]


class EventSimulator:
    """
    Simulates a streaming event source for agent interactions.
    
    In production, this would connect to real event sources like
    WebSocket streams, message queues, or HTTP endpoints.
    """
    
    def __init__(
        self,
        agent_count: int = 2,
        events_per_session: tuple = (15, 30),
        tool_call_probability: float = 0.4,
    ):
        self.agent_count = agent_count
        self.events_per_session = events_per_session
        self.tool_call_probability = tool_call_probability
        
        # Create simulated agents
        self.agents = self._create_agents()
    
    def _create_agents(self) -> List[Agent]:
        """Create simulated agent configurations."""
        agents = []
        for i in range(self.agent_count):
            agents.append(Agent(
                agent_id=f"agent_{i+1:03d}",
                name=f"AI Assistant {i+1}",
                model=random.choice(["gpt-4", "claude-3", "gemini-pro"]),
                version=f"1.{random.randint(0, 5)}.{random.randint(0, 9)}",
                capabilities=random.sample(
                    [t["name"] for t in AVAILABLE_TOOLS],
                    k=random.randint(3, 6)
                )
            ))
        return agents
    
    def generate_sessions(self, count: int) -> Generator[Session, None, None]:
        """Generate session metadata records."""
        for i in range(count):
            agent = random.choice(self.agents)
            session = Session(
                session_id=f"session_{i+1:04d}",
                agent_id=agent.agent_id,
                user_id=f"user_{random.randint(1, 100):03d}",
                started_at=datetime.utcnow().isoformat(),
                ended_at=None,
                status="active"
            )
            yield session
    
    def generate_events_for_session(
        self,
        session: Session,
        agent: Agent,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Generate a realistic sequence of events for a session.
        
        Yields event data dictionaries that can be converted to
        RushDB records.
        """
        base_time = datetime.utcnow() - timedelta(minutes=random.randint(5, 60))
        
        # 1. Session start event
        yield {
            "label": "SESSION",
            "data": SessionEvent(
                event_type=EventType.SESSION_START,
                session_id=session.session_id,
                agent_id=agent.agent_id,
                user_id=session.user_id,
                metadata={"source": "web", "platform": "api"}
            ).to_rushdb_data()
        }
        
        # 2. Initial user message
        user_msg = MessageEvent(
            event_type=EventType.USER_MESSAGE,
            session_id=session.session_id,
            agent_id=agent.agent_id,
            content=random.choice(USER_MESSAGES),
            message_type="text",
            token_count=random.randint(10, 50)
        )
        yield {"label": "MESSAGE", "data": user_msg.to_rushdb_data()}
        
        # 3. Generate conversation turns
        event_count = random.randint(*self.events_per_session)
        for turn in range(event_count):
            current_time = base_time + timedelta(seconds=turn * 30)
            
            # Assistant response (possibly with tool calls)
            assistant_msg = MessageEvent(
                event_type=EventType.ASSISTANT_MESSAGE,
                session_id=session.session_id,
                agent_id=agent.agent_id,
                content=random.choice(ASSISTANT_RESPONSES),
                message_type="text",
                token_count=random.randint(50, 200)
            )
            yield {"label": "MESSAGE", "data": assistant_msg.to_rushdb_data()}
            
            # Possibly generate tool calls
            if random.random() < self.tool_call_probability:
                # Pick a tool the agent has access to
                available_for_agent = [
                    t for t in AVAILABLE_TOOLS
                    if t["name"] in agent.capabilities
                ]
                if available_for_agent:
                    tool = random.choice(available_for_agent)
                    
                    # Tool call event
                    call_id = f"call_{session.session_id}_{turn:02d}"
                    tool_call = ToolCallEvent(
                        event_type=EventType.TOOL_CALL,
                        session_id=session.session_id,
                        agent_id=agent.agent_id,
                        tool_name=tool["name"],
                        tool_args=self._generate_tool_args(tool["name"]),
                        reasoning=f"Using {tool['description']} to assist the user"
                    )
                    yield {"label": "TOOL_CALL", "data": tool_call.to_rushdb_data()}
                    
                    # Tool result (simulated async, but immediate for simplicity)
                    time.sleep(0.01)  # Simulate processing
                    tool_result = ToolResultEvent(
                        event_type=EventType.TOOL_RESULT,
                        session_id=session.session_id,
                        agent_id=agent.agent_id,
                        call_id=call_id,
                        tool_name=tool["name"],
                        status="success",
                        result_data=self._generate_tool_result(tool["name"]),
                        execution_time_ms=random.uniform(10, 500)
                    )
                    yield {"label": "TOOL_RESULT", "data": tool_result.to_rushdb_data()}
            
            # Possibly another user message
            if random.random() < 0.3 and turn < event_count - 1:
                user_followup = MessageEvent(
                    event_type=EventType.USER_MESSAGE,
                    session_id=session.session_id,
                    agent_id=agent.agent_id,
                    content=random.choice(USER_MESSAGES),
                    message_type="text",
                    token_count=random.randint(10, 50)
                )
                yield {"label": "MESSAGE", "data": user_followup.to_rushdb_data()}
        
        # 4. Session end event
        yield {
            "label": "SESSION",
            "data": SessionEvent(
                event_type=EventType.SESSION_END,
                session_id=session.session_id,
                agent_id=agent.agent_id,
                user_id=session.user_id,
                metadata={"reason": "completed", "event_count": event_count + 3}
            ).to_rushdb_data()
        }
    
    def _generate_tool_args(self, tool_name: str) -> Dict[str, Any]:
        """Generate realistic tool arguments based on tool name."""
        args_map = {
            "web_search": {"query": "AI trends 2024", "max_results": 5},
            "database_query": {"table": "users", "filter": "active=true"},
            "file_read": {"path": "/data/sample.json", "encoding": "utf-8"},
            "file_write": {"path": "/output/report.txt", "content": "Report data..."},
            "email_send": {
                "to": "team@company.com",
                "subject": "Meeting Notes",
                "body": "Discussion summary..."
            },
            "calendar_create": {
                "title": "Team Sync", "duration": 30, "attendees": ["alice", "bob"]},
            "code_execute": {"language": "python", "code": "print('Hello')"},
            "image_generate": {"prompt": "A beautiful sunset over mountains", "size": "1024x1024"},
        }
        return args_map.get(tool_name, {"info": "generic args"})
    
    def _generate_tool_result(self, tool_name: str) -> Dict[str, Any]:
        """Generate realistic tool results based on tool name."""
        results_map = {
            "web_search": {"results": ["Article 1", "Article 2", "Article 3"], "count": 3},
            "database_query": {"rows": 42, "columns": ["id", "name", "email"]},
            "file_read": {"bytes_read": 1024, "content_preview": "Sample data..."},
            "file_write": {"bytes_written": 512, "path": "/output/report.txt"},
            "email_send": {"message_id": "msg_12345", "status": "sent"},
            "calendar_create": {"event_id": "evt_67890", "status": "created"},
            "code_execute": {"output": "Hello\n", "exit_code": 0, "execution_time_ms": 50},
            "image_generate": {"image_url": "https://example.com/generated.png", "size_kb": 256},
        }
        return results_map.get(tool_name, {"status": "completed"})
    
    def stream_events(self, session_count: int) -> Generator[Dict[str, Any], None, None]:
        """
        Main entry point for streaming events.
        
        Simulates a continuous stream of events across multiple sessions.
        In production, this would be replaced with a real event source.
        """
        for session in self.generate_sessions(session_count):
            agent = next(a for a in self.agents if a.agent_id == session.agent_id)
            for event in self.generate_events_for_session(session, agent):
                yield event


class BatchEventBuffer:
    """
    Buffers events and yields them in batches for efficient RushDB writes.
    
    This reduces the number of API calls and improves throughput
    for high-volume streaming scenarios.
    """
    
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        self.buffer: List[Dict[str, Any]] = []
    
    def add(self, event: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
        """
        Add an event to the buffer.
        
        Returns completed batches when buffer reaches batch_size.
        """
        self.buffer.append(event)
        
        if len(self.buffer) >= self.batch_size:
            batches = [self.buffer]
            self.buffer = []
            return batches
        
        return []
    
    def flush(self) -> List[List[Dict[str, Any]]]:
        """Flush any remaining events as a final batch."""
        if self.buffer:
            batches = [self.buffer]
            self.buffer = []
            return batches
        return []
