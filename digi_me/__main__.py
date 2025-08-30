"""
Main Entry Point for Digi-Me Digital Clone Framework
===================================================

Command-line interface and main application runner.
"""

import asyncio
import argparse
import logging
import sys
import signal
from pathlib import Path
from typing import Optional

from digi_me import DigitalClone, PersonalityEngine, WhatsAppPlatform, OllamaProvider
from digi_me.config.settings import Settings
from digi_me.plugins.base import PluginManager


def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """Setup logging configuration."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=handlers
    )


async def create_sample_config(path: str = "config.yaml"):
    """Create a sample configuration file."""
    settings = Settings()
    settings.create_sample_config(path)
    print(f"Sample configuration created at: {path}")
    print("Please edit the configuration file and run again.")


async def run_digital_clone(config_path: Optional[str] = None):
    """Run the digital clone with the specified configuration."""
    print("🤖 Starting Digi-Me Digital Clone Framework...")
    
    # Load settings
    settings = Settings(config_path)
    
    # Setup logging
    log_config = settings.logging_config
    setup_logging(
        level=log_config.get('level', 'INFO'),
        log_file=log_config.get('file')
    )
    
    logger = logging.getLogger(__name__)
    
    # Validate configuration
    if not settings.validate_config():
        logger.error("Configuration validation failed. Please check your config file.")
        return False
    
    # Print configuration summary
    summary = settings.get_summary()
    print(f"📝 Configuration: {summary['config_path'] or 'defaults'}")
    print(f"🧠 LLM Provider: {summary['llm_provider']} ({summary['llm_model']})")
    print(f"📱 Platforms: {', '.join(summary['enabled_platforms'])}")
    print(f"🔌 Plugins: {len(summary['enabled_plugins'])} enabled")
    
    # Initialize digital clone
    clone = DigitalClone(config_path)
    
    try:
        # Setup LLM provider
        llm_config = settings.llm
        if llm_config['provider'] == 'ollama':
            ollama_provider = OllamaProvider(llm_config['ollama'])
            if not await ollama_provider.initialize():
                logger.error("Failed to initialize Ollama provider")
                return False
            clone.set_llm_provider(ollama_provider)
            print("✅ Ollama LLM provider initialized")
        
        # Setup platforms
        platform_configs = settings.platforms
        
        if 'whatsapp' in platform_configs and platform_configs['whatsapp'].get('enabled', False):
            whatsapp = WhatsAppPlatform(platform_configs['whatsapp'])
            clone.add_platform('whatsapp', whatsapp)
            print("✅ WhatsApp platform configured")
        
        # Setup plugins (if any)
        plugin_manager = PluginManager()
        # TODO: Load and register plugins based on configuration
        
        # Setup signal handlers for graceful shutdown
        shutdown_event = asyncio.Event()
        
        def signal_handler():
            logger.info("Received shutdown signal")
            shutdown_event.set()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, lambda s, f: signal_handler())
        
        print("\n🚀 Starting Digital Clone...")
        print("📱 Please scan WhatsApp QR code when prompted")
        print("⏹️  Press Ctrl+C to stop\n")
        
        # Start the digital clone
        await clone.start()
        
        print("✅ Digital Clone is running!")
        print("📊 Monitor logs for activity")
        
        # Wait for shutdown signal
        await shutdown_event.wait()
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return False
    finally:
        print("\n🛑 Shutting down Digital Clone...")
        await clone.stop()
        
        # Cleanup LLM provider
        if hasattr(clone, 'llm_provider') and clone.llm_provider:
            await clone.llm_provider.cleanup()
        
        print("✅ Shutdown complete")
    
    return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Digi-Me Digital Clone Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m digi_me                    # Run with default/auto-detected config
  python -m digi_me -c config.yaml    # Run with specific config file
  python -m digi_me --create-config   # Create sample configuration
  python -m digi_me --status          # Show configuration status
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create a sample configuration file and exit'
    )
    
    parser.add_argument(
        '--config-path',
        type=str,
        default='config.yaml',
        help='Path for created configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show configuration status and exit'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate configuration and exit'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Digi-Me Digital Clone Framework v0.1.0'
    )
    
    args = parser.parse_args()
    
    # Handle special commands
    if args.create_config:
        asyncio.run(create_sample_config(args.config_path))
        return
    
    if args.status or args.validate:
        settings = Settings(args.config)
        
        if args.status:
            summary = settings.get_summary()
            print("📊 Digi-Me Configuration Status")
            print(f"Config File: {summary['config_path'] or 'Using defaults'}")
            print(f"LLM Provider: {summary['llm_provider']} ({summary['llm_model']})")
            print(f"Platforms: {', '.join(summary['enabled_platforms']) or 'None'}")
            print(f"Plugins: {len(summary['enabled_plugins'])}")
            print(f"Logging Level: {summary['logging_level']}")
        
        if args.validate:
            if settings.validate_config():
                print("✅ Configuration is valid")
                sys.exit(0)
            else:
                print("❌ Configuration validation failed")
                sys.exit(1)
        return
    
    # Run the digital clone
    try:
        success = asyncio.run(run_digital_clone(args.config))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
