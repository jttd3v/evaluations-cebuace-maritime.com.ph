import imaplib
import email
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv
from db import get_db

load_dotenv()

IMAP_HOST = os.getenv('IMAP_HOST')
IMAP_USER = os.getenv('IMAP_USER')
IMAP_PASSWORD = os.getenv('IMAP_PASSWORD')
ATTACH_DIR = Path(os.getenv('ATTACH_DIR', 'data/evaluations/raw'))
ATTACH_DIR.mkdir(parents=True, exist_ok=True)


def parse_subject(subject):
    # placeholder parser -- implement according to subject format
    return ('VESSEL', 'Q1', '2024', 'CAPT')


def create_eval_record(path, vessel, quarter, year, rank):
    # placeholder for DB insert logic
    pass


def fetch_new_emails():
    imap = imaplib.IMAP4_SSL(IMAP_HOST)
    imap.login(IMAP_USER, IMAP_PASSWORD)
    imap.select('INBOX')
    typ, msgnums = imap.search(None, '(UNSEEN)')
    for num in msgnums[0].split():
        typ, data = imap.fetch(num, '(RFC822)')
        msg = email.message_from_bytes(data[0][1])
        for part in msg.walk():
            if part.get_content_type() == 'application/pdf':
                filename = f'{uuid.uuid4()}.pdf'
                p = ATTACH_DIR / filename
                p.write_bytes(part.get_payload(decode=True))
                vessel, quarter, year, rank = parse_subject(msg['Subject'])
                create_eval_record(p, vessel, quarter, year, rank)
        imap.store(num, '+FLAGS', '\\Seen')
    imap.logout()


if __name__ == '__main__':
    fetch_new_emails()
