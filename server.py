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


def respond_to_whatsapp_event(request):
    logging_whatsapp_event()
    whatsapp_event = WhatsAppEvent(event=request.json)
    message = whatsapp_event.get_event_message()
    answers = RasaBackend().get_answers_to_message(message)
    wpp_messages = WhatsappMessagesParser(
        answers, whatsapp_event.recipient_phone
    ).parse_messages()
    wpp_client = WhatsAppApiClient()
    for message in wpp_messages:
        response_text, _ = wpp_client.send_message(message)
        logging_whatsapp_post_request(response_text)
    return "ok", 200


@app.route("/webhooks/whatsapp/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return verify_webhook(request)
    if request.method == "POST":
        return respond_to_whatsapp_event(request)
