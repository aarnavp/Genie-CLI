from dotenv import load_dotenv
from google import genai
from google.genai.errors import ClientError, ServerError
import os
import time

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
chat = client.chats.create(model="gemini-2.5-flash")

def send(label, message):
    print(f"\n[{label}] Sending: {message[:60]!r}")
    for i in range(5):
        try:
            response = chat.send_message(message=message)
            print(f"[{label}] OK: {response.text[:80]!r}")
            return response.text
        except ClientError as e:
            if e.code == 429:
                print(f"[{label}] 429 on attempt {i+1}/5 — waiting 30s...")
                time.sleep(30)
            else:
                print(f"[{label}] ClientError {e.code}: {e.message}")
                raise
        except ServerError as e:
            print(f"[{label}] ServerError on attempt {i+1}/5 — waiting {2**i}s...")
            time.sleep(2 ** i)

send("init", "You are a helpful assistant. Reply with OK.")
send("msg1", "Say the number 1.")
send("msg2", "Say the number 2.")
send("msg3", "Say the number 3.")

print("\nDone.")
