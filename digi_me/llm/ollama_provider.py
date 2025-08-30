"""
Ollama LLM Provider
==================

Integration with Ollama for local LLM inference to generate personalized responses.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Any
import aiohttp
from datetime import datetime

from ..llm.base import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """
    Ollama LLM provider for local language model inference.
    
    This provider integrates with a locally running Ollama instance
    to generate contextual and personalized responses.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Ollama provider with configuration."""
        super().__init__("ollama", config)
        
        # Ollama configuration
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.model_name = config.get('model', 'llama3.1')
        self.timeout = config.get('timeout', 60)
        
        # Generation parameters
        self.max_tokens = config.get('max_tokens', 500)
        self.temperature = config.get('temperature', 0.7)
        self.top_p = config.get('top_p', 0.9)
        self.repeat_penalty = config.get('repeat_penalty', 1.1)
        
        # System prompt configuration
        self.base_system_prompt = config.get('system_prompt', self._get_default_system_prompt())
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"Ollama Provider initialized - Model: {self.model_name}")
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for the digital clone."""
        return """You are a digital clone representing a real person in their online communications. Your goal is to respond authentically as they would, maintaining their personality, communication style, and behavioral patterns.

Key guidelines:
1. Be authentic - respond as the person would naturally respond
2. Maintain personality consistency across all interactions
3. Consider the relationship context with each contact
4. Keep responses natural and conversational
5. Don't reveal that you are an AI or digital clone
6. Use the provided personality traits and communication style
7. Reference conversation history when relevant
8. Be helpful and engaging while staying true to the person's character

Remember: You ARE this person in digital form. Respond naturally and authentically."""
    
    async def initialize(self) -> bool:
        """Initialize the Ollama connection."""
        try:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
            
            # Test connection and model availability
            await self._check_model_availability()
            self.is_available = True
            
            logger.info("Ollama Provider initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama Provider: {e}")
            self.is_available = False
            return False
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session:
            await self.session.close()
            self.session = None
        logger.info("Ollama Provider cleaned up")
    
    async def generate_response(self, prompt_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate a response using the Ollama model.
        
        Args:
            prompt_data: Dictionary containing message context and personality information
            
        Returns:
            Generated response string or None if generation failed
        """
        if not self.is_available or not self.session:
            logger.error("Ollama Provider is not available")
            return None
        
        try:
            # Build the prompt
            system_prompt = self._build_system_prompt(prompt_data)
            user_prompt = self._build_user_prompt(prompt_data)
            
            # Prepare the request
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Add conversation history if available
            history = prompt_data.get('conversation_history', [])
            if history:
                # Add recent history (last 10 messages to avoid token limits)
                recent_history = history[-10:]
                for msg in recent_history:
                    if msg.get('role') in ['user', 'assistant']:
                        messages.insert(-1, {
                            "role": msg['role'],
                            "content": msg['content']
                        })
            
            # Generate response
            response = await self._call_ollama_chat(messages)
            
            if response:
                # Post-process the response
                processed_response = self._post_process_response(response, prompt_data)
                logger.info(f"Response generated successfully ({len(processed_response)} chars)")
                return processed_response
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None
    
    def _build_system_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """Build the system prompt with personality and context information."""
        personality_context = prompt_data.get('personality', {})
        relationship_context = personality_context.get('relationship_context', {})
        comm_style = personality_context.get('communication_style', {})
        traits = personality_context.get('personality_traits', {})
        guidelines = personality_context.get('behavioral_guidelines', [])
        
        system_prompt_parts = [self.base_system_prompt]
        
        # Add personality traits
        if traits:
            trait_descriptions = []
            for trait_name, weight in traits.items():
                if weight > 0.5:  # Only include prominent traits
                    trait_descriptions.append(f"- {trait_name.title()}: {weight:.1f}/1.0")
            
            if trait_descriptions:
                system_prompt_parts.append(f"\nYour personality traits:\n" + "\n".join(trait_descriptions))
        
        # Add communication style
        if comm_style:
            style_parts = []
            if 'formality_level' in comm_style:
                formality = comm_style['formality_level']
                if formality < 0.3:
                    style_parts.append("Use casual, informal language")
                elif formality > 0.7:
                    style_parts.append("Use formal, professional language")
                else:
                    style_parts.append("Use moderately formal language")
            
            if 'response_length' in comm_style:
                length = comm_style['response_length']
                if length == 'short':
                    style_parts.append("Keep responses brief and concise")
                elif length == 'long':
                    style_parts.append("Provide detailed, comprehensive responses")
                else:
                    style_parts.append("Provide moderate-length responses")
            
            if 'humor_level' in comm_style:
                humor = comm_style['humor_level']
                if humor > 0.6:
                    style_parts.append("Include appropriate humor when suitable")
                elif humor < 0.3:
                    style_parts.append("Maintain a serious, professional tone")
            
            if 'emoji_usage' in comm_style:
                emoji = comm_style['emoji_usage']
                if emoji > 0.6:
                    style_parts.append("Use emojis frequently to express emotions")
                elif emoji > 0.3:
                    style_parts.append("Use emojis occasionally")
                else:
                    style_parts.append("Rarely use emojis")
            
            if style_parts:
                system_prompt_parts.append(f"\nCommunication style:\n" + "\n".join(f"- {part}" for part in style_parts))
        
        # Add relationship context
        if relationship_context:
            rel_type = relationship_context.get('type', 'unknown')
            closeness = relationship_context.get('closeness', 0.5)
            
            relationship_guidance = f"\nRelationship context:\n- This person is a {rel_type}"
            
            if closeness > 0.7:
                relationship_guidance += "\n- You have a close relationship - be warm and personal"
            elif closeness < 0.3:
                relationship_guidance += "\n- Keep interactions professional and somewhat distant"
            else:
                relationship_guidance += "\n- Maintain a friendly but not overly personal tone"
            
            system_prompt_parts.append(relationship_guidance)
        
        # Add behavioral guidelines
        if guidelines:
            system_prompt_parts.append(f"\nBehavioral guidelines:\n" + "\n".join(f"- {guideline}" for guideline in guidelines))
        
        return "\n".join(system_prompt_parts)
    
    def _build_user_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """Build the user prompt with message content and context."""
        sender = prompt_data.get('sender', 'Unknown')
        content = prompt_data.get('content', '')
        platform = prompt_data.get('platform', 'unknown')
        context = prompt_data.get('context', {})
        
        prompt_parts = [
            f"Message from {sender} on {platform}:",
            f'"{content}"',
            "",
            "Please respond naturally as you would to this person."
        ]
        
        # Add any additional context
        if context:
            prompt_parts.insert(-2, f"Additional context: {json.dumps(context)}")
        
        return "\n".join(prompt_parts)
    
    async def _call_ollama_chat(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """Make a chat completion request to Ollama."""
        try:
            url = f"{self.base_url}/api/chat"
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "top_p": self.top_p,
                    "repeat_penalty": self.repeat_penalty,
                    "num_predict": self.max_tokens
                }
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('message', {}).get('content', '').strip()
                else:
                    logger.error(f"Ollama request failed with status {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error response: {error_text}")
                    return None
        
        except asyncio.TimeoutError:
            logger.error("Ollama request timed out")
            return None
        except Exception as e:
            logger.error(f"Ollama request failed: {e}")
            return None
    
    def _post_process_response(self, response: str, prompt_data: Dict[str, Any]) -> str:
        """Post-process the generated response."""
        # Clean up the response
        response = response.strip()
        
        # Remove any unwanted prefixes/suffixes that the model might add
        unwanted_prefixes = [
            "Here's my response:",
            "I would respond:",
            "My response:",
            "Response:",
            "I'd say:"
        ]
        
        for prefix in unwanted_prefixes:
            if response.lower().startswith(prefix.lower()):
                response = response[len(prefix):].strip()
        
        # Ensure response length is appropriate
        comm_style = prompt_data.get('personality', {}).get('communication_style', {})
        response_length = comm_style.get('response_length', 'medium')
        
        if response_length == 'short' and len(response) > 200:
            # Try to truncate at sentence boundary
            sentences = response.split('. ')
            if len(sentences) > 1:
                response = sentences[0] + '.'
        elif response_length == 'long' and len(response) < 50:
            # This is already short, leave as is
            pass
        
        return response
    
    async def _check_model_availability(self) -> bool:
        """Check if the specified model is available in Ollama."""
        try:
            url = f"{self.base_url}/api/tags"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    models = [model['name'] for model in result.get('models', [])]
                    
                    if self.model_name in models:
                        logger.info(f"Model {self.model_name} is available")
                        return True
                    else:
                        logger.warning(f"Model {self.model_name} not found. Available models: {models}")
                        # Try to pull the model
                        await self._pull_model()
                        return True
                else:
                    logger.error(f"Failed to get model list: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
    
    async def _pull_model(self) -> bool:
        """Attempt to pull the specified model."""
        try:
            logger.info(f"Attempting to pull model {self.model_name}...")
            url = f"{self.base_url}/api/pull"
            
            payload = {"name": self.model_name}
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info(f"Successfully pulled model {self.model_name}")
                    return True
                else:
                    logger.error(f"Failed to pull model {self.model_name}: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama."""
        try:
            url = f"{self.base_url}/api/tags"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return [model['name'] for model in result.get('models', [])]
                else:
                    logger.error(f"Failed to get model list: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the provider."""
        return {
            'name': self.name,
            'base_url': self.base_url,
            'model': self.model_name,
            'is_available': self.is_available,
            'config': {
                'max_tokens': self.max_tokens,
                'temperature': self.temperature,
                'top_p': self.top_p,
                'timeout': self.timeout
            }
        }
