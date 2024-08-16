from dataclasses import dataclass
from typing import Dict, Text


@dataclass
class NotSupportedMessage:
    message: Dict
    text: Text = ""


@dataclass
class InteractiveMessage:
    message: Dict
    text: Text = ""

    def __post_init__(self):
        self.set_message()

    def set_message(self):
        interactive: Dict = self.message.get("interactive")
        if interactive.get("type") == "button_reply":
            self.text = str(interactive.get("button_reply").get("id"))
        if interactive.get("type") == "list_reply":
            self.text = str(interactive.get("list_reply").get("id"))


@dataclass
class TextMessage:
    message: Dict
    text: Text = ""

    def __post_init__(self):
        self.set_message()

    def set_message(self):
        self.text = self.message.get("text").get("body")
