# routes/dashboard.py
import os
from flask import Blueprint, render_template, request
from flask_login import login_required
from models import db, Ticket 

# Caminho absoluto para garantir que encontrará os templates
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_path = os.path.join(current_dir, '../templates')

dashboard_bp = Blueprint(
    'dashboard',
    __name__,
    template_folder=templates_path  # Caminho absoluto para a pasta templates
)

#@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    search = request.args.get('search', '')


    # Definir a ordem de prioridade para status
    status_order = {
        'Em Análise': 1,
        'Em Espera': 2,
        'Arquivado': 3
    }

    # Definir a ordem de prioridade para prioridades
    priority_order = {
        'Alta': 1,
        'Média': 2,
        'Baixa': 3
    }

    # Base query com ordenação personalizada
    query = Ticket.query.order_by(
        db.case(
            status_order,
            value=Ticket.status
        ),
        db.case(
            priority_order,
            value=Ticket.priority
        ),
        Ticket.updated_at.desc()
    )

    # Aplicar filtro de busca
    if search:
        query = query.filter(
            (Ticket.title.ilike(f'%{search}%')) |
            (Ticket.case_number.ilike(f'%{search}%')) |
            (Ticket.description.ilike(f'%{search}%'))
        )

    tickets = query.all()

    return render_template('dashboard.html', tickets=tickets)
