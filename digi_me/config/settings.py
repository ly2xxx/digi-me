"""
Configuration System
===================

Manages configuration loading and validation for the digital clone framework.
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class Settings:
    """
    Configuration management for the Digital Clone framework.
    
    Supports loading configuration from:
    - YAML files
    - JSON files
    - Environment variables
    - Default values
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize settings with optional configuration file."""
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        
        # Extract major configuration sections
        self.personality = self.config.get('personality', {})
        self.platforms = self.config.get('platforms', {})
        self.llm = self.config.get('llm', {})
        self.plugins = self.config.get('plugins', {})
        self.logging_config = self.config.get('logging', {})
        
        # General settings
        self.ignore_senders = self.config.get('ignore_senders', [])
        self.response_triggers = self.config.get('response_triggers', ['help', 'question', 'urgent'])
        
        logger.info(f"Settings loaded from: {self.config_path}")
    
    def _find_config_file(self) -> Optional[str]:
        """Find configuration file in standard locations."""
        search_paths = [
            'config.yaml',
            'config.yml',
            'config.json',
            '.digi-me/config.yaml',
            '.digi-me/config.yml',
            '.digi-me/config.json',
            os.path.expanduser('~/.digi-me/config.yaml'),
            os.path.expanduser('~/.digi-me/config.yml'),
            os.path.expanduser('~/.digi-me/config.json')
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        logger.warning("No configuration file found, using defaults")
        return None
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if not self.config_path:
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.endswith('.json'):
                    config = json.load(f)
                else:
                    config = yaml.safe_load(f)
            
            # Merge with defaults
            default_config = self._get_default_config()
            merged_config = self._merge_configs(default_config, config)
            
            # Apply environment variable overrides
            self._apply_env_overrides(merged_config)
            
            return merged_config
            
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            logger.info("Using default configuration")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'personality': {
                'formality_level': 0.5,
                'response_length': 'medium',
                'emoji_usage': 0.3,
                'humor_level': 0.4,
                'technical_depth': 0.6,
                'response_probability': 0.8
            },
            'platforms': {
                'whatsapp': {
                    'enabled': True,
                    'headless': False,
                    'chrome_profile_path': './chrome_profile',
                    'response_delay': [2, 5],
                    'scan_interval': 3,
                    'auto_mark_read': True
                }
            },
            'llm': {
                'provider': 'ollama',
                'ollama': {
                    'base_url': 'http://localhost:11434',
                    'model': 'llama3.1',
                    'timeout': 60,
                    'max_tokens': 500,
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'repeat_penalty': 1.1,
                    'system_prompt': None  # Uses default
                }
            },
            'plugins': {
                'enabled_plugins': []
            },
            'logging': {
                'level': 'INFO',
                'file': 'digi-me.log',
                'max_size': 10485760,  # 10MB
                'backup_count': 5
            },
            'ignore_senders': [],
            'response_triggers': ['help', 'question', 'urgent', 'please'],
            'context': {
                'max_messages_per_conversation': 100,
                'context_window_days': 30
            }
        }
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge user configuration with defaults."""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]):
        """Apply environment variable overrides."""
        env_mappings = {
            'DIGI_ME_OLLAMA_URL': ['llm', 'ollama', 'base_url'],
            'DIGI_ME_OLLAMA_MODEL': ['llm', 'ollama', 'model'],
            'DIGI_ME_LOG_LEVEL': ['logging', 'level'],
            'DIGI_ME_WHATSAPP_HEADLESS': ['platforms', 'whatsapp', 'headless'],
            'DIGI_ME_CHROME_PROFILE': ['platforms', 'whatsapp', 'chrome_profile_path']
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Navigate to the nested config location
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Convert value to appropriate type
                final_key = config_path[-1]
                if final_key in current:
                    original_value = current[final_key]
                    if isinstance(original_value, bool):
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif isinstance(original_value, int):
                        value = int(value)
                    elif isinstance(original_value, float):
                        value = float(value)
                
                current[final_key] = value
                logger.info(f"Applied environment override: {env_var} = {value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with dot notation support."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set a configuration value with dot notation support."""
        keys = key.split('.')
        current = self.config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def save(self, path: Optional[str] = None):
        """Save current configuration to file."""
        save_path = path or self.config_path or 'config.yaml'
        
        try:
            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to: {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {save_path}: {e}")
    
    def create_sample_config(self, path: str = 'config.yaml'):
        """Create a sample configuration file."""
        config = self._get_default_config()
        
        # Add comments and documentation
        config_with_comments = {
            '# Digi-Me Configuration File': None,
            '# This file configures your digital clone behavior and integrations': None,
            '': None,
            'personality': {
                '# Personality configuration (0.0 to 1.0)': None,
                'formality_level': config['personality']['formality_level'],
                'response_length': config['personality']['response_length'],
                'emoji_usage': config['personality']['emoji_usage'],
                'humor_level': config['personality']['humor_level'],
                'technical_depth': config['personality']['technical_depth'],
                'response_probability': config['personality']['response_probability']
            },
            'platforms': config['platforms'],
            'llm': config['llm'],
            'logging': config['logging'],
            '# List of senders to ignore': None,
            'ignore_senders': [],
            '# Words that trigger responses': None,
            'response_triggers': config['response_triggers']
        }
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Sample configuration created at: {path}")
            
        except Exception as e:
            logger.error(f"Failed to create sample configuration: {e}")
    
    def validate_config(self) -> bool:
        """Validate the current configuration."""
        errors = []
        
        # Validate personality values
        personality = self.personality
        for key, value in personality.items():
            if key.endswith('_level') or key.endswith('_usage') or key == 'response_probability':
                if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    errors.append(f"personality.{key} must be a number between 0 and 1")
        
        # Validate response_length
        if personality.get('response_length') not in ['short', 'medium', 'long']:
            errors.append("personality.response_length must be 'short', 'medium', or 'long'")
        
        # Validate LLM configuration
        llm_provider = self.llm.get('provider')
        if llm_provider not in ['ollama']:  # Add more providers as implemented
            errors.append(f"Unsupported LLM provider: {llm_provider}")
        
        # Validate Ollama configuration
        if llm_provider == 'ollama':
            ollama_config = self.llm.get('ollama', {})
            required_fields = ['base_url', 'model']
            for field in required_fields:
                if field not in ollama_config:
                    errors.append(f"Missing required Ollama configuration: {field}")
        
        # Log validation results
        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            return False
        else:
            logger.info("Configuration validation passed")
            return True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            'config_path': self.config_path,
            'personality_summary': {
                'formality': self.personality.get('formality_level', 0.5),
                'response_style': self.personality.get('response_length', 'medium'),
                'humor': self.personality.get('humor_level', 0.4)
            },
            'enabled_platforms': [name for name, config in self.platforms.items() if config.get('enabled', False)],
            'llm_provider': self.llm.get('provider'),
            'llm_model': self.llm.get(self.llm.get('provider', 'ollama'), {}).get('model'),
            'enabled_plugins': self.plugins.get('enabled_plugins', []),
            'logging_level': self.logging_config.get('level', 'INFO')
        }
