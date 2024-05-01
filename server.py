from dataclasses import dataclass, field
import json
import logging
from typing import Any, Dict, Text
import os

from flask import Flask, request
import requests

from dotenv import load_dotenv

from .message import WhatsAppEvent
from .answer import WhatsappMessagesParser, AnswersBackend

load_dotenv()

app = Flask(__name__)
app.logger.setLevel(logging.INFO)


def logging_whatsapp_event():
    # https://stackoverflow.com/questions/11093236/use-logging-print-the-output-of-pprint
    app.logger.info(f"NEW WHATSAPP EVENT: \n {json.dumps(request.json, indent=4)}")

def logging_whatsapp_post_request(response_text):
    # https://stackoverflow.com/questions/11093236/use-logging-print-the-output-of-pprint
    app.logger.info(f"NEW REQUEST TO WHATSAPP: \n {response_text}")


@dataclass
class WhatsAppApiClient:
    url: Text = f"https://graph.facebook.com/v19.0/{os.getenv("WPP_PHONE_NUMBER_IDENTIFIER", "")}/messages"
    headers: Dict[Text, Text] = field(
        default_factory=lambda: (
            {
                "Authorization": f"Bearer {os.getenv("WPP_AUTHORIZATION_TOKEN", "")}",
                "Content-Type": "application/json",
            }
        )
    )

    def send_message(self, message: Any):
        response = requests.post(
            self.url, data=json.dumps(message), headers=self.headers
        )
        return response.text, response.status_code


def verify_webhook(request):
    if request.args.get("hub.verify_token") != os.getenv("WPP_VERIFY_TOKEN", ""):
        return "Invalid verify token", 500
    return request.args.get("hub.challenge")


def respond_to_whatsapp_event(request):
    logging_whatsapp_event()
    whatsapp_event = WhatsAppEvent(event=request.json)
    app.logger.info(f"WPP EVENT {whatsapp_event.recipient_phone}")
    message = whatsapp_event.get_event_message()
    answers = AnswersBackend.get_answers_to_message(message)
    wpp_messages = WhatsappMessagesParser(
        answers, whatsapp_event.recipient_phone
    ).parse_messages()
    wpp_client = WhatsAppApiClient()
    for message in wpp_messages:
        response_text, _ = wpp_client.send_message(message)
        logging_whatsapp_post_request(response_text)
    return "ok", 200


@app.route("/webhooks/whatsapp", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return verify_webhook(request)
    if request.method == "POST":
        return respond_to_whatsapp_event(request)
