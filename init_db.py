# init_db.py
# Script para inicializar o banco de dados: cria todas as tabelas e o usuário admin.

# 1. Importa a FUNÇÃO 'create_app'
from app import create_app
# 2. Importa o 'db' e 'User' diretamente do arquivo de modelos
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
        admin.set_password('admin123')  # IMPORTANTE: Troque esta senha após o primeiro login!
        db.session.add(admin)
        db.session.commit()
        print("Usuário 'admin' criado com sucesso!")
    else:
        print("Usuário 'admin' já existe.")

if __name__ == '__main__':
    # 3. Cria uma instância da aplicação Flask para obter o contexto
    app = create_app()

    # 4. Usa o "contexto da aplicação" para que o script saiba qual banco de dados usar
    with app.app_context():
        initialize_database()
        create_admin_user()

    print("Inicialização do banco de dados concluída.")