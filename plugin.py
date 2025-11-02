from supybot import utils, plugins, ircutils, callbacks, conf
from supybot.commands import *
from supybot.i18n import PluginInternationalization
import re
import requests
import random
import time
import os
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

_ = PluginInternationalization("Pollinations")

class Pollinations(callbacks.Plugin):
    """Use the Pollinations.ai API for text and image generation"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Pollinations, self)
        self.__parent.__init__(irc)
        # Criar session HTTP reutilizável
        self.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=1,
            status_forcelist=[502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def doPrivmsg(self, irc, msg):
        if not irc.isChannel(msg.channel):
            return
        if not self.registryValue("auto_reply", msg.channel):
            return
        if msg.nick == irc.nick:
            return
        trigger_words = self.registryValue("trigger_words", msg.channel)
        if not trigger_words:
            return
        message = msg.args[1]
        for word in trigger_words:
            processed_word = word.replace("_", " ").replace("$botnick", irc.nick)
            
            if word.startswith('*') and word.endswith('*'):
                # Match em qualquer parte: *palavra*
                pattern = re.escape(processed_word.strip('*'))
            elif word.endswith('*'):
                # Match no início: palavra*
                pattern = r'^' + re.escape(processed_word.rstrip('*'))
            elif word.startswith('*'):
                # Match no fim: *palavra
                pattern = re.escape(processed_word.lstrip('*')) + r'$'
            else:
                # Match exato
                pattern = r'^' + re.escape(processed_word) + r'$'
            
            if re.search(pattern, message, re.IGNORECASE):
                probability = self.registryValue("trigger_probability", msg.channel)
                if random.random() <= probability:
                    text = message
                    prefix = irc.nick + " "
                    if text.lower().startswith(prefix.lower()):
                        text = text[len(prefix):].strip()
                    self._chat(irc, msg, text)
                    break



    def _chat(self, irc, msg, text):
        """Internal helper for Pollinations text generation"""
        channel = msg.channel if irc.isChannel(msg.channel) else msg.nick

        max_retries = 3
        base_delay = 3  # segundos

        for attempt in range(max_retries):
            try:
                if self.registryValue("nick_include", msg.channel):
                    text = "%s: %s" % (msg.nick, text)

                prompt = self.registryValue("prompt", msg.channel).replace("$botnick", irc.nick)
                context_lines = self.registryValue("context_lines", msg.channel)
                context = ""

                if context_lines > 0:
                    try:
                        log_dir = conf.supybot.directories.log()
                        network = irc.network
                        channel_lower = channel.lower()
                        log_path = os.path.join(log_dir, "ChannelLogger", network, channel_lower, f"{channel_lower}.log")

                        if os.path.exists(log_path):
                            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                                lines = f.readlines()
                                recent_lines = lines[-context_lines-1:-1]
                                chat_lines = []
                                for line in recent_lines:
                                    if "<" in line and ">" in line:
                                        parts = line.split(">", 1)
                                        if len(parts) == 2:
                                            nick_part = parts[0].split("<")[-1]
                                            message_part = parts[1].strip()
                                            if nick_part and message_part:
                                                chat_lines.append(f"{nick_part}: {message_part}")
                                context = "\n".join(chat_lines[-context_lines:])
                    except Exception:
                        pass

                if context:
                    full_prompt = f"{prompt}\n\nRecent conversation:\n{context}\n\nUser: {text}\nAssistant:"
                else:
                    full_prompt = f"{prompt}\n\nUser: {text}\nAssistant:"

                response = self.session.get(
                    f"https://text.pollinations.ai/{requests.utils.quote(full_prompt)}",
                    timeout=20
                )

                if response.status_code == 200:
                    content = response.text.strip()
                    if not content or len(content) < 3:
                        if attempt < max_retries - 1:
                            time.sleep(base_delay * (2 ** attempt))  # backoff exponencial
                            continue
                        else:
                            irc.reply("Pollinations returned empty response")
                            return

                    if self.registryValue("nick_strip", msg.channel):
                        content = re.sub(r"^%s: " % (irc.nick), "", content)

                    prefix = self.registryValue("nick_prefix", msg.channel)

                    if self.registryValue("reply_intact", msg.channel):
                        for line in content.splitlines():
                            if line:
                                irc.reply(line, prefixNick=prefix)
                    else:
                        response_text = " ".join(content.splitlines())
                        irc.reply(response_text, prefixNick=prefix)
                    return

                elif response.status_code == 502:
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                        continue
                    else:
                        irc.reply("Pollinations API is temporarily unavailable (502). Try again later.")
                        return

                else:
                    if attempt < max_retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
                        continue
                    else:
                        irc.reply(f"API Error {response.status_code}")
                        return

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                else:
                    irc.reply("Request timed out.")
                    return

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue
                else:
                    irc.reply(f"Network error: {str(e)}")
                    return

            except Exception as e:
                irc.reply(f"Unexpected error: {str(e)}")
                return

    def chat(self, irc, msg, args, text):
        """Public command wrapper for _chat"""
        self._chat(irc, msg, text)

    chat = wrap(chat, ["text"])

    def image(self, irc, msg, args, text):
        """Generate image from text prompt using Pollinations.ai"""
        if not text.strip():
            irc.reply("Please provide a prompt")
            return
        
        width = self.registryValue("image_width", msg.channel)
        height = self.registryValue("image_height", msg.channel)
        model = self.registryValue("image_model", msg.channel)
        enhance = self.registryValue("image_enhance", msg.channel)
        nologo = self.registryValue("image_nologo", msg.channel)
        private = self.registryValue("image_private", msg.channel)
        safe = self.registryValue("image_safe", msg.channel)
        negative_prompt = self.registryValue("negative_prompt", msg.channel)
        shorten_urls = self.registryValue("shorten_urls", msg.channel)
        
        seed = random.randint(1, 1000000)
        
        params = {
            "width": width,
            "height": height,
            "seed": seed,
            "model": model,
            "enhance": str(enhance).lower(),
            "nologo": str(nologo).lower(),
            "private": str(private).lower(),
            "safe": str(safe).lower(),
        }
        
        if negative_prompt.strip():
            params["negative_prompt"] = negative_prompt
        
        param_string = "&".join([f"{k}={requests.utils.quote(str(v))}" for k, v in params.items()])
        image_url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(text)}?{param_string}"
        
        try:
            self.log.info(f"Requesting image URL: {image_url[:150]}...")
            response = self.session.get(image_url, timeout=25, allow_redirects=True)
            self.log.info(f"Response status: {response.status_code}, Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if content_type.startswith("image/"):
                    final_url = response.url  # URL final após redirects
                    if shorten_urls:
                        try:
                            shorten_response = self.session.post(
                                "https://is.gd/create.php",
                                data={"format": "simple", "url": final_url},
                                timeout=10,
                            )
                            if shorten_response.status_code == 200:
                                final_url = shorten_response.text.strip()
                        except Exception as e:
                            self.log.warning(f"URL shortener failed: {e}")
                    irc.reply(final_url)
                else:
                    irc.reply("Generated invalid image, try different prompt")
            else:
                irc.reply(f"Error: {response.status_code}")
        except requests.exceptions.Timeout:
            irc.reply("Request timed out")
        except requests.exceptions.RequestException as e:
            irc.reply(f"Network error: {str(e)}")
        except Exception as e:
            irc.reply(f"Error: {str(e)}")

    image = wrap(image, ["text"])

Class = Pollinations

