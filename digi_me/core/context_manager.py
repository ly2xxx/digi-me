"""
Context Manager
==============

Manages conversation history and context for the digital clone.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class ConversationMessage:
    """Represents a single message in a conversation."""
    
    def __init__(self, content: str, role: str, timestamp: Optional[datetime] = None):
        self.content = content
        self.role = role  # 'user' or 'assistant'
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            'content': self.content,
            'role': self.role,
            'timestamp': self.timestamp.isoformat()
        }


class ContextManager:
    """
    Manages conversation context and history across all platforms and contacts.
    
    This class handles:
    - Conversation history storage and retrieval
    - Context-aware message threading
    - Memory management with limits
    - Cross-platform context correlation
    """
    
    def __init__(self, max_messages_per_conversation: int = 100, context_window_days: int = 30):
        """Initialize the context manager."""
        self.max_messages_per_conversation = max_messages_per_conversation
        self.context_window_days = context_window_days
        
        # Storage for conversation histories
        # Key format: "platform:contact_identifier"
        self.conversations: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.max_messages_per_conversation)
        )
        
        # Metadata about conversations
        self.conversation_metadata: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        logger.info("Context Manager initialized")
    
    def add_message(self, conversation_key: str, content: str, role: str, timestamp: Optional[datetime] = None):
        """
        Add a message to a conversation.
        
        Args:
            conversation_key: Unique identifier for the conversation (platform:contact)
            content: Message content
            role: 'user' or 'assistant'
            timestamp: Message timestamp (defaults to now)
        """
        message = ConversationMessage(content, role, timestamp)
        self.conversations[conversation_key].append(message)
        
        # Update metadata
        metadata = self.conversation_metadata[conversation_key]
        metadata['last_activity'] = message.timestamp
        metadata['message_count'] = len(self.conversations[conversation_key])
        
        if 'first_message' not in metadata:
            metadata['first_message'] = message.timestamp
        
        logger.debug(f"Added message to {conversation_key}: {content[:50]}...")
    
    def get_conversation_history(self, conversation_key: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history for a specific conversation.
        
        Args:
            conversation_key: Unique identifier for the conversation
            limit: Maximum number of messages to return (most recent first)
            
        Returns:
            List of message dictionaries
        """
        messages = list(self.conversations[conversation_key])
        
        # Filter by time window
        cutoff_date = datetime.now() - timedelta(days=self.context_window_days)
        messages = [msg for msg in messages if msg.timestamp >= cutoff_date]
        
        # Apply limit
        if limit and len(messages) > limit:
            messages = messages[-limit:]
        
        return [msg.to_dict() for msg in messages]
    
    def get_recent_context(self, conversation_key: str, max_messages: int = 10) -> str:
        """
        Get recent conversation context as a formatted string.
        
        Args:
            conversation_key: Unique identifier for the conversation
            max_messages: Maximum number of recent messages to include
            
        Returns:
            Formatted conversation context string
        """
        messages = self.get_conversation_history(conversation_key, limit=max_messages)
        
        if not messages:
            return "No previous conversation history."
        
        context_lines = []
        for msg in messages:
            role_label = "You" if msg['role'] == 'assistant' else "Them"
            timestamp = datetime.fromisoformat(msg['timestamp']).strftime("%H:%M")
            context_lines.append(f"[{timestamp}] {role_label}: {msg['content']}")
        
        return "\n".join(context_lines)
    
    def get_conversation_summary(self, conversation_key: str) -> Dict[str, Any]:
        """
        Get a summary of a conversation.
        
        Args:
            conversation_key: Unique identifier for the conversation
            
        Returns:
            Dictionary containing conversation summary
        """
        metadata = self.conversation_metadata.get(conversation_key, {})
        messages = list(self.conversations[conversation_key])
        
        if not messages:
            return {
                'message_count': 0,
                'first_message': None,
                'last_activity': None,
                'days_active': 0
            }
        
        first_message = messages[0].timestamp
        last_activity = messages[-1].timestamp
        days_active = (last_activity - first_message).days + 1
        
        return {
            'message_count': len(messages),
            'first_message': first_message.isoformat(),
            'last_activity': last_activity.isoformat(),
            'days_active': days_active,
            'recent_activity': len([m for m in messages if m.timestamp >= datetime.now() - timedelta(days=7)])
        }
    
    def cleanup_old_conversations(self):
        """Clean up conversations outside the context window."""
        cutoff_date = datetime.now() - timedelta(days=self.context_window_days)
        conversations_to_clean = []
        
        for conversation_key in self.conversations:
            metadata = self.conversation_metadata.get(conversation_key, {})
            last_activity = metadata.get('last_activity')
            
            if last_activity and last_activity < cutoff_date:
                conversations_to_clean.append(conversation_key)
        
        for conversation_key in conversations_to_clean:
            del self.conversations[conversation_key]
            del self.conversation_metadata[conversation_key]
            logger.info(f"Cleaned up old conversation: {conversation_key}")
        
        if conversations_to_clean:
            logger.info(f"Cleaned up {len(conversations_to_clean)} old conversations")
    
    def get_active_conversations(self, days: int = 7) -> List[str]:
        """
        Get list of conversations with activity in the last N days.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of conversation keys
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        active_conversations = []
        
        for conversation_key, metadata in self.conversation_metadata.items():
            last_activity = metadata.get('last_activity')
            if last_activity and last_activity >= cutoff_date:
                active_conversations.append(conversation_key)
        
        return active_conversations
    
    def search_conversations(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for messages containing specific text.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching messages with context
        """
        query_lower = query.lower()
        results = []
        
        for conversation_key, messages in self.conversations.items():
            for message in messages:
                if query_lower in message.content.lower():
                    results.append({
                        'conversation_key': conversation_key,
                        'message': message.to_dict(),
                        'context': self.get_recent_context(conversation_key, 3)
                    })
                    
                    if len(results) >= limit:
                        break
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about the context manager."""
        total_conversations = len(self.conversations)
        total_messages = sum(len(messages) for messages in self.conversations.values())
        active_conversations = len(self.get_active_conversations())
        
        return {
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'active_conversations_7d': active_conversations,
            'avg_messages_per_conversation': total_messages / total_conversations if total_conversations > 0 else 0,
            'context_window_days': self.context_window_days,
            'max_messages_per_conversation': self.max_messages_per_conversation
        }
