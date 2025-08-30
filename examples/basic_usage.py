"""
Digi-Me Example Usage
====================

This example shows how to use the Digi-Me Digital Clone framework programmatically.
"""

import asyncio
import logging
from digi_me import DigitalClone, PersonalityEngine, WhatsAppPlatform, OllamaProvider
from digi_me.config.settings import Settings


async def basic_example():
    """Basic example of setting up and running a digital clone."""
    print("🤖 Digi-Me Basic Example")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize with default configuration
    clone = DigitalClone()
    
    # Setup Ollama LLM provider
    ollama_config = {
        'base_url': 'http://localhost:11434',
        'model': 'llama3.1',
        'temperature': 0.7,
        'max_tokens': 300
    }
    
    ollama_provider = OllamaProvider(ollama_config)
    
    # Initialize the provider
    if await ollama_provider.initialize():
        clone.set_llm_provider(ollama_provider)
        print("✅ Ollama provider initialized")
    else:
        print("❌ Failed to initialize Ollama provider")
        return
    
    # Setup WhatsApp platform
    whatsapp_config = {
        'headless': False,  # Set to True to run in background
        'chrome_profile_path': './chrome_profile_example',
        'response_delay': [1, 3],
        'scan_interval': 5
    }
    
    whatsapp = WhatsAppPlatform(whatsapp_config)
    clone.add_platform('whatsapp', whatsapp)
    print("✅ WhatsApp platform configured")
    
    print("\n📝 Clone Status:")
    status = clone.get_status()
    print(f"- Platforms: {status['platforms']}")
    print(f"- LLM Provider: {status['llm_provider']}")
    
    # Note: In a real scenario, you would call clone.start() here
    # For this example, we'll just show the setup
    print("\n✅ Digital Clone setup complete!")
    print("💡 To run: call await clone.start()")
    
    # Cleanup
    await ollama_provider.cleanup()


async def personality_example():
    """Example of customizing personality traits."""
    print("\n🧠 Personality Customization Example")
    
    # Create custom personality configuration
    personality_config = {
        'formality_level': 0.3,      # More casual
        'response_length': 'short',   # Brief responses
        'emoji_usage': 0.7,          # Use emojis frequently
        'humor_level': 0.8,          # Be humorous
        'technical_depth': 0.4,      # Keep it simple
        'response_probability': 0.9   # Almost always respond
    }
    
    # Initialize settings with custom personality
    config = {
        'personality': personality_config,
        'platforms': {'whatsapp': {'enabled': True}},
        'llm': {'provider': 'ollama', 'ollama': {'model': 'llama3.1'}}
    }
    
    # Create personality engine
    personality = PersonalityEngine(personality_config)
    
    # Test personality context generation
    test_sender = "friend123"
    context = personality.get_context_for_sender(test_sender)
    
    print("Generated personality context:")
    print(f"- Communication Style: {context['communication_style']}")
    print(f"- Active Traits: {list(context['personality_traits'].keys())}")
    print(f"- Behavioral Guidelines: {len(context['behavioral_guidelines'])} guidelines")
    
    # Test response probability
    test_message = {
        'sender': 'friend123',
        'content': 'Hey, can you help me with something?',
        'context': {}
    }
    
    should_respond = personality.should_respond(test_message)
    print(f"- Should respond to test message: {should_respond}")


async def configuration_example():
    """Example of working with configuration."""
    print("\n⚙️ Configuration Example")
    
    # Load settings (will use defaults if no config file found)
    settings = Settings()
    
    # Show configuration summary
    summary = settings.get_summary()
    print("Configuration Summary:")
    print(f"- Config Path: {summary['config_path'] or 'Using defaults'}")
    print(f"- LLM Provider: {summary['llm_provider']}")
    print(f"- Enabled Platforms: {summary['enabled_platforms']}")
    
    # Validate configuration
    is_valid = settings.validate_config()
    print(f"- Configuration Valid: {is_valid}")
    
    # Example of accessing nested configuration
    ollama_url = settings.get('llm.ollama.base_url', 'http://localhost:11434')
    print(f"- Ollama URL: {ollama_url}")
    
    # Example of modifying configuration
    settings.set('personality.humor_level', 0.9)
    print("- Modified humor level to 0.9")


async def run_examples():
    """Run all examples."""
    try:
        await basic_example()
        await personality_example()
        await configuration_example()
        
        print("\n🎉 All examples completed successfully!")
        print("\n📚 Next Steps:")
        print("1. Install Ollama and pull a model: ollama pull llama3.1")
        print("2. Copy config.example.yaml to config.yaml and customize")
        print("3. Run: python -m digi_me")
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_examples())
