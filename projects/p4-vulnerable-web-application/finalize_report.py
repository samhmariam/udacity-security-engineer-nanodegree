"""Finalize the Udacity VWA report while retaining the supplied template."""

from datetime import date
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "Copy of Vulnerable Web Application Template 2024.pdf"
OUTPUT = HERE / "Vulnerable Web Application - Final Security Assessment.pdf"
REPORT_ID = "VWA260626"
BASE_URL = "https://hlwmsv5bk5.prod.udacity-student-workspaces.com"

TEAL = colors.HexColor("#22B5CE")
GREEN = colors.HexColor("#16C47F")
GRAY = colors.HexColor("#5A5A5A")
LIGHT = colors.HexColor("#D8D8D8")
WHITE = colors.white

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
for name, filename in {
    "VWA": "DejaVuSans.ttf",
    "VWABold": "DejaVuSans-Bold.ttf",
    "VWAItalic": "DejaVuSans-Oblique.ttf",
    "VWABoldItalic": "DejaVuSans-BoldOblique.ttf",
}.items():
    path = FONT_DIR / filename
    if path.exists():
        pdfmetrics.registerFont(TTFont(name, str(path)))

BODY = "VWA" if "VWA" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
BOLD = "VWABold" if "VWABold" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
ITALIC = "VWAItalic" if "VWAItalic" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Oblique"
BOLD_ITALIC = "VWABoldItalic" if "VWABoldItalic" in pdfmetrics.getRegisteredFontNames() else "Helvetica-BoldOblique"


def template_chrome(c: canvas.Canvas, title: str):
    """Draw the stable visual elements used by the supplied report slides."""
    w, h = letter
    c.setFillColor(WHITE)
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setFillColor(GREEN)
    c.rect(0, h - 148, 3, 62, fill=1, stroke=0)
    c.setFillColor(TEAL)
    title_size = 22 if len(title) <= 46 else 18 if len(title) <= 62 else 12
    c.setFont(BODY, title_size)
    c.drawString(28, h - 126, title)
    c.setFont(BOLD, 18)
    c.drawRightString(w - 21, h - 39, "U")


def styles():
    return {
        "body": ParagraphStyle("body", fontName=BODY, fontSize=9.4, leading=12.2, textColor=GRAY),
        "small": ParagraphStyle("small", fontName=BODY, fontSize=8.3, leading=10.6, textColor=GRAY),
        "label": ParagraphStyle("label", fontName=BOLD_ITALIC, fontSize=10.2, leading=12, textColor=GRAY),
        "value": ParagraphStyle("value", fontName=ITALIC, fontSize=9.5, leading=12, textColor=GRAY),
        "section": ParagraphStyle("section", fontName=BOLD_ITALIC, fontSize=10.5, leading=13, textColor=GRAY),
        "caption": ParagraphStyle("caption", fontName=BOLD, fontSize=8.3, leading=10, textColor=colors.white, alignment=TA_CENTER),
    }


ST = styles()


def pdf_page(draw) -> PdfReader:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    draw(c)
    c.save()
    buf.seek(0)
    return PdfReader(buf)


def cover_overlay() -> PdfReader:
    def draw(c):
        w, _ = letter
        c.setFillColorRGB(0.035, 0.682, 0.843)
        c.rect(0, 36, w, 128, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(BOLD_ITALIC, 19)
        c.drawCentredString(w / 2, 116, "Samuel H. Mariam")
        c.setFont(BOLD_ITALIC, 16)
        c.drawCentredString(w / 2, 80, date.today().strftime("%d %B %Y"))
    return pdf_page(draw)


def header_page() -> PdfReader:
    def draw(c):
        template_chrome(c, "VulnWebApp (VWA) Security Report")
        data = [
            ["Code Revision", "1.0.0.0"],
            ["Company", "USociety"],
            ["Report", REPORT_ID],
            ["Author", "Samuel H. Mariam"],
            ["Date", "26 June 2026"],
        ]
        table = Table([[Paragraph(f"<b>{escape(a)}</b>", ST["body"]), Paragraph(escape(b), ST["body"])] for a, b in data], colWidths=[150, 390], rowHeights=45)
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#999999")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F5F6"))]))
        table.wrapOn(c, 540, 300)
        table.drawOn(c, 36, 370)
        c.setFont(ITALIC, 10)
        c.setFillColor(GRAY)
        c.drawString(36, 336, "Manual web application security assessment")
    return header_page.reader if False else pdf_page(draw)


FINDINGS = {
    23: dict(id="01", name="Broken Authentication", severity="High", owasp="A07:2021 - Identification and Authentication Failures", explanation="The login endpoint accepts repeated username and password attempts without effective rate limiting, progressive delay, temporary lockout, or multi-factor authentication. Using the provided bruteforce.py script and supplied username and password lists, repeated requests identified valid credentials and allowed access to the authenticated dashboard.", recommendations=["Rate-limit failed logins by account, source address, and session.", "Apply progressive delays or temporary lockout after repeated failures.", "Require multi-factor authentication for administrator accounts.", "Log and alert on abnormal authentication activity while returning generic failure messages."]),
    27: dict(id="02", name="Cross-Site Scripting (XSS)", severity="High", owasp="A03:2021 - Injection", explanation="The profile messaging feature stores user-controlled message content and later renders it as HTML without context-appropriate output encoding. A logged-in user can store an HTML element containing an event handler; the JavaScript executes when the affected profile page loads.", recommendations=["Render user messages as text with context-aware output encoding.", "Do not insert untrusted content with raw HTML APIs such as .append().", "If rich text is required, sanitize it server-side with a strict allowlist.", "Use a restrictive Content Security Policy as defense in depth."]),
    31: dict(id="03", name="Broken Access - Customer API", severity="High", owasp="A01:2021 - Broken Access Control", explanation="The customer page correctly denies a normal user, but the backing customer API returns customer records when requested directly with the same session. Authorization is enforced in the user interface but not consistently at the server endpoint, allowing a normal user to retrieve restricted data.", recommendations=["Enforce server-side authorization on every customer page and API endpoint.", "Deny access by default and centralize role checks in tested middleware or decorators.", "Return only records and fields that the authenticated user is authorized to view.", "Add negative authorization tests for normal, unauthenticated, and cross-user sessions."]),
    35: dict(id="04", name="Cookie Role Tampering", severity="Critical", owasp="A01:2021 - Broken Access Control", explanation="The application trusts the client-controlled authInfo cookie to determine the user's role. Because the Base64-encoded value has no integrity protection, a normal user can use the provided performbase64.py script to encode 2:admin, replace the cookie value, and obtain administrative access.", recommendations=["Store only an opaque session identifier in the browser and keep authorization state server-side.", "Use signed, Secure, HttpOnly, and SameSite framework-managed cookies.", "Resolve permissions from trusted server-side state on every sensitive request.", "Invalidate existing sessions after correcting the authorization design."]),
    40: dict(id="05", name="Sensitive Data Exposure", severity="High", owasp="A02:2021 - Cryptographic Failures", explanation="The customer detail endpoint returns every database column, including an MD5 password hash. Source files also contain database credentials and an application secret key. Disclosure of these values increases the impact of unauthorized API access and source-code exposure.", recommendations=["Return explicit safe fields through response schemas; never return password hashes.", "Replace MD5 password storage with Argon2id, bcrypt, or PBKDF2 using current parameters.", "Move secrets to protected deployment configuration and rotate exposed values.", "Apply least privilege to the application database account."]),
    44: dict(id="06", name="SQL Injection", severity="High", owasp="A03:2021 - Injection", explanation="The profile user-list endpoint concatenates a route value directly into a SQL statement. Supplying true and false Boolean expressions in the browser address changes the returned result set, demonstrating attacker control over query logic.", recommendations=["Use parameterized queries for all database operations.", "Constrain identifiers to the expected type at route and service boundaries.", "Use a maintained ORM or safe query builder where practical.", "Apply least-privilege database permissions and add injection regression tests."]),
}


STEPS = {
    24: ("01", "Broken Authentication", ["Open the application login page in a browser.", "Run the provided bruteforce.py script with test-username.txt and test-password.txt against the login form.", "Observe the repeated attempts and record the credential pair for which the response no longer contains the failure marker.", "Enter the discovered credentials in the normal login form.", "Confirm that the authenticated dashboard loads."], "Evidence pages 1-2 show the permitted script execution and successful authenticated dashboard."),
    28: ("02", "Cross-Site Scripting (XSS)", ["Log in as a normal user and open the Profile page.", "Use the messaging form to send <img src=x onerror=alert(1)> to the test profile.", "Reload the profile that displays the stored message.", "Confirm that the browser executes the payload and displays the alert dialog."], "The annotated evidence page shows JavaScript execution in the affected profile."),
    32: ("03", "Broken Access - Customer API", ["Log in as a normal user.", f"Open {BASE_URL}/customers/ and observe the authorization-denied message.", f"Using the same browser session, open {BASE_URL}/customers/id/.", "Confirm that the API returns restricted customer records despite the user's non-administrator role."], "Evidence page 1 shows the expected denial; evidence page 2 shows the API bypass."),
    36: ("04", "Cookie Role Tampering", ["Log in as a normal user and inspect the authInfo cookie in browser Developer Tools.", "Use the provided performbase64.py script to decode the cookie and confirm that it represents 2:user.", "Use performbase64.py to encode 2:admin; the resulting value is MjphZG1pbg==.", "Replace only the authInfo cookie value with MjphZG1pbg== and refresh.", f"Open {BASE_URL}/customers/ and confirm that administrative customer data is accessible."], "Evidence pages show the permitted Base64 script and the resulting administrative access."),
    41: ("05", "Sensitive Data Exposure", ["Authenticate in the lab and open the customer detail endpoint in the browser.", f"Navigate to {BASE_URL}/customers/id/1.", "Inspect the JSON response and identify the returned username and password-hash fields.", "Review Site/db/__init__.py and Site/__init__.py in the supplied source.", "Confirm that database credentials and the Flask secret key are stored directly in source."], "Evidence pages show the password hash returned in browser and Developer Tools responses."),
    45: ("06", "SQL Injection", ["Log in as a normal user.", f"Open the baseline endpoint: {BASE_URL}/profile/userlist/1.", "In the browser address bar, append a URL-encoded false condition: %27%20AND%20%271%27%3D%272.", "Record the returned JSON, then replace it with the true condition: %27%20OR%20%271%27%3D%271.", "Compare the baseline, false-condition, and true-condition responses. Confirm that the predicates change the result set."], "The annotated browser screenshot records the baseline response used for the Boolean comparison."),
}


def finding_page(item) -> PdfReader:
    def draw(c):
        title = f"{REPORT_ID}{item['id']} - {item['name']} - {item['severity']}"
        template_chrome(c, title)
        sev = [[Paragraph("Vulnerability Exploited:", ST["label"]), Paragraph(item["name"], ST["value"])], [Paragraph("Severity:", ST["label"]), Paragraph(item["severity"], ST["value"])], [Paragraph("OWASP TOP 10 reference:", ST["label"]), Paragraph(item["owasp"], ST["value"])]]
        t = Table(sev, colWidths=[270, 270], rowHeights=[32, 32, 44])
        t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#999999")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 8)]))
        t.wrapOn(c, 540, 108); t.drawOn(c, 36, 527)
        c.setFont(BOLD_ITALIC, 10.5); c.setFillColor(GRAY); c.drawString(36, 505, "Vulnerability Explanation")
        exp = Paragraph(escape(item["explanation"]), ST["body"]); _, eh = exp.wrap(540, 110); exp.drawOn(c, 36, 487 - eh)
        y = 468 - eh
        c.line(36, y, 576, y); y -= 20
        c.setFont(BOLD_ITALIC, 10.5); c.drawString(36, y, "Recommendations"); y -= 17
        for rec in item["recommendations"]:
            para = Paragraph("• " + escape(rec), ST["body"]); _, ph = para.wrap(528, 40); para.drawOn(c, 44, y - ph); y -= ph + 4
    return pdf_page(draw)


def steps_page(data) -> PdfReader:
    identifier, name, steps, evidence = data
    def draw(c):
        template_chrome(c, f"{REPORT_ID}{identifier} - {name} - Steps")
        c.setFont(BOLD, 16); c.setFillColor(colors.black); c.drawString(28, 630, "Steps to Reproduce")
        y = 600
        for number, text in enumerate(steps, 1):
            para = Paragraph(f"<b>{number}.</b> {escape(text)}", ST["body"]); _, ph = para.wrap(530, 80); para.drawOn(c, 36, y - ph); y -= ph + 10
        c.setFillColor(colors.HexColor("#F1F5F6")); c.roundRect(28, y - 58, 556, 50, 3, fill=1, stroke=0)
        para = Paragraph("<b>Evidence reference:</b> " + escape(evidence), ST["small"]); _, ph = para.wrap(530, 44); para.drawOn(c, 40, y - 23 - ph / 2)
        c.setFont(ITALIC, 8); c.setFillColor(GRAY); c.drawString(28, 42, "Assessment used the supplied scripts, browser, and browser Developer Tools only.")
    return pdf_page(draw)


CAPTIONS = {
    25: ("1", "bruteforce.py tests the supplied credential lists"), 26: ("2", "Valid credentials open the authenticated dashboard"),
    30: ("1", "Stored message executes JavaScript in the profile"),
    33: ("1", "Normal user is denied by the Customers page"), 34: ("2", "Direct customer API request returns restricted records"),
    37: ("1", "performbase64.py decodes the normal-user role"), 38: ("2", "performbase64.py encodes the administrator role"), 39: ("3", "Modified role cookie grants customer administration access"),
    42: ("1", "Customer API response exposes an MD5 password hash"), 43: ("2", "Developer Tools confirms the sensitive response fields"),
    46: ("1", "Baseline user-list response recorded in the browser"),
}


def annotation_overlay(number: str, caption: str) -> PdfReader:
    def draw(c):
        # Remove the unfilled template instruction and replace it with an evidence caption.
        c.setFillColor(WHITE); c.rect(18, 578, 576, 70, fill=1, stroke=0)
        c.setFillColor(TEAL); c.roundRect(24, 590, 558, 42, 4, fill=1, stroke=0)
        p = Paragraph(f"EVIDENCE {number}: {escape(caption)}", ST["caption"]); _, ph = p.wrap(520, 34); p.drawOn(c, 43, 604 - ph / 2)
        # Numbered callout and arrow point into the existing screenshot.
        c.setFillColor(GREEN); c.circle(45, 553, 14, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont(BOLD, 11); c.drawCentredString(45, 549, number)
        c.setStrokeColor(GREEN); c.setLineWidth(2); c.line(58, 548, 112, 505)
        c.line(112, 505, 103, 508); c.line(112, 505, 108, 514)
    return pdf_page(draw)


source = PdfReader(str(SOURCE), strict=False)
writer = PdfWriter()

# Keep the exact supplied page order and graphics; replace only completed content pages.
submission_pages = [1, 4, *range(6, 13), 13, 19, *range(23, 29), 30, *range(31, 47)]
for original_number in submission_pages:
    page = source.pages[original_number - 1]
    if original_number == 1:
        page.merge_page(cover_overlay().pages[0])
        writer.add_page(page)
        writer.add_page(header_page().pages[0])
        continue
    if original_number in FINDINGS:
        writer.add_page(finding_page(FINDINGS[original_number]).pages[0])
    elif original_number in STEPS:
        writer.add_page(steps_page(STEPS[original_number]).pages[0])
    else:
        if original_number in CAPTIONS:
            number, caption = CAPTIONS[original_number]
            page.merge_page(annotation_overlay(number, caption).pages[0])
        writer.add_page(page)

writer.add_metadata({"/Title": "VulnWebApp (VWA) Security Report", "/Author": "Samuel H. Mariam", "/Subject": f"{REPORT_ID} - USociety", "/Creator": "Udacity template; rubric corrections applied"})
with OUTPUT.open("wb") as output_file:
    writer.write(output_file)
print(OUTPUT)
