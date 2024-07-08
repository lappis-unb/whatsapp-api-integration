import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SERPRO_OAUTH2_TOKEN_URL = "https://api.whatsapp.serpro.gov.br/oauth2/token"
    RASA_WEBHOOK_URL = (
        "https://metawebhooks.pencillabs.tec.br/webhooks/whatsapp/webhook"
    )
    SERPRO_CLIENT_URL = f'https://api.whatsapp.serpro.gov.br/client/{os.getenv("SERPRO_CLIENT_ID", "")}/v2'
    SERPRO_WEBHOOK_REGISTRATION_URL = f"{SERPRO_CLIENT_URL}/webhook"
    SERPRO_WABA_ID = os.getenv("SERPRO_WABA_ID", "")
    SERPRO_TEXT_MESSAGES_URL = f"{SERPRO_CLIENT_URL}/requisicao/mensagem/texto"
    SERPRO_BUTTONS_MESSAGES_URL = (
        f"{SERPRO_CLIENT_URL}/requisicao/mensagem/interativa-botoes"
    )
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = os.getenv("REDIS_PORT", "6379")
