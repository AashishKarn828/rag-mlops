"""
Session memory service for managing conversation history
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

class Message:
    """Represents a single message in conversation"""
    def __init__(self, role: str, content: str, timestamp: datetime = None):
        self.role = role  # 'user' or 'assistant'
        self.content = content
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
    
    def __repr__(self):
        return f"Message(role={self.role}, content={self.content[:50]}...)"


class ConversationSession:
    """Manages a single conversation session"""
    def __init__(self, session_id: str, max_history: int = 10):
        self.session_id = session_id
        self.messages: List[Message] = []
        self.max_history = max_history
        self.created_at = datetime.now()
        self.last_access = datetime.now()
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation"""
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.last_access = datetime.now()
        
        # Keep only last N messages to prevent memory bloat
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
        
        logger.debug(f"Session {self.session_id}: Added {role} message. Total: {len(self.messages)}")
    
    def get_history(self, last_n: Optional[int] = None) -> List[Message]:
        """Get conversation history"""
        if last_n is None:
            return self.messages
        return self.messages[-last_n:]
    
    def get_history_text(self, last_n: Optional[int] = None) -> str:
        """Get conversation history as formatted text"""
        messages = self.get_history(last_n)
        history_text = []
        for msg in messages:
            history_text.append(f"{msg.role.capitalize()}: {msg.content}")
        return "\n".join(history_text)
    
    def clear(self):
        """Clear conversation history"""
        self.messages = []
        logger.info(f"Session {self.session_id}: Cleared conversation history")
    
    def to_dict(self) -> Dict:
        """Convert session to dictionary"""
        return {
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at.isoformat(),
            "last_access": self.last_access.isoformat(),
            "message_count": len(self.messages)
        }


class SessionMemoryService:
    """Service for managing multiple conversation sessions"""
    
    def __init__(self, max_history_per_session: int = 10, session_timeout_hours: int = 24):
        self.sessions: Dict[str, ConversationSession] = {}
        self.max_history_per_session = max_history_per_session
        self.session_timeout = timedelta(hours=session_timeout_hours)
        logger.info(f"SessionMemoryService initialized (max_history={max_history_per_session}, timeout={session_timeout_hours}h)")
    
    def create_session(self) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        session = ConversationSession(
            session_id=session_id,
            max_history=self.max_history_per_session
        )
        self.sessions[session_id] = session
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def get_session(self, session_id: Optional[str] = None) -> ConversationSession:
        """Get or create a session"""
        if session_id is None or session_id not in self.sessions:
            # Create new session if none exists
            new_session_id = self.create_session()
            return self.sessions[new_session_id]
        
        session = self.sessions[session_id]
        
        # Check if session expired
        if datetime.now() - session.last_access > self.session_timeout:
            logger.info(f"Session {session_id} expired, creating new one")
            session.clear()
        
        return session
    
    def add_message(self, session_id: Optional[str], role: str, content: str) -> str:
        """
        Add a message to a session
        Returns the session_id (creates new session if needed)
        """
        session = self.get_session(session_id)
        session.add_message(role, content)
        return session.session_id
    
    def get_conversation_history(
        self, 
        session_id: Optional[str], 
        last_n: Optional[int] = None
    ) -> List[Message]:
        """Get conversation history for a session"""
        if session_id is None or session_id not in self.sessions:
            return []
        
        session = self.sessions[session_id]
        return session.get_history(last_n)
    
    def get_conversation_context(
        self, 
        session_id: Optional[str],
        last_n: Optional[int] = 5
    ) -> str:
        """
        Get conversation history as formatted context for LLM
        Returns last N messages as text
        """
        messages = self.get_conversation_history(session_id, last_n)
        if not messages:
            return ""
        
        context_parts = ["Previous conversation:"]
        for msg in messages:
            context_parts.append(f"{msg.role.capitalize()}: {msg.content}")
        
        return "\n".join(context_parts)
    
    def clear_session(self, session_id: str):
        """Clear a specific session"""
        if session_id in self.sessions:
            self.sessions[session_id].clear()
            logger.info(f"Cleared session: {session_id}")
    
    def delete_session(self, session_id: str):
        """Delete a session completely"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions to free memory"""
        now = datetime.now()
        expired = []
        
        for session_id, session in self.sessions.items():
            if now - session.last_access > self.session_timeout:
                expired.append(session_id)
        
        for session_id in expired:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        
        return len(expired)
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a session"""
        if session_id not in self.sessions:
            return None
        return self.sessions[session_id].to_dict()


# Global instance
session_memory_service = SessionMemoryService(
    max_history_per_session=10,  # Keep last 10 messages
    session_timeout_hours=24      # Sessions expire after 24 hours
)
