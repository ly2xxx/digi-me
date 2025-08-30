"""
Base LLM Provider Class
======================

Abstract base class for all LLM providers.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM implementations (Ollama, OpenAI, etc.) should inherit from this class.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the LLM provider base."""
        self.name = name
        self.config = config
        self.is_available = False
        
        logger.info(f"LLM Provider base initialized: {name}")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the LLM provider.
        
        Returns:
            True if initialization was successful
        """
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup provider resources."""
        pass
    
    @abstractmethod
    async def generate_response(self, prompt_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate a response using the LLM.
        
        Args:
            prompt_data: Dictionary containing message context and personality information
            
        Returns:
            Generated response string or None if generation failed
        """
        pass
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            'name': self.name,
            'is_available': self.is_available,
            'config': self.config
        }
