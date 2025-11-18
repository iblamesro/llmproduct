# utils/export.py

import io
import csv
import json
from typing import List, Dict

def format_conversation_for_export(messages: List[Dict]) -> str:
    lines = []
    for m in messages:
        role = m.get("role", "assistant")
        content = m.get("content", "")
        lines.append(f"{role.upper()}: {content}")
        if m.get("sources"):
            lines.append("SOURCES:")
            lines.append(m["sources"])
            lines.append("")
    return "\n".join(lines)


def export_to_csv(messages: List[Dict]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["role", "content", "sources", "mode"])
    for m in messages:
        writer.writerow(
            [
                m.get("role", ""),
                m.get("content", ""),
                m.get("sources", ""),
                m.get("mode", ""),
            ]
        )
    return output.getvalue().encode("utf-8")


def export_to_json(messages: List[Dict]) -> bytes:
    return json.dumps(messages, ensure_ascii=False, indent=2).encode("utf-8")


def export_to_pdf(messages: List[Dict]) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    except Exception as e:
        raise RuntimeError("reportlab is not installed") from e

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    for m in messages:
        role = m.get("role", "assistant").upper()
        content = m.get("content", "")
        story.append(Paragraph(f"<b>{role}</b>: {content}", styles["Normal"]))
        if m.get("sources"):
            story.append(Paragraph(f"<i>Sources:</i> {m['sources']}", styles["Normal"]))
        story.append(Spacer(1, 12))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
