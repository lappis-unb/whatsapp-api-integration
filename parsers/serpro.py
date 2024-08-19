from ..config import Config
from dataclasses import dataclass
from typing import Any, Dict, Text, List


@dataclass
class SerproApiMessagesParser:
    """
    Converts RasaBackend.get_answers_to_message() to Serpro API data format.
    """

    rasa_messages: list
    recipent_phone: Text

    def get_message_type(self, message: Any):
        if message.get("buttons"):
            buttons: List = message.get("buttons")
            if len(buttons) > 3:
                return "secoes"
            return "buttons"
        return "text"

    def parse_buttons(self, rasa_buttons: List) -> List:
        serpro_buttons = []
        for rasa_button in rasa_buttons:
            button_title = rasa_button.get("title")
            button_payload = rasa_button.get("payload")
            if button_title and button_payload:
                serpro_button = {"id": button_payload, "titulo": button_title}
                serpro_buttons.append(serpro_button)
        return serpro_buttons

    def parse_secoes(self, rasa_buttons: List) -> List:
        serpro_secoes = [{"titulo": "foo", "rows": []}]
        for rasa_button in rasa_buttons:
            button_title = rasa_button.get("title")
            button_payload = rasa_button.get("payload")
            if button_title and button_payload:
                secao = {"id": button_payload, "titulo": button_title, "descricao": ""}
                serpro_secoes[0]["rows"].append(secao)
        return serpro_secoes

    def parse_messages(self) -> Dict:
        parsed_messages = []
        for rasa_message in self.rasa_messages:
            message_type = self.get_message_type(rasa_message)
            payload: Dict = {
                "destinatario": f"{self.recipent_phone}",
                "textoBody": rasa_message.get("text"),
                "wabaId": Config.SERPRO_WABA_ID,
            }
            if message_type == "buttons":
                payload.update(
                    {"buttons": self.parse_buttons(rasa_message.get("buttons"))}
                )
            elif message_type == "secoes":
                payload.update(
                    {"secoes": self.parse_secoes(rasa_message.get("buttons"))}
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
