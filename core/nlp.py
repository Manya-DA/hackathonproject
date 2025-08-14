import re
from typing import Dict, Any, List

# Optional: try to use transformers NER; fall back to regex-only if not available
try:
    from transformers import pipeline
    _ner = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
except Exception:
    _ner = None

AGE_PAT = re.compile(r"""(?:(?:age)\s*[:\-]?\s*(\d{1,3})\b|\b(\d{1,3})\s*(?:y/o|years|yrs|yo)\b)""", re.I)
DOSE_PAT = re.compile(r"""(\d+\s?(?:mg|mcg|g|ml|units|IU))""", re.I)
FREQ_PAT = re.compile(r"""\b(\d-\d-\d|\d\s?\/\s?day|OD|BD|TID|QID|HS|PRN)\b""", re.I)

def _simple_drug_guess(text: str) -> List[Dict[str, str]]:
    drugs = []
    # naive: each line may contain a drug and optional dose/frequency
    for line in text.splitlines():
        line = line.strip()
        if not line or len(line) < 2:
            continue
        # heuristics: drug word at start (capitalized), or contains mg
        dose = DOSE_PAT.search(line)
        freq = FREQ_PAT.search(line)
        # crude drug name guess: first token before dose
        name = None
        if dose:
            before = line[:dose.start()].strip(" -:\t\u2022")
            name = before.split(",")[0].split("–")[0].strip()
        else:
            # if NER exists, we'll rely on it below, otherwise take first word chunk
            parts = re.split(r"\s+-\s+|,|;|\s{2,}", line)
            if parts:
                name = parts[0].strip()
        if name:
            drugs.append({
                "name": re.sub(r"[^A-Za-z0-9\- ]+", "", name)[:64],
                "dosage": dose.group(1) if dose else "",
                "frequency": freq.group(1) if freq else ""
            })
    return drugs

def _apply_ner(text: str, drugs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    if _ner is None:
        return drugs
    try:
        ents = _ner(text)
        # Enhance names if NER tagged something as ORG/DRUG-like (dslim/bert-base-NER has PER/ORG/LOC/MISC)
        # We'll just try to pick capitalized tokens near doses.
        # Minimal enhancement to avoid heavy logic.
        return drugs
    except Exception:
        return drugs

def parse_age(text: str):
    m = AGE_PAT.search(text)
    if not m:
        return None
    for g in m.groups():
        if g:
            try:
                v = int(g)
                if 0 < v < 120:
                    return v
            except ValueError:
                pass
    return None

def extract_drug_structures(text: str) -> Dict[str, Any]:
    text = text or ""
    age = parse_age(text)
    drugs = _simple_drug_guess(text)
    drugs = _apply_ner(text, drugs)
    # deduplicate by name+dosage
    seen = set()
    unique = []
    for d in drugs:
        key = (d.get("name","").lower(), d.get("dosage","").lower(), d.get("frequency","").lower())
        if key in seen:
            continue
        seen.add(key)
        if d.get("name"):
            unique.append(d)
    return {"patient_age": age, "drugs": unique, "raw_text": text}
