from dataclasses import dataclass, field
import json
from typing import Any, Dict, Text
import os

import requests

from dotenv import load_dotenv

load_dotenv()


@dataclass
class WhatsAppApiClient:
    authorization_token: Text = ""
    phone_number_identifier: Text = ""
    messages_endpoint: Text = ""
    headers: Dict[Text, Text] = field(
        default_factory=lambda: (
            {
                "Authorization": "",
                "Content-Type": "application/json",
            }
        )
    )

    def __post_init__(self):
        self.authorization_token = os.getenv("WPP_AUTHORIZATION_TOKEN", "")
        self.phone_number_identifier = os.getenv("WPP_PHONE_NUMBER_IDENTIFIER", "")
        self.headers["Authorization"] = f"Bearer {self.authorization_token}"
        self.messages_endpoint = (
            f"https://graph.facebook.com/v19.0/{self.phone_number_identifier}/messages"
        )

    def send_message(self, message: Any):
        response = requests.post(
            self.messages_endpoint, data=json.dumps(message), headers=self.headers
        )
        return response.text, response.status_code
