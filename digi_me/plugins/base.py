"""
Base Plugin System
=================

Base class for MCP (Model Context Protocol) plugins and extensibility.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class PluginBase(ABC):
    """
    Abstract base class for plugins.
    
    Plugins extend the functionality of the digital clone and can provide:
    - Additional platform integrations
    - Custom response processing
    - External service integrations
    - Data analysis and insights
    - Custom personality behaviors
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """Initialize the plugin."""
        self.name = name
        self.version = version
        self.is_active = False
        self.clone_reference = None
        self.config = {}
        
        logger.info(f"Plugin base initialized: {name} v{version}")
    
    @abstractmethod
    def initialize(self, clone, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with the digital clone reference and configuration.
        
        Args:
            clone: Reference to the main DigitalClone instance
            config: Plugin-specific configuration
            
        Returns:
            True if initialization was successful
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Cleanup plugin resources."""
        pass
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin information."""
        return {
            'name': self.name,
            'version': self.version,
            'is_active': self.is_active,
            'description': self.get_description(),
            'capabilities': self.get_capabilities()
        }
    
    @abstractmethod
    def get_description(self) -> str:
        """Get plugin description."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Get list of plugin capabilities."""
        pass
    
    # Optional hooks - plugins can override these for custom behavior
    
    def on_message_received(self, platform: str, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Hook called when a message is received (before processing).
        
        Args:
            platform: Platform name
            message_data: Message data
            
        Returns:
            Modified message data or None to continue with original
        """
        return None
    
    def on_response_generated(self, platform: str, response: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Hook called when a response is generated (before sending).
        
        Args:
            platform: Platform name
            response: Generated response
            context: Message context
            
        Returns:
            Modified response or None to continue with original
        """
        return None
    
    def on_conversation_started(self, platform: str, sender: str):
        """Hook called when a new conversation is started."""
        pass
    
    def on_conversation_ended(self, platform: str, sender: str):
        """Hook called when a conversation ends."""
        pass


class MCPPlugin(PluginBase):
    """
    Enhanced plugin base class for MCP (Model Context Protocol) integration.
    
    This class provides additional functionality for plugins that want to
    integrate with MCP servers for extended capabilities.
    """
    
    def __init__(self, name: str, mcp_server_url: Optional[str] = None, version: str = "1.0.0"):
        """Initialize MCP plugin."""
        super().__init__(name, version)
        self.mcp_server_url = mcp_server_url
        self.mcp_client = None
        
    async def connect_mcp_server(self) -> bool:
        """
        Connect to MCP server.
        
        Returns:
            True if connection was successful
        """
        if not self.mcp_server_url:
            logger.warning(f"No MCP server URL configured for plugin {self.name}")
            return False
        
        try:
            # TODO: Implement MCP client connection
            # This is a placeholder for future MCP integration
            logger.info(f"Connecting to MCP server: {self.mcp_server_url}")
            
            # Placeholder for actual MCP connection logic
            self.mcp_client = None  # MCPClient(self.mcp_server_url)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def call_mcp_function(self, function_name: str, parameters: Dict[str, Any]) -> Optional[Any]:
        """
        Call a function on the MCP server.
        
        Args:
            function_name: Name of the function to call
            parameters: Function parameters
            
        Returns:
            Function result or None if failed
        """
        if not self.mcp_client:
            logger.error("MCP client not connected")
            return None
        
        try:
            # TODO: Implement MCP function call
            logger.info(f"Calling MCP function: {function_name}")
            return None
            
        except Exception as e:
            logger.error(f"MCP function call failed: {e}")
            return None


class PluginManager:
    """
    Manages plugins for the digital clone.
    
    Handles plugin loading, initialization, lifecycle management,
    and coordination between plugins and the main clone system.
    """
    
    def __init__(self):
        """Initialize the plugin manager."""
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_hooks = {
            'on_message_received': [],
            'on_response_generated': [],
            'on_conversation_started': [],
            'on_conversation_ended': []
        }
        
        logger.info("Plugin Manager initialized")
    
    def register_plugin(self, plugin: PluginBase) -> bool:
        """
        Register a plugin with the manager.
        
        Args:
            plugin: Plugin instance to register
            
        Returns:
            True if registration was successful
        """
        if plugin.name in self.plugins:
            logger.warning(f"Plugin {plugin.name} is already registered")
            return False
        
        self.plugins[plugin.name] = plugin
        
        # Register plugin hooks
        for hook_name in self.plugin_hooks.keys():
            if hasattr(plugin, hook_name):
                self.plugin_hooks[hook_name].append(plugin)
        
        logger.info(f"Plugin registered: {plugin.name} v{plugin.version}")
        return True
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        Unregister a plugin.
        
        Args:
            plugin_name: Name of the plugin to unregister
            
        Returns:
            True if unregistration was successful
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin {plugin_name} is not registered")
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Cleanup plugin
        try:
            plugin.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up plugin {plugin_name}: {e}")
        
        # Remove from hooks
        for hook_list in self.plugin_hooks.values():
            if plugin in hook_list:
                hook_list.remove(plugin)
        
        # Remove from registry
        del self.plugins[plugin_name]
        
        logger.info(f"Plugin unregistered: {plugin_name}")
        return True
    
    def initialize_plugins(self, clone, plugin_configs: Dict[str, Dict[str, Any]]) -> bool:
        """
        Initialize all registered plugins.
        
        Args:
            clone: Reference to the main DigitalClone instance
            plugin_configs: Configuration for each plugin
            
        Returns:
            True if all plugins initialized successfully
        """
        success = True
        
        for plugin_name, plugin in self.plugins.items():
            try:
                config = plugin_configs.get(plugin_name, {})
                if plugin.initialize(clone, config):
                    plugin.is_active = True
                    logger.info(f"Plugin initialized: {plugin_name}")
                else:
                    logger.error(f"Failed to initialize plugin: {plugin_name}")
                    success = False
            except Exception as e:
                logger.error(f"Error initializing plugin {plugin_name}: {e}")
                success = False
        
        return success
    
    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Call a plugin hook and collect results.
        
        Args:
            hook_name: Name of the hook to call
            *args: Positional arguments to pass to hooks
            **kwargs: Keyword arguments to pass to hooks
            
        Returns:
            List of results from all plugins that handled the hook
        """
        results = []
        
        if hook_name not in self.plugin_hooks:
            logger.warning(f"Unknown plugin hook: {hook_name}")
            return results
        
        for plugin in self.plugin_hooks[hook_name]:
            if not plugin.is_active:
                continue
            
            try:
                hook_method = getattr(plugin, hook_name)
                result = hook_method(*args, **kwargs)
                if result is not None:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error calling {hook_name} on plugin {plugin.name}: {e}")
        
        return results
    
    def get_plugin_status(self) -> Dict[str, Any]:
        """Get status of all plugins."""
        return {
            'total_plugins': len(self.plugins),
            'active_plugins': sum(1 for p in self.plugins.values() if p.is_active),
            'plugins': {name: plugin.get_plugin_info() for name, plugin in self.plugins.items()}
        }
