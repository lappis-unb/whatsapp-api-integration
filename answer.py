from dataclasses import dataclass
from typing import Any, Dict, Text
from .message import InteractiveButtonMessage, TextMessage, NotImplementedMessage

RESPONSE_MESSAGES = [
    {
        "recipient_id": "257609550778186",
        "text": "Olá, Eu sou a Duda, a assistente virtual da Plataforma Empurrando Juntas. Meu trabalho é descobrir a opinião das pessoas sobre determinados temas e para isso eu preciso da sua ajuda.  A suas opiniões serão enviadas para a nossa plataforma, conforme o nosso termo de uso https://www.ejparticipe.org/usage/.",
    },
    {
        "recipient_id": "257609550778186",
        "text": "Eu perguntei para algumas pessoas o que elas acham sobre o seguinte assunto:\nO que pode ser feito para superar os desafios da transformação digital do governo?",
    },
    {
        "recipient_id": "257609550778186",
        "text": "Vou te mandar o que me responderam e gostaria da sua opinião:",
    },
    {
        "recipient_id": "257609550778186",
        "text": "Simplicidade, simplicidade e sim+pli+ci+da+de. Ser digital não significa ser complexo. Essa é uma grande barreira a ser superada. \n O que você acha disso (0/97)?",
        "buttons": [
            {"title": "Concordar", "payload": "Concordar"},
            {"title": "Discordar", "payload": "Discordar"},
            {"title": "Pular", "payload": "Pular"},
        ],
    },
]


# Reimplement this class with your message backend.
class AnswersBackend:

    @staticmethod
    def get_answers_to_message(
        message: InteractiveButtonMessage | TextMessage | NotImplementedMessage,
    ) -> list:
        if not message.text:
            return []
        return RESPONSE_MESSAGES


@dataclass
class WhatsappMessagesParser:

    messages: list
    recipent_phone: Text

    def get_message_type(self, message: Any):
        if message.get("buttons"):
            return "interactive"
        return "text"

    def parse_messages(self):
        parsed_messages = []
        for message in self.messages:
            message_type = self.get_message_type(message)
            payload: Dict = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": f"{self.recipent_phone}",
                "type": message_type,
            }
            if message_type == "interactive":
                payload.update(
                    {
                        "interactive": {
                            "type": "button",
                            "body": {"text": message.get("text")},
                            "action": {
                                "buttons": [
                                    {
                                        "type": "reply",
                                        "reply": {"id": "1", "title": "concordar"},
                                    },
                                    {
                                        "type": "reply",
                                        "reply": {"id": "-1", "title": "descordar"},
                                    },
                                    {
                                        "type": "reply",
                                        "reply": {"id": "0", "title": "pular"},
                                    },
                                ]
                            },
                        },
                    }
                )
            else:
                payload.update(
                    {
                        "text": {"body": message.get("text"), "preview_url": False},
                    }
                )
            parsed_messages.append(payload)
        return parsed_messages
