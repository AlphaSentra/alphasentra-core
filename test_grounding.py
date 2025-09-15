import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file.")

from google import genai

client = genai.Client()  # the API key is loaded from the environment variable

MODEL_ID = "gemini-2.5-flash"

print(f"Using API key: {api_key[:6]}...")

response = client.models.generate_content(
    model=MODEL_ID,
    contents='What is the current price of ASX: BHP as of September 15, 2025?',
    config={"tools": [{"google_search": {}}]},
)

# Print the response
print(f"\nResponse:\n{response.text}")