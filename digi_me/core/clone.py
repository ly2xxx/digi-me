"""
Core Digital Clone Implementation
================================

Main class that orchestrates the digital clone functionality across platforms.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from ..config.settings import Settings
from ..core.personality import PersonalityEngine
from ..core.context_manager import ContextManager
from ..llm.base import LLMProvider
from ..platforms.base import PlatformBase
from ..plugins.base import PluginBase


logger = logging.getLogger(__name__)


class DigitalClone:
    """
    Main Digital Clone class that coordinates all components.
    
    This class serves as the central orchestrator for the digital clone,
    managing personality, platforms, LLM providers, and plugins.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the Digital Clone with configuration."""
        self.settings = Settings(config_path)
        self.personality_engine = PersonalityEngine(self.settings.personality)
        self.context_manager = ContextManager()
        
        # Initialize components
        self.llm_provider: Optional[LLMProvider] = None
        self.platforms: Dict[str, PlatformBase] = {}
        self.plugins: Dict[str, PluginBase] = {}
        
        # State management
        self.is_running = False
        self.active_conversations: Dict[str, Any] = {}
        
        logger.info("Digital Clone initialized")
    
    def set_llm_provider(self, provider: LLMProvider):
        """Set the LLM provider for response generation."""
        self.llm_provider = provider
        logger.info(f"LLM Provider set: {provider.__class__.__name__}")
    
    def add_platform(self, name: str, platform: PlatformBase):
        """Add a communication platform (WhatsApp, Teams, etc.)."""
        self.platforms[name] = platform
        platform.set_clone_reference(self)
        logger.info(f"Platform added: {name}")
    
    def add_plugin(self, name: str, plugin: PluginBase):
        """Add a plugin for extended functionality."""
        self.plugins[name] = plugin
        plugin.initialize(self)
        logger.info(f"Plugin added: {name}")
    
    async def start(self):
        """Start the digital clone and all platforms."""
        if self.is_running:
            logger.warning("Digital Clone is already running")
            return
        
        if not self.llm_provider:
            raise ValueError("LLM Provider must be set before starting")
        
        logger.info("Starting Digital Clone...")
        self.is_running = True
        
        # Start all platforms
        tasks = []
        for name, platform in self.platforms.items():
            logger.info(f"Starting platform: {name}")
            tasks.append(asyncio.create_task(platform.start()))
        
        # Wait for all platforms to start
        if tasks:
            await asyncio.gather(*tasks)
        
        logger.info("Digital Clone started successfully")
    
    async def stop(self):
        """Stop the digital clone and all platforms."""
        if not self.is_running:
            return
        
        logger.info("Stopping Digital Clone...")
        self.is_running = False
        
        # Stop all platforms
        tasks = []
        for name, platform in self.platforms.items():
            logger.info(f"Stopping platform: {name}")
            tasks.append(asyncio.create_task(platform.stop()))
        
        if tasks:
            await asyncio.gather(*tasks)
        
        logger.info("Digital Clone stopped")
    
    async def process_message(self, platform_name: str, message_data: Dict[str, Any]) -> Optional[str]:
        """
        Process an incoming message and generate a response.
        
        Args:
            platform_name: Name of the platform the message came from
            message_data: Message data including sender, content, context
            
        Returns:
            Generated response or None if no response needed
        """
        if not self.is_running:
            return None
        
        try:
            # Extract message components
            sender = message_data.get('sender', 'unknown')
            content = message_data.get('content', '')
            context = message_data.get('context', {})
            
            logger.info(f"Processing message from {sender} on {platform_name}")
            
            # Update context
            conversation_key = f"{platform_name}:{sender}"
            self.context_manager.add_message(conversation_key, content, 'user')
            
            # Check if we should respond
            if not await self._should_respond(platform_name, message_data):
                return None
            
            # Generate personality-aware response
            personality_context = self.personality_engine.get_context_for_sender(sender)
            conversation_history = self.context_manager.get_conversation_history(conversation_key)
            
            # Prepare LLM prompt
            prompt_data = {
                'sender': sender,
                'content': content,
                'context': context,
                'personality': personality_context,
                'conversation_history': conversation_history,
                'platform': platform_name
            }
            
            # Generate response using LLM
            response = await self.llm_provider.generate_response(prompt_data)
            
            if response:
                # Update context with our response
                self.context_manager.add_message(conversation_key, response, 'assistant')
                logger.info(f"Generated response for {sender}")
                
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None
    
    async def _should_respond(self, platform_name: str, message_data: Dict[str, Any]) -> bool:
        """
        Determine if the clone should respond to this message.
        
        This can be customized based on various factors:
        - Sender relationship
        - Message content
        - Platform-specific rules
        - Time-based rules
        - Personality settings
        """
        # Basic implementation - can be extended
        sender = message_data.get('sender', '')
        content = message_data.get('content', '').lower()
        
        # Check if sender is in ignore list
        if sender in self.settings.ignore_senders:
            return False
        
        # Check if message contains trigger words
        if any(word in content for word in self.settings.response_triggers):
            return True
        
        # Check personality-based response probability
        return self.personality_engine.should_respond(message_data)
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the digital clone."""
        return {
            'is_running': self.is_running,
            'platforms': list(self.platforms.keys()),
            'plugins': list(self.plugins.keys()),
            'active_conversations': len(self.active_conversations),
            'llm_provider': self.llm_provider.__class__.__name__ if self.llm_provider else None
        }
