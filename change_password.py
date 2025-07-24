# change_password.py
# Script para alterar a senha de um usuário específico sem interação.

from app import create_app
from models import db, User

# Cria uma instância da aplicação Flask para obter o contexto do banco de dados
app = create_app()

# Usa o "contexto da aplicação" para que o script saiba qual banco de dados usar
with app.app_context():
    # --- CONFIGURAÇÃO ---
    # Defina aqui o usuário e a nova senha que deseja aplicar.
    username_to_change = 'admin'
    new_password = '102030'  # <-- IMPORTANTE: Altere para a senha desejada

    # --- LÓGICA DE ALTERAÇÃO ---
    # Encontra o usuário no banco de dados
    user = User.query.filter_by(username=username_to_change).first()

    if user:
        print(f"Alterando senha para o usuário: '{user.username}'...")

        # Define a nova senha (a função set_password faz a criptografia)
        user.set_password(new_password)

        # Salva a alteração no banco de dados
        db.session.commit()

        print(f"Senha do usuário '{user.username}' alterada com sucesso!")
    else:
        print(f"Erro: Usuário '{username_to_change}' não encontrado no banco de dados.")
