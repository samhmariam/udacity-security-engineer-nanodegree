"""
Generates an updated TimeSheets Threat Report PDF that aligns with
industry best-practice threat modelling structure:

  Step 0  – Security Objectives & Scope          ← NEW
  Step 1  – Asset Inventory
  Step 2  – Architecture Review (Trust Boundaries / Attack Surface / DFDs)
  Step 3  – Threat Model Diagram
  Step 4  – Identifying Threat Actors            ← MOVED before threats
  Step 5  – Threats to the Organisation (STRIDE) ← MOVED after actors
  Step 6  – Vulnerability Analysis
  Step 7  – Risk Analysis (Likelihood × Impact)
  Step 8  – Mitigation Plan
  Step 9  – Residual Risk Acceptance & Review    ← NEW
"""

import math
from pathlib import Path
from fpdf import FPDF

# ---------------------------------------------------------------------------
# Colour palette (dark navy + slate grey used by typical security reports)
# ---------------------------------------------------------------------------
NAVY = (15, 37, 65)
SLATE = (70, 90, 115)
WHITE = (255, 255, 255)
LIGHT_GREY = (240, 243, 247)
ACCENT = (220, 80, 50)   # red-orange for section dividers


def _sanitise(text: str) -> str:
    """Replace common Unicode typographic chars with ASCII equivalents
    so the built-in Helvetica (Latin-1) font never raises an encoding error."""
    replacements = {
        "\u2013": "-",   # en-dash
        "\u2014": "--",  # em-dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201C": '"',   # left double quote
        "\u201D": '"',   # right double quote
        "\u00d7": "x",   # multiplication sign
        "\u2192": "->",  # right arrow
        "\u2190": "<-",  # left arrow
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class ReportPDF(FPDF):
    """Custom PDF class with branded header/footer helpers."""

    # ------------------------------------------------------------------ helpers
    def _set_font(self, style: str = "", size: int = 11):
        self.set_font("Helvetica", style, size)

    def cover_page(self, title: str, subtitle: str):
        self.add_page()
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, self.h, "F")
        self.set_text_color(*WHITE)
        self._set_font("B", 28)
        self.set_y(60)
        self.multi_cell(0, 12, title, align="C")
        self._set_font("", 16)
        self.set_y(100)
        self.multi_cell(0, 9, subtitle, align="C")
        self._set_font("", 12)
        self.set_y(130)
        self.multi_cell(0, 8, "Security Engineering Nanodegree\nJune 21, 2026", align="C")
        self.set_text_color(0, 0, 0)

    def section_divider(self, section_num: int, title: str):
        """Full-page coloured section divider slide."""
        self.add_page()
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, self.h, "F")
        self.set_fill_color(*ACCENT)
        self.rect(0, 85, self.w, 4, "F")
        self.set_text_color(*WHITE)
        self._set_font("", 13)
        self.set_y(70)
        self.cell(0, 8, _sanitise(f"Section {section_num}"), align="C", new_x="LMARGIN", new_y="NEXT")
        self._set_font("B", 22)
        self.set_y(95)
        self.multi_cell(0, 11, _sanitise(title), align="C")
        self.set_text_color(0, 0, 0)

    def content_page(self, heading: str, body_lines: list[tuple[str, str]]):
        """
        Slide-style content page.
        body_lines: list of (style, text) where style is 'bullet', 'sub',
                    'body', 'label', or 'placeholder'.
        """
        self.add_page()
        # Top colour bar
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, 22, "F")
        self.set_text_color(*WHITE)
        self._set_font("B", 14)
        self.set_xy(10, 6)
        self.multi_cell(self.w - 20, 8, _sanitise(heading), align="L")
        self.set_text_color(0, 0, 0)
        self.set_y(28)

        for style, text in body_lines:
            text = _sanitise(text)
            if style == "label":
                self._set_font("B", 11)
                self.set_fill_color(*LIGHT_GREY)
                self.set_x(10)
                self.multi_cell(self.w - 20, 7, text, align="L", fill=True)
                self.ln(1)
            elif style == "bullet":
                self._set_font("", 10)
                self.set_x(14)
                self.multi_cell(self.w - 24, 6, f"-  {text}", align="L")
            elif style == "sub":
                self._set_font("", 9)
                self.set_x(20)
                self.multi_cell(self.w - 30, 5, f"    o  {text}", align="L")
            elif style == "placeholder":
                self._set_font("I", 10)
                self.set_text_color(*SLATE)
                self.set_x(14)
                self.multi_cell(self.w - 24, 6, text, align="L")
                self.set_text_color(0, 0, 0)
            else:  # 'body'
                self._set_font("", 10)
                self.set_x(10)
                self.multi_cell(self.w - 20, 6, text, align="L")
            self.ln(1)

    def new_section_badge(self, x: float, y: float, label: str = "NEW SECTION"):
        """Small badge to highlight additions."""
        prev_x, prev_y = self.get_x(), self.get_y()
        self.set_fill_color(*ACCENT)
        self.set_text_color(*WHITE)
        self._set_font("B", 7)
        self.set_xy(x, y)
        self.cell(28, 5, label, align="C", fill=True)
        self.set_text_color(0, 0, 0)
        self.set_xy(prev_x, prev_y)

    def _draw_arrow(self, x1: float, y1: float, x2: float, y2: float,
                    color: tuple = (0, 0, 0)):
        """Directed arrow with filled arrowhead."""
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        if length < 1:
            return
        nx, ny = dx / length, dy / length
        arrow_len, arrow_w = 3.5, 1.8
        ax1 = x2 - arrow_len * nx + arrow_w * (-ny)
        ay1 = y2 - arrow_len * ny + arrow_w * nx
        ax2 = x2 - arrow_len * nx - arrow_w * (-ny)
        ay2 = y2 - arrow_len * ny - arrow_w * nx
        self.set_draw_color(*color)
        self.set_line_width(0.3)
        self.line(x1, y1, x2, y2)
        self.set_fill_color(*color)
        self.polygon([(x2, y2), (ax1, ay1), (ax2, ay2)], style="F")
        self.set_line_width(0.2)

    def _draw_db_symbol(self, cx: float, cy: float, w: float = 38,
                        h: float = 22, label: str = ""):
        """Database cylinder symbol centred at (cx, cy)."""
        self.set_fill_color(*LIGHT_GREY)
        self.set_draw_color(60, 60, 60)
        self.set_line_width(0.4)
        self.rect(cx - w / 2, cy - h / 2 + 4, w, h - 4, style="FD")
        self.ellipse(cx - w / 2, cy - h / 2, w, 8, style="FD")
        self.set_fill_color(*LIGHT_GREY)
        self.ellipse(cx - w / 2, cy + h / 2 - 8, w, 8, style="FD")
        self.set_line_width(0.2)
        if label:
            self._set_font("B", 8)
            self.set_text_color(*NAVY)
            self.set_xy(cx - w / 2 - 4, cy + h / 2 + 1)
            self.cell(w + 8, 5, _sanitise(label), align="C")
            self.set_text_color(0, 0, 0)

    def _threat_badge(self, x: float, y: float, text: str):
        """Small ACCENT-coloured annotation badge."""
        self.set_fill_color(*ACCENT)
        self.set_text_color(*WHITE)
        self._set_font("B", 6)
        badge_w = max(len(text) * 2.1 + 4, 22)
        self.set_xy(x, y)
        self.cell(badge_w, 4, _sanitise(text), align="C", fill=True)
        self.set_text_color(0, 0, 0)

    def threat_model_diagram_page(self):
        """Full DFD page reproducing the TimeSheets threat model with STRIDE annotations."""
        self.add_page()
        old_auto_page_break = self.auto_page_break
        old_bottom_margin = self.b_margin
        self.set_auto_page_break(False)
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, 22, "F")
        self.set_text_color(*WHITE)
        self._set_font("B", 13)
        self.set_xy(10, 6)
        self.cell(0, 8, "Step 3: Threat Model Diagram -- TimeSheets DFD (STRIDE annotated)", align="L")
        self.set_text_color(0, 0, 0)

        cx_cl,  cy_cl  = 32,  95
        cx_ws,  cy_ws  = 125, 88
        cx_as,  cy_as  = 218, 88
        cx_adb, cy_adb = 112, 148
        cx_tdb, cy_tdb = 218, 148

        # Client box
        self.set_fill_color(*LIGHT_GREY)
        self.set_draw_color(60, 60, 60)
        self.set_line_width(0.4)
        self.rect(cx_cl - 15, cy_cl - 10, 30, 20, style="FD")
        self._set_font("B", 9)
        self.set_xy(cx_cl - 15, cy_cl - 5)
        self.cell(30, 10, "Client", align="C")

        # Trust boundary
        self.set_draw_color(40, 160, 70)
        self.set_line_width(0.7)
        self.set_dash_pattern(dash=4, gap=2)
        self.line(70, 28, 70, 190)
        self.set_dash_pattern()
        self.set_line_width(0.2)
        self.set_draw_color(0, 0, 0)
        self._set_font("I", 7)
        self.set_text_color(40, 160, 70)
        self.set_xy(42, 30); self.cell(24, 5, "Internet", align="C")
        self.set_xy(71, 30); self.cell(24, 5, "Internal", align="C")
        self.set_text_color(0, 0, 0)

        # Web Server oval
        self.set_fill_color(*LIGHT_GREY)
        self.set_draw_color(60, 60, 60)
        self.set_line_width(0.4)
        self.ellipse(cx_ws - 22, cy_ws - 15, 44, 30, style="FD")
        self._set_font("B", 9)
        self.set_xy(cx_ws - 22, cy_ws - 5)
        self.cell(44, 10, "Web Server", align="C")

        # Application Server oval
        self.ellipse(cx_as - 25, cy_as - 16, 50, 32, style="FD")
        self._set_font("B", 8)
        self.set_xy(cx_as - 25, cy_as - 7); self.cell(50, 6, "Application", align="C")
        self.set_xy(cx_as - 25, cy_as - 1); self.cell(50, 6, "Server", align="C")

        # Databases
        self._draw_db_symbol(cx_adb, cy_adb, w=38, h=22, label="AuthDB")
        self._draw_db_symbol(cx_tdb, cy_tdb, w=42, h=22, label="TimeSheetsDB")

        ac = (30, 60, 140)
        # 1. Client -> Web Server
        self._draw_arrow(cx_cl + 15, cy_cl - 5, cx_ws - 22, cy_ws - 6, color=ac)
        self._set_font("", 7); self.set_xy(68, 75); self.cell(32, 4, "HTTP Request", align="C")
        self._threat_badge(63, 69, "S,I - No TLS")
        # 2. Web Server -> Client
        self._draw_arrow(cx_ws - 22, cy_ws + 6, cx_cl + 15, cy_cl + 4, color=ac)
        self._set_font("", 7); self.set_xy(68, 97); self.cell(32, 4, "HTTP Response", align="C")
        # 3. Web Server -> App Server
        self._draw_arrow(cx_ws + 22, cy_ws - 5, cx_as - 25, cy_as - 5, color=ac)
        self._set_font("", 7); self.set_xy(155, 77); self.cell(36, 4, "Application Calls", align="C")
        # 4. App Server -> Web Server
        self._draw_arrow(cx_as - 25, cy_as + 5, cx_ws + 22, cy_ws + 5, color=ac)
        self._set_font("", 7); self.set_xy(155, 89); self.cell(36, 4, "App Response", align="C")
        # 5. Web Server -> AuthDB
        self._draw_arrow(cx_ws - 10, cy_ws + 15, cx_adb + 5, cy_adb - 11, color=ac)
        self._set_font("", 7); self.set_xy(95, 125); self.cell(28, 4, "HTTP Request", align="C")
        # 6. AuthDB -> App Server (Auth Data)
        self._draw_arrow(cx_adb + 19, cy_adb - 5, cx_as - 19, cy_as + 13, color=ac)
        self._set_font("", 7); self.set_xy(152, 137); self.cell(28, 4, "Auth Data", align="C")
        self._threat_badge(148, 130, "I - Reversible Enc")
        # 7. App Server -> TimeSheetsDB
        self._draw_arrow(cx_as - 6, cy_as + 16, cx_tdb - 6, cy_tdb - 11, color=ac)
        self._set_font("", 7); self.set_xy(197, 127); self.cell(22, 4, "App Data", align="C")
        self._threat_badge(195, 120, "I - No Enc@Rest")
        # 8. TimeSheetsDB -> App Server
        self._draw_arrow(cx_tdb + 8, cy_tdb - 11, cx_as + 8, cy_as + 16, color=ac)
        self._set_font("", 7); self.set_xy(222, 127); self.cell(22, 4, "HTTP Resp", align="C")

        # STRIDE legend
        self.set_fill_color(*NAVY)
        self.rect(10, 172, 132, 28, style="F")
        self.set_text_color(*WHITE)
        self._set_font("B", 8)
        self.set_xy(12, 174); self.cell(128, 5, "STRIDE Threat Categories", align="L")
        self._set_font("", 7)
        self.set_xy(12, 180); self.cell(64, 4, "S = Spoofing Identity", align="L")
        self.set_xy(76, 180); self.cell(64, 4, "T = Tampering with Data", align="L")
        self.set_xy(12, 185); self.cell(64, 4, "R = Repudiation", align="L")
        self.set_xy(76, 185); self.cell(64, 4, "I = Information Disclosure", align="L")
        self.set_xy(12, 190); self.cell(64, 4, "D = Denial of Service", align="L")
        self.set_xy(76, 190); self.cell(64, 4, "E = Elevation of Privilege", align="L")
        self.set_text_color(0, 0, 0)

        # Observations box
        self.set_fill_color(*LIGHT_GREY)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.5)
        self.rect(147, 172, 140, 28, style="FD")
        self.set_line_width(0.2)
        self._set_font("B", 8)
        self.set_text_color(*ACCENT)
        self.set_xy(149, 174)
        self.cell(136, 5, "Key Architecture Observations (Non-Encryption)", align="L")
        self._set_font("", 7)
        self.set_text_color(0, 0, 0)
        self.set_xy(149, 180)
        self.multi_cell(136, 4.2,
            "1. No firewall/WAF at Boundary 1 (Internet -> Web Server)\n"
            "2. No network segmentation between Web, App, and Data tiers\n"
            "3. HTTP used for DB communication (should use encrypted DB protocol)\n"
            "4. No redundancy -- single points of failure at every tier",
            align="L")

        self._set_font("I", 8)
        self.set_text_color(*SLATE)
        self.set_xy(10, 166)
        self.cell(0, 5,
            "Figure 1: TimeSheets DFD -- STRIDE threat annotations shown in red badges",
            align="C")
        self.set_text_color(0, 0, 0)
        self.set_auto_page_break(old_auto_page_break, old_bottom_margin)

    def secure_architecture_diagram_page(self):
        """Recommended target architecture with encryption and network controls."""
        self.add_page()
        old_auto_page_break = self.auto_page_break
        old_bottom_margin = self.b_margin
        self.set_auto_page_break(False)
        self.set_fill_color(*NAVY)
        self.rect(0, 0, self.w, 22, "F")
        self.set_text_color(*WHITE)
        self._set_font("B", 13)
        self.set_xy(10, 6)
        self.cell(0, 8, "Secure Target Architecture -- TimeSheets", align="L")
        self.set_text_color(0, 0, 0)

        zones = [
            (12, 36, 66, 136, "Internet"),
            (88, 36, 58, 136, "DMZ"),
            (156, 36, 58, 136, "Application Tier"),
            (224, 36, 58, 136, "Data Tier"),
        ]
        for x, y, w, h, label in zones:
            self.set_fill_color(248, 250, 252)
            self.set_draw_color(120, 135, 155)
            self.rect(x, y, w, h, style="FD")
            self._set_font("B", 8)
            self.set_text_color(*SLATE)
            self.set_xy(x, y + 3)
            self.cell(w, 5, label, align="C")
            self.set_text_color(0, 0, 0)

        def node(x, y, w, h, title, subtitle=""):
            self.set_fill_color(*LIGHT_GREY)
            self.set_draw_color(60, 60, 60)
            self.rect(x, y, w, h, style="FD")
            self._set_font("B", 8)
            self.set_xy(x + 2, y + 4)
            self.cell(w - 4, 5, _sanitise(title), align="C")
            if subtitle:
                self._set_font("", 7)
                self.set_xy(x + 2, y + 10)
                self.multi_cell(w - 4, 4, _sanitise(subtitle), align="C")

        node(28, 88, 34, 20, "Client", "HTTPS only")
        node(94, 60, 46, 20, "WAF / Firewall", "TLS 1.3, HSTS,\nrate limiting")
        node(94, 114, 46, 22, "Web Servers", "Redundant DMZ\ninstances")
        node(162, 88, 46, 24, "App Servers", "mTLS service calls,\nleast privilege")
        self._draw_db_symbol(245, 78, w=42, h=20, label="AuthDB")
        self._draw_db_symbol(263, 126, w=42, h=20, label="TimeSheetsDB")

        ac = (30, 60, 140)
        self._draw_arrow(62, 98, 94, 70, ac)
        self._draw_arrow(117, 80, 117, 114, ac)
        self._draw_arrow(140, 125, 162, 100, ac)
        self._draw_arrow(208, 94, 224, 78, ac)
        self._draw_arrow(208, 106, 244, 126, ac)
        self._set_font("", 7)
        self.set_xy(63, 78); self.cell(34, 4, "TLS 1.3", align="C")
        self.set_xy(141, 111); self.cell(24, 4, "mTLS", align="C")
        self.set_xy(211, 85); self.cell(28, 4, "TLS DB", align="C")
        self.set_xy(220, 112); self.cell(28, 4, "TLS DB", align="C")

        self.set_fill_color(*NAVY)
        self.rect(12, 180, 270, 20, style="F")
        self.set_text_color(*WHITE)
        self._set_font("B", 8)
        self.set_xy(15, 183)
        self.cell(260, 4, "Security Controls Added", align="L")
        self._set_font("", 7)
        self.set_xy(15, 188)
        self.multi_cell(
            260,
            4,
            "AES-256 TDE on both databases | Argon2id password hashes | Keys in HSM/KMS | "
            "encrypted backups | internal firewalls between tiers | SIEM alerts for concurrent "
            "sessions and anomalous access",
            align="L",
        )
        self.set_text_color(0, 0, 0)
        self.set_auto_page_break(old_auto_page_break, old_bottom_margin)


# ===========================================================================
# Build document
# ===========================================================================
pdf = ReportPDF(orientation="L", format="A4")
pdf.set_auto_page_break(True, margin=18)
pdf.set_margins(10, 10, 10)

# ── Cover ──────────────────────────────────────────────────────────────────
pdf.cover_page(
    "TimeSheets: Threat Report",
    "Updated to align with industry best-practice\nthreat modelling structure",
)

# ── HOW TO USE ─────────────────────────────────────────────────────────────
pdf.content_page(
    "Executive Summary",
    [
        ("body", "This report evaluates encryption-related vulnerabilities in the TimeSheets "
         "application using STRIDE threat modelling and a Likelihood x Impact risk model. "
         "The analysis focuses on four confirmed encryption weaknesses that expose employee "
         "data, authentication data, and network credentials."),
        ("bullet", "Highest priority: authentication requests are unencrypted in transit. "
         "This vulnerability has already been exploited through a confirmed Man-in-the-Middle "
         "attack and is ranked Critical with a score of 25."),
        ("bullet", "Credential storage must be corrected by replacing reversible encryption "
         "with Argon2id one-way password hashing and retiring the legacy decryption key."),
        ("bullet", "Data-at-rest controls must be added using AES-256 database encryption, "
         "encrypted backups, and centralized key management through an HSM or KMS."),
        ("bullet", "DES must be removed from the application and replaced with AES-256-GCM "
         "to provide modern confidentiality and integrity protection."),
        ("bullet", "The recommended audit strategy combines policy, automated cryptography "
         "checks, vulnerability scanning, penetration testing, SIEM detection, and key "
         "rotation monitoring."),
    ],
)

# ── PURPOSE / UPDATED TOC ──────────────────────────────────────────────────
pdf.content_page(
    "Purpose of this Report",
    [
        ("body", "This is a threat model report for TimeSheets. The report describes the "
         "threats facing TimeSheets using an industry-standard methodology. "
         "The model covers the following sections in recommended order:"),
        ("label", "Section 1 – Initial Threat Assessment"),
        ("sub",   "Step 0: Security Objectives & Scope"),
        ("sub",   "Step 1: Asset Inventory"),
        ("sub",   "Step 2: Architecture Review (Trust Boundaries, Attack Surface, DFDs)"),
        ("sub",   "Step 3: Threat Model Diagram"),
        ("sub",   "Step 4: Identifying Threat Actors"),
        ("sub",   "Step 5: Threats to the Organisation (STRIDE)"),
        ("label", "Section 2 – Vulnerability Analysis"),
        ("label", "Section 3 – Risk Analysis  (Likelihood × Impact scoring)"),
        ("label", "Section 4 – Mitigation Plan"),
        ("label", "Section 5 – Residual Risk Acceptance & Review"),
    ],
)

# ===========================================================================
# SECTION 1 — INITIAL THREAT ASSESSMENT
# ===========================================================================
pdf.section_divider(1, "Initial Threat Assessment")

# ── STEP 0 — Security Objectives & Scope  (NEW) ───────────────────────────
pdf.content_page(
    "Step 0: Security Objectives & Scope",
    [
        ("body",
         "Before enumerating assets or threats, the organisation must define what it is "
         "protecting and why. This step establishes the strategic foundation for the "
         "entire threat model and prevents scope creep during analysis."),
        ("label", "Security Objectives"),
        ("bullet", "Protect the confidentiality of employee timekeeping and payroll data."),
        ("bullet", "Ensure the integrity of hours-worked records to prevent fraudulent entries."),
        ("bullet", "Maintain availability of the TimeSheets application during business hours."),
        ("label", "Compliance & Regulatory Requirements"),
        ("bullet", "GDPR Article 32 requires appropriate technical and organisational measures, "
         "including encryption where appropriate, for personal data."),
        ("bullet", "NIST SP 800-53 and NIST SP 800-131A guide the selection and lifecycle of "
         "approved cryptographic controls."),
        ("bullet", "OWASP Password Storage guidance requires adaptive one-way hashing for "
         "passwords rather than reversible encryption."),
        ("label", "Acceptable Risk Tolerance"),
        ("body", "Critical and High encryption risks must not be accepted without executive "
         "approval. Critical risks require immediate remediation planning; High risks require "
         "a tracked mitigation plan within 30 days; Medium risks require remediation within "
         "90 days or a documented compensating control."),
        ("label", "Scope Boundaries"),
        ("bullet", "In scope: TimeSheets web server, application server, TimeSheetsDB, AuthDB, "
         "client devices accessing the application, network paths."),
        ("bullet", "Out of scope: unrelated corporate systems not used by TimeSheets, except "
         "where compromised TimeSheets credentials could be reused against them."),
    ],
)

# ── STEP 1 — Asset Inventory ───────────────────────────────────────────────
pdf.content_page(
    "Step 1: Asset Inventory",
    [
        ("label", "Components and Functions"),
        ("bullet", "TimeSheets Web Server — serves static content (HTML, images) to clients via HTTP."),
        ("bullet", "TimeSheets Application Server — handles business logic and serves dynamic content."),
        ("bullet", "TimeSheetsDB — stores employee data; queried by the application server."),
        ("bullet", "AuthDB — stores user authentication credentials; queried by the application server."),
        ("label", "Overview of Application Functionality"),
        ("body",  "TimeSheets is used by employees to track hours worked. "
                  "Users log in from their device via the Internet."),
        ("label", "Data Flow Summary"),
        ("body",  "Client request → Internet → TimeSheets Web Server (static content) → "
                  "Application Server (business logic) → TimeSheetsDB / AuthDB (data retrieval) → "
                  "Response returned to client."),
        ("label", "Asset Classification"),
        ("bullet", "AuthDB -- Confidentiality: Critical; Integrity: High; Availability: Medium."),
        ("bullet", "TimeSheetsDB -- Confidentiality: High; Integrity: High; Availability: Medium."),
        ("bullet", "Application Server -- Confidentiality: Medium; Integrity: High; Availability: High."),
        ("bullet", "Web Server -- Confidentiality: Medium; Integrity: Medium; Availability: High."),
    ],
)

# ── STEP 2 — Architecture Review ──────────────────────────────────────────
pdf.content_page(
    "Step 2: Architecture Review — Trust Boundaries, Attack Surface & Data Flows",
    [
        ("body",  "A thorough architecture review goes beyond listing flaws. "
                  "It explicitly maps trust boundaries and entry/exit points, "
                  "which are the primary mechanism for discovering threats."),
        ("label", "Identified Trust Boundaries"),
        ("bullet", "Internet ↔ Web Server  (Boundary 1 — public untrusted zone)"),
        ("bullet", "Web Server ↔ Application Server  (Boundary 2 — DMZ to internal)"),
        ("bullet", "Application Server ↔ TimeSheetsDB / AuthDB  (Boundary 3 — app to data tier)"),
        ("label", "Entry / Exit Points (Attack Surface)"),
        ("bullet", "HTTP/HTTPS endpoint on Web Server (client-facing)"),
        ("bullet", "Internal API between Web Server and Application Server"),
        ("bullet", "Database connection from Application Server to both DBs"),
        ("bullet", "Administrative and monitoring access paths used by SRE, DBA, and audit teams."),
        ("label", "Architecture Flaws Identified"),
        ("bullet", "No encryption at rest — database servers store data on unencrypted disks."),
        ("bullet", "No redundancy — single points of failure across all tiers."),
        ("bullet", "No perimeter firewall filtering inbound Internet traffic."),
        ("bullet", "No enforced TLS on client, application, or database communication paths."),
    ],
)

# ── STEP 3 — Threat Model Diagram ────────────────────────────────────────
pdf.threat_model_diagram_page()

# ── STEP 4 — Identifying Threat Actors  (MOVED before threats) ────────────
pdf.content_page(
    "Step 4: Identifying Threat Actors",
    [
        ("body",  "Threat actors are identified before threat enumeration because "
                  "knowing who the adversaries are shapes which threats are realistic "
                  "and how likely they are to be attempted."),
        ("label", "Primary Threat Actor — Malicious Internal User"),
        ("bullet", "Evidence: Unexpected login originates from an internal IP address."),
        ("bullet", "No data exfiltrated or modified — consistent with reconnaissance by an insider."),
        ("bullet", "Motivation: potential privilege escalation or data access for personal gain."),
        ("label", "Secondary Threat Actor — External Opportunistic Attacker"),
        ("bullet", "Exploits lack of TLS — capable of MitM attacks on unencrypted traffic."),
        ("bullet", "Motivation: credential theft, session hijacking, or competitive espionage."),
        ("label", "Tertiary Threat Actor — Nation-State / Advanced Persistent Threat"),
        ("bullet", "Less likely for a timekeeping application, but the controls recommended "
         "in this report still reduce exposure to advanced actors by removing weak cryptography, "
         "encrypting all network paths, and centralising key management."),
        ("label", "Threat Actor Classification Reference"),
        ("sub", "Use MITRE ATT&CK for Enterprise to map actor TTPs to observed behaviours."),
    ],
)

# ── STEP 5 — Threats to the Organisation (STRIDE) ────────────────────────
pdf.content_page(
    "Step 5: Threats to the Organisation (STRIDE Analysis)",
    [
        ("body",  "Threats are enumerated systematically using the STRIDE framework "
                  "applied to each component and trust boundary crossing."),
        ("label", "Completed Threat Model — Confirmed Threats"),
        ("bullet", "Employee data unencrypted at rest — Information Disclosure (TimeSheetsDB)"),
        ("bullet", "Authentication data using reversible encryption — Information Disclosure / "
                   "Elevation of Privilege (AuthDB)"),
        ("bullet", "Authentication requests unencrypted in transit — Information Disclosure / "
                   "Spoofing (Boundary 1 & 2)"),
        ("bullet", "Sensitive data encrypted with DES — Information Disclosure (weak algorithm, "
                   "brute-forceable)"),
        ("label", "Attack Confirmed — Man-in-the-Middle (MitM)"),
        ("bullet", "A malicious actor sniffed unencrypted traffic and intercepted valid credentials."),
        ("bullet", "Logs show simultaneous successful logins from the expected IP and a different "
                   "location — confirming credential replay."),
        ("label", "STRIDE Coverage — Gaps to Address"),
        ("bullet", "Spoofing: unencrypted credentials allow account impersonation."),
        ("bullet", "Tampering: DES without authenticated encryption permits undetected data changes."),
        ("bullet", "Repudiation: audit logs must be retained and correlated with SIEM alerts."),
        ("bullet", "Information Disclosure: all four confirmed vulnerabilities expose sensitive data."),
        ("bullet", "Denial of Service: single-instance tiers create availability risk."),
        ("bullet", "Elevation of Privilege: stolen or decrypted administrator credentials enable escalation."),
    ],
)

# ===========================================================================
# SECTION 2 — VULNERABILITY ANALYSIS
# ===========================================================================
pdf.section_divider(2, "Vulnerability Analysis")

# Vulnerability pages -- fully completed
pdf.content_page(
    "Vulnerability 1: Employee Data Unencrypted at Rest",
    [
        ("label", "Discovery"),
        ("body",  "During threat modelling, the SRE team confirmed the database server "
                  "does not have encryption at rest enabled."),
        ("label", "Why is this a Vulnerability?"),
        ("body",  "TimeSheetsDB and AuthDB store data on unencrypted disks. If an attacker "
                  "gains physical access to the storage media (hard drive, backup tape, SSD), "
                  "obtains a storage snapshot, or accesses a backup, all data is immediately "
                  "readable with no cryptographic barrier. Database files, backup files, and "
                  "transaction logs all expose sensitive data in plaintext, eliminating the "
                  "last line of defence at the storage layer."),
        ("label", "Result if Exploited"),
        ("bullet", "Full exposure of all employee PII: names, working hours, and payroll data."),
        ("bullet", "Regulatory breach: GDPR Article 32 mandates 'appropriate technical measures' "
                   "including encryption. Fines of up to 4% of annual global turnover apply."),
        ("bullet", "Mandatory breach notification to affected employees and regulators, causing "
                   "reputational damage, loss of employee trust, and potential litigation."),
        ("bullet", "Compound risk: AuthDB exposure combined with Vulnerability 2 enables mass "
                   "credential compromise across all user accounts simultaneously."),
        ("bullet", "Significant operational disruption and recovery costs during incident response."),
    ],
)

pdf.content_page(
    "Vulnerability 2: Authentication Data Stored Using Reversible Encryption",
    [
        ("label", "Discovery"),
        ("body",  "The DBA team confirmed credentials in AuthDB are stored using "
                  "reversible (symmetric) encryption rather than a one-way hash."),
        ("label", "Why is this a Vulnerability?"),
        ("body",  "Reversible encryption means encrypted passwords can be decrypted back to "
                  "plaintext by anyone who obtains both the ciphertext and the encryption key. "
                  "Unlike one-way hashing algorithms (bcrypt, Argon2id, PBKDF2), reversible "
                  "encryption does not prevent bulk password recovery -- the decryption key is "
                  "typically stored on the same server or in the same codebase. OWASP explicitly "
                  "states passwords must never be stored using reversible encryption. An attacker "
                  "who compromises the database (easier given Vulnerability 1) can decrypt ALL "
                  "user credentials in a single operation."),
        ("label", "Result if Exploited"),
        ("bullet", "Mass account takeover for every user simultaneously, including administrators."),
        ("bullet", "Credential stuffing against external services: employees reuse passwords, so "
                   "recovered credentials may unlock email, banking, and other corporate systems."),
        ("bullet", "Complete authentication bypass -- attackers can impersonate any employee."),
        ("bullet", "If admin credentials are recovered: full system compromise, data exfiltration, "
                   "or ransomware deployment becomes possible."),
    ],
)

pdf.content_page(
    "Vulnerability 3: Authentication Requests Unencrypted in Transit",
    [
        ("label", "Discovery"),
        ("body",  "The security team confirmed authentication requests are transmitted "
                  "in plaintext over the network."),
        ("label", "Why is this a Vulnerability?"),
        ("body",  "The threat model DFD shows the Client communicating with the Web Server via "
                  "plain HTTP across the Internet trust boundary (Boundary 1). Credentials travel "
                  "in cleartext, visible to any on-path observer or Man-in-the-Middle attacker. "
                  "The DFD also shows HTTP used between the Web Server and AuthDB, and between "
                  "the App Server and TimeSheetsDB -- all four trust boundary crossings are "
                  "unencrypted. This directly enabled the confirmed MitM attack: logs show "
                  "simultaneous logins from the expected IP and a second, unexpected location."),
        ("label", "Result if Exploited"),
        ("bullet", "Direct credential theft confirmed: attacker captured valid credentials in "
                   "transit and replayed them to gain access from a different location."),
        ("bullet", "Session cookie theft via traffic interception enables persistent access "
                   "without needing the password again."),
        ("bullet", "Replay attacks: captured credentials remain valid until the victim changes "
                   "their password -- the window of exploitation is unlimited."),
        ("bullet", "Internal traffic interception: an insider with network access can also capture "
                   "credentials at Boundaries 2 and 3 (internal tiers)."),
    ],
)

pdf.content_page(
    "Vulnerability 4: DES Algorithm in Use",
    [
        ("label", "Discovery"),
        ("body",  "While conducting threat modelling, the security team identified "
                  "sensitive data being stored using the Data Encryption Standard (DES) algorithm."),
        ("label", "Why is this a Vulnerability?"),
        ("body",  "DES uses a 56-bit key, demonstrated insecure in 1998 when the EFF Deep Crack "
                  "cracked a DES key in 56 hours using $250,000 of hardware. NIST formally "
                  "withdrew DES (FIPS 46-3) in 2005 and explicitly prohibits its use under "
                  "NIST SP 800-131A Rev. 2. Today, cloud compute makes brute-forcing a 56-bit "
                  "key achievable in minutes at minimal cost. Additionally, DES in ECB/CBC mode "
                  "provides no integrity protection -- ciphertext can be tampered with undetected."),
        ("label", "Result if Exploited"),
        ("bullet", "Any DES-encrypted data can be decrypted by a well-resourced attacker once "
                   "they obtain the ciphertext (e.g., via the storage vulnerability above)."),
        ("bullet", "Employee timekeeping records, payroll data, and PII fields protected only "
                   "by DES are effectively exposed."),
        ("bullet", "Regulatory non-compliance: GDPR 'appropriate technical measures' are not met; "
                   "PCI-DSS explicitly prohibits DES if payment data is in scope."),
        ("bullet", "No integrity protection means DES-encrypted fields can be silently tampered "
                   "with, corrupting timekeeping records without any detection mechanism."),
    ],
)

# ── Additional Architecture Review ───────────────────────────────────────
pdf.content_page(
    "Additional Architecture Issues Identified from the DFD",
    [
        ("label", "Issue 1: No Firewall/WAF at Boundary 1 (Internet -> Web Server)"),
        ("body",  "The DFD shows a direct, unfiltered path from the Client to the Web Server "
                  "with no inspection or filtering layer between them."),
        ("sub",   "Recommendation: Deploy a Web Application Firewall (WAF) at Boundary 1 to "
                  "filter SQLi, XSS, and CSRF attempts, rate-limit login requests, and block "
                  "known malicious IP ranges."),
        ("sub",   "Why: A WAF is the first line of defence, reducing the attack surface before "
                  "any request reaches the application tier."),
        ("label", "Issue 2: No Network Segmentation Between Tiers"),
        ("body",  "The DFD shows Web Server, App Server, and databases appearing on the same "
                  "logical network with no internal firewalls between tiers."),
        ("sub",   "Recommendation: Segment into three zones -- DMZ (Web Server only), Application "
                  "tier, and Data tier. Apply strict firewall rules so only the App Server can "
                  "query the databases."),
        ("sub",   "Why: Segmentation limits lateral movement -- a compromised Web Server cannot "
                  "directly reach the database tier."),
        ("label", "Issue 3: HTTP Used for Database Communication"),
        ("body",  "The DFD shows HTTP Request/Response between the App Server and TimeSheetsDB. "
                  "Databases should communicate over encrypted native database protocols, not HTTP."),
        ("sub",   "Recommendation: Replace HTTP-based DB calls with TLS-secured native database "
                  "driver connections (e.g., TLS-enabled PostgreSQL/MySQL)."),
        ("label", "Issue 4: No Redundancy -- Single Points of Failure"),
        ("body",  "Every component in the DFD is a single instance. Any single failure brings "
                  "the entire application down."),
        ("sub",   "Recommendation: Deploy redundant Web and App Server instances behind a load "
                  "balancer; implement database replication with automatic failover."),
    ],
)

# ===========================================================================
# SECTION 3 — RISK ANALYSIS
# ===========================================================================
pdf.section_divider(3, "Risk Analysis")

pdf.content_page(
    "Risk Evaluation -- Likelihood x Impact Scoring",
    [
        ("body",
         "Risks are ranked using a Likelihood x Impact matrix. "
         "Both dimensions are scored 1-5; the product gives a risk score (1-25). "
         "Higher scores represent greater priority for remediation."),
        ("label", "Risk Scoring Formula"),
        ("body",  "Risk Score  =  Likelihood (1-5)  x  Impact (1-5)"),
        ("sub",   "Likelihood: 1=Rare, 2=Unlikely, 3=Possible, 4=Likely, 5=Almost Certain"),
        ("sub",   "Impact:     1=Negligible, 2=Minor, 3=Significant, 4=Major, 5=Catastrophic"),
        ("label", "Risk Ranking Results (Completed)"),
        ("bullet", "Rank 1  (Score 25): Authentication Requests Unencrypted in Transit "
                   "[Likelihood 5 x Impact 5]"),
        ("bullet", "Rank 2  (Score 20): Authentication Data Using Reversible Encryption "
                   "[Likelihood 4 x Impact 5]"),
        ("bullet", "Rank 3  (Score 12): Employee Data Unencrypted at Rest "
                   "[Likelihood 3 x Impact 4]"),
        ("bullet", "Rank 4  (Score  9): DES Algorithm in Use "
                   "[Likelihood 3 x Impact 3]"),
    ],
)

# Risk rationale pages -- fully completed
pdf.content_page(
    "Risk Rationale -- Ranks 1 and 2",
    [
        ("label", "#1: Authentication Requests Unencrypted in Transit  (Score: 25)"),
        ("bullet", "Likelihood: 5 (Almost Certain) -- The MitM attack is CONFIRMED. Logs "
                   "provide irrefutable evidence of simultaneous logins from two different "
                   "locations. The exploit is active and immediately repeatable."),
        ("bullet", "Impact: 5 (Catastrophic) -- Direct credential compromise achieved. The "
                   "attacker can access any account, escalate privileges, and pivot to "
                   "other vulnerabilities for full system compromise."),
        ("bullet", "Risk Score: 5 x 5 = 25  (maximum possible score)."),
        ("body",   "Ranked #1 because this is not theoretical -- the exploit has already "
                   "succeeded. An active, repeatable, confirmed attack demands the highest "
                   "priority. Remediation is also the fastest to implement (deploy TLS)."),
        ("label", "#2: Authentication Data Using Reversible Encryption  (Score: 20)"),
        ("bullet", "Likelihood: 4 (Likely) -- The confirmed MitM and the lack of storage "
                   "encryption (Rank 3) together create a realistic path to database access. "
                   "Once access is achieved, decryption of all credentials is trivial."),
        ("bullet", "Impact: 5 (Catastrophic) -- All user credentials can be recovered in "
                   "bulk from a single DB compromise, enabling mass account takeover and "
                   "administrator-level access."),
        ("bullet", "Risk Score: 4 x 5 = 20."),
        ("body",   "Ranked #2 because bulk credential recovery from a DB compromise is "
                   "catastrophic even though it requires an additional step beyond Rank 1."),
    ],
)

pdf.content_page(
    "Risk Rationale -- Ranks 3 and 4",
    [
        ("label", "#3: Employee Data Unencrypted at Rest  (Score: 12)"),
        ("bullet", "Likelihood: 3 (Possible) -- Requires physical access to storage media, "
                   "a privileged DB account, or access to backup media. Higher barrier than "
                   "network-based attacks, but the flat network in the DFD means a network "
                   "attacker could pivot to reach the storage tier."),
        ("bullet", "Impact: 4 (Major) -- Complete exposure of all employee PII and timekeeping "
                   "data. Significant GDPR regulatory breach with fines up to 4% of annual "
                   "global turnover and mandatory public breach notification."),
        ("bullet", "Risk Score: 3 x 4 = 12."),
        ("body",   "Ranked #3 because physical/privileged access creates a higher exploitation "
                   "barrier, but the regulatory and PII impact remains major."),
        ("label", "#4: DES Algorithm in Use  (Score: 9)"),
        ("bullet", "Likelihood: 3 (Possible) -- An attacker must first obtain the DES ciphertext "
                   "(requiring DB or storage access, as above) and then invest compute resources "
                   "to brute-force the 56-bit key. A two-step exploit reduces likelihood."),
        ("bullet", "Impact: 3 (Significant) -- Scope is limited to data specifically protected "
                   "by DES. Other data may use different controls. However, the lack of integrity "
                   "protection in DES means affected fields could also be silently tampered with."),
        ("bullet", "Risk Score: 3 x 3 = 9."),
        ("body",   "Ranked #4 because exploitation requires prior access to ciphertext AND "
                   "brute-force compute time -- the hardest attack to execute. However, it "
                   "remains a critical compliance failure regardless of rank."),
    ],
)

# ===========================================================================
# SECTION 4 — MITIGATION PLAN
# ===========================================================================
pdf.section_divider(4, "Mitigation Plan")

# Mitigation pages -- fully completed
pdf.content_page(
    "Mitigation 1: Employee Data Unencrypted at Rest",
    [
        ("label", "Recommended Mitigation Plan"),
        ("body",  "Enable Transparent Data Encryption (TDE) on TimeSheetsDB and AuthDB using "
                  "AES-256. Decrypt and re-encrypt existing data during a scheduled maintenance "
                  "window. Store encryption keys in a Hardware Security Module (HSM) or cloud "
                  "Key Management Service (e.g., AWS KMS, Azure Key Vault) -- physically and "
                  "logically separated from the database servers. Enforce encryption on all "
                  "database backups."),
        ("label", "Why This Course of Action?"),
        ("bullet", "TDE is a native RDBMS feature (SQL Server, PostgreSQL, MySQL Enterprise) "
                   "operating at the storage layer with no application code changes required."),
        ("bullet", "AES-256 is NIST FIPS 197 approved and computationally infeasible to "
                   "brute-force -- physical access to the disk is useless without the key."),
        ("bullet", "Storing keys in an HSM/KMS ensures the key and ciphertext are never "
                   "co-located, eliminating single-point-of-compromise for the entire database."),
        ("bullet", "Encrypting backups closes the common physical theft vector where unencrypted "
                   "backup tapes are removed from the premises."),
    ],
)

pdf.content_page(
    "Mitigation 2: Authentication Data Stored Using Reversible Encryption",
    [
        ("label", "Recommended Mitigation Plan"),
        ("body",  "Migrate credential storage from reversible encryption to Argon2id (OWASP "
                  "recommended) with minimum parameters: memory=64 MB, iterations=3, "
                  "parallelism=4. Migration strategy: (1) Add a 'hash_algorithm' column; "
                  "(2) On next successful login, re-hash the plaintext password with Argon2id; "
                  "(3) Force password resets via email for users inactive for more than 30 days; "
                  "(4) Retire and delete the old encryption key after all records are migrated."),
        ("label", "Why This Course of Action?"),
        ("bullet", "One-way hashing makes bulk password recovery computationally infeasible -- "
                   "a full database export cannot yield passwords without per-hash brute-forcing."),
        ("bullet", "Argon2id won the Password Hashing Competition (2015) and is specifically "
                   "memory-hard, resisting GPU, ASIC, and side-channel attacks."),
        ("bullet", "The phased migration minimises operational disruption while rapidly securing "
                   "the most active accounts first."),
        ("bullet", "Deleting the old encryption key after migration removes residual risk -- "
                   "legacy reversibly-encrypted records can no longer be decrypted."),
    ],
)

pdf.content_page(
    "Mitigation 3: Authentication Requests Unencrypted in Transit",
    [
        ("label", "Recommended Mitigation Plan"),
        ("body",  "Deploy TLS 1.3 certificates on all externally-facing endpoints. Configure "
                  "HTTP Strict Transport Security (HSTS) with max-age >= 31,536,000 (1 year) "
                  "and includeSubDomains. Redirect all HTTP (port 80) to HTTPS (port 443) at "
                  "the load balancer/WAF. Enforce TLS on ALL internal connections: Web Server "
                  "to App Server, and App Server to both databases. Disable TLS 1.0, 1.1, and "
                  "weak cipher suites (RC4, 3DES, NULL)."),
        ("label", "Why This Course of Action?"),
        ("bullet", "TLS 1.3 directly eliminates the confirmed MitM attack vector -- all "
                   "credentials and session data become encrypted in transit."),
        ("bullet", "HSTS prevents SSL stripping attacks where an attacker downgrades the "
                   "connection to HTTP before TLS is established."),
        ("bullet", "Enforcing TLS on internal connections (Boundaries 2 and 3 in the DFD) "
                   "addresses insider threats and compromised-host pivot attacks."),
        ("bullet", "This is the highest-priority mitigation given the active exploit. "
                   "Implementation time is hours; cost is near-zero with Let's Encrypt."),
    ],
)

pdf.content_page(
    "Mitigation 4: DES Algorithm in Use",
    [
        ("label", "Recommended Mitigation Plan"),
        ("body",  "Conduct a full codebase audit (SAST scan via SonarQube or Semgrep with "
                  "cryptography rule sets) to identify all DES usage. Replace with AES-256-GCM "
                  "(authenticated encryption providing both confidentiality and integrity). "
                  "Re-encrypt all DES-protected data during a maintenance window. Manage "
                  "256-bit keys via HSM/KMS (aligned with Mitigation 1). Add SAST checks "
                  "to the CI/CD pipeline to prevent regression."),
        ("label", "Why This Course of Action?"),
        ("bullet", "AES-256 is the NIST FIPS 197 standard -- computationally infeasible to "
                   "brute-force with any known technology."),
        ("bullet", "GCM mode (authenticated encryption, AEAD) provides both confidentiality "
                   "AND integrity -- it detects any tampering with the ciphertext, fixing the "
                   "integrity gap that DES in ECB/CBC mode leaves open."),
        ("bullet", "DES is explicitly prohibited under NIST SP 800-131A Rev. 2, making "
                   "this a compliance requirement, not just best practice."),
        ("bullet", "CI/CD integration prevents regression: future commits using DES, 3DES, "
                   "or RC4 automatically fail the build before reaching production."),
    ],
)

# ── Security Audit ────────────────────────────────────────────────────────
pdf.content_page(
    "Security Audit -- Ensuring Recommendations are Followed",
    [
        ("label", "1. Establish a Formal Encryption Policy"),
        ("body",  "No encryption policy currently exists. The audit team should champion "
                  "creation of an Encryption Standard mandating: AES-256 for data at rest, "
                  "TLS 1.3 for data in transit, Argon2id/bcrypt for passwords, and explicit "
                  "prohibition of DES, 3DES, RC4, MD5, and SHA-1."),
        ("label", "2. Automated SAST in the CI/CD Pipeline"),
        ("body",  "Integrate SonarQube or Semgrep with cryptography rule sets into the build "
                  "pipeline. Any commit introducing deprecated algorithms fails the build "
                  "automatically, preventing regression before code reaches production."),
        ("label", "3. Quarterly Authenticated Vulnerability Scans"),
        ("body",  "Use Nessus, Qualys, or OpenVAS to scan all in-scope systems quarterly. "
                  "Authenticated scans detect misconfigurations that unauthenticated scans miss, "
                  "including weak cipher suites and unencrypted storage."),
        ("label", "4. Annual Penetration Testing"),
        ("body",  "Commission a qualified third-party (CREST/CHECK certified) for annual pen "
                  "tests covering network, web application, and database security. Include "
                  "social engineering to test the insider-threat dimension."),
        ("label", "5. SIEM Rule: Concurrent Session Detection"),
        ("body",  "The MitM was detected by simultaneous logins from two IPs. Formalise this "
                  "as a permanent SIEM alert: flag any account with concurrent active sessions "
                  "from geographically or logically distant IP addresses."),
        ("label", "6. TLS Certificate and Key Rotation Monitoring"),
        ("body",  "Automate certificate expiry alerts at 30-day and 7-day thresholds. "
                  "Enforce annual encryption key rotation with auditable rotation logs stored "
                  "in the HSM/KMS."),
    ],
)

# ===========================================================================
# SECTION 5 — RESIDUAL RISK ACCEPTANCE & REVIEW  (NEW)
# ===========================================================================
pdf.section_divider(5, "Residual Risk Acceptance & Review")

pdf.content_page(
    "Residual Risk Acceptance & Review",
    [
        ("body",  "After mitigations are applied, some risk will remain (residual risk). "
                  "This section formally documents accepted residual risks and establishes "
                  "a review cadence — both are required in any auditable threat model."),
        ("label", "Residual Risk Register"),
        ("bullet", "Unencrypted at rest -- Residual risk after TDE and encrypted backups: Low. "
         "Database administrators with approved key access can still read data through normal "
         "application and administrative paths."),
        ("bullet", "Reversible credential encryption -- Residual risk after Argon2id migration: "
         "Low. Password guessing remains possible against individual hashes, so MFA and rate "
         "limiting are still required."),
        ("bullet", "Unencrypted authentication requests -- Residual risk after TLS 1.3, HSTS, "
         "and internal mTLS: Low. Risk remains from endpoint compromise and misissued certificates."),
        ("bullet", "DES usage -- Residual risk after AES-256-GCM migration: Low. Risk remains "
         "from future cryptographic misuse, controlled through CI/CD checks and audit review."),
        ("label", "Acceptance Criteria"),
        ("bullet", "Residual risks rated Low may be formally accepted by the system owner."),
        ("bullet", "Residual risks rated Medium must have a compensating control documented."),
        ("bullet", "Residual risks rated High or Critical must be escalated to executive leadership "
                   "and may not be accepted without written approval."),
        ("label", "Review Schedule"),
        ("bullet", "Next scheduled threat model review: within 12 months, or earlier after any "
         "significant architecture, authentication, cryptography, or data-store change."),
        ("bullet", "Owner responsible for triggering review: TimeSheets system owner with Security "
         "Engineering and SRE participation."),
        ("label", "Validation"),
        ("body", "Each mitigation should be verified with evidence: TLS scan results, database "
         "encryption status, key-management logs, password-hash migration metrics, SAST results, "
         "and SIEM alert test records. Audit should retain this evidence with the risk register."),
    ],
)

# ── Secure Architecture ──────────────────────────────────────────────────
pdf.secure_architecture_diagram_page()

pdf.content_page(
    "Secure Architecture Diagram -- Control Mapping",
    [
        ("body",  "The diagram below describes the recommended secure architecture that "
                  "addresses all identified vulnerabilities and non-encryption issues."),
        ("label", "Key Security Controls Added vs. Original Architecture"),
        ("bullet", "Boundary 1: WAF/Firewall deployed in front of the Web Server. "
                   "All traffic is TLS 1.3 encrypted (HTTPS only; HTTP redirected)."),
        ("bullet", "Network Segmentation: Three isolated zones -- DMZ (Web Server), "
                   "Application tier, Data tier -- separated by internal firewalls with "
                   "least-privilege access rules."),
        ("bullet", "TimeSheetsDB and AuthDB: AES-256 TDE enabled on both databases. "
                   "Encryption keys stored in a dedicated HSM/KMS."),
        ("bullet", "AuthDB: Credentials migrated to Argon2id one-way hashes."),
        ("bullet", "All inter-tier communication (Web->App, App->DB) uses TLS-secured "
                   "protocols -- no unencrypted HTTP between internal components."),
        ("bullet", "Redundancy: Load balancer in front of dual Web/App Server instances; "
                   "DB primary/replica replication with automatic failover."),
        ("bullet", "SIEM with concurrent-session and anomalous-access alerting."),
    ],
)

pdf.content_page(
    "Additional Preventative Recommendations",
    [
        ("body",  "Additional steps beyond the four core mitigations to prevent this "
                  "attack and reduce the risk of future incidents:"),
        ("label", "Multi-Factor Authentication (MFA)"),
        ("body",  "Require MFA for all employee logins. Even if credentials are stolen via "
                  "MitM, MFA prevents the attacker from completing authentication without "
                  "the second factor. Use TOTP (RFC 6238) or hardware security keys (FIDO2)."),
        ("label", "Intrusion Detection/Prevention System (IDS/IPS)"),
        ("body",  "Deploy a network IDS/IPS at Boundary 1 to detect and block known attack "
                  "signatures (e.g., credential brute-forcing, SQL injection probes). "
                  "Integrate alerts into the SIEM for centralised monitoring."),
        ("label", "Privileged Access Management (PAM)"),
        ("body",  "Enforce PAM controls for all database administrator accounts. Use "
                  "just-in-time (JIT) privileged access with session recording and "
                  "automatic de-provisioning after task completion."),
        ("label", "Employee Security Awareness Training"),
        ("body",  "The confirmed insider threat actor accessed data they do not normally "
                  "access. Regular security awareness training (including data access "
                  "policies) reduces the risk of malicious or inadvertent insider incidents."),
    ],
)

# ===========================================================================
# Save
# ===========================================================================
output_path = Path(__file__).with_name("TimeSheets Threat Report - Updated.pdf")
pdf.output(output_path)
print(f"PDF written to: {output_path}")
