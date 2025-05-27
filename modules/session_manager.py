"""
Session management module.
Handles session state and manages conversational chains per user.
"""

import uuid
from typing import Dict, Optional, Tuple, List, Any
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage


class SessionManager:
    """Manages user sessions and their associated conversational chains."""
    
    def __init__(self, session_timeout_hours: int = 24):
        """
        Initialize session manager.
        
        Args:
            session_timeout_hours: Hours after which inactive sessions expire
        """
        self.sessions: Dict[str, dict] = {}
        self.session_timeout = timedelta(hours=session_timeout_hours)
    
    def create_session(self, chain: Any, 
                      retriever: Any, 
                      chat_history: List,
                      article_title: str) -> str:
        """
        Create a new session with a conversational chain.
        
        Args:
            chain: Retrieval chain for this session
            retriever: History-aware retriever for this session
            chat_history: Chat history list for this session
            article_title: Title of the Wikipedia article
            
        Returns:
            str: Unique session ID
        """
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            'chain': chain,
            'retriever': retriever,
            'chat_history': chat_history,
            'article_title': article_title,
            'created_at': datetime.now(),
            'last_accessed': datetime.now(),
            'message_count': 0,
            'question_topics': []  # Track topics of questions asked
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session data by ID.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            dict or None: Session data if found and not expired
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session has expired
        if datetime.now() - session['last_accessed'] > self.session_timeout:
            self.delete_session(session_id)
            return None
        
        # Update last accessed time
        session['last_accessed'] = datetime.now()
        return session
    
    def get_chain_and_history(self, session_id: str) -> Optional[Tuple[Any, List]]:
        """
        Get chain and chat history for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            tuple or None: (chain, chat_history) if session exists
        """
        session = self.get_session(session_id)
        if session:
            return session['chain'], session['chat_history']
        return None
    
    def add_message_to_history(self, session_id: str, human_message: str, ai_message: str) -> None:
        """
        Add messages to the chat history.
        
        Args:
            session_id: Session ID
            human_message: Human message to add
            ai_message: AI response to add
        """
        if session_id in self.sessions:
            chat_history = self.sessions[session_id]['chat_history']
            chat_history.extend([
                HumanMessage(content=human_message),
                AIMessage(content=ai_message)
            ])
            
            # Track question topic for diversity
            self._track_question_topic(session_id, human_message)
    
    def _track_question_topic(self, session_id: str, question: str) -> None:
        """
        Track the topic/theme of questions to help identify repetitive queries.
        
        Args:
            session_id: Session ID
            question: User's question
        """
        if session_id in self.sessions:
            # Simple keyword-based topic detection
            question_lower = question.lower()
            topic_keywords = {
                'color': ['color', 'colour', 'colored', 'coloured', 'hue', 'shade'],
                'appearance': ['look', 'appearance', 'shape', 'form', 'size'],
                'description': ['describe', 'tell me about', 'what is', 'explain'],
                'summary': ['summarize', 'summary', 'main points', 'overview'],
                'cultivation': ['grow', 'plant', 'cultivation', 'garden', 'care'],
                'habitat': ['where', 'native', 'habitat', 'location', 'found'],
                'uses': ['use', 'purpose', 'benefit', 'application', 'medicine']
            }
            
            detected_topics = []
            for topic, keywords in topic_keywords.items():
                if any(keyword in question_lower for keyword in keywords):
                    detected_topics.append(topic)
            
            if not detected_topics:
                detected_topics = ['general']
            
            self.sessions[session_id]['question_topics'].extend(detected_topics)
    
    def get_recent_topics(self, session_id: str, last_n: int = 3) -> List[str]:
        """
        Get recently asked question topics.
        
        Args:
            session_id: Session ID
            last_n: Number of recent topics to return
            
        Returns:
            List of recent topics
        """
        if session_id in self.sessions:
            topics = self.sessions[session_id]['question_topics']
            return topics[-last_n:] if topics else []
        return []
    
    def increment_message_count(self, session_id: str) -> None:
        """
        Increment message count for a session.
        
        Args:
            session_id: Session ID
        """
        if session_id in self.sessions:
            self.sessions[session_id]['message_count'] += 1
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            bool: True if session was deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions.
        
        Returns:
            int: Number of sessions cleaned up
        """
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if current_time - session['last_accessed'] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        return len(expired_sessions)
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        Get session information without updating access time.
        
        Args:
            session_id: Session ID
            
        Returns:
            dict or None: Session information
        """
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return {
            'session_id': session_id,
            'article_title': session['article_title'],
            'created_at': session['created_at'].isoformat(),
            'last_accessed': session['last_accessed'].isoformat(),
            'message_count': session['message_count'],
            'is_expired': datetime.now() - session['last_accessed'] > self.session_timeout
        }
    
    def list_active_sessions(self) -> list[dict]:
        """
        Get list of all active (non-expired) sessions.
        
        Returns:
            list[dict]: List of session information
        """
        active_sessions = []
        current_time = datetime.now()
        
        for session_id, session in self.sessions.items():
            if current_time - session['last_accessed'] <= self.session_timeout:
                active_sessions.append(self.get_session_info(session_id))
        
        return active_sessions
    
    def get_stats(self) -> dict:
        """
        Get session manager statistics.
        
        Returns:
            dict: Statistics about sessions
        """
        current_time = datetime.now()
        active_count = 0
        expired_count = 0
        total_messages = 0
        
        for session in self.sessions.values():
            if current_time - session['last_accessed'] <= self.session_timeout:
                active_count += 1
            else:
                expired_count += 1
            total_messages += session['message_count']
        
        return {
            'total_sessions': len(self.sessions),
            'active_sessions': active_count,
            'expired_sessions': expired_count,
            'total_messages': total_messages,
            'session_timeout_hours': self.session_timeout.total_seconds() / 3600
        } 