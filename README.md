API Flask que permite receber webhooks do WhatsApp API Cloud.

# Quick Start

Crie um virtualenv com a versão 3.12 do Python:

    poetry env use 3.12

Habilite o virtualenv:

    poetry shell

Instale as dependências:

    poetry install

Inicialize o servidor:

    python3 -m flask --app server run -p 5006
