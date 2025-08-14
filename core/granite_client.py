import os
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

MOCK_MODE = os.getenv("MOCK_MODE", "true").lower() == "true"

# Small, hardcoded knowledge base for demo
RISKY_PAIRS = {
    ("ibuprofen", "warfarin"): "Bleeding risk (NSAID + anticoagulant)",
    ("aspirin", "warfarin"): "Bleeding risk (antiplatelet + anticoagulant)",
    ("clopidogrel", "omeprazole"): "Reduced clopidogrel activation (CYP2C19)"
}

ALTERNATIVES = {
    "ibuprofen": ["paracetamol"],
    "aspirin": ["paracetamol"],
    "omeprazole": ["ranitidine (if appropriate)", "famotidine"],
    "warfarin": ["dabigatran (specialist advice)", "apixaban (specialist advice)"]
}

AGE_FLAGS = [
    # (predicate, message, risk_add)
    (lambda age, d: age is not None and age >= 65 and "ibuprofen" in d, "NSAIDs can increase GI bleeding risk in 65+.", 20),
    (lambda age, d: age is not None and age <= 12 and "aspirin" in d, "Avoid aspirin in children due to Reye's syndrome risk.", 40),
]

def analyze(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Simulated Granite: returns structured safety analysis."""
    age = parsed.get("patient_age")
    drugs = [ (d.get("name","").lower(), d) for d in parsed.get("drugs", []) if d.get("name") ]
    flags: List[str] = []
    suggestions: List[str] = []
    risk_score = 15  # base

    # Pairwise interactions
    names = [n for n, _ in drugs]
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            pair = (names[i], names[j])
            pair_rev = (names[j], names[i])
            if pair in RISKY_PAIRS or pair_rev in RISKY_PAIRS:
                reason = RISKY_PAIRS.get(pair) or RISKY_PAIRS.get(pair_rev)
                flags.append(f"Interaction: {names[i].title()} + {names[j].title()} → {reason}")
                risk_score += 45
                # alternatives for each involved drug
                for nm in (names[i], names[j]):
                    if nm in ALTERNATIVES:
                        suggestions.extend(ALTERNATIVES[nm])

    # Age-specific checks
    for nm, _d in drugs:
        for pred, msg, radd in AGE_FLAGS:
            if pred(age, nm):
                flags.append(f"Age warning for {nm.title()}: {msg}")
                risk_score += radd
                if nm in ALTERNATIVES:
                    suggestions.extend(ALTERNATIVES[nm])

    # Dosage sanity (very naive): >1000mg single dose paracetamol
    for nm, d in drugs:
        dose = (d.get("dosage") or "").lower().replace(" ", "")
        if "paracetamol" in nm and ("1000mg" in dose or "1g" in dose):
            flags.append("High single dose of Paracetamol detected; ensure total daily dose <= 4g.")
            risk_score += 10

    # Normalize
    suggestions = sorted(set(suggestions))
    risk_score = max(0, min(100, risk_score))
    level = "high" if risk_score >= 70 else "medium" if risk_score >= 40 else "low"

    return {
        "interaction_risk": level,
        "risk_score": risk_score,
        "flags": flags,
        "alternatives": suggestions,
        "explanation": "Generated locally (Granite-mock). Replace with real Granite API later for production."
    }
