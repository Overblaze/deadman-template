"""Emails every file in send/ to the contact(s). Runs inside GitHub Actions.

TEST=true sends only to the owner, with a [TEST] subject prefix.
"""
import mimetypes
import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

test = os.environ.get("TEST", "").lower() == "true"
owner = os.environ["OWNER_NAME"]

if test:
    recipients = [os.environ["OWNER_EMAIL"]]
else:
    recipients = [e.strip() for e in os.environ["CONTACT_EMAILS"].split(",") if e.strip()]
if not recipients:
    raise SystemExit("No recipients configured")

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

msg = EmailMessage()
msg["From"] = os.environ["SMTP_USER"]
msg["To"] = ", ".join(recipients)
msg["Subject"] = ("[TEST] " if test else "") + f"Please check on {owner}"
msg.set_content(
    f"""{'THIS IS A TEST. No action needed.' + chr(10) + chr(10) if test else ''}This is an automated message sent {now}.

{owner} set up a check-in system and has not responded for several days.
This does not necessarily mean something is wrong. Their phone may be dead
or they may be travelling.

Please:
  1. Try to reach {owner} by phone or text.
  2. If you can't reach them, go by their place and check on them.
  3. Read the attached instructions before opening anything.

If you believe there is an emergency, call emergency services first.
"""
)

send_dir = Path("send")
for f in sorted(p for p in send_dir.iterdir() if p.is_file() and not p.name.startswith(".")):
    ctype, _ = mimetypes.guess_type(f.name)
    maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
    msg.add_attachment(f.read_bytes(), maintype=maintype, subtype=subtype, filename=f.name)

host = os.environ["SMTP_HOST"]
port = int(os.environ.get("SMTP_PORT") or 465)
user, password = os.environ["SMTP_USER"], os.environ["SMTP_PASS"]

if port == 465:
    with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context()) as s:
        s.login(user, password)
        s.send_message(msg)
else:
    with smtplib.SMTP(host, port) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(user, password)
        s.send_message(msg)

print(f"Sent to {len(recipients)} recipient(s){' (test)' if test else ''}")
