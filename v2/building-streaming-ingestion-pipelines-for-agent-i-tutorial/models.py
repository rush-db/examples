"""
Data models for agent interaction events.

These Pydantic-style classes define the structure of events
that flow through the streaming pipeline.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import uuid


class EventType(str, Enum):
    """Supported event types in the agent interaction log."""
    USER_MESSAGE = "user_message"
    ASSISTANT_MESSAGE = "assistant_message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


@dataclass
class BaseEvent:
    """Base class for all agent interaction events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    session_id: str = ""
    agent_id: str = ""
    
    def to_rushdb_data(self) -> Dict[str, Any]:
        """Convert event to RushDB record format."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            **self._get_event_data()
        }
    
    def _get_event_data(self) -> Dict[str, Any]:
        """Override in subclasses to add event-specific data."""
        return {}


@dataclass
class SessionEvent(BaseEvent):
    """Session lifecycle events (start/end)."""
    event_type: EventType = EventType.SESSION_START
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "user_id": self.user_id,
            "metadata": self.metadata
        }


@dataclass
class MessageEvent(BaseEvent):
    """User or assistant message events."""
    event_type: EventType = EventType.USER_MESSAGE
    content: str = ""
    message_type: str = ""  # e.g., "text", "code", "system"
    token_count: Optional[int] = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "content": self.content,
            "message_type": self.message_type,
            "token_count": self.token_count
        }


@dataclass
class ToolCallEvent(BaseEvent):
    """Agent tool invocation events."""
    event_type: EventType = EventType.TOOL_CALL
    tool_name: str = ""
    tool_args: Dict[str, Any] = field(default_factory=dict)
    reasoning: Optional[str] = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "reasoning": self.reasoning
        }


@dataclass
class ToolResultEvent(BaseEvent):
    """Tool execution result events."""
    event_type: EventType = EventType.TOOL_RESULT
    call_id: str = ""  # Links to the ToolCallEvent
    tool_name: str = ""
    status: str = "success"  # success, error, timeout
    result_data: Any = None
    execution_time_ms: Optional[float] = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "type": self.event_type.value,
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "status": self.status,
            "result_data": self.result_data,
            "execution_time_ms": self.execution_time_ms
        }


@dataclass
class Agent:
    """Agent configuration/metadata record."""
    agent_id: str
    name: str
    model: str
    version: str
    capabilities: List[str] = field(default_factory=list)
    
    def to_rushdb_data(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "model": self.model,
            "version": self.version,
            "capabilities": self.capabilities
        }


@dataclass
class Session:
    """Session metadata record."""
    session_id: str
    agent_id: str
    user_id: str
    started_at: str
    ended_at: Optional[str] = None
    status: str = "active"
    
    def to_rushdb_data(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "status": self.status
        }
