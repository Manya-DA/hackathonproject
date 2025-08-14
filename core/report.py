# core/report.py
from fpdf import FPDF
import networkx as nx
from pyvis.network import Network
from typing import List, Dict, Any

# ------------------- PDF Builder (existing) -------------------
def build_pdf(case: Dict[str, Any], outfile: str) -> str:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "AI Prescription Safety Report", ln=1)
    pdf.set_font("Arial", "", 12)

    pdf.cell(0, 8, f"Case ID: {case.get('id','')}", ln=1)
    pdf.cell(0, 8, f"Timestamp: {case.get('timestamp','')}", ln=1)
    pdf.cell(0, 8, f"Patient Age: {case.get('patient_age','')}", ln=1)
    pdf.cell(0, 8, f"Risk Score: {case.get('risk_score','')}", ln=1)

    pdf.ln(4)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Drugs:", ln=1)
    pdf.set_font("Arial", "", 12)
    for d in case.get("drugs", []):
        line = f"- {d.get('name','')}  {d.get('dosage','')}  {d.get('frequency','')}"
        pdf.multi_cell(0, 6, line)

    pdf.ln(2)
    res = case.get("result", {})
    flags = res.get("flags", [])
    alts = res.get("alternatives", [])
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Flags:", ln=1)
    pdf.set_font("Arial", "", 12)
    if flags:
        for f in flags:
            pdf.multi_cell(0, 6, f"- {f}")
    else:
        pdf.cell(0, 6, "None", ln=1)

    pdf.ln(2)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Alternatives:", ln=1)
    pdf.set_font("Arial", "", 12)
    if alts:
        for a in alts:
            pdf.multi_cell(0, 6, f"- {a}")
    else:
        pdf.cell(0, 6, "None", ln=1)

    pdf.output(outfile)
    return outfile

# ------------------- HTML Interaction Report -------------------
def build_interaction_html(drugs: List[Dict[str, Any]], interactions: List[Dict[str, Any]], outfile: str) -> str:
    """
    Creates an interactive HTML network showing drug interactions.
    """
    net = Network(height="600px", width="100%", bgcolor="#f9f9f9", font_color="black")

    # Add drugs as nodes
    for d in drugs:
        name = d.get("name", "Unknown")
        net.add_node(name, label=name, color="#4CAF50")

    # Add interactions as edges
    for i in interactions:
        d1 = i.get("drug1")
        d2 = i.get("drug2")
        risk = i.get("risk", "Moderate")
        color = "red" if risk.lower() == "high" else "orange"
        net.add_edge(d1, d2, color=color, title=f"{d1} ↔ {d2}: {risk} Risk")

    # Save HTML
    net.show(outfile)
    return outfile
