from __future__ import annotations

from io import BytesIO
from pathlib import Path

import fitz
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "Copy of Adversarial Resilience Tempalte 2024.pdf"
OUTPUT = ROOT / "Adversarial_Resilience_Faithful_Presentation.pdf"
PAGE = (960, 540)
W, H = PAGE

CHARCOAL = HexColor("#2E4050")
INK = HexColor("#334E5C")
MUTED = HexColor("#6B7C85")
TEAL = HexColor("#1BAF9A")
CYAN = HexColor("#18B9D4")
GREEN = HexColor("#2FBF8F")
RED = HexColor("#D94B4B")
AMBER = HexColor("#F3A522")
LINE = HexColor("#D9E2E7")
PALE = HexColor("#F5F8FA")


def st(name, size, color=INK, leading=None, font="Helvetica", align=TA_LEFT):
    return ParagraphStyle(
        name,
        fontName=font,
        fontSize=size,
        leading=leading or size * 1.25,
        textColor=color,
        alignment=align,
    )


TITLE = st("title", 25, CHARCOAL, 30, "Helvetica")
H2 = st("h2", 16, CHARCOAL, 20, "Helvetica-Bold")
H3 = st("h3", 11, CHARCOAL, 14, "Helvetica-Bold")
BODY = st("body", 10, INK, 14)
SMALL = st("small", 8.2, MUTED, 11)
WHITE_TITLE = st("white-title", 28, white, 33)
WHITE_BODY = st("white-body", 11, white, 15)


def para(c, text, x, top, width, style=BODY):
    p = Paragraph(text, style)
    _, h = p.wrap(width, H)
    p.drawOn(c, x, top - h)
    return h


def card(c, x, y, w, h, fill=white, stroke=LINE, radius=8):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def brand(c, number, title, subtitle=None):
    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(0, H - 8, W, 8, fill=1, stroke=0)
    if subtitle:
        para(c, subtitle.upper(), 46, H - 34, 820, st("eyebrow", 7.5, GREEN, 9, "Helvetica-Bold"))
    para(c, title, 46, H - 52, 850, TITLE)
    c.setStrokeColor(LINE)
    c.line(46, 30, W - 46, 30)
    c.setFont("Helvetica", 7)
    c.setFillColor(MUTED)
    c.drawString(46, 17, "ADVERSARIAL RESILIENCE | STATICSpeed GOLDEN IMAGE ASSESSMENT")
    c.drawRightString(W - 46, 17, f"{number:02d}")


def status(c, value, x, y):
    color = GREEN if value == "Yes" else RED
    c.setFillColor(Color(color.red, color.green, color.blue, alpha=0.12))
    c.roundRect(x, y, 62, 25, 12, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + 31, y + 8, value.upper())


def bullets(c, items, x, top, width, style=BODY, gap=5):
    y = top
    for item in items:
        c.setFillColor(TEAL)
        c.circle(x + 3, y - 6, 2.2, fill=1, stroke=0)
        h = para(c, item, x + 14, y, width - 14, style)
        y -= h + gap


class Source:
    def __init__(self):
        self.doc = fitz.open(SOURCE)
        self.cache = {}

    def image(self, page, crop=None, scale=1.5):
        key = (page, crop, scale)
        if key in self.cache:
            return self.cache[key]
        p = self.doc[page - 1]
        clip = None
        if crop:
            x0, y0, x1, y1 = crop
            clip = fitz.Rect(
                p.rect.width * x0,
                p.rect.height * y0,
                p.rect.width * x1,
                p.rect.height * y1,
            )
        pix = p.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
        image = ImageReader(BytesIO(pix.tobytes("png")))
        self.cache[key] = image
        return image

    def evidence(self, page):
        """Extract the embedded evidence screenshot without surrounding slide chrome."""
        key = ("evidence", page)
        if key in self.cache:
            return self.cache[key]
        p = self.doc[page - 1]
        candidates = []
        for info in p.get_image_info(xrefs=True):
            x0, y0, x1, y1 = info["bbox"]
            if info["xref"] and info["width"] >= 700 and y0 < p.rect.height:
                visible_area = max(0, min(x1, p.rect.width) - max(x0, 0)) * max(
                    0, min(y1, p.rect.height) - max(y0, 0)
                )
                candidates.append((visible_area, info["xref"]))
        if not candidates:
            return self.image(page, (0, 0.27, 1, 1), 1.8)
        _, xref = max(candidates)
        extracted = self.doc.extract_image(xref)
        image = ImageReader(BytesIO(extracted["image"]))
        self.cache[key] = image
        return image


def image_contain(c, image, x, y, w, h):
    card(c, x, y, w, h)
    iw, ih = image.getSize()
    scale = min((w - 8) / iw, (h - 8) / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(image, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, mask="auto")


def cover(c):
    c.setFillColor(CYAN)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(Color(1, 1, 1, alpha=0.14))
    for x, y, r in [(760, 375, 220), (900, 80, 260), (610, 20, 150)]:
        c.circle(x, y, r, fill=1, stroke=0)
    para(c, "ADVERSARIAL RESILIENCE", 72, 416, 500, st("cover-eye", 10, white, 12, "Helvetica-Bold"))
    para(c, "Security Assessment of<br/>Golden Images", 72, 370, 610, st("cover", 37, white, 43))
    para(c, "Windows • Ubuntu • Access • Forensics • Vulnerabilities", 72, 246, 650, WHITE_BODY)
    card(c, 72, 80, 380, 88, fill=CHARCOAL, stroke=CHARCOAL)
    para(c, "Prepared for NuttyUtility stakeholders", 96, 143, 330, st("cover-meta", 10, white, 13, "Helvetica-Bold"))
    para(c, "StaticSpeed integration readiness review<br/>25 June 2026", 96, 113, 330, st("cover-meta-2", 8.5, white, 12))


def scenario(c, n):
    brand(c, n, "Project Scenario", "Project context")
    para(
        c,
        "NuttyUtility has acquired StaticSpeed, whose systems appear to have been inadequately maintained. Outdated applications and security misconfigurations may expose the combined environment to internal and external malicious actors.",
        58,
        420,
        390,
        BODY,
    )
    para(
        c,
        "The assessment covers the Windows and Ubuntu virtual machines used as golden images. Stakeholders and the infrastructure team must decide whether the images are ready for integration or require controls and mitigations first.",
        58,
        292,
        390,
        BODY,
    )
    card(c, 505, 105, 395, 290, fill=PALE)
    para(c, "Assessment objective", 535, 360, 335, H2)
    bullets(
        c,
        [
            "Evaluate selected CIS benchmarks.",
            "Review Linux and Windows folder permissions.",
            "Analyze PCAP evidence of brute force and lateral movement.",
            "Identify exposed services and critical vulnerabilities.",
            "Provide evidence and remediation for every failed control.",
        ],
        535,
        324,
        330,
        BODY,
        7,
    )


def divider(c, number, section, title):
    c.setFillColor(CHARCOAL)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(TEAL)
    c.rect(70, 125, 85, 4, fill=1, stroke=0)
    para(c, f"SECTION {section}", 70, 385, 300, st("section", 9, TEAL, 11, "Helvetica-Bold"))
    para(c, title, 70, 338, 650, WHITE_TITLE)
    para(c, "Adversarial Resilience", 70, 210, 350, st("section-small", 10, white, 13))
    c.setFont("Helvetica-Bold", 88)
    c.setFillColor(Color(1, 1, 1, alpha=0.08))
    c.drawRightString(W - 65, 70, f"{number:02d}")


def intro(c, n, title, text, tasks):
    brand(c, n, title, "Assessment brief")
    para(c, text, 55, 415, 455, BODY)
    card(c, 540, 96, 365, 300, fill=PALE)
    para(c, "Your task", 568, 363, 300, H2)
    bullets(c, tasks, 568, 324, 300, BODY, 8)


def benchmark(c, n, platform, item, compliant, remediation, source, page):
    brand(c, n, f"Compliance Evaluation on {platform}", "CIS benchmark")
    card(c, 48, 329, 864, 80, fill=PALE)
    para(c, "BENCHMARK", 67, 392, 100, st("label", 7.5, MUTED, 9, "Helvetica-Bold"))
    para(c, item, 67, 369, 680, st("benchmark-name", 13, CHARCOAL, 16, "Helvetica-Bold"))
    para(c, "COMPLIANCE", 775, 392, 100, st("label-2", 7.5, MUTED, 9, "Helvetica-Bold"))
    status(c, compliant, 785, 348)

    # Remediation text is compact; the evidence screenshot receives most of the
    # lower slide so policy values and terminal output remain readable.
    card(c, 48, 54, 214, 252, fill=white)
    para(c, "Remediation strategy", 66, 281, 178, H3)
    para(
        c,
        remediation if remediation else "No remediation required for this compliant control. Retain the configuration and verify it during future golden-image reviews.",
        66,
        247,
        178,
        st("remediation", 9, INK, 12),
    )
    image_contain(c, source.evidence(page), 280, 54, 632, 252)
    para(c, "Screenshot evidence from the assessed virtual machine.", 294, 45, 600, SMALL)


def qa_slide(c, n, title, prompt, rows, section="Access and forensics"):
    brand(c, n, title, section)
    para(c, prompt, 52, 423, 850, st("prompt", 9, MUTED, 12, "Helvetica-Oblique"))
    y = 360
    for question, answer in rows:
        card(c, 52, y - 48, 856, 54, fill=white)
        para(c, question, 70, y - 8, 390, H3)
        para(c, answer, 485, y - 8, 390, BODY)
        y -= 62


def screenshot_slide(c, n, title, prompt, source, page, note=None):
    brand(c, n, title, "Vulnerability assessment")
    para(c, prompt, 52, 420, 850, st("prompt2", 9, MUTED, 12, "Helvetica-Oblique"))
    image_contain(c, source.image(page, (0, 0.18, 1, 0.96), 1.8), 120, 64, 720, 320)
    if note:
        para(c, note, 120, 54, 720, SMALL)


WINDOWS = [
    (6, "1.1.5 (L1) Ensure 'Password must meet complexity requirements' is set to 'Enabled'", "No", "Enable password complexity requirements through Local Security Policy or Group Policy."),
    (7, "1.2.1 Ensure 'Account lockout duration' is set to '15 or more minute(s)'", "No", "Configure Account lockout duration to 15 minutes or more through Local Security Policy, Group Policy, or the command line."),
    (8, "2.2.2 Ensure 'Access this computer from the network' is set to 'Administrators, Remote Desktop Users'", "No", "Configure the policy so that only Administrators and Remote Desktop Users have the Access this computer from the network right."),
    (9, "2.3.1.1 Ensure 'Accounts: Administrator account status' is set to 'Disabled'", "No", "Disable the built-in local Administrator account through Local Security Policy, PowerShell, or the command line."),
    (10, "18.3.4 Ensure 'Enable Structured Exception Handling Overwrite Protection (SEHOP)' is set to 'Enabled'", "No", "Create DisableExceptionChainValidation under HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\kernel and set the relevant registry value to 0."),
    (11, "18.9.102.2 Ensure 'Configure Automatic Updates' is set to 'Enabled'", "No", "Enable the Configure Automatic Updates Group Policy setting and select an appropriate automatic update behavior."),
]

UBUNTU = [
    (14, "1.2.1 Ensure package manager repositories are configured", "Yes", ""),
    (15, "1.6.2 Ensure address space layout randomization (ASLR) is enabled", "Yes", ""),
    (16, "3.5.3.1 Ensure iptables are flushed", "Yes", ""),
    (17, "4.2.1.1 Ensure rsyslog is installed", "Yes", ""),
    (18, "4.2.1.3 Ensure logging is configured", "Yes", ""),
    (19, "5.2.1 Ensure permissions on /etc/ssh/sshd_config are configured", "No", "Set ownership of /etc/ssh/sshd_config to root:root and restrict permissions to 600."),
    (20, "5.2.13 Ensure only strong ciphers are used", "Yes", ""),
    (21, "5.3.1 Ensure password creation requirements are configured", "No", "Install libpam-pwquality, configure PAM to use pam_pwquality.so, and define password length and complexity settings in /etc/security/pwquality.conf."),
]


def references(c, n):
    brand(c, n, "Review Notes and References", "Appendix")
    para(c, "Interpretive notes", 52, 413, 390, H2)
    bullets(
        c,
        [
            "The Linux directory mode <b>drw-rw-r--</b> lacks execute/traverse permission. Read permission can expose directory entries, but opening files also requires traverse permission.",
            "The original NSE screenshot shows the scanner's older severity output. The current NVD CVSS 3.1 base score for CVE-2017-7494 is <b>9.8 Critical</b>.",
            "Compliance results cover only the selected controls in the source assessment and do not constitute full CIS certification.",
        ],
        58,
        378,
        390,
        BODY,
        8,
    )
    card(c, 500, 105, 405, 285, fill=PALE)
    para(c, "References", 528, 360, 350, H2)
    links = [
        ("NVD: CVE-2017-7494", "https://nvd.nist.gov/vuln/detail/CVE-2017-7494"),
        ("Samba security advisory", "https://www.samba.org/samba/security/CVE-2017-7494.html"),
    ]
    y = 315
    for label, url in links:
        para(c, label, 528, y, 340, H3)
        para(c, url, 528, y - 24, 340, SMALL)
        c.linkURL(url, (528, y - 34, 870, y + 5), relative=0)
        y -= 70
    para(c, "Source: Copy of Adversarial Resilience Tempalte 2024.pdf", 528, 160, 340, SMALL)


def build():
    source = Source()
    c = canvas.Canvas(str(OUTPUT), pagesize=PAGE, pageCompression=1)
    c.setTitle("Adversarial Resilience: Faithful Security Assessment Presentation")
    c.setAuthor("NuttyUtility Security Assessment")
    c.setSubject("StaticSpeed Windows and Ubuntu golden-image assessment")
    number = 1

    cover(c); c.showPage(); number += 1
    scenario(c, number); c.showPage(); number += 1

    divider(c, number, "ONE", "Windows Assessment"); c.showPage(); number += 1
    intro(c, number, "CIS Benchmark Compliance Evaluation on Windows",
          "The Windows assessment evaluates selected CIS benchmarks on the provided virtual machine. Each decision is paired with screenshot evidence and a remediation strategy when the control is not met.",
          ["Decide whether each benchmark is compliant.", "Provide screenshot evidence.", "Provide remediation for every failed or unset control."])
    c.showPage(); number += 1
    for page, item, compliant, remediation in WINDOWS:
        benchmark(c, number, "Windows", item, compliant, remediation, source, page)
        c.showPage(); number += 1

    divider(c, number, "TWO", "Ubuntu Assessment"); c.showPage(); number += 1
    intro(c, number, "CIS Benchmark Compliance Evaluation on Ubuntu 18.04",
          "The Ubuntu assessment reviews the security configuration of the Linux golden image against selected CIS controls and retains the terminal evidence for every decision.",
          ["Decide whether each benchmark is compliant.", "Provide terminal screenshot evidence.", "Provide remediation for every failed control."])
    c.showPage(); number += 1
    for page, item, compliant, remediation in UBUNTU:
        benchmark(c, number, "Ubuntu", item, compliant, remediation, source, page)
        c.showPage(); number += 1

    divider(c, number, "THREE", "Access and Forensics"); c.showPage(); number += 1
    intro(c, number, "Access and Forensics",
          "This section evaluates permissions on designated Linux and Windows folders and analyzes packet captures for malicious activity, compromised accounts, and successful file access.",
          ["Identify folder owners and effective permissions.", "Provide commands to correct access.", "Identify attack source, target port, credentials, and affected resources."])
    c.showPage(); number += 1
    qa_slide(c, number, "Access and Permissions - Ubuntu", "Use /home/ustudent/Documents/data to answer the following questions.", [
        ("What is the folder mode?", "<b>drw-rw-r--</b>"),
        ("Who can read the directory entries?", "The owner and group members can read/write; others can read. However, the missing execute bit prevents traversal."),
        ("Who owns the folder?", "<b>ustudent</b>"),
        ("What permission allows only the owner?", "<b>drwx------</b>, numeric mode <b>700</b>"),
        ("Who can read the file inside?", "The file's mode may grant read access, but users also need execute/traverse permission on the containing directory."),
    ])
    c.showPage(); number += 1
    qa_slide(c, number, "Access and Permissions - Windows", "Use C:\\data to answer the following questions.", [
        ("Who can access the folder?", "student, Everyone, Administrators, and SYSTEM"),
        ("Who has full control?", "student, Everyone, Administrators, and SYSTEM"),
        ("How do you remove Everyone?", '<font name="Courier">icacls "C:\\data" /remove "Everyone"</font>'),
        ("How do you grant user2 read access?", '<font name="Courier">icacls "C:\\data" /grant "user2:R"</font>'),
    ])
    c.showPage(); number += 1
    qa_slide(c, number, "Packet Analysis - Brute Force", "Use bruteforce2.pcap on the Ubuntu VM.", [
        ("What was the source IP?", "<b>10.0.2.7</b>"),
        ("What port was targeted?", "<b>23 / Telnet</b>"),
        ("What password was used?", "<b>eSq_</b>"),
        ("Which user was compromised?", "<b>ubu-ustudent</b>"),
    ])
    c.showPage(); number += 1
    qa_slide(c, number, "Packet Analysis - Lateral Movement", "Use lateralmovement.pcap on the Windows VM.", [
        ("What was the source IP?", "<b>10.0.2.7</b>"),
        ("Was the attacker on the same network?", "<b>Yes</b>"),
        ("What port was targeted?", "<b>445 / SMB</b>"),
        ("What file was targeted?", "<b>payroll_20200927000951_1871.xls</b>"),
        ("Was the file accessed?", "<b>Yes</b>"),
    ])
    c.showPage(); number += 1

    divider(c, number, "FOUR", "Vulnerability Assessment"); c.showPage(); number += 1
    intro(c, number, "Vulnerability Assessment",
          "Nmap service discovery and NSE scripts identify the attack surface and critical vulnerabilities on both golden images.",
          ["Identify open ports on Windows and Ubuntu.", "Run an NSE vulnerability scan.", "Document one critical CVE, its score, impact, and remediation."])
    c.showPage(); number += 1
    screenshot_slide(c, number, "Open Ports - Windows", "Nmap service and version scan of the Windows VM.", source, 30,
                     "Observed exposure includes legacy diagnostic services, HTTP, RPC, NetBIOS/SMB, and Remote Desktop.")
    c.showPage(); number += 1
    screenshot_slide(c, number, "Open Ports - Ubuntu", "Nmap service and version scan of the Ubuntu VM.", source, 31,
                     "Observed exposure includes Telnet, FTP, SSH, HTTP, NetBIOS/SMB, and legacy diagnostic services.")
    c.showPage(); number += 1
    screenshot_slide(c, number, "NSE Script Scan", "The nmap-vulners scan identifies CVE-2017-7494 in the Samba service.", source, 32,
                     "The finding is remote code execution through a writable Samba share.")
    c.showPage(); number += 1
    qa_slide(c, number, "Vulnerability Analysis - CVE-2017-7494", "Critical Samba remote code execution finding.", [
        ("CVE and CVSS score", "<b>CVE-2017-7494 — CVSS 3.1: 9.8 Critical</b>"),
        ("Description", "Samba versions from 3.5.0 to vulnerable 4.4.x, 4.5.x, and 4.6.x releases allow a malicious client to upload a shared library to a writable share and cause smbd to execute it."),
        ("Remediation", "Upgrade to a vendor-supported patched Samba release. Restrict writable shares. The historical workaround <font name='Courier'>nt pipe support = no</font> may disrupt Windows clients and should be temporary."),
    ], section="Vulnerability assessment")
    c.showPage(); number += 1
    references(c, number); c.showPage()

    c.save()
    return OUTPUT


if __name__ == "__main__":
    print(build())
