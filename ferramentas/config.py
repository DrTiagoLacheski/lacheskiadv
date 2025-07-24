import os
from dotenv import load_dotenv

load_dotenv()
# config.py
# Arquivo para armazenar configurações e constantes.

# Chave secreta para proteger as sessões do usuário.
SECRET_KEY = os.getenv('SECRET_KEY') or 'sua_chave_secreta_aqui'

# --- DADOS DOS ADVOGADOS (ESTRUTURA MELHORADA) ---
# Agora, cada advogado tem seu próprio endereço e as OABs são um dicionário.
DADOS_ADVOGADOS = {
    "TIAGO": {
        "nome": "TIAGO LACHESKI SILVEIRA DE OLIVEIRA",
        "is_principal": True,
        "estado_civil": "casado",
        "profissao": "advogado",
        "cpf": "017.353.012-56",
        "rg": "",
        "orgao_emissor": "SESP/PR",
        "oab": {
            "pr": "102.510",
            "ro": "11.124"
        },
        "endereco_profissional": "Av. Tancredo Neves nº 2.871, Bairro Centro, Machadinho D'Oeste/RO, CEP 76.868-000"
    },
    "BRINATI": {
        "nome": "SEBASTIÃO BRINATI LOPES SIMIQUELI",
        "is_principal": False,
        "estado_civil": "solteiro",
        "profissao": "advogado",
        "cpf": "003.698.752-22",
        "rg": "",
        "orgao_emissor": "SSP/RO",
        "oab": {
            "pr": "",
            "ro": "14.719"
        },
        "endereco_profissional": "Av. Tancredo Neves nº 2.871, Bairro Centro, Machadinho D'Oeste/RO, CEP 76.868-000"
    },
"ThayRONE": {
        "nome": "THAYRONE DANIEL ROSA SANTOS",
        "is_principal": False,
        "estado_civil": "solteiro",
        "profissao": "advogado",
        "cpf": "025.586.412-47",
        "rg": "",
        "orgao_emissor": "SESP/PR",
        "oab": {
            "pr": "",
            "ro": "15231"
        },
        "endereco_profissional": ""
    }
    # Você pode adicionar mais advogados aqui, seguindo o mesmo modelo.
}

# A constante ENDERECO_ADV não é mais necessária, pois cada advogado tem o seu.

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'uma-chave-secreta-muito-segura'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///legal_tickets.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1024MB max upload size