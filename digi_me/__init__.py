"""
Digi-Me: A Digital Clone Framework
==================================

A comprehensive framework for creating digital clones that can represent you
in various online work and life scenarios with extensible plugin architecture.
"""

__version__ = "0.1.0"
__author__ = "ly2xxx"
__description__ = "Digital Clone Framework with MCP Plugin Support"

from .core.clone import DigitalClone
from .core.personality import PersonalityEngine
from .platforms.whatsapp import WhatsAppPlatform
from .llm.ollama_provider import OllamaProvider

__all__ = [
    "DigitalClone",
    "PersonalityEngine", 
    "WhatsAppPlatform",
    "OllamaProvider"
]
