from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"

def load_prompt(relative_path: str) -> str:
    """
    Load a prompt text file from /prompts.
    Example: load_prompt("system/base_system.txt")
    """
    path = PROMPTS_DIR / relative_path
    return path.read_text(encoding="utf-8")