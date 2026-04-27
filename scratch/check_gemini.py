import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

try:
    client = genai.Client(api_key=api_key)
    print("Listing models...")
    for m in client.models.list():
        if "gemini" in m.name.lower():
            print(f"Model: {m.name}, Actions: {m.supported_actions}")
except Exception as e:
    print(f"Error: {e}")
