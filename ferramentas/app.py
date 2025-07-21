# app.py
# Ponto de entrada da aplicação.
# Este arquivo inicializa o app Flask e registra os blueprints (conjuntos de rotas).

import os
import logging
from flask import Flask

def create_app():
    """
    Cria e configura uma instância da aplicação Flask.
    Este é um padrão conhecido como 'Application Factory',
    que ajuda a criar múltiplas instâncias do app para testes ou configurações diferentes.
    """
    app = Flask(__name__)

    # --- CONFIGURAÇÃO DE LOGGING MELHORADA ---
    # Configura o logging para ser mais detalhado, o que ajuda na depuração.
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(name)s : %(message)s')

    # Carrega a configuração do arquivo config.py
    # É importante que o arquivo config.py esteja na mesma pasta.
    app.config.from_pyfile('config.py')

    # Importa e registra os blueprints
    # Blueprints ajudam a organizar as rotas em módulos separados.
    # Ao registrar 'ferramentas_bp' e 'auth_bp', todas as rotas dentro deles
    # (incluindo as novas para contratos) tornam-se ativas.
    from auth import auth_bp
    from views import ferramentas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(ferramentas_bp)

    # Garante que o diretório para arquivos temporários exista
    # Usa o caminho da aplicação para criar a pasta 'static/temp' de forma segura.
    temp_dir = os.path.join(app.root_path, 'static', 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    
    app.logger.info('Aplicação Flask criada e configurada com sucesso.')

    return app

# Cria a instância da aplicação para ser executada
app = create_app()

if __name__ == '__main__':
    # Inicia o servidor de desenvolvimento do Flask
    # O modo debug recarrega o servidor automaticamente a cada mudança no código.
    app.run(debug=True)
