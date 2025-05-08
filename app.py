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

from datetime import datetime

@app.route('/webhook', methods=['POST'])
def handle_transcript():
    print("📥 Binnenkomende /webhook request", flush=True)

    try:
        data = request.get_json(force=True, silent=True)
        print("📦 JSON geladen:", data, flush=True)
    except Exception as e:
        print("❌ Fout bij verwerken JSON:", str(e), flush=True)
        return '❌ Fout bij verwerken JSON', 400

    if not data:
        return '❌ Geen geldige data ontvangen', 400

    name = data.get('name', 'onbekende beller')
    transcript = data.get('transcription', 'Geen transcript ontvangen')
    phone = data.get('number', 'onbekend nummer')  # Als CallFluent dit ooit meegeeft
    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    subject = "CallFluent Transcriptie"
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2>📞 Nieuw gesprek ontvangen</h2>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
          <tr>
            <th align="left">🕒 Tijdstip</th>
            <td>{timestamp}</td>
          </tr>
          <tr>
            <th align="left">👤 Naam</th>
            <td>{name}</td>
          </tr>
          <tr>
            <th align="left">📱 Telefoonnummer</th>
            <td>{phone}</td>
          </tr>
          <tr>
            <th align="left">📝 Transcript</th>
            <td><pre style="white-space: pre-wrap;">{transcript}</pre></td>
          </tr>
        </table>
      </body>
    </html>
    """

    try:
        send_email(subject, html_body)
        return '✅ Transcript ontvangen en gemaild', 200
    except Exception as e:
        print("❌ Fout bij verzenden e-mail:", str(e), flush=True)
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

