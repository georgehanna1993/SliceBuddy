from core.rag.index import build_or_update_index
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    build_or_update_index()
    print("✅ Chroma index built.")