# app.py
# Ponto de entrada principal da aplicação Flask
import os
import logging
from flask import Flask
from flask_login import LoginManager
from extensions.extensions import limiter
from flask_migrate import Migrate
from models import db, User
from config import Config
from core.utils import clean_temp_folder


def create_app():
    """
    Factory de aplicação Flask que configura e inicializa todos os componentes.
    Padrão recomendado para criação flexível da aplicação.
    """
    app = Flask(__name__)
    # Proteção contra DDOS
    limiter.init_app(app)
    # --- CONFIGURAÇÕES INICIAIS ---
    app.config.from_object(Config)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- CONFIGURAÇÃO DE LOGGING ---
    logging.basicConfig(
        level=logging.INFO,  # Recomendo INFO para produção para não poluir os logs
        format='%(asctime)s %(levelname)s %(name)s : %(message)s'
    )
    app.logger.info('Iniciando configuração da aplicação Flask')

    # --- INICIALIZAÇÃO DE EXTENSÕES ---
    db.init_app(app)
    # ---- INICIALIZAÇÃO DA MIGRAÇÃO ----
    migrate = Migrate(app, db)   # <--- MIGRATE INICIALIZADO

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        """Carrega o usuário a partir do ID da sessão."""
        return db.session.get(User, int(user_id))

    # --- REGISTRO DOS BLUEPRINTS (ROTAS SEPARADAS) ---
    from triagem.routes.auth import auth_bp
    from triagem.routes.dashboard import dashboard_bp
    from triagem.routes.ticket import ticket_bp
    from views import main_bp
    from ferramentas.views import ferramentas_bp
    from routes.appointment import appointment_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(ticket_bp, url_prefix='/ticket')
    app.register_blueprint(main_bp)
    app.register_blueprint(ferramentas_bp, url_prefix='/ferramentas')
    app.register_blueprint(appointment_bp)

    # --- CONFIGURAÇÕES FINAIS ---
    with app.app_context():
        # ALTERAÇÃO: A função de limpeza é chamada aqui, antes de criar as tabelas.
        clean_temp_folder(app)

        # Removido upgrade() automático!
        app.logger.info('Tabelas do banco de dados NÃO serão atualizadas automaticamente.')

    app.logger.info('Aplicação Flask configurada com sucesso')
    return app


# Cria a instância da aplicação
app = create_app()

if __name__ == '__main__':
    # Em modo de debug, o servidor reinicia a cada alteração, executando a limpeza.
    # Em produção, a limpeza rodará apenas uma vez na inicialização.
    app.run(host='0.0.0.0', port=5001, debug=True)