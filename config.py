import os
from dotenv import load_dotenv

load_dotenv()
# config.py
# Arquivo para armazenar configurações e constantes.
# Separar a configuração do código principal torna o app mais seguro e fácil de manter.

# Chave secreta para proteger as sessões do usuário.
# Em um ambiente de produção, use um valor mais complexo e seguro.
SECRET_KEY = 'sua_chave_secreta_aqui'

# Dados fixos do advogado
DADOS_ADVOGADOS = {
    "TIAGO": {
        "nome": "TIAGO LACHESKI SILVEIRA DE OLIVEIRA",
        "estado_civil": "casado",
        "profissao": "advogado",
        "cpf": "017.353.012-56",
        "rg": "13.437.948-0",
        "orgao_emissor": "SESP/PR",
        "oab": ["102.510", "11.124"],  # OAB/PR e OAB/RO
    }
}

# Endereço profissional do advogado
ENDERECO_ADV = "Av. Tancredo Neves nº 2.871, Bairro Centro, Machadinho D'Oeste/RO, CEP 76.868-000"

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'uma-chave-secreta-muito-segura'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///legal_tickets.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1024MB max upload size