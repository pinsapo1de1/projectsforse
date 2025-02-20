import os
import requests
from flask import Flask, request

app = Flask(__name__)

# Configuración del WhatsApp Cloud API
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")  # Token de WhatsApp Cloud API desde .env file
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")  # Phone ID de WhatsApp desde .env file
CHATBOT_API_URL = os.getenv("CHATBOT_API_URL")  # URL API del chatbot desde .env file
CHATBOT_API_KEY = os.getenv("CHATBOT_API_KEY")  # Clave API del chatbot desde .env file

@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    """Verificación del Webhook de WhatsApp Cloud API"""
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")  # Leer desde las variables de entorno
    challenge = request.args.get("hub.challenge")
    token = request.args.get("hub.verify_token")
    
    if token == verify_token:
        return challenge  # Responder con el challenge recibido si el token es válido
    else:
        return "Token de verificación inválido", 403

def enviar_mensaje_whatsapp(numero, mensaje):
    """Enviar mensaje a través de WhatsApp Cloud API"""
    url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {"body": mensaje}
    }

    response = requests.post(url, headers=headers, json=data)
    
    # Usar print para ver si WhatsApp devuelve un error
    print("Respuesta de WhatsApp:", response.json())

    return response.json()

@app.route("/webhook", methods=["POST"])
def recibir_mensaje():
    """Recibir y procesar mensajes de WhatsApp"""
    data = request.json
    if "messages" in data["entry"][0]["changes"][0]["value"]:
        mensaje = data["entry"][0]["changes"][0]["value"]["messages"][0]
        numero = mensaje["from"]
        texto = mensaje["text"]["body"]

        # Enviar el texto al endpoint de la API del chatbot
        headers = {
            "content-type": "application/json",
            "x-api-key": CHATBOT_API_KEY  # Usamos la clave API del chatbot
        }

        # Datos a enviar a la API del chatbot
        payload = {
            "message": texto,  # El texto del mensaje
            "history": [],      # Historial de conversación, si lo necesitas
            "stream": False,    # Si se usa streaming o no
            "include_sources": False  # Si se incluyen fuentes, ajusta según tus necesidades
        }

        # Llamada a la API del chatbot
        try:
            response = requests.post(CHATBOT_API_URL, json=payload, headers=headers)
            response.raise_for_status()  # Lanza un error si la respuesta no es 200 OK
            bot_respuesta = response.json()  # Asumimos que la respuesta es JSON
            print(f"Respuesta del bot: {bot_respuesta}")  # Para depuración
            respuesta = bot_respuesta['bot']['text']  # Accedemos correctamente a la respuesta
        except requests.exceptions.RequestException as e:
            print(f"Error al conectar con el chatbot: {e}")
            respuesta = "Hubo un error al procesar tu solicitud."

        # Enviar respuesta a WhatsApp
        enviar_mensaje_whatsapp(numero, respuesta)

    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
