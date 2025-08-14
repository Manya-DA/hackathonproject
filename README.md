# AI Prescription Verifier (Granite-mock + Hugging Face)

One-night-ready prototype. Uses:
- **Tesseract OCR** (via `pytesseract`) to read prescription images
- **Hugging Face** for simple NER-based parsing (with regex fallback)
- **Mock Granite** for interaction risk, age checks, and alternatives
- **Streamlit** UI with tabs: Upload, Verification, Doctor Override, Reports & History
- **SQLite** for simple history
- **FPDF** to export a one-page PDF report

## 1) Install system dependency
- **Tesseract**:
  - Windows: install from UB Mannheim build and note the install path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`).
  - macOS: `brew install tesseract`
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`

## 2) Create environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

## 3) Configure
```bash
cp .env.example .env
# If Windows, set TESSERACT_PATH in .env to your tesseract.exe path.
# Keep MOCK_MODE=true for offline demo. Set to false if you later add real Granite.
```

## 4) Run
```bash
streamlit run app/app.py
```

## Notes
- First run of Hugging Face models will download weights (needs internet once).
- PDF extraction is text-only via PyPDF for now. For image-based PDFs, export as image or paste text.
- To swap mock Granite with real IBM Granite later, implement API call in `core/granite_client.py` where marked.
