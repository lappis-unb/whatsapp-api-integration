from dataclasses import dataclass, field
import json
import logging
from typing import Any, Dict, Text
import os

from flask import Flask, request
import requests

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.logger.setLevel(logging.INFO)


@dataclass
class NotImplementedMessage:
    message: Dict
    text: Text = ""


@dataclass
class InteractiveButtonMessage:
    message: Dict
    text: Text = ""

    def __post_init__(self):
        self.set_message()

    def set_message(self):
        interactive = self.message.get("interactive")
        self.text = interactive.get("button_reply").get("id")
        app.logger.info("INTERACTIVE MESSAGE: %s", self.text)


@dataclass
class TextMessage:
    message: Dict
    text: Text = ""

    def __post_init__(self):
        self.set_message()

    def set_message(self):
        self.text = self.message.get("text").get("body")


@dataclass
class WhatsAppEvent:
    event: Dict
    message_types: Dict[str, Any] = field(
        default_factory=lambda: {
            "interactive": InteractiveButtonMessage,
            "text": TextMessage,
        }
    )

    def get_event_message(
        self,
    ) -> InteractiveButtonMessage | TextMessage | NotImplementedMessage:
        event_changes = self.event["entry"][0]["changes"][0]
        event_value = event_changes.get("value")
        event_messages = event_value.get("messages")
        if event_messages:
            message = event_messages[0]
            message_class = self.message_types[message.get("type")]
            return message_class(message)
        return NotImplementedMessage({})


def logging_whatsapp_event():
    # https://stackoverflow.com/questions/11093236/use-logging-print-the-output-of-pprint
    app.logger.info(f"NEW WHATSAPP EVENT: \n {json.dumps(request.json, indent=4)}")


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


# Reimplement this class with your message backend.
@dataclass
class ResponseService:

    message: InteractiveButtonMessage | TextMessage | NotImplementedMessage

    def get_responses_to_message(self) -> list:
        if not self.message.text:
            return []
        return RESPONSE_MESSAGES


@dataclass
class WhatsAppApiClient:
    url: Text = "https://graph.facebook.com/v19.0/326737040513319/messages"
    headers: Dict[Text, Text] = field(
        default_factory=lambda: (
            {
                "Authorization": f"Bearer {os.getenv("WPP_AUTHORIZATION_TOKEN", "")}",
                "Content-Type": "application/json",
            }
        )
    )

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


def verify_webhook(request):
    if request.args.get("hub.verify_token") != "1234":
        return "Invalid verify token", 500
    return request.args.get("hub.challenge")


def respond_to_whatsapp_event(request):
    logging_whatsapp_event()
    whatsapp_event = WhatsAppEvent(event=request.json)
    message = whatsapp_event.get_event_message()
    response_service = ResponseService(message)
    responses = response_service.get_responses_to_message()
    wpp_client = WhatsAppApiClient()
    for response in responses:
        wpp_client.send_message(response)
    return "ok", 200


@app.route("/webhooks/whatsapp", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return verify_webhook(request)
    if request.method == "POST":
        return respond_to_whatsapp_event(request)
