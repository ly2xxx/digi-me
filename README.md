# 🤖 Digi-Me: Digital Clone Framework

**A comprehensive framework for creating digital clones that can represent you in various online work and life scenarios with extensible plugin architecture.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## 🎯 What is Digi-Me?

Digi-Me is a production-ready digital clone framework that can represent you authentically in online communications. The MVP focuses on **WhatsApp Web automation** with **Ollama LLM integration**, allowing your digital clone to respond to messages in your personal style.

### Key Features

- 🧠 **Advanced Personality Engine** - Maintains your communication style, personality traits, and relationship dynamics
- 📱 **WhatsApp Web Integration** - Automated message monitoring and response via Selenium
- 🤖 **Local LLM Integration** - Uses Ollama for private, local AI inference
- 🔗 **Extensible Plugin System** - MCP (Model Context Protocol) support for future integrations
- 💬 **Context-Aware Responses** - Remembers conversation history and relationship context  
- ⚙️ **Flexible Configuration** - YAML/JSON config with environment variable overrides
- 🛡️ **Privacy-First** - All processing happens locally, no data sent to external APIs

## 🏗️ Architecture

```
digi_me/
├── core/                   # Core framework components
│   ├── clone.py           # Main DigitalClone orchestrator
│   ├── personality.py     # Personality engine and traits
│   └── context_manager.py # Conversation history management
├── platforms/             # Platform integrations
│   ├── base.py           # Abstract platform base class
│   └── whatsapp.py       # WhatsApp Web automation
├── llm/                  # LLM providers
│   ├── base.py           # Abstract LLM provider base
│   └── ollama_provider.py # Ollama integration
├── plugins/              # Plugin system
│   └── base.py           # Plugin framework with MCP support
├── config/               # Configuration management
│   └── settings.py       # Settings and config loading
└── __main__.py          # CLI entry point
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed on your system
2. **Ollama** installed and running ([Download here](https://ollama.ai))
3. **Google Chrome** browser installed
4. **WhatsApp Web** access (you'll need to scan QR code)

### Step 1: Install Dependencies

```bash
# Clone the repository
git clone https://github.com/ly2xxx/digi-me.git
cd digi-me

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Setup Ollama

```bash
# Install Ollama (if not already installed)
# Visit https://ollama.ai for installation instructions

# Pull a language model (required)
ollama pull llama3.1

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### Step 3: Configure Your Digital Clone

```bash
# Create configuration file
python -m digi_me --create-config

# Edit the configuration
# Copy config.example.yaml to config.yaml and customize:
cp config.example.yaml config.yaml
```

**Key configuration options:**

```yaml
# Personality settings
personality:
  formality_level: 0.5      # 0.0=casual, 1.0=formal
  response_length: "medium" # short, medium, long
  humor_level: 0.4          # 0.0=serious, 1.0=humorous
  emoji_usage: 0.3          # 0.0=never, 1.0=frequently

# WhatsApp settings  
platforms:
  whatsapp:
    enabled: true
    headless: false           # Set true for background operation
    response_delay: [2, 5]    # Natural response delay range

# LLM settings
llm:
  provider: "ollama"
  ollama:
    model: "llama3.1"         # Ensure this model is pulled
    temperature: 0.7          # Response creativity
```

### Step 4: Run Your Digital Clone

```bash
# Start the digital clone
python -m digi_me

# Or with specific config
python -m digi_me -c config.yaml

# Check configuration
python -m digi_me --status
```

### Step 5: Setup WhatsApp Web

1. When you start the digital clone, Chrome will open to WhatsApp Web
2. Scan the QR code with your phone's WhatsApp
3. The system will start monitoring for new messages
4. Your digital clone will respond based on your configured personality!

## 📖 Usage Examples

### Basic Programmatic Usage

```python
import asyncio
from digi_me import DigitalClone, WhatsAppPlatform, OllamaProvider

async def main():
    # Initialize digital clone
    clone = DigitalClone()
    
    # Setup Ollama LLM
    ollama = OllamaProvider({
        'base_url': 'http://localhost:11434',
        'model': 'llama3.1',
        'temperature': 0.7
    })
    await ollama.initialize()
    clone.set_llm_provider(ollama)
    
    # Add WhatsApp platform
    whatsapp = WhatsAppPlatform({
        'headless': False,
        'response_delay': [2, 5]
    })
    clone.add_platform('whatsapp', whatsapp)
    
    # Start the clone
    await clone.start()

asyncio.run(main())
```

### Advanced Personality Customization

```python
from digi_me.core.personality import PersonalityTrait, RelationshipProfile

# Create custom personality trait
creative_trait = PersonalityTrait(
    name="creativity",
    weight=0.8,
    description="Highly creative and innovative responses",
    examples=["What if we tried...", "Here's a creative approach..."],
    active_contexts=["brainstorming", "problem_solving"]
)

# Add relationship-specific behavior
family_profile = RelationshipProfile(
    contact_identifier="+1234567890",
    relationship_type="family",
    closeness_level=0.9,
    personality_adjustments={"friendliness": 0.3, "formality": -0.2}
)
```

## 🎛️ Configuration Reference

### Personality Configuration

| Setting | Type | Range | Description |
|---------|------|--------|-------------|
| `formality_level` | float | 0.0-1.0 | Communication formality (0=casual, 1=formal) |
| `response_length` | string | short/medium/long | Preferred response length |
| `emoji_usage` | float | 0.0-1.0 | Frequency of emoji usage |
| `humor_level` | float | 0.0-1.0 | Amount of humor in responses |
| `technical_depth` | float | 0.0-1.0 | Technical vs. simple language |
| `response_probability` | float | 0.0-1.0 | Likelihood to respond to messages |

### Platform Configuration

#### WhatsApp Settings
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `enabled` | boolean | true | Enable WhatsApp platform |
| `headless` | boolean | false | Run browser in background |
| `chrome_profile_path` | string | "./chrome_profile" | Persistent browser profile |
| `response_delay` | array | [2, 5] | Random delay range (seconds) |
| `scan_interval` | integer | 3 | Message check interval (seconds) |
| `auto_mark_read` | boolean | true | Automatically mark messages as read |

### LLM Configuration

#### Ollama Settings
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `base_url` | string | "http://localhost:11434" | Ollama server URL |
| `model` | string | "llama3.1" | Model to use (must be pulled) |
| `timeout` | integer | 60 | Request timeout (seconds) |
| `max_tokens` | integer | 500 | Maximum response length |
| `temperature` | float | 0.7 | Response creativity (0.0-1.0) |
| `top_p` | float | 0.9 | Token selection randomness |

## 🔧 Advanced Features

### Relationship Management

Define specific behaviors for different contacts:

```yaml
relationships:
  "+1234567890":  # Phone number
    type: "professional"     # family, friend, colleague, professional
    closeness_level: 0.3     # 0.0=distant, 1.0=very close
    formality_override: 0.8  # Override personality settings
    notes: "Important client"
```

### Context Management

The system maintains conversation history and context:

- **Memory**: Remembers up to 100 messages per conversation (configurable)
- **Context Window**: Keeps 30 days of history (configurable)
- **Relationship Tracking**: Learns from interaction patterns
- **Smart Responses**: Uses conversation history for contextual replies

### Plugin System (Future-Ready)

Built-in support for MCP (Model Context Protocol) plugins:

```python
from digi_me.plugins.base import MCPPlugin

class CustomPlugin(MCPPlugin):
    def get_description(self):
        return "Custom functionality plugin"
    
    def on_message_received(self, platform, message_data):
        # Custom message processing
        return modified_message_data
```

## 🛡️ Security & Privacy

- **Local Processing**: All AI inference happens locally via Ollama
- **Data Privacy**: No conversation data sent to external APIs
- **Secure Storage**: Browser profiles and configs stored locally
- **Access Control**: Built-in sender ignore lists and filtering
- **Session Management**: Persistent browser sessions for security

## 🔍 Monitoring & Debugging

### Logging Configuration

```yaml
logging:
  level: "INFO"              # DEBUG, INFO, WARNING, ERROR
  file: "digi-me.log"        # Log file path
  max_size: 10485760         # Max log file size (10MB)
  backup_count: 5            # Number of backup files
```

### Status Commands

```bash
# Check system status
python -m digi_me --status

# Validate configuration
python -m digi_me --validate

# Create sample config
python -m digi_me --create-config
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export DIGI_ME_LOG_LEVEL=DEBUG
python -m digi_me
```

## 🚧 Troubleshooting

### Common Issues

**1. Ollama Connection Failed**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

**2. Chrome/WhatsApp Issues**
- Ensure Chrome is installed and updated
- Check chrome_profile_path permissions
- Try running with `headless: false` first

**3. Model Not Found**
```bash
# List available models
ollama list

# Pull required model
ollama pull llama3.1
```

**4. Configuration Errors**
```bash
# Validate your config
python -m digi_me --validate

# Reset to defaults
python -m digi_me --create-config
```

### Performance Optimization

- Use `headless: true` for better performance
- Adjust `scan_interval` based on message frequency
- Limit `max_tokens` for faster responses
- Use faster models for real-time responses

## 🗺️ Roadmap

### Current (v0.1.0)
- ✅ WhatsApp Web integration
- ✅ Ollama LLM support  
- ✅ Advanced personality engine
- ✅ Configuration management
- ✅ Plugin framework

### Near Future (v0.2.0)
- 🔄 Microsoft Teams integration
- 🔄 Outlook email automation
- 🔄 Advanced relationship learning
- 🔄 Voice message support
- 🔄 Multi-language support

### Future (v1.0.0)
- 🔮 Slack integration
- 🔮 Discord support
- 🔮 Calendar integration
- 🔮 Document analysis
- 🔮 Video call participation
- 🔮 Full MCP ecosystem support

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/ly2xxx/digi-me.git
cd digi-me

# Development dependencies
pip install -r requirements.txt
pip install black flake8 mypy pytest pytest-asyncio

# Run tests
pytest

# Format code
black digi_me/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for local LLM inference
- [Selenium](https://selenium.dev) for web automation
- [WhatsApp Web](https://web.whatsapp.com) for messaging platform
- The open-source community for inspiration and tools

## 💬 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/ly2xxx/digi-me/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/ly2xxx/digi-me/discussions)
- 📧 **Email**: [support@digi-me.dev](mailto:support@digi-me.dev)
- 💬 **Discord**: [Join our community](https://discord.gg/digi-me)

---

**⚠️ Disclaimer**: This tool is for personal and educational use. Please respect WhatsApp's Terms of Service and use responsibly. The developers are not responsible for any misuse of this software.

**🔒 Privacy Notice**: All processing is done locally on your machine. No data is sent to external servers except for the LLM inference via your local Ollama instance.
