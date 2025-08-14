import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")  # Ensure this is set in .env file

# ✅ Using a free public model to avoid permission issues
HF_MODEL = "tiiuae/falcon-7b-instruct"
HF_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

def query_huggingface(prompt):
    """
    Send a prompt to Hugging Face Inference API and return generated text.
    """
    try:
        response = requests.post(
            HF_URL,
            headers=HEADERS,
            json={
                "inputs": prompt,
                "parameters": {"max_new_tokens": 200, "temperature": 0.7}
            }
        )

        # Handle API errors
        if response.status_code != 200:
            return f"❌ Hugging Face API error: {response.status_code} - {response.text}"

        data = response.json()

        # Parse response depending on API format
        if isinstance(data, list) and len(data) > 0 and "generated_text" in data[0]:
            return data[0]["generated_text"].strip()
        elif isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"].strip()

        return "⚠️ No valid response from Hugging Face model."

    except Exception as e:
        return f"❌ Hugging Face API request failed: {e}"

def get_ai_alternatives(drug_name):
    """
    Ask Hugging Face AI for safer/effective alternatives.
    """
    prompt = (
        f"Suggest safer and equally effective alternatives for the medicine '{drug_name}'. "
        f"Provide the answer in bullet points and keep it short."
    )
    return query_huggingface(prompt)

def get_ai_dosage_warnings(drug_name, dosage):
    """
    Ask Hugging Face AI for dosage warnings.
    """
    prompt = (
        f"Check if the dosage '{dosage}' for the drug '{drug_name}' is safe for an adult. "
        f"List possible side effects or risks in bullet points."
    )
    return query_huggingface(prompt)
