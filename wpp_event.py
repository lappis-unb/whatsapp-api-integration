from dataclasses import dataclass, field
from typing import Any, Dict, Text
import re

from .serpro_api_client import SerproApiClient
from .wpp_api_client import CloudApiClient
from .rasa import CloudApiMessagesParser
from .serpro import SerproApiMessagesParser
from .message import InteractiveButtonMessage, TextMessage, NotSupportedMessage


@dataclass
class CloudApiEvent:
    """
    Implements the logic to deal with Cloud API webhook events.
    """

    event: Dict

    def get_event_key(self, key: Text):
        """
        Retrieves a key from self.event dictionary.
        """
        event_changes = self.event["entry"][0]["changes"][0]
        event_value = event_changes.get("value")
        return event_value.get(key)


@dataclass
class SerproEvent:
    """
    Implements the logic to deal with Serpro webhook events.
    """

    event: Dict

    def get_event_key(self, key: Text):
        """
        Retrieves a key from self.event dictionary.
        """
        return self.event.get(key)


@dataclass
class WhatsAppEvent:
    """
    Generic implementation to manage WhatsApp API events.
    """

    event: Dict
    event_source: SerproEvent | CloudApiEvent | None = None
    parser_class: SerproApiMessagesParser | CloudApiMessagesParser | None = None
    recipient_phone: Text = ""
    message_types: Dict[str, Any] = field(
        default_factory=lambda: {
            "interactive": InteractiveButtonMessage,
            "text": TextMessage,
        }
    )
    sender_id: Text = ""

    def __post_init__(self):
        if self._event_is_from_cloud_api():
            self.event_source = CloudApiEvent(self.event)
            self.parser_class = CloudApiMessagesParser
            self.wpp_client = CloudApiClient()
        else:
            self.event_source = SerproEvent(self.event)
            self.parser_class = SerproApiMessagesParser
            self.wpp_client = SerproApiClient()
        self.set_recipient_phone()

    def get_event_message(
        self,
    ) -> InteractiveButtonMessage | TextMessage | NotSupportedMessage:
        event_messages = self.get_event_key("messages")
        if event_messages:
            message = event_messages[0]
            message_class = self.message_types[message.get("type")]
            return message_class(message)
        return NotSupportedMessage({})

    # TODO: check if self.event is a WhatsApp event
    def get_event_key(self, key: Text) -> Text | None:
        return self.event_source.get_event_key(key)

    def _event_is_from_cloud_api(self) -> bool:
        """
        Returns true if self.event is a Cloud API webhook event.
        """
        return (
            self.event.get("object")
            and self.event.get("object") == "whatsapp_business_account"
        )

    def set_recipient_phone(self):
        contacts = self.get_event_key("contacts")
        if contacts:
            contact = contacts[0]
            phone_number = contact["wa_id"]
            if not re.search(r"^(\d{4}9)", phone_number):
                phone_number = phone_number[:4] + "9" + phone_number[4:]
            self.recipient_phone = f"+{phone_number}"
