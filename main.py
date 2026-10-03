import os
import sys
import warnings
from dotenv import load_dotenv

# Suppress minor SDK notifications
warnings.filterwarnings("ignore", category=UserWarning)

from google import genai

# Load environment variables from .env file
load_dotenv()

# Verify API key
if not os.getenv("GEMINI_API_KEY"):
    print("Error: GEMINI_API_KEY not found in environment or .env file.")
    sys.exit(1)

# Initialize the GenAI Client
client = genai.Client()

# Generate content with Gemma 4 26B
response = client.models.generate_content(
    model="gemma-4-26b-a4b-it",
    contents="Roses are red...",
)

print(response.text)
