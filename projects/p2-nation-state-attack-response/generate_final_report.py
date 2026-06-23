from __future__ import annotations

import html
import re
from pathlib import Path

import fitz
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parent
SOURCE_PDF = ROOT / "Copy of Responding to a Nation-State Cyber Attack 2024 Q2.pdf"
SOURCE_MD = ROOT / "final_report.md"
OUTPUT_PDF = ROOT / "Responding to a Nation-State Cyber Attack - Final.pdf"
ASSET_DIR = ROOT / "report_assets"


def extract_evidence() -> dict[str, Path]:
    ASSET_DIR.mkdir(exist_ok=True)
    document = fitz.open(SOURCE_PDF)
    evidence = {
        "hids": (11, 87),
        "ssh": (15, 110),
        "openvas": (18, 130),
    }
    paths: dict[str, Path] = {}
    for name, (page_number, xref) in evidence.items():
        image = document.extract_image(xref)
        path = ASSET_DIR / f"{name}.{image['ext']}"
        path.write_bytes(image["image"])
        paths[name] = path
    return paths


def parse_markdown(text: str, styles, evidence: dict[str, Path]):
    story = []
    in_code = False
    code_lines: list[str] = []
    bullets: list[str] = []

    def inline(value: str) -> str:
        value = html.escape(value, quote=False)
        value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
        value = re.sub(r"`(.+?)`", r'<font name="Courier">\1</font>', value)
        return value

    def flush_bullets():
        nonlocal bullets
        if bullets:
            for item in bullets:
                story.append(Paragraph(f"• {inline(item)}", styles["BodyIndent"]))
            story.append(Spacer(1, 5))
            bullets = []

    def flush_code():
        nonlocal code_lines
        if code_lines:
            story.append(Preformatted("\n".join(code_lines), styles["CodeBlock"]))
            story.append(Spacer(1, 7))
            code_lines = []

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_bullets()
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line:
            flush_bullets()
            story.append(Spacer(1, 4))
            continue
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            flush_bullets()
            heading = line[3:]
            story.append(Paragraph(inline(heading), styles["Heading1"]))
            continue
        if line.startswith("### "):
            flush_bullets()
            heading = line[4:]
            heading_flowable = Paragraph(inline(heading), styles["Heading2"])
            if heading == "2.1 Host-based intrusion detection":
                story.append(
                    KeepTogether(
                        [
                            heading_flowable,
                            Image(str(evidence["hids"]), width=6.55 * inch, height=4.09 * inch),
                            Spacer(1, 8),
                        ]
                    )
                )
            elif heading == "2.4 Disable SSH root access":
                story.append(
                    KeepTogether(
                        [
                            heading_flowable,
                            Image(str(evidence["ssh"]), width=6.55 * inch, height=4.09 * inch),
                            Spacer(1, 8),
                        ]
                    )
                )
            elif heading == "3.1 OpenVAS vulnerability scan":
                story.append(
                    KeepTogether(
                        [
                            heading_flowable,
                            Image(str(evidence["openvas"]), width=6.55 * inch, height=3.72 * inch),
                            Spacer(1, 8),
                        ]
                    )
                )
            else:
                story.append(heading_flowable)
            continue
        if line.startswith("|"):
            flush_bullets()
            # This document has one small two-column Markdown table.
            continue
        if len(line) > 2 and line[0].isdigit() and line[1] in ".)":
            bullets.append(line)
            continue
        if line.startswith("- "):
            bullets.append(line[2:])
            continue
        flush_bullets()
        story.append(Paragraph(inline(line), styles["Body"]))

    flush_bullets()
    flush_code()
    return story


class ReportDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
        )
        self.addPageTemplates(PageTemplate(id="report", frames=frame, onPage=self.draw_page))

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in {"Heading1", "Heading2"}:
            level = 0 if flowable.style.name == "Heading1" else 1
            text = flowable.getPlainText()
            key = f"heading-{self.seq.nextf('heading')}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=False)
            self.notify("TOCEntry", (level, text, self.page, key))

    def draw_page(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D9E2E8"))
        canvas.line(doc.leftMargin, 0.55 * inch, letter[0] - doc.rightMargin, 0.55 * inch)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#52616B"))
        canvas.drawString(doc.leftMargin, 0.35 * inch, "Nation-State Cyber Attack Response")
        canvas.drawRightString(letter[0] - doc.rightMargin, 0.35 * inch, f"Page {doc.page}")
        canvas.restoreState()


def build_report():
    evidence = extract_evidence()
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "CoverTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17324D"),
            spaceAfter=20,
        )
    )
    styles.add(
        ParagraphStyle(
            "CoverMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#52616B"),
        )
    )
    styles["Heading1"].fontName = "Helvetica-Bold"
    styles["Heading1"].fontSize = 20
    styles["Heading1"].leading = 24
    styles["Heading1"].textColor = colors.HexColor("#0B7A75")
    styles["Heading1"].spaceBefore = 10
    styles["Heading1"].spaceAfter = 12
    styles["Heading2"].fontName = "Helvetica-Bold"
    styles["Heading2"].fontSize = 13
    styles["Heading2"].leading = 16
    styles["Heading2"].textColor = colors.HexColor("#17324D")
    styles["Heading2"].spaceBefore = 10
    styles["Heading2"].spaceAfter = 7
    styles.add(
        ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#263238"),
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "BodyIndent",
            parent=styles["Body"],
            leftIndent=14,
            firstLineIndent=-8,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            "CodeBlock",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=7.4,
            leading=9.2,
            leftIndent=9,
            rightIndent=9,
            borderColor=colors.HexColor("#CAD5DC"),
            borderWidth=0.6,
            borderPadding=7,
            backColor=colors.HexColor("#F5F7F8"),
            spaceBefore=3,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "TOCHeading",
            parent=styles["Heading1"],
            alignment=TA_CENTER,
            spaceAfter=18,
        )
    )

    doc = ReportDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        rightMargin=0.68 * inch,
        leftMargin=0.68 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.75 * inch,
        title="Responding to a Nation-State Cyber Attack",
        author="Samuel Hailemariam",
        subject="Threat detection, mitigation, and system hardening report",
    )

    story = [
        Spacer(1, 1.45 * inch),
        Paragraph("RESPONDING TO A<br/>NATION-STATE CYBER ATTACK", styles["CoverTitle"]),
        Spacer(1, 0.25 * inch),
        Table(
            [["INCIDENT RESPONSE REPORT"]],
            colWidths=[3.2 * inch],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0B7A75")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ]
            ),
            hAlign="CENTER",
        ),
        Spacer(1, 1.0 * inch),
        Paragraph("Samuel Hailemariam", styles["CoverMeta"]),
        Paragraph("23 June 2026", styles["CoverMeta"]),
        Paragraph("South Udan Tridanium Processing Plant", styles["CoverMeta"]),
        PageBreak(),
        Paragraph("Contents", styles["TOCHeading"]),
    ]
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOC1",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=15,
            leftIndent=8,
            firstLineIndent=-8,
            textColor=colors.HexColor("#17324D"),
        ),
        ParagraphStyle(
            "TOC2",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            leftIndent=24,
            firstLineIndent=-8,
            textColor=colors.HexColor("#52616B"),
        ),
    ]
    story.extend([toc, PageBreak()])
    story.extend(parse_markdown(SOURCE_MD.read_text(encoding="utf-8"), styles, evidence))
    doc.multiBuild(story)
    print(OUTPUT_PDF)


if __name__ == "__main__":
    build_report()
