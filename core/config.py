import os
from dotenv import load_dotenv


def load_env() -> None:
    """Load environment variables from a local .env file (if present)."""
    load_dotenv()


def get_openai_key() -> str | None:
    """Return the OpenAI API key from environment variables."""
    return os.getenv("OPENAI_API_KEY")


def get_bool_env(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable with a conservative fallback."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_max_model_upload_bytes() -> int:
    """Return the configured model-file upload limit in bytes."""
    raw_value = os.getenv("MAX_STL_UPLOAD_MB", "25")
    try:
        megabytes = int(raw_value)
    except ValueError:
        megabytes = 25
    return max(1, megabytes) * 1024 * 1024


def get_max_stl_upload_bytes() -> int:
    """Backwards-compatible alias for the model-file upload limit."""
    return get_max_model_upload_bytes()


def get_cors_origins() -> list[str]:
    """Return the comma-separated browser origins allowed to call the API."""
    raw_value = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]
