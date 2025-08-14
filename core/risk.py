# core/risk.py
def score_from_drugs(drugs, patient_age):
    """
    Returns a dictionary with:
    - risk_score (0-100)
    - flags (list of issues)
    - alternatives (list of safer drugs)
    - interactions (list of dangerous combos)
    """

    # ------------------- DRUG RULES -------------------
    DRUG_RULES = {
        "aspirin": {"flags": ["May cause stomach bleeding"], "alternatives": ["Acetaminophen"]},
        "ibuprofen": {"flags": ["May affect kidneys"], "alternatives": ["Naproxen"]},
        "naproxen": {"flags": ["May cause stomach irritation"], "alternatives": ["Ibuprofen"]},
        "paracetamol": {"flags": [], "alternatives": []},
        "warfarin": {"flags": ["Blood thinning – risk of bleeding"], "alternatives": ["Heparin"]},
        "amoxicillin": {"flags": ["May cause allergy"], "alternatives": ["Cefalexin"]},
        "ciprofloxacin": {"flags": ["Can affect tendons and nerves"], "alternatives": ["Levofloxacin"]},
        "levofloxacin": {"flags": ["QT prolongation risk"], "alternatives": ["Ciprofloxacin"]},
        "metformin": {"flags": ["Monitor kidney function"], "alternatives": []},
        "lisinopril": {"flags": ["May increase potassium levels"], "alternatives": ["Losartan"]},
        "losartan": {"flags": ["Monitor blood pressure"], "alternatives": ["Lisinopril"]},
        "atorvastatin": {"flags": ["May cause muscle pain"], "alternatives": ["Rosuvastatin"]},
        "simvastatin": {"flags": ["May interact with grapefruit juice"], "alternatives": ["Atorvastatin"]},
        "rosuvastatin": {"flags": ["Check liver function"], "alternatives": ["Atorvastatin"]},
        "prednisone": {"flags": ["May increase blood sugar"], "alternatives": ["Hydrocortisone"]},
        "hydrocortisone": {"flags": ["Monitor for immune suppression"], "alternatives": ["Prednisone"]},
        "omeprazole": {"flags": ["Long-term use may cause kidney issues"], "alternatives": ["Pantoprazole"]},
        "pantoprazole": {"flags": ["Rare liver effects"], "alternatives": ["Omeprazole"]},
        "hydrochlorothiazide": {"flags": ["May lower potassium"], "alternatives": ["Chlorthalidone"]},
        "chlorthalidone": {"flags": ["Electrolyte imbalance risk"], "alternatives": ["Hydrochlorothiazide"]},
        "furosemide": {"flags": ["May cause dehydration"], "alternatives": ["Bumetanide"]},
        "bumetanide": {"flags": ["Monitor electrolytes"], "alternatives": ["Furosemide"]},
        "levothyroxine": {"flags": ["Take on empty stomach"], "alternatives": []},
        "insulin": {"flags": ["Risk of hypoglycemia"], "alternatives": []},
        "clopidogrel": {"flags": ["May increase bleeding risk"], "alternatives": ["Ticagrelor"]},
        "ticagrelor": {"flags": ["Monitor platelet function"], "alternatives": ["Clopidogrel"]},
        "heparin": {"flags": ["Monitor platelet count"], "alternatives": []},
        "gentamicin": {"flags": ["May affect kidneys and hearing"], "alternatives": ["Amikacin"]},
        "amikacin": {"flags": ["Ototoxicity risk"], "alternatives": ["Gentamicin"]},
        "azithromycin": {"flags": ["May prolong QT interval"], "alternatives": ["Clarithromycin"]},
        "clarithromycin": {"flags": ["May prolong QT interval"], "alternatives": ["Azithromycin"]},
        "tizanidine": {"flags": ["May cause low blood pressure"], "alternatives": []},
        "potassium supplement": {"flags": ["High potassium risk"], "alternatives": []},
    }

    # ------------------- HIGH-RISK COMBOS -------------------
    HIGH_RISK_COMBOS = [
        ("aspirin", "ibuprofen"),
        ("warfarin", "naproxen"),
        ("warfarin", "aspirin"),
        ("lisinopril", "potassium supplement"),
        ("ciprofloxacin", "tizanidine"),
        ("atorvastatin", "gemfibrozil"),
        ("simvastatin", "clarithromycin"),
        ("prednisone", "insulin"),
        ("furosemide", "lisinopril"),
        ("gentamicin", "furosemide"),
        ("azithromycin", "simvastatin"),
        ("ciprofloxacin", "warfarin"),
        ("amoxicillin", "methotrexate"),
        ("heparin", "clopidogrel"),
    ]

    # ------------------- INITIALIZE -------------------
    flags = []
    alternatives = []
    interactions = []
    dosage_suggestions = []
    risk_score = 0

    drugs_lower = [d["name"].lower() for d in drugs if "name" in d]

    # ------------------- CHECK INDIVIDUAL DRUGS -------------------
    for d in drugs_lower:
        if d in DRUG_RULES:
            flags.extend(DRUG_RULES[d]["flags"])
            alternatives.extend(DRUG_RULES[d]["alternatives"])
            if DRUG_RULES[d]["flags"]:
                risk_score += 15  # assign points for flagged drug
            # Dosage suggestions placeholder
            if "dosage" in d:
                dosage = d.get("dosage", None)
                max_dose = DRUG_RULES[d]["max_dosage"]
                if dosage and dosage > max_dose:
                    dosage_suggestions.append(f"Reduce {d} dosage to <= {max_dose} mg")

    # ------------------- CHECK COMBINATIONS -------------------
    for combo in HIGH_RISK_COMBOS:
        if combo[0] in drugs_lower and combo[1] in drugs_lower:
            interactions.append({"drug1": combo[0], "drug2": combo[1], "risk": "High"})
            risk_score += 40  # extra points for dangerous combo

    # ------------------- AGE-SPECIFIC RISK -------------------
    if patient_age < 12 or patient_age > 65:
        risk_score += 10  # children and elderly have higher sensitivity
    # ------------------- PREDICTED FUTURE RISKS -------------------
    predicted_risks = []
    for d in drugs_lower:
        if d in ["prednisone", "insulin"]:
            predicted_risks.append("Monitor blood sugar for next 1-2 weeks")
        if d in ["ciprofloxacin", "tizanidine"]:
            predicted_risks.append("May cause muscle weakness or dizziness")
    # ------------------- FINALIZE -------------------
    risk_score = min(risk_score, 100)

    if risk_score > 70:
        interaction_risk = "High"
    elif risk_score > 30:
        interaction_risk = "Moderate"
    else:
        interaction_risk = "Low"
    
    return {
    "risk_score": risk_score,
    "flags": list(set(flags)),  # remove duplicates
    "alternatives": list(set(alternatives)),
    "interactions": interactions,
    "interaction_risk": interaction_risk,
    "predicted_risks": predicted_risks,  # ✅ correct way to include
    "dosage_suggestions": dosage_suggestions,
    "explanation": "This is a demo-ready, extended risk analysis for Hackathon. Includes a large set of drugs, high-risk combos, and age considerations."
}

