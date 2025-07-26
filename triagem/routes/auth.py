# triagem/routes/auth.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from extensions.extensions import limiter
from models import db, User, Advogado
from urllib.parse import urlsplit
import re

auth_bp = Blueprint('auth', __name__, template_folder='../../../templates')

def senha_forte(password):
    # Pelo menos 8 caracteres, uma maiúscula, uma minúscula, um número e um caractere especial
    if (len(password) < 8 or
        not re.search(r'[A-Z]', password) or
        not re.search(r'[a-z]', password) or
        not re.search(r'\d', password) or
        not re.search(r'[!@#$%^&*(),.?":{}|<>]', password)):
        return False
    return True

# Rota de login (sem alterações)
@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Usuário ou senha inválidos', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=True)

        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '' and urlsplit(next_page).netloc != request.host:
            next_page = url_for('main.index')

        return redirect(next_page)

    return render_template('login.html', title='Entrar')


# --- NOVO CÓDIGO: ROTA DE CADASTRO ---
@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])
def register():

    """Lida com o cadastro de novos usuários."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        # Validações
        if not senha_forte(password):
            flash('A senha deve ter pelo menos 8 caracteres, incluindo maiúscula, minúscula, número e caractere especial.', 'danger')
            return redirect(url_for('auth.register'))

        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Este nome de usuário já está em uso.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Este e-mail já foi cadastrado.', 'danger')
            return redirect(url_for('auth.register'))

        # Cria o novo usuário
        new_user = User(username=username, email=email, is_admin=False)
        new_user.set_password(password)

        # Cria um perfil de advogado padrão para o novo usuário
        # Isso é crucial para que as outras ferramentas funcionem
        default_advogado = Advogado(
            nome=username.upper(),
            estado_civil="não informado",
            cpf=f"000.000.000-00-{username}", # CPF único para evitar conflitos
            endereco_profissional="Endereço não informado",
            is_principal=True # É o principal para ESTA conta
        )
        new_user.advogados.append(default_advogado)

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)

        flash('Conta criada com sucesso! Por favor, faça o login.', 'success')
        return redirect(url_for('main.index'))

    return render_template('register.html', title='Criar Conta')


# Rota de logout (sem alterações)
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))