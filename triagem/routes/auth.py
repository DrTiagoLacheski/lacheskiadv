# routes/auth.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required # <--- Adicione aqui!
from models import User
from urllib.parse import urlsplit

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Usuário ou senha inválidos', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=True)

        # --- LÓGICA DE REDIRECIONAMENTO ---
        next_page = request.args.get('next')

        # A nova verificação: permite URLs relativas (sem domínio)
        # OU URLs absolutas que apontam para o MESMO domínio do site.
        if not next_page or urlsplit(next_page).netloc != '' and urlsplit(next_page).netloc != request.host:
            next_page = url_for('main.index')

        return redirect(next_page)

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('auth.login'))