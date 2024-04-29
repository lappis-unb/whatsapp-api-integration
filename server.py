from dataclasses import dataclass
import json
from typing import Any, Dict, Text

import requests

from flask import Flask, request

app = Flask(__name__)

RESPONSE_MESSAGES = [
    {
        "recipient_id": "257609550778186",
        "text": "Olá, Eu sou a Duda, a assistente virtual da Plataforma Empurrando Juntas. Meu trabalho é descobrir a opinião das pessoas sobre determinados temas e para isso eu preciso da sua ajuda.  A suas opiniões serão enviadas para a nossa plataforma, conforme o nosso termo de uso https://www.ejparticipe.org/usage/.",
    },
    {
        "recipient_id": "257609550778186",
        "text": "Eu perguntei para algumas pessoas o que elas acham sobre o seguinte assunto:\nO que pode ser feito para superar os desafios da transformação digital do governo?",
    },
    {
        "recipient_id": "257609550778186",
        "text": "Vou te mandar o que me responderam e gostaria da sua opinião:",
    },
    {
        "recipient_id": "257609550778186",
        "text": "Simplicidade, simplicidade e sim+pli+ci+da+de. Ser digital não significa ser complexo. Essa é uma grande barreira a ser superada. \n O que você acha disso (0/97)?",
        "buttons": [
            {"title": "Concordar", "payload": "Concordar"},
            {"title": "Discordar", "payload": "Discordar"},
            {"title": "Pular", "payload": "Pular"},
        ],
    },
]


@dataclass
class WhatsAppApiClient:
    url: str = "https://graph.facebook.com/v19.0/326737040513319/messages"
    headers = {
        "Authorization": "Bearer EAARUraCBHf4BOwVsh63BR1ipOjwdD8lf8d7ZBf5K6thXTjwDpWHOQc2ggZCXDtsyKSb0lKzCuLEijmZCx5ZBdmpDOZBFZAwumQgsIatiyZAInkRZBHFSPtzUwvlUfo216t8kTZCd7xW8cTKLTlpZCyXZBvqOxqoTXLGpn0MHxcIpLFLXZCZAFag49eR3PEmrw2gT8M0x10qC8vKC98brOBrC2XZCQZD",
        "Content-Type": "application/json",
    }

    def get_message_type(self, rasa_message: Any):
        if rasa_message.get("buttons"):
            return "interactive"
        return "text"

    def send_message(self, rasa_message: Any):
        message_type = self.get_message_type(rasa_message)
        payload: Dict = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "+5561981178174",
            "type": message_type,
        }
        if message_type == "interactive":
            payload.update(
                {
                    "interactive": {
                        "type": "button",
                        "body": {"text": rasa_message.get("text")},
                        "action": {
                            "buttons": [
                                {
                                    "type": "reply",
                                    "reply": {"id": "1", "title": "concordar"},
                                },
                                {
                                    "type": "reply",
                                    "reply": {"id": "-1", "title": "descordar"},
                                },
                                {
                                    "type": "reply",
                                    "reply": {"id": "0", "title": "pular"},
                                },
                            ]
                        },
                    },
                }
            )
        else:
            payload.update(
                {
                    "text": {"body": rasa_message.get("text"), "preview_url": False},
                }
            )
        response = requests.post(
            self.url, data=json.dumps(payload), headers=self.headers
        )
        return response.text, response.status_code


@app.route("/webhooks/whatsapp", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") != "1234":
            return "Invalid verify token", 500
        return request.args.get("hub.challenge")
    if request.method == "POST":
        user_message = get_whatsapp_message(request)
        messages = get_response_messages(user_message)
        wpp_client = WhatsAppApiClient()
        for rasa_message in messages:
            response_text, status_code = wpp_client.send_message(rasa_message)
            print(response_text, status_code)
        return "ok", 200


# Reimplement this method with your message backend.
def get_response_messages(user_message: Text):
    if not user_message:
        return []
    return RESPONSE_MESSAGES


def get_whatsapp_message(request):
    print("WHATSAPP EVENT: ", request.json)
    value = request.json.get("entry")[0].get("changes")[0].get("value")
    if value.get("messages"):
        message = value.get("messages")[0]
        if message.get('interactive'):
            interactive = message.get('interactive')
            vote = interactive.get("button_reply").get("id")
            print("CONVERSATION COMMENT VOTE: ", vote)
            return vote
        else:
            return value.get("messages")[0].get("text").get("body")
    return ""
