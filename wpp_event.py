from dataclasses import dataclass, field
from typing import Any, Dict, List, Text
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
class EventContact:
    contacts: List
    name: Text = "Participante"
    phone: Text = ""

    def __post_init__(self):
        if self.contacts and len(self.contacts) > 0:
            self._set_name(self.contacts[0])
            self._set_phone(self.contacts[0])

    def _set_name(self, contact):
        if contact:
            phone_number = contact["wa_id"]
            if not re.search(r"^(\d{4}9)", phone_number):
                phone_number = phone_number[:4] + "9" + phone_number[4:]
            self.phone = f"+{phone_number}"

    def _set_phone(self, contact):
        if contact:
            profile = contact.get("profile")
            if profile:
                self.name = profile.get("name")


@dataclass
class WhatsAppEvent:
    """
    Generic implementation to manage WhatsApp API events.
    """

    event: Dict
    event_source: SerproEvent | CloudApiEvent | None = None
    parser_class: SerproApiMessagesParser | CloudApiMessagesParser | None = None
    recipient_phone: Text = ""
    profile_name: Text = "Participante"
    message_types: Dict[str, Any] = field(
        default_factory=lambda: {
            "interactive": InteractiveButtonMessage,
            "text": TextMessage,
        }
    )
    sender_id: Text = ""
    contact: EventContact = field(default_factory=lambda: EventContact([]))

    def __post_init__(self):
        if self._event_is_from_cloud_api():
            self.event_source = CloudApiEvent(self.event)
            self.parser_class = CloudApiMessagesParser
            self.wpp_client = CloudApiClient()
        else:
            self.event_source = SerproEvent(self.event)
            self.parser_class = SerproApiMessagesParser
            self.wpp_client = SerproApiClient()
        self._set_contact()

    def get_event_message(
        self,
    ) -> InteractiveButtonMessage | TextMessage | NotSupportedMessage:
        event_messages: List = self.get_event_key("messages")
        if event_messages:
            message: Dict = event_messages[0]
            message_class = self.message_types[message.get("type")]
            return message_class(message)
        return NotSupportedMessage({})

    # TODO: check if self.event is a WhatsApp event
    def get_event_key(self, key: Text):
        return self.event_source.get_event_key(key)

    def _event_is_from_cloud_api(self) -> bool:
        """
        Returns true if self.event is a Cloud API webhook event.
        """
        return (
            self.event.get("object")
            and self.event.get("object") == "whatsapp_business_account"
        )

    def _set_contact(self):
        contacts: List = self.get_event_key("contacts")
        self.contact = EventContact(contacts)
