from flask import Flask, request
import smtplib
import os
from email.message import EmailMessage

app = Flask(__name__)

# Laad SMTP-configuratie uit omgevingsvariabelen
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")

# Controleer of alle variabelen aanwezig zijn
if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, TO_EMAIL, FROM_EMAIL]):
    raise RuntimeError("❌ SMTP-configuratie ontbreekt of is onvolledig.")

@app.route('/webhook', methods=['POST'])
def handle_transcript():
    # Automatische content-type detectie
    if request.content_type and request.content_type.startswith("application/x-www-form-urlencoded"):
        data = request.form.to_dict()
        print("📥 Ontvangen via form-data:", data)
    else:
        data = request.get_json(force=True, silent=True)
        print("📥 Ontvangen via JSON:", data)

    if not data:
        return '❌ Geen geldige data ontvangen', 400

    number = data.get('number', 'onbekend nummer')
    name = data.get('name', 'onbekende beller')
    email = data.get('email', 'geen e-mailadres opgegeven')
    transcript = data.get('transcript')

    if not transcript:
        return '❌ Geen transcript gevonden', 400

    subject = f"Nieuw gesprek van {name} ({number})"
    body = f"""
📞 Nieuw gesprek ontvangen:

👤 Naam: {name}
📱 Telefoonnummer: {number}
✉️ E-mailadres: {email}

📝 Transcript:
{transcript}
"""

    try:
        send_email(subject, body)
        return '✅ Transcript ontvangen en gemaild', 200
    except Exception as e:
        print("❌ Fout bij verzenden e-mail:", str(e))
        return '❌ Fout bij verzenden e-mail', 500

def send_email(subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg.set_content(body)

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
    print("📧 E-mail succesvol verzonden.")

@app.route('/', methods=['GET'])
def index():
    return '✅ API staat online', 200

@app.route('/debug', methods=['POST'])
def debug_webhook():
    print("==== DEBUGGING CALLFLUENT ====", flush=True)
    print("Headers:", dict(request.headers), flush=True)
    print("Raw Body:", request.data.decode(), flush=True)
    print("JSON:", request.get_json(silent=True), flush=True)
    return '✅ Debug ontvangen', 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("✅ Server draait op poort:", port)
    app.run(host="0.0.0.0", port=port)

