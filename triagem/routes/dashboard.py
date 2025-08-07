# triagem/routes/dashboard.py

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import db, Ticket

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates')

@dashboard_bp.route('/')  # Rota vazia, que combina com o prefixo '/dashboard' em app.py
@login_required
def dashboard():
    """
    Exibe o dashboard com os tickets do usuário, permitindo busca e ordenação.
    - Administradores veem todos os tickets.
    - Usuários comuns veem apenas os seus próprios tickets E os tickets nos quais são delegados.
    """
    search_term = request.args.get('search', '')

    # 1. INICIA A CONSULTA BASE
    query = Ticket.query

    # 2. FILTRO DE PERMISSÃO
    # Admin vê tudo; usuário comum vê seus tickets E os onde é delegado
    if not current_user.is_admin:
        query = query.filter(
            (Ticket.user_id == current_user.id) |
            (Ticket.delegado_id == current_user.id)
        )

    # 3. FILTRO DE BUSCA
    if search_term:
        query = query.filter(
            (Ticket.title.ilike(f'%{search_term}%')) |
            (Ticket.case_number.ilike(f'%{search_term}%')) |
            (Ticket.description.ilike(f'%{search_term}%'))
        )

    # 4. ORDENAÇÃO INTELIGENTE
    status_order = {'Em Análise': 1, 'Em Espera': 2, 'Arquivado': 3}
    priority_order = {'Alta': 1, 'Média': 2, 'Baixa': 3}

    query = query.order_by(
        db.case(status_order, value=Ticket.status),
        db.case(priority_order, value=Ticket.priority),
        Ticket.updated_at.desc()
    )

    tickets = query.all()

    return render_template('dashboard.html', tickets=tickets, search_term=search_term)