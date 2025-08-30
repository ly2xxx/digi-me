"""
Base Platform Class
==================

Abstract base class for all platform integrations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class PlatformBase(ABC):
    """
    Abstract base class for platform integrations.
    
    All platform implementations (WhatsApp, Teams, Outlook, etc.) 
    should inherit from this class.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize the platform base."""
        self.name = name
        self.config = config
        self.is_active = False
        self.clone_reference = None  # Will be set by the DigitalClone
        
        logger.info(f"Platform base initialized: {name}")
    
    def set_clone_reference(self, clone):
        """Set reference to the main DigitalClone instance."""
        self.clone_reference = clone
    
    @abstractmethod
    async def start(self):
        """Start the platform integration."""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the platform integration."""
        pass
    
    @abstractmethod
    async def send_message(self, recipient: str, message: str) -> bool:
        """
        Send a message through this platform.
        
        Args:
            recipient: The recipient identifier
            message: Message content to send
            
        Returns:
            True if message was sent successfully
        """
        pass
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information."""
        return {
            'name': self.name,
            'is_active': self.is_active,
            'config': self.config
        }
