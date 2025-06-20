import re
from difflib import get_close_matches

TECHNICAL_TERMS = []

def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def load_terms(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
        terms = re.findall(r'"(.*?)"', text)
        return [t.strip() for t in terms if t.strip()]

def ensure_russian_request(text: str) -> str:
    normalized = text.strip().lower()
    if "ответь на русском" not in normalized and "на русском языке" not in normalized:
        return text.strip() + " Ответь строго на русском языке."
    return text

def correct_tech_terms(text: str) -> str:
    words = text.lower().split()
    corrected = []
    for w in words:
        if w in TECHNICAL_TERMS:
            corrected.append(w)
        else:
            m = get_close_matches(w, TECHNICAL_TERMS, n=1, cutoff=0.8)
            corrected.append(m[0] if m else w)
    return " ".join(corrected)
