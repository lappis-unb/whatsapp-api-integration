from dataclasses import dataclass, field
import json
from typing import Dict, Text, Any
import os
import redis

import requests

from dotenv import load_dotenv

from .config import Config

load_dotenv()


@dataclass
class SerproApiClient:
    """
    Send requests to Serpro WhatsApp API.

    To receive webhooks on /webhooks/whatsapp/webhook route,
    call the method register_webhook manually.
    """

    client_id: Text = ""
    client_secret: Text = ""
    access_token: Text = ""
    phone_number_identifier: Text = ""
    messages_endpoint: Text = ""
    oauth2_endpoint: Text = Config.SERPRO_OAUTH2_TOKEN_URL
    webhook_url: Text = Config.RASA_WEBHOOK_URL
    authenticated_headers: Dict[Text, Text] = field(
        default_factory=lambda: (
            {
                "content-type": "application/json",
            }
        )
    )
    access_token_headers: Dict[Text, Text] = field(
        default_factory=lambda: (
            {
                "content-type": "application/x-www-form-urlencoded",
            }
        )
    )
    webhook_registration_headers: Dict[Text, Text] = field(
        default_factory=lambda: (
            {
                "content-type": "text/plain",
            }
        )
    )

    def __post_init__(self):
        self.client_id = os.getenv("SERPRO_CLIENT_ID", "")
        self.client_secret = os.getenv("SERPRO_CLIENT_SECRET", "")
        self.phone_number_identifier = os.getenv("WPP_PHONE_NUMBER_IDENTIFIER", "")
        self.redis_client = redis.Redis(
            host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True
        )
        self.oauth2_credentials = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        self.authenticate()

    def _set_access_token_header(self, headers):
        headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _message_has_buttons(self, message: Any):
        return message.get("buttons")

    def _message_has_secoes(self, message: Any):
        return message.get("secoes")

    def authenticate(self, force_authentication=False):
        """
        Requests Serpro API access_token.
        """
        self.access_token = self.redis_client.get("serpro_access_token")
        if not self.access_token or force_authentication:
            response = requests.post(
                self.oauth2_endpoint,
                data=self.oauth2_credentials,
                headers=self.access_token_headers,
            )
            if response.status_code == 200:
                response_data = response.json()
                self.access_token = response_data.get("access_token")
                self.redis_client.set("serpro_access_token", self.access_token)
                self.authenticated_headers = self._set_access_token_header(
                    self.authenticated_headers
                )
            else:
                raise Exception

        self.authenticated_headers = self._set_access_token_header(
            self.authenticated_headers
        )

    def register_webhook(self):
        """
        Register on Serpro API the Rasa endpoint to Receive WhatsApp events.
        Call this method manually to create the Serpro webhook.
        """
        if not self.access_token:
            self.authenticate()
        self.webhook_registration_header = self._set_access_token_header(
            self.webhook_registration_headers
        )
        response = requests.post(
            Config.SERPRO_WEBHOOK_REGISTRATION_URL,
            data=Config.RASA_WEBHOOK_URL,
            headers=self.webhook_registration_headers,
        )
        return response

    def _request_on_message_endpoint(self, message_endpoint: Text, message: Dict):
        return requests.post(
            message_endpoint,
            data=json.dumps(message),
            headers=self.authenticated_headers,
        )

    def _get_endpoint(self, message: Dict):
        if self._message_has_buttons(message):
            return Config.SERPRO_BUTTONS_MESSAGES_URL
        if self._message_has_secoes(message):
            return Config.SERPRO_LIST_MESSAGES_URL
        return Config.SERPRO_TEXT_MESSAGES_URL

    def send_message(self, message: Dict):
        """
        Send a Rasa dialogue response to Sepro API.
        """
        message_endpoint = self._get_endpoint(message)
        response = self._request_on_message_endpoint(message_endpoint, message)
        if response.status_code == 401:
            self.authenticate(force_authentication=True)
            response = self._request_on_message_endpoint(message_endpoint, message)
            if response.status_code == 401:
                raise Exception
        return response
