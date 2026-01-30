import os
from dotenv import load_dotenv

def load_env() -> None:
    """Load environment variables from a local .env file (if present)."""
    load_dotenv()

def get_openai_key() -> str | None:
    """Return the OpenAI API key from environment variables."""
    return os.getenv("OPENAI_API_KEY")