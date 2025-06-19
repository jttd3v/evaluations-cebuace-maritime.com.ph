# Crew Evaluation Automation Blueprint

This repository holds a technical blueprint for semi-automating the paper-based quarterly crew-evaluation workflow using a Flask + MySQL web application. The goal is to keep the original handwritten forms while eliminating manual collection, filing, and status reporting.

## Architecture Overview

```
flowchart TD
    A[Ship – scans handwritten eval<br>(mobile scanner app)] -->|PDF email to evaluations@| B(IMAP Collector – Python)
    B -->|store file| C[/File store/]
    B -->|create/refresh record| D[(MySQL)]
    D --> E[Flask Admin<br>& React/Vue dashboard]
    E -->|assign, review, sign| F[Digital Sign Service<br>(DocuSign / LibreSign / custom pad)]
    F -->|signed PDF + status update| D
    D -->|read-only link| G[Owner / Shipmanager Portal]
    D -->|daily digest & overdue alerts| H[Notification Engine]
```

The system runs on an existing XAMPP stack (Apache and MySQL). Flask can be deployed behind `mod_wsgi` or via a simple Gunicorn/Waitress reverse proxy.

## Key Components

| Layer | Tech / Libs | Responsibilities |
| ----- | ----------- | ---------------- |
| **Email/Upload Collector** | `imaplib`, `email` | Monitors the evaluations mailbox, parses subject lines, and saves attachments to the file store. |
| **Database** | MySQL | Tables: `seafarers`, `vessels`, `voyages`, `evaluation_forms`, `review_tasks`, `users`. |
| **OCR Service (optional)** | `pytesseract` or AWS Textract | Extracts scores and text from forms to populate analytics tables. |
| **Web Dashboard** | Flask + Jinja2 / small SPA | Lists forms by ship/quarter/rank, embeds PDF viewer, allows "Approve & Sign". |
| **Digital Signature** | DocuSign, Adobe Sign, LibreSign | Sends PDFs for e-signature and updates records when complete. |
| **Notification Engine** | `apscheduler` cron job | Sends reminders to vessels and nightly digests to the quality team. |
| **Owner/Manager Access** | Flask route with expiring JWT links | Provides read-only view of signed evaluations without requiring login. |

## Database Schema Example

```sql
CREATE TABLE seafarers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crew_no VARCHAR(20) UNIQUE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    rank VARCHAR(30)
);

CREATE TABLE vessels (
    id INT AUTO_INCREMENT PRIMARY KEY,
    imo VARCHAR(10) UNIQUE,
    name VARCHAR(50),
    flag ENUM('PAN', 'SGP', 'BHS')
);

CREATE TABLE evaluation_forms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    seafarer_id INT,
    vessel_id INT,
    quarter ENUM('Q1','Q2','Q3','Q4'),
    year SMALLINT,
    pdf_path VARCHAR(255),
    ocr_json JSON,
    status ENUM('Received','In Review','Signed','Sent to Owner') DEFAULT 'Received',
    signed_pdf_path VARCHAR(255),
    FOREIGN KEY (seafarer_id) REFERENCES seafarers(id),
    FOREIGN KEY (vessel_id)  REFERENCES vessels(id)
);
```

Additional tables such as `users`, `review_tasks`, and `audit_log` keep ISO 9001 traceability.

## Sample Python Snippets

### IMAP Collector
```python
import imaplib, email, os, uuid
from pathlib import Path
from db import create_eval_record

def fetch_new_emails():
    imap = imaplib.IMAP4_SSL("mail.yourdomain.com")
    imap.login("evaluations@yourdomain.com", os.getenv("MAIL_PWD"))
    imap.select("INBOX")
    typ, msgnums = imap.search(None, '(UNSEEN)')
    for num in msgnums[0].split():
        typ, data = imap.fetch(num, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])
        for part in msg.walk():
            if part.get_content_type() == "application/pdf":
                fn = f"{uuid.uuid4()}.pdf"
                p = Path("/data/evaluations/raw") / fn
                p.write_bytes(part.get_payload(decode=True))
                vessel, quarter, year, rank = parse_subject(msg["Subject"])
                create_eval_record(p, vessel, quarter, year, rank)
        imap.store(num, '+FLAGS', '\\Seen')
```

### Flask Review & Sign Endpoint
```python
@app.route("/review/<int:eval_id>", methods=["POST"])
@login_required(role="evaluator")
def review(eval_id):
    signed_url = docusign_send_and_wait(pdf_path)
    EvaluationForm.query.get(eval_id).update(
        status="Signed", signed_pdf_path=signed_url
    )
    db.session.commit()
    send_owner_link(eval_id)
    return jsonify({"ok": True})
```

## Compliance Touch-Points

| Requirement | How Covered |
|-------------|-------------|
| **Document Control** | Each form revision and approval timestamp is logged in the `audit_log` table. |
| **Traceability** | Evaluation IDs tie back to crew numbers and voyages; PDFs stored in immutable storage. |
| **Management Review Evidence** | Dashboards export CSV/PDF summaries for quarterly review. |

## Roll-out Plan

1. **Sprint 0 (1 w)** – Confirm subject lines and PDF templates. Create a test mailbox.
2. **Sprint 1 (2 w)** – Implement email collector, database, and a basic dashboard showing received forms.
3. **Sprint 2 (2 w)** – Build reviewer UI with manual upload fallback.
4. **Sprint 3 (2 w)** – Integrate digital signing and owner portal.
5. **Sprint 4 (1 w)** – Add reminder scheduler and KPI widgets.

Total estimated duration: ~8–9 weeks with one full-time developer or a small team.

## Long-Term Enhancements

- OCR analytics to generate competency heat maps.
- Power BI integration for fleet-wide dashboards.
- Mobile progressive web app for offline capture and upload.
- API integration with a Django DMS to auto-link PDFs to crew files.

## Contributing

1. Clone the repository.
2. On Windows, run `setup.cmd` to create a virtual environment and install dependencies automatically. Linux/macOS users can run `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and update the credentials for MySQL and IMAP.
4. Initialize the database tables: `python -c 'from app import db; db.create_all()'`.
5. In one terminal run the email collector: `python collector.py`.
6. In another terminal run the web app: `flask --app app run`.
7. Submit pull requests with descriptive commits.

