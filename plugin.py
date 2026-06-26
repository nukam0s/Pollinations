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
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import threading
from supybot import ircmsgs

_ = PluginInternationalization("Pollinations")

class Pollinations(callbacks.Plugin):
    """Use the Pollinations.ai API for text and image generation"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Pollinations, self)
        self.__parent.__init__(irc)
        self.session = requests.Session()
        retry_strategy = Retry(total=4, backoff_factor=1, status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.max_workers = 10
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self.pending = 0
        self.pending_lock = threading.Lock()
        self.max_pending = 10  
        self.last_reply_time = {}
        self.cleanup_interval = 3600
        self.last_cleanup = time.time()
        self.context_cache = {}
        self.context_cache_ttl = 90
        self.active_requests = threading.Semaphore(5)

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
        min_interval = self.registryValue("min_reply_interval", msg.channel)
        now = time.time()
        last = self.last_reply_time.get(msg.channel, 0)
        if now - last < min_interval:
            return
        if now - self.last_cleanup > self.cleanup_interval:
            cutoff = now - self.cleanup_interval
            self.last_reply_time = {k: v for k, v in self.last_reply_time.items() if v > cutoff}
            self.last_cleanup = now
        for word in trigger_words:
            processed_word = word.replace("_", " ").replace("$botnick", irc.nick)
            if word.startswith('*') and word.endswith('*'):
                pattern = re.escape(processed_word.strip('*'))
            elif word.endswith('*'):
                pattern = r'^' + re.escape(processed_word.rstrip('*'))
            elif word.startswith('*'):
                pattern = re.escape(processed_word.lstrip('*')) + r'$'
            else:
                pattern = r'^' + re.escape(processed_word) + r'$'
            if re.search(pattern, message, re.IGNORECASE):
                probability = self.registryValue("trigger_probability", msg.channel)
                if random.random() <= probability:
                    with self.pending_lock:
                        if self.pending >= self.max_pending:
                            return
                        self.pending += 1
                    def _run():
                        if not self.active_requests.acquire(blocking=False):
                            with self.pending_lock:
                                self.pending -= 1
                            return
                        try:
                            text = message
                            prefix = irc.nick + " "
                            if text.lower().startswith(prefix.lower()):
                                text = text[len(prefix):].strip()
                            self._chat(irc, msg, text)
                        finally:
                            with self.pending_lock:
                                self.pending -= 1
                            self.active_requests.release()
                    self.executor.submit(_run)
                    break
    
    @staticmethod
    def tail_lines(path, n):
        try:
            with open(path, "rb") as f:
                f.seek(0, 2)
                size = f.tell()

                block_size = n * 150
                max_size = 524288  # 512KB max

                if size > max_size:
                    size = max_size
                
                if size < block_size:
                    f.seek(0)
                else:
                    f.seek(size - block_size)
                    f.readline()  
                
                lines = [line.decode("utf-8", errors="ignore").rstrip() for line in f]
                return lines[-n:] if len(lines) > n else lines
        except Exception:
            return []
    
    def _read_context(self, irc, channel, context_lines):
        try:
            start_time = time.time()
            timeout = 3.5  # 1.5 segundos max
            log_dir = conf.supybot.directories.log()
            network = irc.network
            channel_lower = channel.lower()
            log_path = os.path.join(log_dir, "ChannelLogger", network, channel_lower, f"{channel_lower}.log")
            
            if not os.path.exists(log_path):
                return ""
            
            if time.time() - start_time > timeout:
                return ""
            recent = self.tail_lines(log_path, context_lines)
            chat_lines = []
            for line in recent:
                if "<" in line and ">" in line:
                    parts = line.split(">", 1)
                    if len(parts) == 2:
                        nick_part = parts[0].split("<")[-1]
                        message_part = parts[1].strip()
                        if nick_part and message_part:
                            chat_lines.append(f"{nick_part}: {message_part}")
            return "\n".join(chat_lines[-context_lines:])
        except Exception:
            return ""
    
    def _chat(self, irc, msg, text):
        channel = msg.channel if irc.isChannel(msg.channel) else msg.nick
        try:
            if self.registryValue("nick_include", msg.channel):
                text = "%s: %s" % (msg.nick, text)
            
            prompt = self.registryValue("prompt", msg.channel).replace("$botnick", irc.nick)
            context_lines = self.registryValue("context_lines", msg.channel)
            context = ""
            
            if context_lines > 0:
                cache_key = msg.channel
                now = time.time()
                
                if cache_key in self.context_cache:
                    cached_time, cached_context = self.context_cache[cache_key]
                    if now - cached_time < self.context_cache_ttl:
                        context = cached_context
                    else:
                        context = self._read_context(irc, channel, context_lines)
                        self.context_cache[cache_key] = (now, context)
                else:
                    context = self._read_context(irc, channel, context_lines)
                    self.context_cache[cache_key] = (now, context)
            
            timeout = self.registryValue("text_timeout", msg.channel) 
            text_model = self.registryValue("text_model", msg.channel) 
            api_token = self.registryValue("api_token", msg.channel)

            # Construir mensagens para o novo formato
            messages = [
                {"role": "system", "content": prompt}
            ]

            if context:
                messages.append({"role": "system", "content": f"Recent conversation:\n{context}"})

            messages.append({"role": "user", "content": text})

            payload = {
                "messages": messages,
                "model": text_model,
                "jsonMode": False

            }
            headers = {"Content-Type": "application/json"}

            
            if api_token:
                headers["Authorization"] = f"Bearer {api_token}"

            
            response = self.session.post(
                "https://gen.pollinations.ai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    choice = data.get("choices", [{}])[0]
                    finish_reason = choice.get("finish_reason", "")
                    
                    # Verifica se foi filtrado
                    if finish_reason == "content_filter":
                        filter_results = choice.get("content_filter_results", {})
                        filtered_categories = [k for k, v in filter_results.items() if isinstance(v, dict) and v.get("filtered")]
                        if filtered_categories:
                            irc.reply(f"Response filtered by content policy ({', '.join(filtered_categories)})", prefixNick=False)
                        else:
                            irc.reply("Response filtered by content policy", prefixNick=False)
                        return
                    
                    content = choice.get("message", {}).get("content", "").strip()
                except (ValueError, KeyError, IndexError) as e:
                    self.log.error(f"Parse error: {e}")
                    irc.reply("Failed to parse API response", prefixNick=False)
                    return
                
                if not content or len(content) < 3:
                    irc.reply("No response generated", prefixNick=False)
                    return
                
                if self.registryValue("nick_strip", msg.channel):
                    content = re.sub(r"^%s: " % (irc.nick), "", content)
                
                prefix = self.registryValue("nick_prefix", msg.channel)
                if self.registryValue("reply_intact", msg.channel):
                    for line in content.splitlines():
                        if line:
                            text = f"{msg.nick}: {line}" if prefix else line
                            irc.queueMsg(ircmsgs.privmsg(channel, text))
                else:
                    response_text = " ".join(content.splitlines())
                    text = f"{msg.nick}: {response_text}" if prefix else response_text
                    irc.reply(text, prefixNick=False, to=channel)
                
                self.last_reply_time[msg.channel] = time.time()
                return
            else:
                irc.reply(f"API Error {response.status_code}", prefixNick=False)
                return
        
        except requests.exceptions.Timeout:
            irc.reply("Request timed out.", prefixNick=False)
            return
        except requests.exceptions.RequestException as e:
            self.log.warning(f"Network error: {repr(e)}")
            irc.reply("Network error.", prefixNick=False)
            return
        except Exception as e:
            self.log.error(f"Unexpected error in _chat: {repr(e)}")
            irc.reply("Unexpected error.", prefixNick=False)
            return

    def chat(self, irc, msg, args, text):
        """Public command wrapper for _chat"""
        self._chat(irc, msg, text)

    chat = wrap(chat, ["text"])

    def image(self, irc, msg, args, text):
        """Generate image from text prompt using Pollinations.ai"""
        if not text.strip():
            irc.reply("Please provide a prompt", prefixNick=False)
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
            response = self.session.get(image_url, timeout=15, allow_redirects=True)
            self.log.info(f"Response status: {response.status_code}, Content-Type: {response.headers.get('Content-Type', 'unknown')}")
            
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if content_type.startswith("image/"):
                    final_url = response.url
                    if shorten_urls:
                        try:
                            shorten_response = self.session.post(
                                "https://is.gd/create.php",
                                data={"format": "simple", "url": final_url},
                                timeout=5,
                            )
                            if shorten_response.status_code == 200:
                                final_url = shorten_response.text.strip()
                        except Exception as e:
                            self.log.warning(f"URL shortener failed: {e}")
                    irc.reply(final_url, prefixNick=False)
                else:
                    irc.reply("Generated invalid image, try different prompt", prefixNick=False)
            else:
                irc.reply(f"Error: {response.status_code}", prefixNick=False)
        except requests.exceptions.Timeout:
            irc.reply("Request timed out", prefixNick=False)
        except requests.exceptions.RequestException as e:
            self.log.warning(f"Network error in image(): {repr(e)}")
            irc.reply("Network error", prefixNick=False)
        except Exception as e:
            self.log.error(f"Error in image(): {repr(e)}")
            irc.reply("Error generating image", prefixNick=False)


    image = wrap(image, ["text"])

    def die(self):
        try:
            self.executor.shutdown(wait=True, timeout=5)
        except Exception:
            pass
        self.__parent.die()

Class = Pollinations


