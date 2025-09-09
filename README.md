# Pollinations Plugin for Limnoria
A Limnoria IRC bot plugin that integrates with [Pollinations.ai](https://pollinations.ai) for AI-powered text generation and image creation.

## Features
- **Text Generation**: Generate AI responses using chat context
- **Image Generation**: Create images from text prompts
- **Auto-Reply**: Automatically respond to trigger words in channel
- **Context Awareness**: Uses recent channel conversation for better responses
- **Highly Configurable**: Multiple settings for customization
- **URL Shortening**: Optional shortened URLs for generated images

## Installation
1. Download the plugin files to your Limnoria plugins directory
2. Load the plugin: `/msg yourbot load Pollinations`
3. Configure the plugin settings as needed

## Commands
### Text Generation
chat <prompt>

Generate AI text responses. The bot can use recent channel conversation as context.  
**Examples:**
chat Explain quantum physics simply
chat What do you think about the previous discussion?

### Image Generation
image <prompt>

Generate images from text descriptions.  
**Examples:**
image beautiful sunset over mountains
image cute cat playing with yarn
image cyberpunk city at night
image realistic portrait of a medieval knight

## Configuration
All settings can be configured per-channel using:
/msg yourbot config channel #yourchannel plugins.Pollinations.<setting> <value>

### Text Generation Settings
| Setting | Default | Description |
|---------|---------|-------------|
| `prompt` | "You are $botnick the #channel bot. Be nice and helpfull" | System prompt for the AI ($botnick = bot's nickname) |
| `context_lines` | 50 | Number of recent messages to include as context |
| `nick_include` | True | Include user's nickname in the prompt |
| `nick_strip` | True | Remove bot's nickname from responses |
| `nick_prefix` | False | Prefix responses with user's nickname |
| `reply_intact` | False | Send multi-line responses as separate messages |

### Auto-Reply Settings
| Setting | Default | Description |
|---------|---------|-------------|
| `auto_reply` | False | Enable automatic replies to trigger words |
| `trigger_words` | [] | List of words that trigger auto-reply (space-separated). Use underscores for multi-word phrases and `*` wildcards for flexible matching. |
| `trigger_probability` | 1.0 | Probability (0.0-1.0) of responding to trigger words |

#### Trigger Words Wildcard Logic
- `bom_dia`  
  Matches **only** when the message is exactly “bom dia”
- `bom_dia*`  
  Matches messages **starting** with “bom dia”, e.g., “bom dia a todos”
- `*bom_dia*`  
  Matches messages containing “bom dia” anywhere, e.g., “olá bom dia a todos”

### Image Generation Settings
| Setting | Default | Description |
|---------|---------|-------------|
| `image_width` | 1024 | Image width in pixels |
| `image_height` | 1024 | Image height in pixels |
| `image_model` | "flux" | AI model to use for generation |
| `image_enhance` | True | Enable image enhancement |
| `image_nologo` | True | Remove Pollinations watermark |
| `image_private` | True | Make images private |
| `image_safe` | False | Enable safe content filtering |
| `negative_prompt` | "" | What to avoid in generated images |
| `shorten_urls` | True | Use is.gd to shorten image URLs |

## Configuration Examples
### Basic Setup
/msg yourbot config channel #mychannel plugins.Pollinations.prompt "You are a friendly bot assistant."
/msg yourbot config channel #mychannel plugins.Pollinations.context_lines 5

### Auto-Reply Setup
Enable auto-reply
/msg yourbot config channel #mychannel plugins.Pollinations.auto_reply True

Set trigger words (bot will respond when these words appear in messages)
/msg yourbot config channel #mychannel plugins.Pollinations.trigger_words $botnick bom_dia boa_noite

Set probability (50% chance to respond)
/msg yourbot config channel #mychannel plugins.Pollinations.trigger_probability 0.5

### Image Settings
/msg yourbot config channel #mychannel plugins.Pollinations.image_width 512
/msg yourbot config channel #mychannel plugins.Pollinations.image_height 512
/msg yourbot config channel #mychannel plugins.Pollinations.negative_prompt "blurry, low quality"

### Disable URL Shortening
/msg yourbot config channel #mychannel plugins.Pollinations.shorten_urls False

## How It Works
### Text Generation
1. Reads recent channel messages for context (configurable amount)
2. Combines system prompt + context + user input
3. Sends request to Pollinations.ai text API
4. Returns formatted response to channel

### Auto-Reply Feature
1. Monitors all channel messages for configured trigger words
2. When a trigger word is detected, automatically calls the chat function
3. Uses the entire message as input (not just the trigger word)
4. Respects probability setting to avoid spam
5. Supports `$botnick` placeholder to use bot's actual nickname

### Image Generation
1. Takes user prompt and combines with configured parameters
2. Generates image using Pollinations.ai image API
3. Optionally shortens the URL using is.gd
4. Returns image URL to channel

## Requirements
- Limnoria IRC bot
- Python 3.6+
- `requests` library
- Internet connection

## API Usage
This plugin uses the free Pollinations.ai API:
- **Text API**: `https://text.pollinations.ai/`
- **Image API**: `https://pollinations.ai/p/`
No API key required - completely free to use!

## Troubleshooting
### Common Issues
**"Please provide a prompt"**
- You need to include text after the command
- Example: `chat hello` not just `chat`

**"Generated blank image"**
- Try a more detailed prompt
- Check if the prompt might be filtered by safety settings

**Auto-reply not working**
- Ensure `auto_reply` is set to `True`
- Check that `trigger_words` is properly configured
- Verify `trigger_probability` is > 0.0
- Make sure the trigger word appears in the message

**Bot responds to its own messages**
- This shouldn't happen (built-in protection), but if it does, check logs

**Context not working**
- Ensure ChannelLogger plugin is enabled
- Check if log files exist and are readable

### Debug Information
To see current configuration:
/msg yourbot config list plugins.Pollinations

To check if the plugin is loaded:
/msg yourbot list Pollinations


## Contributing
Feel free to submit issues and pull requests on GitHub.

## License
This plugin is released under the same license as Limnoria.

## Credits
- Uses [Pollinations.ai](https://pollinations.ai) API
- Built for [Limnoria](https://github.com/ProgVal/Limnoria) IRC bot
