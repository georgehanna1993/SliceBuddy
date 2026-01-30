from core.config import load_env, get_openai_key

def main() -> None:
    load_env()
    key_loaded = bool(get_openai_key())

    print("SliceBuddy is set up ✅")
    print("OPENAI_API_KEY loaded:", key_loaded)

if __name__ == "__main__":
    main()