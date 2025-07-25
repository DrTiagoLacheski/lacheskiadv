# triagem/routes/dashboard.py

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import db, Ticket

# Definição do Blueprint simplificada. O Flask encontra a pasta /templates automaticamente.
dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates')


@dashboard_bp.route('/')  # Rota vazia, que combina com o prefixo '/dashboard' em app.py
@login_required
def dashboard():
    """
    Exibe o dashboard com os tickets do usuário, permitindo busca e ordenação.
    - Administradores veem todos os tickets.
    - Usuários comuns veem apenas os seus próprios tickets.
    """
    search_term = request.args.get('search', '')

    # 1. INICIA A CONSULTA BASE
    # A consulta começa aqui e será refinada nos passos seguintes.
    query = Ticket.query

    # 2. FILTRO DE PERMISSÃO (A MUDANÇA MAIS IMPORTANTE)
    # Se o usuário logado NÃO for um administrador, aplicamos um filtro
    # para que a consulta retorne apenas os tickets que pertencem a ele.
    if not current_user.is_admin:
        query = query.filter(Ticket.user_id == current_user.id)

    # 3. FILTRO DE BUSCA
    # Se um termo de busca foi fornecido, filtramos a consulta (já filtrada por permissão).
    if search_term:
        query = query.filter(
            (Ticket.title.ilike(f'%{search_term}%')) |
            (Ticket.case_number.ilike(f'%{search_term}%')) |
            (Ticket.description.ilike(f'%{search_term}%'))
        )

    # 4. ORDENAÇÃO INTELIGENTE
    # Define a ordem de prioridade para status e prioridades.
    # O que já estava ótimo no seu código foi mantido.
    status_order = {'Em Análise': 1, 'Em Espera': 2, 'Arquivado': 3}
    priority_order = {'Alta': 1, 'Média': 2, 'Baixa': 3}

    # Aplica a ordenação em múltiplos níveis diretamente no banco de dados.
    query = query.order_by(
        db.case(status_order, value=Ticket.status),
        db.case(priority_order, value=Ticket.priority),
        Ticket.updated_at.desc()
    )

    # 5. EXECUÇÃO FINAL
    # A consulta é finalmente executada e todos os resultados são obtidos.
    tickets = query.all()

    return render_template('dashboard.html', tickets=tickets, search_term=search_term)
