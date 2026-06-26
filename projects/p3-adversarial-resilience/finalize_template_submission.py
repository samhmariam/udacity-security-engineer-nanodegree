from __future__ import annotations

from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "Copy of Adversarial Resilience Tempalte 2024.pdf"
OUTPUT = ROOT / "Adversarial_Resilience_Final_Submission.pdf"

CYAN = (2 / 255, 179 / 255, 228 / 255)
GRAY = (89 / 255, 89 / 255, 89 / 255)
BLACK = (0, 0, 0)
WHITE = (1, 1, 1)


def replace_text(
    page: fitz.Page,
    redact_rect: fitz.Rect,
    text_rect: fitz.Rect,
    text: str,
    *,
    fill: tuple[float, float, float],
    fontname: str,
    fontfile: str | None,
    fontsize: float,
    color: tuple[float, float, float],
    align: int = fitz.TEXT_ALIGN_CENTER,
    lineheight: float = 1.15,
) -> None:
    page.add_redact_annot(redact_rect, fill=fill)
    page.apply_redactions()
    if fontfile:
        page.insert_font(fontname=fontname, fontfile=fontfile)
    result = page.insert_textbox(
        text_rect,
        text,
        fontname=fontname,
        fontsize=fontsize,
        color=color,
        align=align,
        lineheight=lineheight,
        overlay=True,
    )
    if result < 0:
        raise RuntimeError(f"Text did not fit: {text!r} ({result=})")


def finalize() -> Path:
    document = fitz.open(SOURCE)

    # Cover: fill the two required fields while retaining the original artwork.
    cover = document[0]
    cover.add_redact_annot(fitz.Rect(165, 650, 447, 766), fill=CYAN)
    cover.apply_redactions()
    for rect, text, size in [
        (fitz.Rect(160, 654, 452, 710), "Samuel", 34),
        (fitz.Rect(160, 708, 452, 762), "25 June 2026", 27),
    ]:
        result = cover.insert_textbox(
            rect,
            text,
            fontname="hebi",
            fontsize=size,
            color=WHITE,
            align=fitz.TEXT_ALIGN_CENTER,
            lineheight=1.0,
            overlay=True,
        )
        if result < 0:
            raise RuntimeError(f"Cover text did not fit: {text!r}")

    # Preserve the template table while applying the submitted permission answers.
    permissions = document[23]
    permission_answers = [
        (
            fitz.Rect(308, 250, 590, 301),
            fitz.Rect(314, 255, 584, 296),
            "[drwxrwxrwx (777)]",
            14,
        ),
        (
            fitz.Rect(308, 304, 590, 391),
            fitz.Rect(315, 310, 583, 385),
            "[Everyone can read it.]",
            14,
        ),
        (
            fitz.Rect(308, 470, 590, 550),
            fitz.Rect(315, 484, 583, 535),
            "[Change the permissions to 700 (or rwx------).]",
            12,
        ),
        (
            fitz.Rect(308, 551, 590, 674),
            fitz.Rect(315, 558, 583, 668),
            "[Everyone (the Owner, members of the Group, and all Other users) "
            "has permission to read this file.]",
            11,
        ),
    ]
    for redact_rect, text_rect, text, size in permission_answers:
        replace_text(
            permissions,
            redact_rect,
            text_rect,
            text,
            fill=WHITE,
            fontname="heit",
            fontfile=None,
            fontsize=size,
            color=GRAY,
        )

    # Keep the filename intact instead of splitting the extension over two lines.
    packet_analysis = document[26]
    replace_text(
        packet_analysis,
        fitz.Rect(307, 470, 590, 532),
        fitz.Rect(313, 482, 584, 520),
        "[payroll_20200927000951_1871.xls]",
        fill=WHITE,
        fontname="heit",
        fontfile=None,
        fontsize=11.5,
        color=GRAY,
    )

    # The template asks for both the CVE identifier and score. The source answer
    # included the score but omitted the identifier from this field.
    vulnerability = document[32]
    replace_text(
        vulnerability,
        fitz.Rect(27, 270, 585, 307),
        fitz.Rect(31, 275, 581, 304),
        "[CVE-2017-7494 - 9.8 Critical under CVSS v3.1 according to NVD.]",
        fill=WHITE,
        fontname="helv",
        fontfile=None,
        fontsize=13.5,
        color=BLACK,
        align=fitz.TEXT_ALIGN_LEFT,
        lineheight=1.0,
    )

    # The official instructions explicitly require deleting these two pages:
    # "How to Use this Template" and "Project Scenario."
    document.delete_page(2)
    document.delete_page(1)

    document.set_metadata(
        {
            "title": "Adversarial Resilience",
            "author": "Samuel",
            "subject": "Windows and Ubuntu Golden Image Security Assessment",
            "keywords": "Udacity, Adversarial Resilience, CIS, Nmap, Forensics",
            "creator": "Udacity project template",
            "producer": "PyMuPDF",
        }
    )
    OUTPUT.unlink(missing_ok=True)
    document.save(OUTPUT, garbage=4, deflate=True, clean=True)
    document.close()
    return OUTPUT


if __name__ == "__main__":
    print(finalize())
