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
        retry_strategy = Retry(total=2, backoff_factor=1, status_forcelist=[502, 503, 504])
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
        self.context_cache_ttl = 30

    def doPrivmsg(self, irc, msg):
        def _process():
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
                            try:
                                text = message
                                prefix = irc.nick + " "
                                if text.lower().startswith(prefix.lower()):
                                    text = text[len(prefix):].strip()
                                self._chat(irc, msg, text)
                            finally:
                                with self.pending_lock:
                                    self.pending -= 1
                        self.executor.submit(_run)
                        break
        
        thread = threading.Thread(target=_process)
        thread.daemon = True
        thread.start()
    
    @staticmethod
    def tail_lines(path, n):
        """Lê últimas N linhas de forma eficiente"""
        try:
            with open(path, "rb") as f:
                # Vai para o fim
                f.seek(0, 2)
                size = f.tell()
                
                # Estima 150 bytes por linha (média IRC)
                block_size = n * 150
                
                if size < block_size:
                    # Ficheiro pequeno, lê tudo
                    f.seek(0)
                else:
                    # Lê só o necessário
                    f.seek(size - block_size)
                    f.readline()  # descarta linha parcial
                
                lines = [line.decode("utf-8", errors="ignore").rstrip() for line in f]
                return lines[-n:] if len(lines) > n else lines
        except Exception:
            return []
    
    def _read_context(self, irc, channel, context_lines):
        """Lê contexto do log do canal"""
        try:
            log_dir = conf.supybot.directories.log()
            network = irc.network
            channel_lower = channel.lower()
            log_path = os.path.join(log_dir, "ChannelLogger", network, channel_lower, f"{channel_lower}.log")
            
            if not os.path.exists(log_path):
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
                
                # Verifica cache
                if cache_key in self.context_cache:
                    cached_time, cached_context = self.context_cache[cache_key]
                    if now - cached_time < self.context_cache_ttl:
                        context = cached_context
                    else:
                        # Cache expirado, lê novamente
                        context = self._read_context(irc, channel, context_lines)
                        self.context_cache[cache_key] = (now, context)
                else:
                    # Primeira vez, lê e guarda
                    context = self._read_context(irc, channel, context_lines)
                    self.context_cache[cache_key] = (now, context)
            
            if context:
                full_prompt = f"{prompt}\n\nRecent conversation:\n{context}\n\nUser: {text}\nAssistant:"
            else:
                full_prompt = f"{prompt}\n\nUser: {text}\nAssistant:"
            
            timeout = self.registryValue("text_timeout", msg.channel)
            # --> NOVO: Obtém o modelo de texto do registro
            text_model = self.registryValue("text_model", msg.channel) 
            
            # --> MODIFICADO: Constrói a URL da API incluindo o parâmetro 'model'
            api_url = f"https://text.pollinations.ai/{requests.utils.quote(full_prompt)}?model={requests.utils.quote(text_model)}"

            response = self.session.get(
                api_url,
                timeout=timeout
            )
            
            if response.status_code == 200:
                content = response.text.strip()
                if not content or len(content) < 3:
                    # CORRIGIDO: usa 'channel'
                    irc.queueMsg(ircmsgs.privmsg(channel, "Pollinations returned empty response")) 
                    return
                
                if self.registryValue("nick_strip", msg.channel):
                    content = re.sub(r"^%s: " % (irc.nick), "", content)
                
                prefix = self.registryValue("nick_prefix", msg.channel)
                if self.registryValue("reply_intact", msg.channel):
                    for line in content.splitlines():
                        if line:
                            text = f"{msg.nick}: {line}" if prefix else line
                            # CORRIGIDO: usa 'channel'
                            irc.queueMsg(ircmsgs.privmsg(channel, text))
                else:
                    response_text = " ".join(content.splitlines())
                    text = f"{msg.nick}: {response_text}" if prefix else response_text
                    # CORRIGIDO: usa 'channel'
                    irc.queueMsg(ircmsgs.privmsg(channel, text))
                
                self.last_reply_time[msg.channel] = time.time()
                return
            else:
                # CORRIGIDO: usa 'channel'
                irc.queueMsg(ircmsgs.privmsg(channel, f"API Error {response.status_code}"))
                return
        
        except requests.exceptions.Timeout:
            # CORRIGIDO: usa 'channel'
            irc.queueMsg(ircmsgs.privmsg(channel, "Request timed out."))
            return
        except requests.exceptions.RequestException as e:
            self.log.warning(f"Network error: {repr(e)}")
            # CORRIGIDO: usa 'channel'
            irc.queueMsg(ircmsgs.privmsg(channel, "Network error."))
            return
        except Exception as e:
            self.log.error(f"Unexpected error in _chat: {repr(e)}")
            # CORRIGIDO: usa 'channel'
            irc.queueMsg(ircmsgs.privmsg(channel, "Unexpected error."))
            return

    def chat(self, irc, msg, args, text):
        """Public command wrapper for _chat"""
        self._chat(irc, msg, text)

    chat = wrap(chat, ["text"])

    def image(self, irc, msg, args, text):
        """Generate image from text prompt using Pollinations.ai"""
        if not text.strip():
            irc.queueMsg(ircmsgs.privmsg(msg.channel, "Please provide a prompt"))
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
                    irc.queueMsg(ircmsgs.privmsg(msg.channel, final_url))
                else:
                    irc.queueMsg(ircmsgs.privmsg(msg.channel, "Generated invalid image, try different prompt"))
            else:
                irc.queueMsg(ircmsgs.privmsg(msg.channel, f"Error: {response.status_code}"))
        except requests.exceptions.Timeout:
            irc.queueMsg(ircmsgs.privmsg(msg.channel, "Request timed out"))
        except requests.exceptions.RequestException as e:
            self.log.warning(f"Network error in image(): {repr(e)}")
            irc.queueMsg(ircmsgs.privmsg(msg.channel, "Network error"))
        except Exception as e:
            self.log.error(f"Error in image(): {repr(e)}")
            irc.queueMsg(ircmsgs.privmsg(msg.channel, "Error generating image"))


    image = wrap(image, ["text"])

    def die(self):
        try:
            self.executor.shutdown(wait=False)
        except Exception:
            pass
        self.__parent.die()

Class = Pollinations


