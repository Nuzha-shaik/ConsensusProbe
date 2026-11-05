"""Export utilities: neutralizes formula injection and generates PDF/Excel audit reports."""
from __future__ import annotations
import io
import pandas as pd
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def neutralize_cell(val):
    """Formula injection protection: prefix strings starting with =, +, -, @ with single quote."""
    if isinstance(val, str) and val.startswith(("=", "+", "-", "@")):
        return f"'{val}"
    return val

def neutralize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply formula injection protection to all string cells in DataFrame."""
    clean_df = df.copy()
    for col in clean_df.columns:
        if clean_df[col].dtype == object or pd.api.types.is_string_dtype(clean_df[col]):
            clean_df[col] = clean_df[col].apply(neutralize_cell)
    return clean_df

def export_csv(df: pd.DataFrame) -> bytes:
    """Export DataFrame as neutralized CSV bytes."""
    clean_df = neutralize_dataframe(df)
    output = io.StringIO()
    clean_df.to_csv(output, index=False)
    return output.getvalue().encode("utf-8")

def export_xlsx(df: pd.DataFrame, audit_log: list[str] | None = None) -> bytes:
    """Export DataFrame and audit log as Excel workbook using openpyxl."""
    clean_df = neutralize_dataframe(df)
    wb = openpyxl.Workbook()

    # Sheet 1: Cleaned Data
    ws_data = wb.active
    ws_data.title = "Cleaned Data"

    # Write headers
    ws_data.append(list(clean_df.columns))
    for row in clean_df.itertuples(index=False):
        ws_data.append([neutralize_cell(v) for v in row])

    # Sheet 2: Audit Log
    if audit_log:
        ws_audit = wb.create_sheet(title="Audit Log")
        ws_audit.append(["Timestamp / Step", "Action Summary"])
        for idx, entry in enumerate(audit_log, 1):
            ws_audit.append([f"Step {idx}", str(entry)])

    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()

def export_pdf(summary_info: dict, audit_log: list[str]) -> bytes:
    """Export cleaning summary and audit report as PDF using ReportLab."""
    bio = io.BytesIO()
    doc = SimpleDocTemplate(bio, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
    )
    story.append(Paragraph("ConsensusProbe: Data Cleaning Audit Report", title_style))
    story.append(Spacer(1, 15))

    # Summary Table
    meta_data = [
        ["Dataset ID", str(summary_info.get("dataset_id", "N/A"))],
        ["Filename", str(summary_info.get("filename", "N/A"))],
        ["Original SHA-256", str(summary_info.get("sha256", "N/A"))[:16] + "..."],
        ["Initial Rows / Cols", f"{summary_info.get('rows', 0)} / {summary_info.get('cols', 0)}"],
        ["Consensus Status", str(summary_info.get("status", "N/A"))],
    ]
    t = Table(meta_data, colWidths=[150, 350])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    # Audit Steps
    story.append(Paragraph("Transformation & Audit Log", styles["Heading2"]))
    story.append(Spacer(1, 10))

    if not audit_log:
        story.append(Paragraph("No transformation steps recorded.", styles["Normal"]))
    else:
        for idx, item in enumerate(audit_log, 1):
            story.append(Paragraph(f"<b>{idx}.</b> {item}", styles["Normal"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    return bio.getvalue()
