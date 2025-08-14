import re
import pytesseract
from PIL import Image

def extract_drug_info(image_path):
    """
    Extracts drug name and dosage from an image using OCR.
    """
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)

    # Example regex: match "DrugName 500mg" or "DrugName 250 mg"
    match = re.search(r"([A-Za-z]+)\s+(\d+\s?mg)", text, re.IGNORECASE)
    if match:
        drug_name = match.group(1).strip()
        dosage = match.group(2).replace(" ", "").strip()
    else:
        drug_name = ""
        dosage = ""

    return {
        "drug_name": drug_name,
        "dosage": dosage,
        "raw_text": text.strip()
    }
