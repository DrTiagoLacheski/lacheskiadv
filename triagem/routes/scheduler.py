# triagem/routes/scheduler.py
from flask import Blueprint, jsonify, current_app
from flask_login import login_required
from triagem.Utils.utils_ticket import reschedule_overdue_todos

# Criação do blueprint para tarefas de agendamento e manutenção
scheduler_bp = Blueprint(
    'scheduler',
    __name__,
    url_prefix='/scheduler'
)

@scheduler_bp.route('/check_overdue_tasks', methods=['POST'])
@login_required
def check_overdue_tasks():
    """
    Endpoint para verificar e remarcar tarefas vencidas.
    Chamado via AJAX quando certas páginas são carregadas.
    """
    try:
        current_app.logger.info("Iniciando verificação de tarefas vencidas...")
        count = reschedule_overdue_todos()
        return jsonify({
            'success': True,
            'message': f'Verificação concluída. {count} tarefas remarcadas.',
            'tasks_rescheduled': count
        })
    except Exception as e:
        current_app.logger.error(f"Erro ao remarcar tarefas: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Erro ao remarcar tarefas: {str(e)}'
        }), 500