# backend/utils/session.py
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class SessionManager:
    """Manages active game sessions"""
    
    # Singleton instance
    _instance = None
    
    # Session storage
    _sessions: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance
    
    def get_session(self, session_id: str) -> Optional[Any]:
        """Get session by ID"""
        if session_id not in self._sessions:
            return None
        
        # Update last access time
        self._sessions[session_id]["last_access"] = datetime.now()
        
        return self._sessions[session_id]["data"]
    
    def create_session(self, session_id: str, data: Any) -> None:
        """Create a new session"""
        self._sessions[session_id] = {
            "data": data,
            "created_at": datetime.now(),
            "last_access": datetime.now()
        }
    
    def update_session(self, session_id: str, data: Any) -> None:
        """Update an existing session"""
        if session_id not in self._sessions:
            raise ValueError(f"Session {session_id} not found")
        
        self._sessions[session_id]["data"] = data
        self._sessions[session_id]["last_access"] = datetime.now()
    
    def delete_session(self, session_id: str) -> None:
        """Delete a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def cleanup_sessions(self, timeout_minutes: int = 30) -> None:
        """Clean up expired sessions"""
        now = datetime.now()
        timeout = timedelta(minutes=timeout_minutes)
        
        expired_sessions = [
            session_id for session_id, session_data in self._sessions.items()
            if now - session_data["last_access"] > timeout
        ]
        
        for session_id in expired_sessions:
            del self._sessions[session_id]