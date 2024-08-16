from dataclasses import dataclass, field
from typing import Any, Dict, Text, List
from .message import InteractiveMessage, TextMessage, NotSupportedMessage


@dataclass
class RasaBackend:
    """
    Fake Rasa backend to processing WhatsApp user message.

    This class is for tests only. You should implement or consume some real Rasa instance
    or any other service that will decide what to do with the WhatsApp message.
    """

    answers: List[Dict[Text, Text]] = field(
        default_factory=lambda: [
            {
                "recipient_id": "257609550778186",
                "text": "Olá, Eu sou a Duda, a assistente virtual da Plataforma Empurrando Juntas. "
                "Meu trabalho é descobrir a opinião das pessoas sobre determinados temas e "
                "para isso eu preciso da sua ajuda.  A suas opiniões serão enviadas para "
                "a nossa plataforma, conforme o nosso "
                "termo de uso https://www.ejparticipe.org/usage/.",
            },
            {
                "recipient_id": "257609550778186",
                "text": "Eu perguntei para algumas pessoas o que elas acham sobre "
                "o seguinte assunto:\nO que pode ser feito para superar os desafios da "
                "transformação digital do governo?",
            },
            {
                "recipient_id": "257609550778186",
                "text": "Vou te mandar o que me responderam e gostaria da sua opinião:",
            },
            {
                "recipient_id": "257609550778186",
                "text": "Simplicidade, simplicidade e sim+pli+ci+da+de. Ser digital "
                "não significa ser complexo. Essa é uma grande barreira a ser superada. "
                "\n O que você acha disso (0/97)?",
                "buttons": [
                    {"title": "Concordar", "payload": "Concordar"},
                    {"title": "Discordar", "payload": "Discordar"},
                    {"title": "Pular", "payload": "Pular"},
                ],
            },
        ]
    )

    def get_answers_to_message(
        self,
        message: InteractiveMessage | TextMessage | NotSupportedMessage,
    ) -> list:
        """Returns a list of Rasa messages to send back to WhatsApp."""
        if not message.text:
            return []
        return self.answers


@dataclass
class CloudApiMessagesParser:
    """
    Converts RasaBackend.get_answers_to_message() to WhatsApp data format.
    """

    rasa_messages: list
    recipent_phone: Text

    def get_message_type(self, message: Any):
        if message.get("buttons"):
            return "interactive"
        return "text"

    def get_interactive_type(self, message: Any):
        buttons = message.get("buttons")
        buttons: List = message.get("buttons")
        if len(buttons) > 3:
            return "list"
        return "buttons"

    def parse_buttons(self, rasa_buttons: List) -> List:
        cloud_buttons = []
        for rasa_button in rasa_buttons:
            button_title = rasa_button.get("title")
            button_payload = rasa_button.get("payload")
            if button_title and button_payload:
                cloud_button = {
                    "type": "reply",
                    "reply": {"id": button_payload, "title": button_title},
                }
                cloud_buttons.append(cloud_button)
        return cloud_buttons

    def parse_rows(self, rasa_buttons: List) -> List:
        cloud_rows = []
        for rasa_button in rasa_buttons:
            button_title = rasa_button.get("title")
            button_payload = rasa_button.get("payload")
            if button_title and button_payload:
                row = {"id": button_payload, "title": button_title, "description": ""}
                cloud_rows.append(row)
        return cloud_rows

    def parse_messages(self) -> Dict:
        parsed_messages = []
        for rasa_message in self.rasa_messages:
            message_type = self.get_message_type(rasa_message)
            payload: Dict = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": f"{self.recipent_phone}",
                "type": message_type,
            }
            if message_type == "interactive":
                interactive_type = self.get_interactive_type(rasa_message)
                if interactive_type == "buttons":
                    payload.update(
                        {
                            "interactive": {
                                "type": "button",
                                "body": {"text": rasa_message.get("text")},
                                "action": {
                                    "buttons": self.parse_buttons(
                                        rasa_message.get("buttons")
                                    )
                                },
                            },
                        }
                    )
                elif interactive_type == "list":
                    payload.update(
                        {
                            "interactive": {
                                "type": "list",
                                "header": {
                                    "type": "text",
                                    "text": "",
                                },
                                "body": {"text": rasa_message.get("text")},
                                "footer": {"text": ""},
                                "action": {
                                    "button": "opções",
                                    "sections": [
                                        {
                                            "title": "",
                                            "rows": self.parse_rows(
                                                rasa_message.get("buttons")
                                            ),
                                        }
                                    ],
                                },
                            },
                        }
                    )
            else:
                payload.update(
                    {
                        "text": {
                            "body": rasa_message.get("text"),
                            "preview_url": False,
                        },
                    }
                )
            parsed_messages.append(payload)
        return parsed_messages
