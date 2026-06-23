from __future__ import annotations

import html
from pathlib import Path

import fitz
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, Paragraph, Preformatted, Table, TableStyle


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "Copy of Responding to a Nation-State Cyber Attack 2024 Q2.pdf"
OUTPUT = ROOT / "Responding to a Nation-State Cyber Attack - Final.pdf"
ASSETS = ROOT / "presentation_assets"

PAGE_W, PAGE_H = letter
NAVY = colors.HexColor("#293E4B")
TEAL = colors.HexColor("#17B978")
CYAN = colors.HexColor("#16A9E0")
TEXT = colors.HexColor("#53565A")
LIGHT = colors.HexColor("#F3F6F7")
BORDER = colors.HexColor("#CFD8DC")


def extract_assets() -> dict[str, Path]:
    ASSETS.mkdir(exist_ok=True)
    doc = fitz.open(SOURCE)
    items = {
        "cover": 15,
        "logo": 31,
        "hids": 87,
        "ssh": 110,
        "openvas": 130,
    }
    result = {}
    for name, xref in items.items():
        data = doc.extract_image(xref)
        path = ASSETS / f"{name}.{data['ext']}"
        path.write_bytes(data["image"])
        result[name] = path
    return result


BODY = ParagraphStyle(
    "body",
    fontName="Helvetica",
    fontSize=15,
    leading=21,
    textColor=TEXT,
)
BODY_SMALL = ParagraphStyle(
    "body-small",
    parent=BODY,
    fontSize=12.2,
    leading=17,
)
BULLET = ParagraphStyle(
    "bullet",
    parent=BODY,
    leftIndent=18,
    firstLineIndent=-11,
    bulletIndent=0,
    spaceAfter=7,
)
BULLET_SMALL = ParagraphStyle(
    "bullet-small",
    parent=BULLET,
    fontSize=12,
    leading=16,
    spaceAfter=4,
)
CODE = ParagraphStyle(
    "code",
    fontName="Courier",
    fontSize=9.1,
    leading=11.5,
    textColor=colors.HexColor("#263238"),
    leftIndent=9,
    rightIndent=9,
    borderColor=BORDER,
    borderWidth=0.7,
    borderPadding=8,
    backColor=colors.white,
)
CODE_SMALL = ParagraphStyle(
    "code-small",
    parent=CODE,
    fontSize=7.6,
    leading=9.3,
)


def inline(text: str) -> str:
    return html.escape(text, quote=False).replace("`", "")


def draw_logo(c: canvas.Canvas, assets: dict[str, Path], white: bool = False):
    if white:
        c.setStrokeColor(colors.white)
        c.setLineWidth(2)
        c.arc(PAGE_W - 47, PAGE_H - 48, PAGE_W - 22, PAGE_H - 23, 180, 180)
        c.line(PAGE_W - 47, PAGE_H - 35, PAGE_W - 47, PAGE_H - 51)
        c.line(PAGE_W - 22, PAGE_H - 35, PAGE_W - 22, PAGE_H - 51)
    else:
        c.drawImage(str(assets["logo"]), PAGE_W - 61, PAGE_H - 60, 42, 42, mask="auto")


def title(c: canvas.Canvas, assets: dict[str, Path], text: str, subtitle: str | None = None):
    draw_logo(c, assets)
    c.setFillColor(TEAL)
    c.rect(0, PAGE_H - 194, 4, 96, stroke=0, fill=1)
    c.setFillColor(CYAN)
    c.setFont("Helvetica", 29)
    c.drawString(37, PAGE_H - 160, text)
    if subtitle:
        c.setFillColor(TEXT)
        c.setFont("Helvetica", 10)
        c.drawRightString(PAGE_W - 25, PAGE_H - 180, subtitle)


def footer(c: canvas.Canvas, number: int):
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#9AA5AA"))
    c.drawRightString(PAGE_W - 22, 18, str(number))


def paragraph(c: canvas.Canvas, text: str, x: float, y_top: float, width: float, style=BODY):
    p = Paragraph(inline(text), style)
    _, height = p.wrap(width, PAGE_H)
    p.drawOn(c, x, y_top - height)
    return y_top - height


def bullets(c: canvas.Canvas, items: list[str], x: float, y_top: float, width: float, style=BULLET):
    y = y_top
    for item in items:
        p = Paragraph(f"• {inline(item)}", style)
        _, height = p.wrap(width, PAGE_H)
        p.drawOn(c, x, y - height)
        y -= height
    return y


def code(c: canvas.Canvas, text: str, x: float, y_top: float, width: float, style=CODE):
    p = Preformatted(text.strip(), style)
    _, height = p.wrap(width, PAGE_H)
    p.drawOn(c, x, y_top - height)
    return y_top - height


def screenshot(c: canvas.Canvas, path: Path, x: float, y: float, width: float, height: float):
    c.drawImage(str(path), x, y, width, height, preserveAspectRatio=True, anchor="c")
    c.setStrokeColor(BORDER)
    c.rect(x, y, width, height, stroke=1, fill=0)


def section_slide(c: canvas.Canvas, assets: dict[str, Path], number: int, section: str):
    c.setFillColor(NAVY)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    draw_logo(c, assets, white=True)
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 28)
    c.drawString(56, 420, f"Section {number}:")
    c.drawString(56, 382, section)
    c.setFillColor(TEAL)
    c.rect(56, 330, 98, 3, stroke=0, fill=1)


def cover_slide(c: canvas.Canvas, assets: dict[str, Path]):
    c.setFillColor(colors.white)
    c.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    c.setFillColor(CYAN)
    c.rect(0, 68, PAGE_W, PAGE_H - 136, stroke=0, fill=1)
    c.drawImage(str(assets["cover"]), 78, 185, 456, 456, preserveAspectRatio=True, mask="auto")
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 25)
    c.drawCentredString(PAGE_W / 2, 708, "Responding to a")
    c.drawCentredString(PAGE_W / 2, 676, "Nation-State Cyber Attack")
    c.setFont("Helvetica-BoldOblique", 14)
    c.drawCentredString(PAGE_W / 2, 115, "Samuel Hailemariam")
    c.drawCentredString(PAGE_W / 2, 94, "23 June 2026")


def project_overview(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "Project Overview")
    paragraph(
        c,
        "A Linux jump host connecting the Tridanium processing plant to the internet was compromised during a national holiday. The response focused on three objectives:",
        38,
        575,
        535,
    )
    bullets(
        c,
        [
            "Detect malware, command-and-control infrastructure, and host indicators.",
            "Contain access, block the attacker, remove persistence, and secure SSH.",
            "Scan for vulnerabilities and harden the exposed Apache service.",
        ],
        50,
        465,
        510,
    )
    c.setFillColor(LIGHT)
    c.roundRect(38, 160, 535, 135, 7, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(56, 264, "Final deliverables")
    bullets(
        c,
        [
            "Threat evidence and indicators of compromise",
            "YARA and iptables controls",
            "SSH and Apache hardening changes",
            "Executive-level incident summary",
        ],
        58,
        240,
        485,
        BULLET_SMALL,
    )


def scenario_one(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "What Are We Doing?")
    paragraph(
        c,
        "South Udan developed a cleaner Tridanium nuclear-fission process that generates significantly more energy while reducing nuclear waste.",
        38,
        570,
        535,
    )
    paragraph(
        c,
        "North Udan, still dependent on fossil fuels, sought to disrupt the program through a state-sponsored cyberattack.",
        38,
        420,
        535,
    )
    c.setFillColor(LIGHT)
    c.roundRect(38, 175, 535, 125, 7, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(58, 260, "Target")
    c.setFont("Helvetica", 15)
    c.setFillColor(TEXT)
    c.drawString(58, 225, "Internet-connected Linux jump host")
    c.drawString(58, 198, "Tridanium processing plant")


def scenario_two(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "What Are We Doing?")
    paragraph(
        c,
        "The National Peace Agency launched the attack during a South Udan national holiday. Password brute forcing against an employee account triggered the initial alarm.",
        38,
        580,
        535,
    )
    bullets(
        c,
        [
            "The attacker obtained SSH access to the jump host.",
            "A rogue account and root-owned backdoor were created for persistence.",
            "The host was mission-critical, requiring immediate containment and hardening.",
            "The investigation started from the compromised jump box.",
        ],
        48,
        430,
        510,
    )


def clamav_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "ClamAV Scan")
    paragraph(c, "Command executed: clamscan -r /home/ubuntu/Downloads/", 38, 590, 535, BODY_SMALL)
    scan = """
/home/ubuntu/Downloads/moni.lod: OK
/home/ubuntu/Downloads/notes.txt: OK
/home/ubuntu/Downloads/SSH-One: OK
/home/ubuntu/Downloads/gates.lod: OK
/home/ubuntu/Downloads/ft32: Unix.Malware.Agent-6774375-0 FOUND
/home/ubuntu/Downloads/ft64: Unix.Malware.Agent-6774336-0 FOUND
/home/ubuntu/Downloads/wipefs: Unix.Tool.Miner-6443173-0 FOUND
/home/ubuntu/Downloads/tmplog: OK

----------- SCAN SUMMARY -----------
Known viruses: 8874078
Engine version: 0.100.3
"""
    code(c, scan, 34, 550, 544, CODE_SMALL)
    c.setFillColor(colors.HexColor("#A33A3A"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(38, 112, "Evidence note: the source capture did not preserve the remaining ClamAV summary lines.")


def suspicious_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "Suspicious File Identification")
    data = [
        ["Suspicious file", "SSH-One"],
        ["Callout URL 1", "http://darkl0rd.com:7758/SSH-T"],
        ["Callout URL 2", "http://darkl0rd.com:7758/SSH-One"],
    ]
    t = Table(data, colWidths=[135, 385], rowHeights=[42, 58, 58])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.7, BORDER),
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Courier"),
                ("FONTSIZE", (0, 0), (-1, -1), 11),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    t.wrapOn(c, 520, 200)
    t.drawOn(c, 42, 355)
    paragraph(
        c,
        "Assessment: SSH-One is a Bash downloader that contacts darkl0rd.com on TCP port 7758 and retrieves additional payloads. It evaded the original ClamAV scan.",
        42,
        310,
        520,
        BODY_SMALL,
    )


def yara_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "YARA Rule Creation")
    yara = """
rule NPA_Darkl0rd_Domain
{
    meta:
        description = "Detects the darkl0rd.com C2 domain"
        author = "Samuel Hailemariam"
        date = "2026-06-23"
        severity = "high"

    strings:
        $domain = "darkl0rd.com" ascii wide nocase
        $url_ssh_t = "http://darkl0rd.com:7758/SSH-T" ascii nocase
        $url_ssh_one = "http://darkl0rd.com:7758/SSH-One" ascii nocase

    condition:
        $domain or any of ($url_*)
}
"""
    code(c, yara, 36, 590, 540, CODE)
    paragraph(c, "Validation: yara npa_darkl0rd_domain.yar /home/ubuntu/Downloads/", 38, 148, 530, BODY_SMALL)


def hids_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "Implement HIDS")
    paragraph(
        c,
        "OSSEC monitored the server while an SSH login was performed. The event view records authentication success and an opened SSH session for ubuntu.",
        38,
        590,
        535,
        BODY_SMALL,
    )
    screenshot(c, assets["hids"], 24, 115, 564, 352)


def attacker_ip_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "Locate Suspicious IP")
    paragraph(
        c,
        "OSSEC authentication events were reviewed for failed logins followed by successful access and privilege escalation.",
        38,
        575,
        535,
    )
    c.setFillColor(LIGHT)
    c.roundRect(38, 315, 535, 145, 8, stroke=0, fill=1)
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(58, 418, "Attacker source IP")
    c.setFillColor(CYAN)
    c.setFont("Courier-Bold", 32)
    c.drawCentredString(PAGE_W / 2, 350, "192.168.56.1")
    paragraph(
        c,
        "This address is an indicator of compromise for containment and correlation; it is not sufficient by itself for permanent attribution.",
        48,
        255,
        515,
        BODY_SMALL,
    )


def iptables_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "IPtables Rule")
    paragraph(c, "Block SSH connections from the identified attacker address:", 38, 570, 535)
    code(
        c,
        "sudo iptables -I INPUT 1 -p tcp \\\n  -s 192.168.56.1 --dport 22 -j DROP",
        40,
        475,
        530,
        CODE,
    )
    paragraph(c, "Verify and persist the rule:", 38, 330, 535, BODY_SMALL)
    code(
        c,
        "sudo iptables -L INPUT -n --line-numbers\nsudo netfilter-persistent save",
        40,
        275,
        530,
        CODE,
    )


def backdoor_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "Detect Username, Process & Port")
    data = [
        ["Backdoor user", "darklord"],
        ["Backdoor process", "remotesec"],
        ["Listening endpoint", "0.0.0.0:56565/tcp"],
    ]
    t = Table(data, colWidths=[200, 325], rowHeights=[58, 58, 58])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.8, BORDER),
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Courier-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 15),
                ("TEXTCOLOR", (1, 0), (1, -1), NAVY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    t.wrapOn(c, 525, 220)
    t.drawOn(c, 42, 335)
    bullets(
        c,
        [
            "Terminate the process after evidence preservation.",
            "Lock and remove the rogue account.",
            "Search systemd, cron, SSH keys, and startup files for persistence.",
        ],
        50,
        285,
        510,
        BULLET_SMALL,
    )


def ssh_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "Disable SSH Root Access")
    screenshot(c, assets["ssh"], 24, 320, 564, 352)
    paragraph(c, "Configuration file: /etc/ssh/sshd_config", 38, 285, 535, BODY_SMALL)
    code(c, "PermitRootLogin no", 40, 232, 530, CODE)
    paragraph(
        c,
        "Validate with sudo sshd -t, reload SSH, and test a second non-root session before closing the current session.",
        38,
        142,
        535,
        BODY_SMALL,
    )


def recommendations_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "Remote Access & Password Security")
    bullets(
        c,
        [
            "Require MFA for VPN, bastion, privileged, and break-glass access.",
            "Route administrative SSH through an approved VPN or hardened bastion.",
            "Disable password authentication after managed key access is tested.",
            "Use individual accounts, least privilege, sudo, and session logging.",
            "Rate-limit failed authentication and centralize HIDS and SSH alerts.",
            "Require long, unique passphrases and block compromised passwords.",
            "Store credentials in approved password and secrets managers.",
            "Rotate credentials and revoke keys immediately after compromise.",
            "Inventory, expire, and remove dormant accounts and stale SSH keys.",
        ],
        42,
        590,
        530,
        BULLET_SMALL,
    )


def openvas_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "OpenVAS Scan")
    screenshot(c, assets["openvas"], 18, 300, 576, 328)
    paragraph(
        c,
        "Scan date visible: Tuesday, 23 June 2026 at 7:55 PM. The report shows 89 results for host 192.168.56.101, including SSH protocol, exposed service, OS-detection, and OpenSSH findings.",
        38,
        265,
        535,
        BODY_SMALL,
    )
    bullets(
        c,
        [
            "Validate and prioritize actionable findings.",
            "Patch supported packages and remove unnecessary services.",
            "Rescan and document residual risk.",
        ],
        48,
        165,
        510,
        BULLET_SMALL,
    )


def apache_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "Patching Apache")
    data = [
        ["Current version", "Apache HTTP Server 2.4.7"],
        ["Configuration file", "/etc/apache2/conf-available/security.conf"],
    ]
    t = Table(data, colWidths=[155, 370], rowHeights=[52, 60])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.7, BORDER),
                ("BACKGROUND", (0, 0), (0, -1), LIGHT),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Courier"),
                ("FONTSIZE", (0, 0), (-1, -1), 10.5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    t.wrapOn(c, 525, 150)
    t.drawOn(c, 42, 445)
    paragraph(c, "Required banner-hardening settings:", 42, 400, 520, BODY_SMALL)
    code(c, "ServerTokens Prod\nServerSignature Off", 42, 345, 525, CODE)
    bullets(
        c,
        [
            "Run apache2ctl configtest and reload Apache.",
            "Verify with curl -I http://127.0.0.1/.",
            "Upgrade Apache through the supported operating-system package channel.",
        ],
        48,
        220,
        510,
        BULLET_SMALL,
    )


def apache_account_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "De-Privilege Apache Account")
    code(
        c,
        "sudo groupadd --system apache-group\n"
        "sudo useradd --system --gid apache-group \\\n"
        "  --no-create-home --shell /usr/sbin/nologin apache-user\n"
        "sudo chown -R apache-user:apache-group /etc/apache2",
        38,
        590,
        535,
        CODE_SMALL,
    )
    paragraph(c, "Configuration file: /etc/apache2/envvars", 38, 395, 535, BODY_SMALL)
    code(
        c,
        "Replace:\n"
        "export APACHE_RUN_USER=www-data\n"
        "export APACHE_RUN_GROUP=www-data\n\n"
        "With:\n"
        "export APACHE_RUN_USER=apache-user\n"
        "export APACHE_RUN_GROUP=apache-group",
        38,
        345,
        535,
        CODE_SMALL,
    )
    paragraph(
        c,
        "Production note: Apache configuration is normally root-owned. Delegate only required writable runtime paths outside this lab requirement.",
        38,
        115,
        535,
        BODY_SMALL,
    )


def executive_slide(c: canvas.Canvas, assets: dict[str, Path]):
    title(c, assets, "Executive Summary")
    bullets(
        c,
        [
            "A password-based SSH attack compromised the Tridanium plant's Linux jump host.",
            "ClamAV identified three malicious tools; manual analysis found an additional downloader contacting darkl0rd.com:7758.",
            "The attacker used source IP 192.168.56.1 and established persistence with user darklord and the remotesec backdoor on TCP 56565.",
            "Containment included HIDS validation, firewall blocking, SSH root-login denial, and documented eradication actions.",
            "OpenVAS and Apache hardening reduced exposed attack surface and service privilege.",
            "Because a privileged backdoor ran on the host, the safest recovery is rebuild from a known-good image, rotate all exposed credentials, and monitor the identified indicators.",
        ],
        42,
        590,
        530,
        BULLET_SMALL,
    )
    c.setFillColor(NAVY)
    c.roundRect(42, 104, 525, 90, 7, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(60, 162, "Strategic outcome")
    c.setFont("Helvetica", 11)
    c.drawString(60, 135, "Attack contained, persistence identified, and a hardened recovery path defined.")


def build():
    assets = extract_assets()
    c = canvas.Canvas(
        str(OUTPUT),
        pagesize=letter,
        pageCompression=1,
    )
    c.setTitle("Responding to a Nation-State Cyber Attack")
    c.setAuthor("Samuel Hailemariam")
    c.setSubject("Incident response presentation")

    slides = [
        lambda: cover_slide(c, assets),
        lambda: project_overview(c, assets),
        lambda: section_slide(c, assets, 0, "Project Scenario"),
        lambda: scenario_one(c, assets),
        lambda: scenario_two(c, assets),
        lambda: section_slide(c, assets, 1, "Detection"),
        lambda: clamav_slide(c, assets),
        lambda: suspicious_slide(c, assets),
        lambda: yara_slide(c, assets),
        lambda: section_slide(c, assets, 2, "Mitigation"),
        lambda: hids_slide(c, assets),
        lambda: attacker_ip_slide(c, assets),
        lambda: iptables_slide(c, assets),
        lambda: backdoor_slide(c, assets),
        lambda: ssh_slide(c, assets),
        lambda: recommendations_slide(c, assets),
        lambda: section_slide(c, assets, 3, "Hardening"),
        lambda: openvas_slide(c, assets),
        lambda: apache_slide(c, assets),
        lambda: apache_account_slide(c, assets),
        lambda: executive_slide(c, assets),
    ]

    for number, draw in enumerate(slides, start=1):
        draw()
        if number not in {1, 3, 6, 10, 17}:
            footer(c, number)
        c.showPage()

    c.save()
    print(OUTPUT)


if __name__ == "__main__":
    build()
