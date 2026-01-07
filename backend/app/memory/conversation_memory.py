"""Conversation Memory Management System"""
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.models import Conversation, Message, User, Booking


class ConversationMemory:
    """Manages conversation history with database persistence"""
    
    def __init__(self, memory_dir: str = None):
        """
        Initialize conversation memory
        memory_dir is kept for compatibility but not used
        """
        pass
        
    def get_db(self) -> Session:
        return SessionLocal()

    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation session
        
        Args:
            user_id: Optional user identifier (Phone Number)
            
        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        db = self.get_db()
        try:
            db_user_id = None
            if user_id:
                # user_id is treated as phone_number
                user = db.query(User).filter(User.phone_number == user_id).first()
                if not user:
                    user = User(phone_number=user_id)
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                db_user_id = user.id

            new_session = Conversation(
                session_id=session_id,
                user_id=db_user_id,
                metadata_json={}
            )
            db.add(new_session)
            db.commit()
            return session_id
        finally:
            db.close()
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a conversation session
        """
        db = self.get_db()
        try:
            conversation = db.query(Conversation).filter(Conversation.session_id == session_id).first()
            if not conversation:
                return None
            
            # Format session data to match previous dictionary structure
            history = []
            for msg in conversation.messages:
                history.append({
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                })
            
            user_phone = None
            if conversation.user:
                user_phone = conversation.user.phone_number

            return {
                "session_id": conversation.session_id,
                "user_id": user_phone,
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
                "conversation_history": history,
                "metadata": conversation.metadata_json or {}
            }
        finally:
            db.close()
    
    def add_message(self, session_id: str, role: str, content: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to the conversation history
        """
        db = self.get_db()
        try:
            conversation = db.query(Conversation).filter(Conversation.session_id == session_id).first()
            if not conversation:
                return False
            
            new_message = Message(
                conversation_id=conversation.id,
                role=role,
                content=content
            )
            db.add(new_message)
            
            # Update conversation timestamp
            conversation.updated_at = func.now()
            
            db.commit()
            return True
        except Exception as e:
            print(f"Error adding message: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def get_conversation_history(self, session_id: str, 
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session
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
        """
        history = self.get_conversation_history(session_id, limit)
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history
        ]
    
    def update_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update session metadata
        """
        db = self.get_db()
        try:
            conversation = db.query(Conversation).filter(Conversation.session_id == session_id).first()
            if not conversation:
                return False
            
            current_metadata = conversation.metadata_json or {}
            current_metadata.update(metadata)
            conversation.metadata_json = current_metadata
            
            db.commit()
            return True
        finally:
            db.close()
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all conversation sessions
        user_id is treated as phone_number
        """
        db = self.get_db()
        try:
            query = db.query(Conversation)
            if user_id:
                query = query.join(User).filter(User.phone_number == user_id)
            
            conversations = query.order_by(Conversation.updated_at.desc()).all()
            
            sessions = []
            for conv in conversations:
                user_phone = conv.user.phone_number if conv.user else None
                sessions.append({
                    "session_id": conv.session_id,
                    "user_id": user_phone,
                    "created_at": conv.created_at.isoformat() if conv.created_at else None,
                    "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
                    "message_count": len(conv.messages),
                    "metadata": conv.metadata_json or {}
                })
            return sessions
        finally:
            db.close()
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a conversation session
        """
        db = self.get_db()
        try:
            conversation = db.query(Conversation).filter(Conversation.session_id == session_id).first()
            if not conversation:
                return False
            
            db.delete(conversation)
            db.commit()
            return True
        finally:
            db.close()
    
    def clear_history(self, session_id: str) -> bool:
        """
        Clear conversation history but keep session
        """
        db = self.get_db()
        try:
            conversation = db.query(Conversation).filter(Conversation.session_id == session_id).first()
            if not conversation:
                return False
            
            # Delete all messages
            db.query(Message).filter(Message.conversation_id == conversation.id).delete()
            db.commit()
            return True
        finally:
            db.close()
            
    # Helper to access DB if needed directly
    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        db = self.get_db()
        try:
            return db.query(User).filter(User.phone_number == phone_number).first()
        finally:
            db.close()

from sqlalchemy import func

