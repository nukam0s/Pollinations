# Pollinations Plugin for Limnoria

Use the Pollinations.ai API for text and image generation in your IRC bot.

## Features

- **Text Generation**: Generate text responses using Pollinations.ai text API
- **Image Generation**: Create images from text prompts using Pollinations.ai image API  
- **Context Awareness**: Use recent chat history as context for better responses
- **Configurable**: Extensive configuration options for both text and image generation

## Installation

1. Copy the plugin files to your Limnoria plugins directory
2. Load the plugin: `@load Pollinations`

## Configuration

### Basic Setup

Set up the bot's personality:
```
@config plugins.pollinations.prompt "You are $botnick the IRC bot. Be brief, helpful"
```

### Text Generation Options

Control context usage:
```
@config plugins.pollinations.context_lines 50
```

Response formatting:
```
@config plugins.pollinations.nick_prefix False
@config plugins.pollinations.nick_strip True
@config plugins.pollinations.reply_intact False
```

### Image Generation Options

Set default image dimensions:
```
@config plugins.pollinations.image_width 1024
@config plugins.pollinations.image_height 1024
```

Choose image model:
```
@config plugins.pollinations.image_model flux
```

Image enhancements:
```
@config plugins.pollinations.image_enhance True
@config plugins.pollinations.image_nologo True
@config plugins.pollinations.image_private True
@config plugins.pollinations.image_safe False
```

URL shortening:
```
@config plugins.pollinations.shorten_urls True
```

### View All Options

```
@config list plugins.pollinations
```

## Usage

### Text Generation
```
@chat Hello, how are you today?
```

### Image Generation
```
@image a beautiful sunset over the ocean
```

### Automatic Responses

Set up automatic replies to mentions:
```
@messageparser add "(?i)(.*BOT_NICK_HERE.*)" "chat $1"
```

Replace `BOT_NICK_HERE` with your bot's nick.

You might also want to disable default nick responses:
```
@config reply.whenaddressedby.nick False
```

## Dependencies

- requests
- supybot/limnoria

## License
