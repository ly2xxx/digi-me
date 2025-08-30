"""
Personality Engine
==================

Manages personality traits, communication patterns, and behavioral consistency
to ensure the digital clone responds authentically as the person would.
"""

import random
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, time

logger = logging.getLogger(__name__)


@dataclass
class PersonalityTrait:
    """Represents a single personality trait with weight and context."""
    name: str
    weight: float  # 0.0 to 1.0
    description: str
    examples: List[str]
    active_contexts: List[str]  # When this trait is most active


@dataclass
class CommunicationStyle:
    """Defines communication preferences and patterns."""
    formality_level: float  # 0.0 (casual) to 1.0 (very formal)
    response_length: str  # 'short', 'medium', 'long'
    emoji_usage: float  # 0.0 (never) to 1.0 (frequently)
    humor_level: float  # 0.0 (serious) to 1.0 (very humorous)
    technical_depth: float  # 0.0 (simple) to 1.0 (very technical)


@dataclass
class RelationshipProfile:
    """Stores relationship-specific personality adjustments."""
    contact_identifier: str
    relationship_type: str  # 'family', 'friend', 'colleague', 'professional'
    closeness_level: float  # 0.0 (distant) to 1.0 (very close)
    communication_style_override: Optional[CommunicationStyle]
    personality_adjustments: Dict[str, float]  # trait_name -> adjustment
    last_interaction: Optional[datetime]
    interaction_frequency: int  # interactions per month
    notes: str


class PersonalityEngine:
    """
    Core personality management system for the digital clone.
    
    This engine maintains personality consistency across all interactions
    while allowing for natural variation and context-appropriate responses.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the personality engine with configuration."""
        self.config = config
        
        # Core personality traits
        self.traits: Dict[str, PersonalityTrait] = {}
        self.base_communication_style = CommunicationStyle(
            formality_level=config.get('formality_level', 0.5),
            response_length=config.get('response_length', 'medium'),
            emoji_usage=config.get('emoji_usage', 0.3),
            humor_level=config.get('humor_level', 0.4),
            technical_depth=config.get('technical_depth', 0.6)
        )
        
        # Relationship management
        self.relationships: Dict[str, RelationshipProfile] = {}
        
        # Response patterns
        self.response_probability = config.get('response_probability', 0.8)
        self.active_hours = {
            'start': time(8, 0),  # 8 AM
            'end': time(22, 0)    # 10 PM
        }
        
        # Initialize default personality traits
        self._initialize_default_traits()
        
        logger.info("Personality Engine initialized")
    
    def _initialize_default_traits(self):
        """Initialize default personality traits."""
        default_traits = [
            PersonalityTrait(
                name="helpfulness",
                weight=0.8,
                description="Tendency to help others and provide useful information",
                examples=["Let me help you with that", "Here's what I would suggest"],
                active_contexts=["work", "professional", "support"]
            ),
            PersonalityTrait(
                name="analytical",
                weight=0.7,
                description="Tendency to analyze problems systematically",
                examples=["Let me break this down", "There are several factors to consider"],
                active_contexts=["problem_solving", "technical", "planning"]
            ),
            PersonalityTrait(
                name="friendliness",
                weight=0.6,
                description="Warm and approachable communication style",
                examples=["Hope you're doing well!", "Thanks for reaching out"],
                active_contexts=["casual", "social", "greeting"]
            ),
            PersonalityTrait(
                name="decisiveness",
                weight=0.5,
                description="Ability to make clear decisions and recommendations",
                examples=["I'd go with option A", "My recommendation would be"],
                active_contexts=["decision_making", "leadership", "advice"]
            )
        ]
        
        for trait in default_traits:
            self.traits[trait.name] = trait
    
    def add_trait(self, trait: PersonalityTrait):
        """Add or update a personality trait."""
        self.traits[trait.name] = trait
        logger.info(f"Added/updated personality trait: {trait.name}")
    
    def add_relationship(self, profile: RelationshipProfile):
        """Add or update a relationship profile."""
        self.relationships[profile.contact_identifier] = profile
        logger.info(f"Added/updated relationship profile for: {profile.contact_identifier}")
    
    def get_context_for_sender(self, sender: str) -> Dict[str, Any]:
        """
        Get personality context tailored for a specific sender.
        
        Args:
            sender: The person we're responding to
            
        Returns:
            Dictionary containing personality context for response generation
        """
        # Get relationship profile if exists
        relationship = self.relationships.get(sender)
        
        # Determine communication style
        if relationship and relationship.communication_style_override:
            comm_style = relationship.communication_style_override
        else:
            comm_style = self.base_communication_style
        
        # Get active personality traits
        active_traits = self._get_active_traits(relationship)
        
        # Build context
        context = {
            'communication_style': {
                'formality_level': comm_style.formality_level,
                'response_length': comm_style.response_length,
                'emoji_usage': comm_style.emoji_usage,
                'humor_level': comm_style.humor_level,
                'technical_depth': comm_style.technical_depth
            },
            'personality_traits': active_traits,
            'relationship_context': {
                'type': relationship.relationship_type if relationship else 'unknown',
                'closeness': relationship.closeness_level if relationship else 0.5,
                'frequency': relationship.interaction_frequency if relationship else 1
            },
            'behavioral_guidelines': self._get_behavioral_guidelines(relationship),
            'response_examples': self._get_response_examples(active_traits)
        }
        
        return context
    
    def _get_active_traits(self, relationship: Optional[RelationshipProfile]) -> Dict[str, float]:
        """Get personality traits adjusted for the specific relationship."""
        active_traits = {}
        
        for name, trait in self.traits.items():
            # Start with base weight
            weight = trait.weight
            
            # Apply relationship-specific adjustments
            if relationship and name in relationship.personality_adjustments:
                adjustment = relationship.personality_adjustments[name]
                weight = max(0.0, min(1.0, weight + adjustment))
            
            active_traits[name] = weight
        
        return active_traits
    
    def _get_behavioral_guidelines(self, relationship: Optional[RelationshipProfile]) -> List[str]:
        """Get behavioral guidelines for response generation."""
        guidelines = [
            "Maintain consistency with established personality",
            "Be authentic and natural in responses",
            "Consider the relationship context and history"
        ]
        
        if relationship:
            if relationship.relationship_type == 'professional':
                guidelines.extend([
                    "Keep responses professional and focused",
                    "Provide clear, actionable information"
                ])
            elif relationship.relationship_type == 'family':
                guidelines.extend([
                    "Be warm and supportive",
                    "Show personal interest and care"
                ])
            elif relationship.relationship_type == 'friend':
                guidelines.extend([
                    "Be casual and friendly",
                    "Include appropriate humor if suitable"
                ])
        
        return guidelines
    
    def _get_response_examples(self, active_traits: Dict[str, float]) -> List[str]:
        """Get response examples based on active personality traits."""
        examples = []
        
        for trait_name, weight in active_traits.items():
            if weight > 0.5 and trait_name in self.traits:
                trait = self.traits[trait_name]
                # Add examples with some randomness
                if random.random() < weight:
                    examples.extend(random.sample(trait.examples, min(2, len(trait.examples))))
        
        return examples[:5]  # Limit to 5 examples
    
    def should_respond(self, message_data: Dict[str, Any]) -> bool:
        """
        Determine if we should respond based on personality and context.
        
        Args:
            message_data: Information about the incoming message
            
        Returns:
            Boolean indicating if we should respond
        """
        sender = message_data.get('sender', '')
        content = message_data.get('content', '').lower()
        
        # Base probability
        base_prob = self.response_probability
        
        # Adjust based on relationship
        if sender in self.relationships:
            relationship = self.relationships[sender]
            # Closer relationships get higher response probability
            base_prob *= (0.5 + 0.5 * relationship.closeness_level)
        
        # Adjust based on message content
        if any(word in content for word in ['help', 'question', 'urgent', 'please']):
            base_prob *= 1.2
        
        # Adjust based on time of day
        current_time = datetime.now().time()
        if not (self.active_hours['start'] <= current_time <= self.active_hours['end']):
            base_prob *= 0.3  # Much less likely to respond outside active hours
        
        # Add some randomness to seem natural
        return random.random() < min(1.0, base_prob)
    
    def update_interaction_history(self, sender: str, message_type: str = 'received'):
        """Update interaction history for a sender."""
        if sender in self.relationships:
            relationship = self.relationships[sender]
            relationship.last_interaction = datetime.now()
            if message_type == 'received':
                relationship.interaction_frequency += 1
    
    def get_personality_summary(self) -> Dict[str, Any]:
        """Get a summary of the current personality configuration."""
        return {
            'traits': {name: trait.weight for name, trait in self.traits.items()},
            'communication_style': {
                'formality_level': self.base_communication_style.formality_level,
                'response_length': self.base_communication_style.response_length,
                'emoji_usage': self.base_communication_style.emoji_usage,
                'humor_level': self.base_communication_style.humor_level,
                'technical_depth': self.base_communication_style.technical_depth
            },
            'relationships_count': len(self.relationships),
            'response_probability': self.response_probability
        }
