import json
import logging
import os

from flask import Flask, request

from .message import WhatsAppEvent
from .rasa import RasaBackend, WhatsappMessagesParser
from .wpp_api_client import WhatsAppApiClient


app = Flask(__name__)
app.logger.setLevel(logging.INFO)


def logging_whatsapp_event():
    # https://stackoverflow.com/questions/11093236/use-logging-print-the-output-of-pprint
    app.logger.info(f"NEW WHATSAPP EVENT: \n {json.dumps(request.json, indent=4)}")


def logging_whatsapp_post_request(response_text):
    # https://stackoverflow.com/questions/11093236/use-logging-print-the-output-of-pprint
    app.logger.info(f"NEW REQUEST TO WHATSAPP: \n {response_text}")


def verify_webhook(request):
    if request.args.get("hub.verify_token") != os.getenv("WPP_VERIFY_TOKEN", ""):
        return "Invalid verify token", 500
    return request.args.get("hub.challenge")


def poll_event(request, message, whatsapp_event):
    wpp_messages = [
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": whatsapp_event.recipient_phone,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": "Participe da nossa pesquisa sobre a praça Dominguinhos",
                },
                "body": {
                    "text": "É verdade isso sobre a praça da Dominguinho em Votorantim??? (Praça José Ermírio de Moraes) \n"
                    "O que você acha sobre essa opinião: **A praça é nossa mas temos que cobrar a prefeitura pra tratar ela com mais carinho**"
                },
                "footer": {"text": "<MESSAGE_FOOTER_TEXT>"},
                "action": {
                    "sections": [
                        {
                            "title": "Participe",
                            "rows": [
                                {
                                    "id": "1",
                                    "title": "Concordar",
                                    "description": "",
                                },
                                {
                                    "id": "2",
                                    "title": "Discordar",
                                    "description": "",
                                },
                                {
                                    "id": "3",
                                    "title": "Pular",
                                    "description": "",
                                },
                            ],
                        }
                    ],
                    "button": "options",
                },
            },
        }
    ]
    pass
    wpp_client = WhatsAppApiClient()
    for message in wpp_messages:
        response_text, _ = wpp_client.send_message(message)
        logging_whatsapp_post_request(response_text)


def opinion_bot_event(request, message, whatsapp_event):
    answers = RasaBackend().get_answers_to_message(message)
    wpp_messages = WhatsappMessagesParser(
        answers, whatsapp_event.recipient_phone
    ).parse_messages()
    wpp_client = WhatsAppApiClient()
    for message in wpp_messages:
        response_text, _ = wpp_client.send_message(message)
        logging_whatsapp_post_request(response_text)


def respond_to_whatsapp_event(request):
    whatsapp_event = WhatsAppEvent(event=request.json)
    message = whatsapp_event.get_event_message()
    logging_whatsapp_event()
    if message.text == "/poll 15":
        poll_event(request, message, whatsapp_event)
    else:
        opinion_bot_event(request, message, whatsapp_event)

    return "ok", 200


@app.route("/webhooks/whatsapp/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return verify_webhook(request)
    if request.method == "POST":
        return respond_to_whatsapp_event(request)
