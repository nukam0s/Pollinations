# Pollinations Plugin for Limnoria
A Limnoria IRC bot plugin that integrates with [Pollinations.ai](https://pollinations.ai) for AI-powered text generation and image creation.

## Features
- **Text Generation**: Generate AI responses using chat context via the unified gen.pollinations.ai API
- **Image Generation**: Create images from text prompts
- **Auto-Reply**: Automatically respond to trigger words in channel
- **Context Awareness**: Uses recent channel conversation for better responses
- **Highly Configurable**: Multiple settings for customization
- **URL Shortening**: Optional shortened URLs for generated images

## Installation
1. Download the plugin files to your Limnoria plugins directory
2. Load the plugin: `/msg yourbot load Pollinations`
3. Configure your API token (required for text generation)
4. Configure other plugin settings as needed

## Commands
### Text Generation
```
chat <prompt>
```
Generate AI text responses. The bot can use recent channel conversation as context.  
**Examples:**
```
chat Explain quantum physics simply
chat What do you think about the previous discussion?
```

### Image Generation
```
image <prompt>
```
Generate images from text descriptions.  
**Examples:**
```
image beautiful sunset over mountains
image cute cat playing with yarn
image cyberpunk city at night
image realistic portrait of a medieval knight
```

## Configuration
All settings can be configured per-channel using:
```
/msg yourbot config channel #yourchannel plugins.Pollinations.<setting> <value>
```

### Text Generation Settings
| Setting | Default | Description |
|---------|---------|-------------|
| `api_token` | "" | **Required** - Pollinations.ai API token from auth.pollinations.ai |
| `prompt` | "You are $botnick the IRC bot. Be brief, helpful" | System prompt for the AI ($botnick = bot's nickname) |
| `text_model` | "openai" | AI model: openai (GPT-4o), claude (Claude Sonnet), mistral, llama |
| `text_timeout` | 10 | Timeout in seconds for text generation requests |
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
| `min_reply_interval` | 6 | Minimum seconds between automatic replies in a channel |

#### Trigger Words Wildcard Logic
- `good_morning`  
  Matches **only** when the message is exactly "good morning"
- `good_morning*`  
  Matches messages **starting** with "good morning", e.g., "good morning all"
- `*good_morning*`  
  Matches messages containing "good morning" anywhere, e.g., "hello good morning everyone"
- `*$botnick*`  
  Matches messages containing the bot nickname anywhere

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

### API Token Setup (Required)
Get your API token from [auth.pollinations.ai](https://auth.pollinations.ai), then configure it:
```
# Global configuration
/msg yourbot config plugins.Pollinations.api_token your_token_here

# Or per-channel
/msg yourbot config channel #mychannel plugins.Pollinations.api_token your_token_here
```

### Basic Setup
```
/msg yourbot config channel #mychannel plugins.Pollinations.prompt "You are a friendly bot assistant."
/msg yourbot config channel #mychannel plugins.Pollinations.context_lines 25
/msg yourbot config channel #mychannel plugins.Pollinations.text_model claude
```

### Auto-Reply Setup
Enable auto-reply:
```
/msg yourbot config channel #mychannel plugins.Pollinations.auto_reply True
```

Set trigger words (bot will respond when these words appear in messages):
```
/msg yourbot config channel #mychannel plugins.Pollinations.trigger_words $botnick bom_dia boa_noite
```

Set probability (50% chance to respond):
```
/msg yourbot config channel #mychannel plugins.Pollinations.trigger_probability 0.5
```

### Image Settings
```
/msg yourbot config channel #mychannel plugins.Pollinations.image_width 512
/msg yourbot config channel #mychannel plugins.Pollinations.image_height 512
/msg yourbot config channel #mychannel plugins.Pollinations.negative_prompt "blurry, low quality"
```

### Disable URL Shortening
```
/msg yourbot config channel #mychannel plugins.Pollinations.shorten_urls False
```

## How It Works

### Text Generation
1. Reads recent channel messages for context (configurable amount)
2. Constructs a chat conversation with system prompt + context + user input
3. Sends POST request to Pollinations.ai unified API with authentication
4. Parses JSON response and extracts AI-generated content
5. Returns formatted response to channel

### Auto-Reply Feature
1. Monitors all channel messages for configured trigger words
2. When a trigger word is detected, automatically calls the chat function
3. Uses the entire message as input (not just the trigger word)
4. Respects probability setting and minimum reply interval to avoid spam
5. Supports `$botnick` placeholder to use bot's actual nickname
6. Limits concurrent requests to prevent overload

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
- Pollinations.ai API token (get from [auth.pollinations.ai](https://auth.pollinations.ai))

## API Usage
This plugin uses the Pollinations.ai API:
- **Text API**: `https://gen.pollinations.ai/v1/chat/completions` (unified API)
- **Image API**: `https://image.pollinations.ai/prompt/`

**Authentication**: API token required for text generation. Get yours at [auth.pollinations.ai](https://auth.pollinations.ai)

**Available Models**:
- Text: `openai` (GPT-4o), `claude` (Claude Sonnet), `mistral`, `llama`
- Image: `flux` (default), `turbo`

## Troubleshooting

### Common Issues

**"API Error 401" or "UNAUTHORIZED"**
- You need to configure your API token
- Get token from [auth.pollinations.ai](https://auth.pollinations.ai)
- Set it: `/msg yourbot config plugins.Pollinations.api_token your_token_here`

**"API Error 400" with model error**
- Invalid model name for the unified API
- Use: `openai`, `claude`, `mistral`, or `llama`
- Set it: `/msg yourbot config plugins.Pollinations.text_model openai`

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
- Check that `min_reply_interval` hasn't been triggered recently
- Make sure the trigger word appears in the message

**Bot responds to its own messages**
- This shouldn't happen (built-in protection), but if it does, check logs

**Context not working**
- Ensure ChannelLogger plugin is enabled
- Check if log files exist and are readable

**Request timeout or ping timeout**
- Default timeout is 10 seconds
- Reduce `context_lines` if context reading is slow
- Check `min_reply_interval` to reduce auto-reply frequency
- The plugin limits concurrent requests to prevent overload

### Debug Information

To see current configuration:
```
/msg yourbot config list plugins.Pollinations
```

To check if the plugin is loaded:
```
/msg yourbot list Pollinations
```

To reload the plugin after changes:
```
/msg yourbot reload Pollinations
```

## Performance & Stability

The plugin includes several safeguards to prevent IRC ping timeouts:
- **Request limiting**: Maximum 5 concurrent text generation requests
- **Timeouts**: 10-second default timeout for API requests
- **Thread management**: Controlled shutdown of background threads
- **Rate limiting**: Minimum interval between auto-replies per channel

## Contributing
Feel free to submit issues and pull requests on GitHub.

## License
This plugin is released under the same license as Limnoria.

## Credits
- Uses [Pollinations.ai](https://pollinations.ai) API
- Built for [Limnoria](https://github.com/ProgVal/Limnoria) IRC bot
