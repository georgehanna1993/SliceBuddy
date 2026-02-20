import re
from core.state import PlanState

# tiny list, enough to catch junk without being language-police
COMMON_WORDS = {
    "for", "and", "with", "without", "use", "used", "print", "holder", "stand", "mount",
    "bracket", "case", "box", "toy", "fidget", "ball", "hook", "clip", "cover", "cap",
    "screw", "container", "organizer", "shelf", "phone", "camera", "wall", "desk"
}

def _looks_like_gibberish(text: str) -> bool:
    s = text.strip().lower()
    if len(s) < 6:
        return True  # too short to be meaningful in your UI

    # must contain at least some letters
    letters = sum(ch.isalpha() for ch in s)
    if letters / max(len(s), 1) < 0.5:
        return True

    # tokenize words
    words = re.findall(r"[a-zA-Z]{2,}", s)
    if len(words) < 2:
        # allow 1-word only if it's a common known keyword like "bracket" / "holder"
        return not any(w in COMMON_WORDS for w in words)

    # block obvious keyboard mash (very low vowel ratio)
    joined = "".join(words)
    vowels = sum(ch in "aeiou" for ch in joined)
    if vowels / max(len(joined), 1) < 0.20:
        # BUT don't punish real words that include a known keyword
        if not any(w in COMMON_WORDS for w in words):
            return True

    # block extreme repetition like "aaaaaa" / "qweqweqwe"
    if re.fullmatch(r"(.)\1{5,}", s):
        return True

    return False


def intent_guard_node(state: PlanState) -> PlanState:
    desc = (state.get("description") or "").strip()
    h = state.get("height_mm", None)
    w = state.get("width_mm", None)

    has_stl = bool((state.get("stl_path") or "").strip())

    dims_ok = isinstance(h, (int, float)) and isinstance(w, (int, float)) and h > 0 and w > 0

    # NEW: Meaning check (especially when STL exists)
    desc_ok = len(desc) >= 6 and not _looks_like_gibberish(desc)

    is_plan_request = desc_ok and (dims_ok or has_stl)
    state["stop"] = not is_plan_request

    if state["stop"]:
        state["plan"] = {"summary": "Not a print-plan request"}
        state["plan_explanation"] = (
            "I need a short meaningful description of what the STL is used for.\n"
            "Examples: 'phone stand', 'wall mount bracket', 'open-top box for screws'."
        )

    return state