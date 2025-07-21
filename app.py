# app.py
# Ponto de entrada principal da aplicação Flask
import os
import logging
from flask import Flask
from flask_login import LoginManager
from models import db, User
from config import Config

def create_app():
    """
    Factory de aplicação Flask que configura e inicializa todos os componentes.
    Padrão recomendado para criação flexível da aplicação.
    """
    app = Flask(__name__)

    # --- CONFIGURAÇÕES INICIAIS ---
    app.config.from_object(Config)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- CONFIGURAÇÃO DE LOGGING ---
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s : %(message)s'
    )
    app.logger.info('Iniciando configuração da aplicação Flask')

    # --- INICIALIZAÇÃO DE EXTENSÕES ---
    # Banco de dados
    db.init_app(app)

    # Autenticação (Flask-Login)
    login_manager = LoginManager()
    login_manager.init_app(app)
    # Define a view padrão para login (redireciona usuários não logados)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        """Carrega o usuário a partir do ID da sessão."""
        # AJUSTE: Usando a sintaxe moderna do SQLAlchemy para evitar warnings.
        return db.session.get(User, int(user_id))

    # --- REGISTRO DOS BLUEPRINTS (ROTAS SEPARADAS) ---
    from triagem.routes.auth import auth_bp
    from triagem.routes.dashboard import dashboard_bp
    from triagem.routes.ticket import ticket_bp
    from views import main_bp
    from ferramentas.views import ferramentas_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(ticket_bp, url_prefix='/ticket')
    app.register_blueprint(main_bp)
    app.register_blueprint(ferramentas_bp, url_prefix='/ferramentas')

    # --- CONFIGURAÇÕES FINAIS ---
    # Garante que o diretório para arquivos temporários exista
    temp_dir = os.path.join(app.root_path, 'static', 'temp')
    os.makedirs(temp_dir, exist_ok=True)

    # Cria as tabelas do banco de dados (se não existirem)
    with app.app_context():
        db.create_all()
        app.logger.info('Tabelas do banco de dados verificadas/criadas.')

    app.logger.info('Aplicação Flask configurada com sucesso')
    return app


# Cria a instância da aplicação
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)