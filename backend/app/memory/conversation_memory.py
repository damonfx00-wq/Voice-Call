"""Conversation Memory Management System"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid


class ConversationMemory:
    """Manages conversation history with persistence"""
    
    def __init__(self, memory_dir: str = "./data/conversations"):
        """
        Initialize conversation memory
        
        Args:
            memory_dir: Directory to store conversation files
        """
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)
        
    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation session
        
        Args:
            user_id: Optional user identifier
            
        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "conversation_history": [],
            "metadata": {}
        }
        
        self._save_session(session_id, session_data)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a conversation session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
        """
        filepath = self._get_session_filepath(session_id)
        if not os.path.exists(filepath):
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None
    
    def add_message(self, session_id: str, role: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to the conversation history
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata for the message
            
        Returns:
            Success status
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            message["metadata"] = metadata
        
        session_data["conversation_history"].append(message)
        session_data["updated_at"] = datetime.now().isoformat()
        
        self._save_session(session_id, session_data)
        return True
    
    def get_conversation_history(self, session_id: str, 
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages to return (most recent)
            
        Returns:
            List of messages
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return []
        
        history = session_data.get("conversation_history", [])
        
        if limit and limit > 0:
            return history[-limit:]
        
        return history
    
    def get_formatted_history(self, session_id: str, 
                            limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for LLM API
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of messages in LLM format (role, content)
        """
        history = self.get_conversation_history(session_id, limit)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]
    
    def update_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update session metadata
        
        Args:
            session_id: Session identifier
            metadata: Metadata to update
            
        Returns:
            Success status
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        session_data["metadata"].update(metadata)
        session_data["updated_at"] = datetime.now().isoformat()
        
        self._save_session(session_id, session_data)
        return True
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all conversation sessions
        
        Args:
            user_id: Optional filter by user_id
            
        Returns:
            List of session summaries
        """
        sessions = []
        
        for filename in os.listdir(self.memory_dir):
            if filename.endswith('.json'):
                session_id = filename[:-5]  # Remove .json extension
                session_data = self.get_session(session_id)
                
                if session_data:
                    # Filter by user_id if provided
                    if user_id and session_data.get("user_id") != user_id:
                        continue
                    
                    # Create summary
                    summary = {
                        "session_id": session_data["session_id"],
                        "user_id": session_data.get("user_id"),
                        "created_at": session_data["created_at"],
                        "updated_at": session_data["updated_at"],
                        "message_count": len(session_data.get("conversation_history", [])),
                        "metadata": session_data.get("metadata", {})
                    }
                    sessions.append(summary)
        
        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Success status
        """
        filepath = self._get_session_filepath(session_id)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print(f"Error deleting session {session_id}: {e}")
                return False
        return False
    
    def clear_history(self, session_id: str) -> bool:
        """
        Clear conversation history but keep session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Success status
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        session_data["conversation_history"] = []
        session_data["updated_at"] = datetime.now().isoformat()
        
        self._save_session(session_id, session_data)
        return True
    
    def _get_session_filepath(self, session_id: str) -> str:
        """Get filepath for a session"""
        return os.path.join(self.memory_dir, f"{session_id}.json")
    
    def _save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Save session data to file"""
        filepath = self._get_session_filepath(session_id)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")
            raise
