import sys
from core.stl import analyze_stl

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/stl_analyze.py path/to/file.stl")
        return
    feats = analyze_stl(sys.argv[1])
    for k, v in feats.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()