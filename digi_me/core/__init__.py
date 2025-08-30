"""
Core package for Digital Clone framework.
"""

from .clone import DigitalClone
from .personality import PersonalityEngine, PersonalityTrait, CommunicationStyle, RelationshipProfile
from .context_manager import ContextManager, ConversationMessage

__all__ = [
    "DigitalClone",
    "PersonalityEngine",
    "PersonalityTrait", 
    "CommunicationStyle",
    "RelationshipProfile",
    "ContextManager",
    "ConversationMessage"
]
