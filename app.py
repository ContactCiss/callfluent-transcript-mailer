from flask import Flask, request
import smtplib
import os
from email.message import EmailMessage

app = Flask(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")

@app.route('/webhook', methods=['POST'])
def handle_transcript():
    data = request.json
    transcript = data.get('transcript')
    caller = data.get('caller', 'onbekend')
    subject = f"Nieuw gesprek van {caller}"
    
    if transcript:
        send_email(subject, transcript)
        return 'Transcript ontvangen en gemaild', 200
    else:
        return 'Geen transcript gevonden', 400

def send_email(subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

if __name__ == '__main__':
    app.run()
