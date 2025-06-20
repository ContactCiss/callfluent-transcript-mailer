from flask import Flask, request
import smtplib
import os
import requests
from email.message import EmailMessage
from datetime import datetime

app = Flask(__name__)

# Laad SMTP-configuratie uit omgevingsvariabelen
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
TO_EMAIL = os.getenv("TO_EMAIL")
FROM_EMAIL = os.getenv("FROM_EMAIL")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

# Controleer of alle variabelen aanwezig zijn
if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, TO_EMAIL, FROM_EMAIL]):
    raise RuntimeError("❌ SMTP-configuratie ontbreekt of is onvolledig.")

def generate_audio_with_speed(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.7,
            "similarity_boost": 0.8,
            "style": 1.5,
            "speed": 1.3
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        with open("output_ruth.wav", "wb") as f:
            f.write(response.content)
        print("🔊 Audio succesvol gegenereerd.", flush=True)
    else:
        print("❌ Fout bij ElevenLabs:", response.status_code, response.text, flush=True)

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
    phone = data.get('number', 'onbekend nummer')
    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

    # 🔊 Genereer audio met versneld tempo
    generate_audio_with_speed(transcript)

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

def send_email(subject, html_body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg.set_content("Deze e-mail bevat een transcript van een CallFluent-gesprek.")
    msg.add_alternative(html_body, subtype='html')

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

    print("📧 E-mail succesvol verzonden.", flush=True)

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
