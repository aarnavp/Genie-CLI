from dotenv import load_dotenv
from google import genai
import os
import sys
import time
import re
from google.genai import Client
from google.genai.errors import ServerError, ClientError

current_file_dir = os.path.dirname(os.path.abspath(__file__))


if current_file_dir not in sys.path:
    sys.path.insert(0, current_file_dir)

from utils.constant_prompts import *
from base import Provider

def _retry_delay(e):
    match = re.search(r'retryDelay.*?(\d+)s', str(e.details))
    return int(match.group(1)) + 1 if match else 30

class GemeniWorker(Provider):
    def __init__(self, name, model):
        self.name = name
        self.model = model.strip()

        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.chat = self.client.chats.create(
            model=self.model,
            config={"system_instruction": STARTING_PROMPT}
        )
        self.total_tokens = 0
        self.requests = 0

    def generate_content_stream(self, prompt):
        for i in range(5):
            try:
                response = self.chat.send_message(message=prompt)
                self.requests += 1
                if response.usage_metadata:
                    self.total_tokens += response.usage_metadata.total_token_count
                yield response.text
                break

            except ServerError as e:
                print(f"\r  \033[33m⚠\033[0m  Retry {i+1}/5: server busy, waiting {2**i}s...")
                time.sleep(2 ** i)

            except ClientError as e:
                if e.code == 429:
                    delay = _retry_delay(e)
                    print(f"\r  \033[33m⚠\033[0m  Retry {i+1}/5: rate limited, waiting {delay}s...")
                    time.sleep(delay)
                else:
                    raise

    def clear_history(self):
        self.chat = self.client.chats.create(
            model=self.model,
            config={"system_instruction": STARTING_PROMPT}
        )
    
    def compact(self):
        return self.chat.send_message(message=COMPACT_PROMPT)
    
    def read(self, prompt):
        for i in range(5):
            try:
                response = self.chat.send_message(message=CONTEXT_PROMPT+prompt)
                self.requests += 1
                if response.usage_metadata:
                    self.total_tokens += response.usage_metadata.total_token_count
                break
            except ClientError as e:
                if e.code == 429:
                    delay = _retry_delay(e)
                    print(f"\r  \033[33m⚠\033[0m  Retry {i+1}/5: rate limited, waiting {delay}s...")
                    time.sleep(delay)
                else:
                    raise
            except ServerError:
                print(f"\r  \033[33m⚠\033[0m  Retry {i+1}/5: server busy, waiting {2**i}s...")
                time.sleep(2 ** i)
    
