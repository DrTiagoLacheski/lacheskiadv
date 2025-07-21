# auth.py
# Gerencia a autenticação de usuários lendo credenciais de um arquivo JSON.
# Usa um Blueprint para agrupar as rotas de autenticação.

import json
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from functools import wraps

# Cria um Blueprint chamado 'auth'. Blueprints são como mini-aplicações.
auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """
    Decorator para garantir que o usuário esteja logado antes de acessar uma página.
    Se o usuário não estiver logado, ele é redirecionado para a página de login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def _carregar_usuarios():
    """
    Carrega os dados dos usuários a partir do arquivo usuarios.json.
    Retorna um dicionário com os usuários.
    """
    # Constrói um caminho absoluto para o arquivo JSON para garantir que ele seja encontrado.
    # Isso torna a aplicação mais robusta, independentemente de onde o script é executado.
    file_path = os.path.join(current_app.root_path, 'usuarios.json')
    try:
        # Abre o arquivo JSON que contém os usuários e senhas
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Em caso de erro (arquivo não encontrado ou JSON inválido),
        # retorna um dicionário vazio para evitar que a aplicação quebre.
        # A mensagem de aviso agora mostra o caminho completo, ajudando a depurar.
        print(f"AVISO: O arquivo em '{file_path}' não foi encontrado ou está mal formatado.")
        return {}

def _validar_credenciais(username, password):
    """
    Função auxiliar para validar as credenciais do usuário
    comparando com os dados do arquivo JSON.
    """
    usuarios_validos = _carregar_usuarios()
    
    # Garante que usuário e senha não são nulos antes de verificar
    if not username or not password:
        return False
    
    # Verifica se o usuário existe no dicionário e se a senha corresponde
    return usuarios_validos.get(username) == password

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Rota para a página de login, compatível com JSON e Form data."""
    if request.method == 'POST':
        username = None
        password = None

        # Verifica se os dados foram enviados como JSON
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        # Caso contrário, trata como um envio de formulário tradicional
        else:
            username = request.form.get('username')
            password = request.form.get('password')

        # Valida as credenciais usando a função que lê o JSON
        if _validar_credenciais(username, password):
            session['logged_in'] = True
            session['username'] = username
            
            next_page = request.args.get('next') or url_for('main.index')

            if request.is_json:
                return jsonify({'success': True, 'redirect_url': next_page})
            
            return redirect(next_page)
        else:
            # Se as credenciais são inválidas, retorna um erro
            if request.is_json:
                return jsonify({'success': False, 'error': 'Credenciais inválidas'}), 401
            
            return render_template('login.html', error="Credenciais inválidas")

    # Para requisições GET, apenas exibe a página de login
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Rota para fazer logout."""
    session.clear()
    return redirect(url_for('auth.login'))
