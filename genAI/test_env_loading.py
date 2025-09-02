import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load AI_MODEL_PROMPTS from environment variable
AI_MODEL_PROMPTS_JSON = os.getenv("AI_MODEL_PROMPTS")
print("AI_MODEL_PROMPTS_JSON loaded:", AI_MODEL_PROMPTS_JSON is not None)

if AI_MODEL_PROMPTS_JSON:
    try:
        AI_MODEL_PROMPTS = json.loads(AI_MODEL_PROMPTS_JSON)
        print("JSON parsing successful!")
        print("Keys in AI_MODEL_PROMPTS:", list(AI_MODEL_PROMPTS.keys()))
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        print("First 100 characters of AI_MODEL_PROMPTS_JSON:")
        print(AI_MODEL_PROMPTS_JSON[:100])
else:
    print("AI_MODEL_PROMPTS not found in environment variables")