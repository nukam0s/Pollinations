from supybot import conf, registry

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization("Pollinations")
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

def configure(advanced):
    # This will be called by supybot to configure this module. advanced is
    # a bool that specifies whether the user identified themself as an advanced
    # user or not. You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin("Pollinations", True)

Pollinations = conf.registerPlugin("Pollinations")

conf.registerChannelValue(
    Pollinations,
    "prompt",
    registry.String(
        "You are $botnick the IRC bot. Be brief, helpful",
        _(
            """
            The prompt defining your bot's personality.
            """
        ),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "api_token",
    registry.String(
        "",  
        _("""Pollinations.ai API token (x-enter-token). Leave empty for anonymous access."""),
        private=True,
    ),
)

conf.registerChannelValue(
    Pollinations,
    "reply_intact",
    registry.Boolean(
        False,
        _(
            """
            Get spammy and enable line per line reply...
            """
        ),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "nick_prefix",
    registry.Boolean(
        False,
        _(
            """
            Prefix nick on replies true/false...
            """
        ),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "nick_include",
    registry.Boolean(
        True,
        _(
            """
            Include user nicks in queries.
            """
        ),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "nick_strip",
    registry.Boolean(
        True,
        _(
            """
            Prevent the bot from starting replies with its own nick.
            """
        ),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "text_model",
    registry.String(
        "openai",
        _("""Text models: openai, openai-fast, openai-large, claude, claude-fast, claude-large, gemini, gemini-fast, gemini-large, gemini-search, mistral, grok, deepseek, qwen-coder, perplexity-fast, perplexity-reasoning, midijourney, chickytutor, kimi-k2-thinking, nova-micro"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "context_lines",
    registry.Integer(
        50,
        _("""Number of recent chat lines to use as context (0 to disable)"""),
    ),
)

# Image generation parameters
conf.registerChannelValue(
    Pollinations,
    "image_width",
    registry.Integer(
        1024,
        _("""Image width in pixels"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "image_height", 
    registry.Integer(
        1024,
        _("""Image height in pixels"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "image_model",
    registry.String(
        "flux",
        _("""Image models: flux (default), turbo, zimage, gptimage, gptimage-large, seedream, seedream-pro, kontext, nanobanana, nanobanana-pro"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "image_enhance",
    registry.Boolean(
        True,
        _("""Enhance image quality"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "image_nologo",
    registry.Boolean(
        True,
        _("""Remove watermark/logo"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "image_private",
    registry.Boolean(
        True,
        _("""Private generation"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "image_safe",
    registry.Boolean(
        False,
        _("""Apply safety filters"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "negative_prompt",
    registry.String(
        "",
        _("""Negative prompt (what to avoid in image)"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "shorten_urls",
    registry.Boolean(
        True,
        _("""Shorten image URLs using URL shortener"""),
    ),
)

# Auto-reply configuration
conf.registerChannelValue(
    Pollinations,
    "auto_reply",
    registry.Boolean(
        False,
        _("""Enable automatic replies to trigger words"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "trigger_words",
    registry.SpaceSeparatedListOfStrings(
        [],
        _("""Space-separated list of words that trigger auto-reply"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "trigger_probability",
    registry.Float(
        1.0,
        _("""Probability (0.0-1.0) of responding to trigger words"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "text_timeout",
    registry.Integer(
        10,
        _("""Timeout (s) for text generation requests"""),
    ),
)

conf.registerChannelValue(
    Pollinations,
    "min_reply_interval",
    registry.Integer(
        6,
        _("""Minimum seconds between automatic replies in a channel"""),
    ),
)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
