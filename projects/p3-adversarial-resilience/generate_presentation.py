from __future__ import annotations

from io import BytesIO
from pathlib import Path

import fitz
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).resolve().parent
SOURCE_PDF = ROOT / "Copy of Adversarial Resilience Tempalte 2024.pdf"
OUTPUT_PDF = ROOT / "Adversarial_Resilience_Security_Assessment_Presentation.pdf"

# 16:9 widescreen slide size in points.
PAGE = landscape((540, 960))
W, H = PAGE

NAVY = HexColor("#102A43")
INK = HexColor("#243B53")
MUTED = HexColor("#627D98")
PALE = HexColor("#F0F4F8")
LINE = HexColor("#D9E2EC")
CYAN = HexColor("#00A8C6")
TEAL = HexColor("#0E918C")
GREEN = HexColor("#2F9E68")
AMBER = HexColor("#F5A623")
RED = HexColor("#D64545")
SOFT_RED = HexColor("#FDECEC")
SOFT_AMBER = HexColor("#FFF4D6")
SOFT_GREEN = HexColor("#E8F7EF")


def style(
    name: str,
    size: float,
    color=INK,
    leading: float | None = None,
    font: str = "Helvetica",
    align: int = TA_LEFT,
) -> ParagraphStyle:
    return ParagraphStyle(
        name,
        fontName=font,
        fontSize=size,
        leading=leading or size * 1.22,
        textColor=color,
        alignment=align,
        spaceAfter=0,
        spaceBefore=0,
    )


TITLE = style("title", 28, NAVY, 32, "Helvetica-Bold")
H2 = style("h2", 20, NAVY, 24, "Helvetica-Bold")
H3 = style("h3", 13, NAVY, 16, "Helvetica-Bold")
BODY = style("body", 11, INK, 15)
SMALL = style("small", 8.5, MUTED, 11)
WHITE_BODY = style("white-body", 11, white, 15)
WHITE_SMALL = style("white-small", 8.5, white, 11)
CENTER_SMALL = style("center-small", 9, MUTED, 11, align=TA_CENTER)


def paragraph(c: canvas.Canvas, text: str, x: float, y_top: float, width: float, st=BODY) -> float:
    p = Paragraph(text, st)
    _, height = p.wrap(width, H)
    p.drawOn(c, x, y_top - height)
    return height


def rounded_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    fill=white,
    stroke=LINE,
    radius: float = 12,
) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(0.8)
    c.roundRect(x, y, width, height, radius, fill=1, stroke=1)


def slide_header(c: canvas.Canvas, number: int, title: str, eyebrow: str | None = None) -> None:
    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, H - 11, W, 11, fill=1, stroke=0)
    if eyebrow:
        paragraph(c, eyebrow.upper(), 52, H - 38, 840, style("eyebrow", 8.5, TEAL, 10, "Helvetica-Bold"))
    paragraph(c, title, 52, H - 58, 830, TITLE)
    c.setStrokeColor(LINE)
    c.line(52, 37, W - 52, 37)
    c.setFont("Helvetica", 7.5)
    c.setFillColor(MUTED)
    c.drawString(52, 22, "ADVERSARIAL RESILIENCE | STATICSpeed SECURITY ASSESSMENT")
    c.drawRightString(W - 52, 22, f"{number:02d}")


def pill(c: canvas.Canvas, text: str, x: float, y: float, color, width: float | None = None) -> float:
    width = width or stringWidth(text, "Helvetica-Bold", 8) + 20
    c.setFillColor(Color(color.red, color.green, color.blue, alpha=0.13))
    c.setStrokeColor(color)
    c.roundRect(x, y, width, 22, 11, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(color)
    c.drawCentredString(x + width / 2, y + 7, text)
    return width


def metric_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    width: float,
    height: float,
    value: str,
    label: str,
    color,
    note: str = "",
) -> None:
    rounded_card(c, x, y, width, height)
    c.setFillColor(color)
    c.roundRect(x + 16, y + height - 45, 42, 28, 8, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(white)
    c.drawCentredString(x + 37, y + height - 35, value)
    paragraph(c, label, x + 16, y + height - 60, width - 32, H3)
    if note:
        paragraph(c, note, x + 16, y + 34, width - 32, SMALL)


class Evidence:
    def __init__(self, source: Path):
        self.doc = fitz.open(source)
        self.cache: dict[tuple[int, tuple[float, float, float, float] | None], ImageReader] = {}

    def image(
        self,
        page_number: int,
        crop: tuple[float, float, float, float] | None = None,
        scale: float = 1.7,
    ) -> ImageReader:
        key = (page_number, crop)
        if key in self.cache:
            return self.cache[key]
        page = self.doc[page_number - 1]
        clip = None
        if crop:
            x0, y0, x1, y1 = crop
            clip = fitz.Rect(
                page.rect.x0 + page.rect.width * x0,
                page.rect.y0 + page.rect.height * y0,
                page.rect.x0 + page.rect.width * x1,
                page.rect.y0 + page.rect.height * y1,
            )
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
        reader = ImageReader(BytesIO(pix.tobytes("png")))
        self.cache[key] = reader
        return reader


def draw_image_contain(
    c: canvas.Canvas,
    image: ImageReader,
    x: float,
    y: float,
    width: float,
    height: float,
    border: bool = True,
) -> None:
    iw, ih = image.getSize()
    ratio = min(width / iw, height / ih)
    dw, dh = iw * ratio, ih * ratio
    dx, dy = x + (width - dw) / 2, y + (height - dh) / 2
    if border:
        rounded_card(c, x, y, width, height, fill=white, stroke=LINE, radius=8)
    c.drawImage(image, dx, dy, dw, dh, preserveAspectRatio=True, mask="auto")


def bullets(c: canvas.Canvas, items: list[str], x: float, y_top: float, width: float, st=BODY, gap: float = 8) -> float:
    y = y_top
    for item in items:
        c.setFillColor(CYAN)
        c.circle(x + 4, y - 7, 2.6, fill=1, stroke=0)
        height = paragraph(c, item, x + 16, y, width - 16, st)
        y -= height + gap
    return y


def risk_row(
    c: canvas.Canvas,
    y: float,
    severity: str,
    finding: str,
    impact: str,
    color,
) -> None:
    rounded_card(c, 68, y, 824, 46, fill=white, stroke=LINE, radius=8)
    pill(c, severity, 82, y + 12, color, 82)
    paragraph(c, finding, 182, y + 34, 300, style("risk-find", 10, NAVY, 12, "Helvetica-Bold"))
    paragraph(c, impact, 500, y + 34, 370, SMALL)


def add_slide_1(c: canvas.Canvas) -> None:
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, H - 14, W, 14, fill=1, stroke=0)
    c.setFillColor(Color(0, 0.66, 0.78, alpha=0.16))
    c.circle(825, 90, 260, fill=1, stroke=0)
    c.circle(880, 500, 175, fill=1, stroke=0)
    paragraph(c, "ADVERSARIAL RESILIENCE", 72, H - 92, 500, style("cover-eye", 10, CYAN, 12, "Helvetica-Bold"))
    paragraph(c, "Security Assessment<br/>and Integration Readiness", 72, H - 145, 650, style("cover-title", 34, white, 39, "Helvetica-Bold"))
    paragraph(
        c,
        "StaticSpeed golden images assessed for CIS alignment, access control, attack evidence, network exposure, and critical vulnerabilities.",
        72,
        H - 260,
        620,
        WHITE_BODY,
    )
    pill(c, "INTEGRATION HOLD", 72, 170, RED, 142)
    paragraph(c, "Prepared for NuttyUtility stakeholders", 72, 125, 460, WHITE_SMALL)
    paragraph(c, "25 June 2026", 72, 101, 460, WHITE_SMALL)
    c.setFont("Helvetica-Bold", 90)
    c.setFillColor(Color(1, 1, 1, alpha=0.08))
    c.drawRightString(W - 65, 70, "01")


def add_slide_2(c: canvas.Canvas) -> None:
    slide_header(c, 2, "Executive decision", "Integration readiness")
    rounded_card(c, 52, 270, 856, 185, fill=NAVY, stroke=NAVY, radius=16)
    paragraph(c, "Do not integrate StaticSpeed into the extended network yet.", 80, 420, 800, style("decision", 25, white, 30, "Helvetica-Bold"))
    paragraph(
        c,
        "The assessed images expose a credible path from weak configuration to credential compromise, lateral movement, and remote code execution.",
        80,
        355,
        770,
        WHITE_BODY,
    )
    metric_card(c, 52, 112, 200, 125, "0/6", "Windows controls compliant", RED, "All sampled Windows CIS controls failed.")
    metric_card(c, 270, 112, 200, 125, "6/8", "Ubuntu controls compliant", AMBER, "Two high-impact baseline gaps remain.")
    metric_card(c, 488, 112, 200, 125, "9.8", "Critical CVSS score", RED, "Samba RCE, CVE-2017-7494.")
    metric_card(c, 706, 112, 202, 125, "2", "Successful attack outcomes", RED, "Credential compromise and file access.")


def add_slide_3(c: canvas.Canvas) -> None:
    slide_header(c, 3, "Assessment scope and evidence", "Method")
    cards = [
        ("CIS configuration", "6 Windows and 8 Ubuntu benchmark checks, supported by policy, registry, and terminal screenshots."),
        ("Access control", "Linux directory permissions and Windows NTFS access on the designated data folders."),
        ("Forensics", "PCAP review for brute force activity and SMB lateral movement."),
        ("Vulnerability discovery", "Nmap service discovery and NSE vulnerability scanning on both golden images."),
    ]
    for i, (title, text) in enumerate(cards):
        x = 52 + (i % 2) * 438
        y = 267 - (i // 2) * 145
        rounded_card(c, x, y, 418, 120)
        c.setFillColor(CYAN if i < 2 else TEAL)
        c.circle(x + 34, y + 85, 14, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + 34, y + 81, str(i + 1))
        paragraph(c, title, x + 60, y + 103, 330, H3)
        paragraph(c, text, x + 60, y + 76, 330, SMALL)
    paragraph(
        c,
        "<b>Scoring note:</b> the compliance percentage treats each sampled benchmark equally. It is a directional readiness indicator, not a complete CIS certification.",
        52,
        82,
        856,
        SMALL,
    )


def add_slide_4(c: canvas.Canvas) -> None:
    slide_header(c, 4, "Security posture at a glance", "Findings")
    rounded_card(c, 52, 258, 408, 130, fill=SOFT_RED, stroke=RED)
    paragraph(c, "Windows baseline", 76, 361, 220, H3)
    paragraph(c, "0%", 76, 332, 160, style("pct-red", 34, RED, 38, "Helvetica-Bold"))
    paragraph(c, "Six of six sampled controls require remediation.", 190, 330, 230, SMALL)
    rounded_card(c, 500, 258, 408, 130, fill=SOFT_AMBER, stroke=AMBER)
    paragraph(c, "Ubuntu baseline", 524, 361, 220, H3)
    paragraph(c, "75%", 524, 332, 160, style("pct-amber", 34, AMBER, 38, "Helvetica-Bold"))
    paragraph(c, "Six of eight sampled controls passed.", 650, 330, 220, SMALL)
    risks = [
        ("CRITICAL", "Samba remote code execution", "Network-accessible code execution on the Ubuntu image.", RED),
        ("CRITICAL", "Compromised credentials over Telnet", "Cleartext service exposure enabled account compromise.", RED),
        ("HIGH", "SMB lateral movement succeeded", "The payroll file was accessed from the attack source.", RED),
        ("HIGH", "Weak identity and patch controls", "Password, lockout, administrator, and update controls failed.", AMBER),
    ]
    y = 188
    for row in risks:
        risk_row(c, y, *row)
        y -= 56


def add_slide_5(c: canvas.Canvas, ev: Evidence) -> None:
    slide_header(c, 5, "Windows: every sampled control failed", "CIS benchmark review")
    left = [
        "<b>1.1.5</b> Password complexity not enabled",
        "<b>1.2.1</b> Account lockout duration below 15 minutes",
        "<b>2.2.2</b> Network logon right overly broad",
        "<b>2.3.1.1</b> Built-in Administrator account enabled",
        "<b>18.3.4</b> SEHOP not enabled",
        "<b>18.9.102.2</b> Automatic updates not enabled",
    ]
    bullets(c, left, 62, 390, 390, style("win-bullets", 10, INK, 13), 6)
    rounded_card(c, 52, 84, 410, 82, fill=SOFT_RED, stroke=RED)
    paragraph(c, "<b>Business effect:</b> weak authentication, elevated persistence risk, avoidable exploitability, and delayed patching.", 70, 145, 374, SMALL)
    draw_image_contain(c, ev.image(6, (0, 0.28, 1, 1)), 500, 225, 185, 190)
    draw_image_contain(c, ev.image(10, (0, 0.28, 1, 1)), 704, 225, 185, 190)
    draw_image_contain(c, ev.image(11, (0, 0.28, 1, 1)), 500, 64, 389, 145)


def add_slide_6(c: canvas.Canvas, ev: Evidence) -> None:
    slide_header(c, 6, "Ubuntu: stronger baseline, two material gaps", "CIS benchmark review")
    metric_card(c, 52, 292, 190, 102, "6", "Controls passed", GREEN, "Repositories, ASLR, iptables, rsyslog, logging, and ciphers.")
    metric_card(c, 258, 292, 190, 102, "2", "Controls failed", AMBER, "SSH configuration permissions and password quality.")
    paragraph(c, "Required remediation", 52, 255, 390, H3)
    bullets(
        c,
        [
            "<b>SSH configuration:</b> set <font name='Courier'>/etc/ssh/sshd_config</font> ownership to root:root and mode to 600.",
            "<b>Password quality:</b> install and configure libpam-pwquality, then enforce minimum length and complexity in PAM.",
            "<b>Validation:</b> re-run checks after remediation and capture evidence from the rebuilt golden image.",
        ],
        58,
        228,
        390,
        style("ubuntu-bullets", 9.5, INK, 13),
        7,
    )
    draw_image_contain(c, ev.image(19, (0, 0.25, 1, 1)), 500, 235, 190, 180)
    draw_image_contain(c, ev.image(21, (0, 0.25, 1, 1)), 710, 235, 190, 180)
    rounded_card(c, 500, 76, 400, 135, fill=SOFT_GREEN, stroke=GREEN)
    paragraph(c, "What is already working", 522, 185, 350, H3)
    paragraph(c, "ASLR, repository configuration, firewall state, logging services, and strong SSH ciphers all showed compliant evidence.", 522, 150, 350, SMALL)


def add_slide_7(c: canvas.Canvas, ev: Evidence) -> None:
    slide_header(c, 7, "Access controls allow unnecessary exposure", "Permissions")
    rounded_card(c, 52, 238, 408, 165, fill=SOFT_AMBER, stroke=AMBER)
    paragraph(c, "Ubuntu data directory", 74, 378, 350, H3)
    paragraph(c, "<b>Observed:</b> drw-rw-r--", 74, 348, 350, BODY)
    paragraph(
        c,
        "The directory lacks execute/traverse bits. Read permission may expose names, but users cannot reliably access entries without execute permission. Set owner-only access to <b>drwx------ (700)</b>.",
        74,
        319,
        350,
        SMALL,
    )
    rounded_card(c, 500, 238, 408, 165, fill=SOFT_RED, stroke=RED)
    paragraph(c, "Windows data folder", 522, 378, 350, H3)
    paragraph(c, "<b>Observed:</b> Everyone has full control", 522, 348, 350, BODY)
    paragraph(
        c,
        "This permits broad read, modify, and deletion rights. Remove Everyone and grant named users only the permissions required for their role.",
        522,
        319,
        350,
        SMALL,
    )
    draw_image_contain(c, ev.image(24, (0, 0.12, 1, 0.85)), 52, 74, 408, 145)
    draw_image_contain(c, ev.image(25, (0, 0.12, 1, 0.82)), 500, 74, 408, 145)


def add_slide_8(c: canvas.Canvas) -> None:
    slide_header(c, 8, "Attack evidence confirms exploitable paths", "PCAP analysis")
    c.setStrokeColor(LINE)
    c.setLineWidth(5)
    c.line(110, 250, 850, 250)
    events = [
        (130, RED, "1", "10.0.2.7", "Attack source observed"),
        (340, AMBER, "2", "TCP/23", "Telnet targeted"),
        (550, RED, "3", "ubu-ustudent", "Password eSq_ accepted"),
        (760, RED, "4", "TCP/445", "Payroll file accessed"),
    ]
    for x, color, num, title, caption in events:
        c.setFillColor(color)
        c.circle(x, 250, 19, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x, 246, num)
        paragraph(c, title, x - 80, 216, 160, style(f"event-{num}", 12, NAVY, 15, "Helvetica-Bold", TA_CENTER))
        paragraph(c, caption, x - 85, 180, 170, CENTER_SMALL)
    rounded_card(c, 70, 310, 820, 96, fill=NAVY, stroke=NAVY)
    paragraph(c, "The assessment does not show only theoretical weakness. It records successful credential compromise and successful access to payroll data.", 96, 378, 770, style("attack-summary", 17, white, 21, "Helvetica-Bold", TA_CENTER))
    rounded_card(c, 70, 72, 820, 72, fill=SOFT_RED, stroke=RED)
    paragraph(c, "<b>Immediate containment:</b> disable Telnet, rotate the compromised account and related credentials, isolate SMB exposure, and investigate the accessed payroll file.", 92, 124, 776, SMALL)


def add_slide_9(c: canvas.Canvas, ev: Evidence) -> None:
    slide_header(c, 9, "Network exposure increases the attack surface", "Nmap discovery")
    draw_image_contain(c, ev.image(30, (0, 0.23, 1, 0.92)), 52, 150, 414, 250)
    draw_image_contain(c, ev.image(31, (0, 0.23, 1, 0.92)), 494, 150, 414, 250)
    paragraph(c, "Windows image", 52, 132, 414, H3)
    paragraph(c, "Legacy diagnostic services plus HTTP, RPC, NetBIOS, and SMB are reachable.", 52, 105, 414, SMALL)
    paragraph(c, "Ubuntu image", 494, 132, 414, H3)
    paragraph(c, "Telnet, FTP, SSH, HTTP, NetBIOS, SMB, and legacy services are exposed.", 494, 105, 414, SMALL)
    pill(c, "REDUCE TO REQUIRED SERVICES", 52, 65, RED, 190)
    paragraph(c, "Disable echo, discard, daytime, qotd, chargen, time, Telnet, and FTP unless a documented dependency requires them.", 260, 83, 648, SMALL)


def add_slide_10(c: canvas.Canvas, ev: Evidence) -> None:
    slide_header(c, 10, "Critical vulnerability: Samba remote code execution", "CVE-2017-7494")
    rounded_card(c, 52, 238, 375, 164, fill=SOFT_RED, stroke=RED)
    paragraph(c, "CVSS 3.1", 76, 372, 150, SMALL)
    paragraph(c, "9.8 CRITICAL", 76, 346, 300, style("cvss", 27, RED, 31, "Helvetica-Bold"))
    paragraph(
        c,
        "A malicious client can upload a shared library to a writable Samba share and cause the server to load and execute it.",
        76,
        292,
        325,
        SMALL,
    )
    draw_image_contain(c, ev.image(32, (0, 0.20, 1, 0.94)), 468, 185, 440, 217)
    paragraph(c, "Remediation", 52, 205, 375, H3)
    bullets(
        c,
        [
            "Upgrade to a vendor-supported, patched Samba release.",
            "Remove or tightly restrict writable shares exposed to untrusted clients.",
            "Apply the vendor workaround only as a temporary measure and test client impact.",
        ],
        58,
        178,
        370,
        SMALL,
        4,
    )
    paragraph(
        c,
        "Verified against NVD and the Samba vendor advisory. The original scan screenshot reports an older scanner score; the current NVD CVSS 3.1 base score is 9.8.",
        468,
        155,
        440,
        SMALL,
    )


def add_slide_11(c: canvas.Canvas) -> None:
    slide_header(c, 11, "Prioritized remediation roadmap", "Action plan")
    phases = [
        ("0-24 HOURS", RED, "Contain", [
            "Isolate both golden images from integration paths.",
            "Disable Telnet and unnecessary legacy services.",
            "Rotate compromised credentials and review payroll access.",
            "Patch or remove vulnerable Samba exposure.",
        ]),
        ("7 DAYS", AMBER, "Harden", [
            "Apply Windows password, lockout, administrator, SEHOP, and update policies.",
            "Correct Ubuntu SSH permissions and password quality.",
            "Remove Everyone from C:\\data and set Linux owner-only permissions.",
        ]),
        ("30 DAYS", TEAL, "Prove", [
            "Rebuild golden images through controlled configuration.",
            "Run authenticated CIS scans and service discovery.",
            "Re-test attack paths and archive evidence.",
            "Approve integration only after acceptance criteria pass.",
        ]),
    ]
    for i, (window, color, heading, items) in enumerate(phases):
        x = 52 + i * 292
        rounded_card(c, x, 92, 270, 305, fill=white, stroke=color, radius=12)
        c.setFillColor(color)
        c.roundRect(x, 347, 270, 50, 12, fill=1, stroke=0)
        paragraph(c, window, x + 18, 380, 234, style(f"phase-window-{i}", 8, white, 10, "Helvetica-Bold"))
        paragraph(c, heading, x + 18, 351, 234, style(f"phase-title-{i}", 18, white, 21, "Helvetica-Bold"))
        bullets(c, items, x + 18, 325, 234, SMALL, 6)


def add_slide_12(c: canvas.Canvas) -> None:
    slide_header(c, 12, "Integration acceptance criteria", "Decision gate")
    criteria = [
        ("1", "Configuration", "All sampled CIS failures remediated and independently revalidated."),
        ("2", "Exposure", "Only approved business services reachable; Telnet and legacy diagnostics removed."),
        ("3", "Vulnerabilities", "No critical or high exploitable findings on the release candidate images."),
        ("4", "Access", "Least-privilege permissions confirmed for Linux and Windows data locations."),
        ("5", "Forensics", "Compromised credentials rotated and payroll access investigation closed."),
        ("6", "Evidence", "Screenshots, scan outputs, and change records attached to the approval package."),
    ]
    for i, (num, title, text) in enumerate(criteria):
        x = 52 + (i % 2) * 438
        y = 324 - (i // 2) * 105
        rounded_card(c, x, y, 418, 88, fill=PALE, stroke=LINE)
        c.setFillColor(TEAL)
        c.circle(x + 31, y + 44, 15, fill=1, stroke=0)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + 31, y + 40, num)
        paragraph(c, title, x + 58, y + 68, 330, H3)
        paragraph(c, text, x + 58, y + 43, 330, SMALL)
    rounded_card(c, 52, 58, 856, 50, fill=NAVY, stroke=NAVY)
    paragraph(c, "Decision owner: infrastructure and security stakeholders jointly approve the rebuilt images before network integration.", 72, 92, 816, WHITE_SMALL)


def add_slide_13(c: canvas.Canvas) -> None:
    slide_header(c, 13, "Evidence and source notes", "Appendix")
    paragraph(c, "Source assessment", 52, 388, 360, H3)
    paragraph(
        c,
        "Copy of Adversarial Resilience Tempalte 2024.pdf, 33 pages. The source includes screenshots for configuration checks and Nmap results, plus completed PCAP and permissions findings.",
        52,
        358,
        390,
        BODY,
    )
    paragraph(c, "External verification", 500, 388, 360, H3)
    paragraph(
        c,
        "<b>NVD:</b> CVE-2017-7494, CVSS 3.1 score 9.8.<br/><b>Samba:</b> vendor advisory and fixed release guidance.",
        500,
        358,
        390,
        BODY,
    )
    urls = [
        ("NVD vulnerability record", "https://nvd.nist.gov/vuln/detail/CVE-2017-7494"),
        ("Samba security advisory", "https://www.samba.org/samba/security/CVE-2017-7494.html"),
    ]
    y = 275
    for label, url in urls:
        c.setFillColor(CYAN)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(500, y, label)
        c.linkURL(url, (500, y - 3, 860, y + 13), relative=0)
        paragraph(c, url, 500, y - 13, 390, SMALL)
        y -= 54
    rounded_card(c, 52, 95, 856, 88, fill=SOFT_AMBER, stroke=AMBER)
    paragraph(c, "Review note", 74, 160, 160, H3)
    paragraph(
        c,
        "This presentation preserves the source findings while correcting the Linux directory-permission interpretation and distinguishing the current NVD score from the older score displayed by the scanner.",
        205,
        160,
        675,
        SMALL,
    )


def build() -> Path:
    if not SOURCE_PDF.exists():
        raise FileNotFoundError(SOURCE_PDF)
    ev = Evidence(SOURCE_PDF)
    c = canvas.Canvas(str(OUTPUT_PDF), pagesize=PAGE, pageCompression=1)
    c.setTitle("Adversarial Resilience Security Assessment")
    c.setSubject("StaticSpeed golden image security assessment and integration readiness")
    c.setAuthor("NuttyUtility Security Assessment")

    slides = [
        lambda: add_slide_1(c),
        lambda: add_slide_2(c),
        lambda: add_slide_3(c),
        lambda: add_slide_4(c),
        lambda: add_slide_5(c, ev),
        lambda: add_slide_6(c, ev),
        lambda: add_slide_7(c, ev),
        lambda: add_slide_8(c),
        lambda: add_slide_9(c, ev),
        lambda: add_slide_10(c, ev),
        lambda: add_slide_11(c),
        lambda: add_slide_12(c),
        lambda: add_slide_13(c),
    ]
    for draw in slides:
        draw()
        c.showPage()
    c.save()
    return OUTPUT_PDF


if __name__ == "__main__":
    print(build())
