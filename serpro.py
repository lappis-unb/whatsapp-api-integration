from .config import Config
from dataclasses import dataclass
from typing import Any, Dict, Text, List


@dataclass
class SerproApiMessagesParser:
    """
    Converts RasaBackend.get_answers_to_message() to WhatsApp data format.
    """

    rasa_messages: list
    recipent_phone: Text

    def get_message_type(self, message: Any):
        if message.get("buttons"):
            return "interactive"
        return "text"

    def parse_buttons(self, rasa_buttons: List) -> List:
        wpp_buttons = []
        wpp_options = {
            "Concordar": {"id": "1", "titulo": "Concordar"},
            "Discordar": {"id": "-1", "titulo": "Discordar"},
            "Pular": {"id": "0", "titulo": "Pular"},
            "Sim": {"id": "sim", "titulo": "sim"},
            "Não": {"id": "não", "titulo": "não"},
            "Confirmar": {
                "id": "check_participant_authentication",
                "titulo": "Confirmar",
            },
            "Encerrar": {
                "id": "end_participant_conversation",
                "titulo": "Encerrar",
            },
        }
        for rasa_button in rasa_buttons:
            rasa_button_title = rasa_button.get("title")
            if rasa_button_title:
                reply_options = wpp_options.get(rasa_button_title)
                wpp_buttons.append(reply_options)
        return wpp_buttons

    def parse_messages(self) -> Dict:
        parsed_messages = []
        for rasa_message in self.rasa_messages:
            message_type = self.get_message_type(rasa_message)
            payload: Dict = {
                "destinatario": f"{self.recipent_phone}",
                "textoBody": rasa_message.get("text"),
                "wabaId": Config.SERPRO_WABA_ID,
            }
            if message_type == "interactive":
                payload.update(
                    {"buttons": self.parse_buttons(rasa_message.get("buttons"))}
                )
            else:
                payload.update(
                    {
                        "body": rasa_message.get("text"),
                        "preview_url": False,
                    }
                )
            parsed_messages.append(payload)
        return parsed_messages
