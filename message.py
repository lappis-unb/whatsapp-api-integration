from dataclasses import dataclass, field
from typing import Any, Dict, Text
import re


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
    recipient_phone: Text = ""
    message_types: Dict[str, Any] = field(
        default_factory=lambda: {
            "interactive": InteractiveButtonMessage,
            "text": TextMessage,
        }
    )

    def __post_init__(self):
        self.set_recipient_phone()

    def get_event_message(
        self,
    ) -> InteractiveButtonMessage | TextMessage | NotImplementedMessage:
        event_messages = self.get_event_value_key("messages")
        if event_messages:
            message = event_messages[0]
            message_class = self.message_types[message.get("type")]
            return message_class(message)
        return NotImplementedMessage({})

    # TODO: check if self.event is a WhatsApp event
    def get_event_value_key(self, key: Text) -> Text | None:
        event_changes = self.event["entry"][0]["changes"][0]
        event_value = event_changes.get("value")
        return event_value.get(key)

    def set_recipient_phone(self):
        contacts = self.get_event_value_key("contacts")
        if contacts:
            contact = contacts[0]
            phone_number = contact["wa_id"]
            if not re.search(r"^(\d{4}9)", phone_number):
                phone_number = phone_number[:4] + '9' + phone_number[4:]
            self.recipient_phone = f"+{phone_number}"
