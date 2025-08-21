# Pollinations Plugin for Limnoria

A Limnoria IRC bot plugin that integrates with [Pollinations.ai](https://pollinations.ai) for AI-powered text generation and image creation.

## Features

- **Text Generation**: Generate AI responses using chat context
- **Image Generation**: Create images from text prompts
- **Context Awareness**: Uses recent channel conversation for better responses
- **Highly Configurable**: Multiple settings for customization
- **URL Shortening**: Optional shortened URLs for generated images

## Installation

1. Download the plugin files to your Limnoria plugins directory
2. Load the plugin: `/msg yourbot load Pollinations`
3. Configure the plugin settings as needed

## Commands

### Text Generation
```
chat <prompt>
```
Generate AI text responses. The bot can use recent channel conversation as context.

**Examples:**
```
chat How's the weather today?
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
| `prompt` | "You are a helpful AI assistant in an IRC channel." | System prompt for the AI |
| `context_lines` | 10 | Number of recent messages to include as context |
| `nick_include` | True | Include user's nickname in the prompt |
| `nick_strip` | True | Remove bot's nickname from responses |
| `nick_prefix` | True | Prefix responses with user's nickname |
| `reply_intact` | False | Send multi-line responses as separate messages |

### Image Generation Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `image_width` | 1024 | Image width in pixels |
| `image_height` | 1024 | Image height in pixels |
| `image_model` | "flux" | AI model to use for generation |
| `image_enhance` | True | Enable image enhancement |
| `image_nologo` | True | Remove Pollinations watermark |
| `image_private` | False | Make images private |
| `image_safe` | True | Enable safe content filtering |
| `negative_prompt` | "" | What to avoid in generated images |
| `shorten_urls` | True | Use is.gd to shorten image URLs |

## Configuration Examples

### Basic Setup
```
/msg yourbot config channel #mychannel plugins.Pollinations.prompt "You are a friendly bot assistant."
/msg yourbot config channel #mychannel plugins.Pollinations.context_lines 5
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
2. Combines system prompt + context + user input
3. Sends request to Pollinations.ai text API
4. Returns formatted response to channel

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

**Timeout errors**
- The API might be slow or unavailable
- Try again in a few moments

**Context not working**
- Ensure ChannelLogger plugin is enabled
- Check if log files exist and are readable

### Debug Information

To see current configuration:
```
/msg yourbot config list plugins.Pollinations
```

To check if the plugin is loaded:
```
/msg yourbot list Pollinations
```

## Contributing

Feel free to submit issues and pull requests on GitHub.

## License

This plugin is released under the same license as Limnoria.

## Credits

- Uses [Pollinations.ai](https://pollinations.ai) API
- Built for [Limnoria](https://github.com/ProgVal/Limnoria) IRC bot
