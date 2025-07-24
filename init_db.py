# init_db.py
# Script para inicializar o banco de dados: cria todas as tabelas e os usuários.

from app import create_app
from models import db, User

def initialize_database():
    """
    Cria todas as tabelas do banco de dados com base nos modelos.
    """
    print("Criando tabelas do banco de dados...")
    db.create_all()
    print("Tabelas criadas com sucesso.")

def create_admin_user():
    """
    Verifica se o usuário admin existe e, se não, o cria.
    """
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@escritorio.com',
            is_admin=True
        )
        admin.set_password('102030')
        db.session.add(admin)
        db.session.commit()
        print("Usuário 'admin' criado com sucesso!")
    else:
        print("Usuário 'admin' já existe.")

def create_user2_user():
    """
    Verifica se o usuário user2 existe e, se não, o cria.
    """
    user = User.query.filter_by(username='user2').first()
    if not user:
        user = User(
            username='user2',
            email='user2@escritorio.com',
            is_admin=False # Não é administrador
        )
        user.set_password('user')
        db.session.add(user)
        db.session.commit()
        print("Usuário 'user2' criado com sucesso!")
    else:
        print("Usuário 'user2' já existe.")

def create_user_user():
    """
    Verifica se o usuário user existe e, se não, o cria.
    """
    user = User.query.filter_by(username='user').first()
    if not user:
        user = User(
            username='user',
            email='user@escritorio.com',
            is_admin=False # Não é administrador
        )
        user.set_password('user')
        db.session.add(user)
        db.session.commit()
        print("Usuário 'user' criado com sucesso!")
    else:
        print("Usuário 'user' já existe.")


if __name__ == '__main__':
    # Cria uma instância da aplicação Flask para obter o contexto
    app = create_app()

    # Usa o "contexto da aplicação" para que o script saiba qual banco de dados usar
    with app.app_context():
        initialize_database()
        create_admin_user()
        # Chama as novas funções para criar os outros usuários
        create_user2_user()
        create_user_user()

    print("Inicialização do banco de dados concluída.")
