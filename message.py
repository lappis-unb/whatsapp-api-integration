from dataclasses import dataclass, field
from typing import Any, Dict, Text


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


