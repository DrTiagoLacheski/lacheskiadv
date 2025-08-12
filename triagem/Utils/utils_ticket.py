# triagem/Utils/utils_ticket.py
from datetime import datetime, timedelta, date as dt_date
from models import db, TodoItem, Appointment, User, Ticket
from flask import current_app


def ensure_todo_appointments(ticket):
    """
    Garante que todas as tarefas com data marcada tenham compromissos correspondentes
    para todos os usuários relevantes (admin, autor e delegado).
    """
    todos_with_date = ticket.todos.filter(TodoItem.date.isnot(None)).all()

    for todo in todos_with_date:
        # Coletar IDs de usuários que devem ter este compromisso
        user_ids = set()
        # Admin do ticket
        admin_user_id = ticket.author.id if ticket.author.is_admin else None
        if admin_user_id:
            user_ids.add(admin_user_id)
        # Delegado (se existir)
        if ticket.delegado_id:
            user_ids.add(ticket.delegado_id)
        # Autor (se não for admin)
        if not ticket.author.is_admin:
            user_ids.add(ticket.author.id)

        # Verificar e criar compromissos para cada usuário
        for user_id in user_ids:
            appointment = Appointment.query.filter_by(
                user_id=user_id,
                todo_id=todo.id
            ).first()

            if not appointment:
                new_appointment = Appointment(
                    content=f"Tarefa: {todo.content} (Caso #{ticket.id})",
                    appointment_date=todo.date,
                    appointment_time=todo.time if todo.time else "--:--",
                    user_id=user_id,
                    priority=todo.priority,
                    todo_id=todo.id,
                    source='triagem'
                )
                db.session.add(new_appointment)

    db.session.commit()
    current_app.logger.info(f"Compromissos sincronizados para o ticket {ticket.id}")


def reschedule_overdue_todos():
    """
    Versão aprimorada que garante a remarcação de TODAS as tarefas vencidas,
    incluindo tarefas antigas, sempre que a página é atualizada.
    Retorna o número de tarefas remarcadas.
    """
    today = dt_date.today()

    # Busca TODAS as tarefas vencidas não concluídas, incluindo as antigas
    overdue_todos = TodoItem.query.filter(
        (TodoItem.date < today) &
        (TodoItem.is_completed == False)
    ).all()

    remarcadas_count = 0
    for todo in overdue_todos:
        # Preservar a data original na primeira remarcação
        if hasattr(todo, 'data_original') and not todo.data_original:
            todo.data_original = todo.date

        # Calcular próximo dia útil
        next_date = get_next_business_day(today)

        # Limpar marcações anteriores
        clean_content = limpar_marcacoes_remarcacao(todo.content)

        # Incrementar contador de remarcações
        if hasattr(todo, 'remarcada_count'):
            todo.remarcada_count = (todo.remarcada_count or 0) + 1

            # Formatar conteúdo com contador
            if todo.remarcada_count > 1:
                todo.content = f"[Remarcada {todo.remarcada_count}x] {clean_content}"
            else:
                todo.content = f"[Remarcada] {clean_content}"
        else:
            # Comportamento de fallback para compatibilidade
            todo.content = f"[Remarcada] {clean_content}"

        # Atualizar a data e marcar como remarcada
        old_date = todo.date
        todo.date = next_date
        todo.was_rescheduled = True

        # Atualizar compromissos relacionados
        update_related_appointments(todo, old_date, next_date)
        remarcadas_count += 1

    if remarcadas_count > 0:
        db.session.commit()
        current_app.logger.info(f"Total de {remarcadas_count} tarefas remarcadas")

    return remarcadas_count


def limpar_marcacoes_remarcacao(content):
    """
    Remove todas as marcações de remarcação anteriores do conteúdo
    para evitar duplicações.
    """
    # Remover marcações do tipo [Remarcada]
    if "[Remarcada]" in content:
        content = content.replace("[Remarcada] ", "")

    # Remover marcações do tipo [Remarcada 2x], [Remarcada 3x], etc
    import re
    content = re.sub(r'\[Remarcada \d+x\] ', '', content)

    return content


def get_next_business_day(from_date):
    """
    Retorna o próximo dia útil (ignorando finais de semana).
    """
    next_day = from_date + timedelta(days=1)
    # Se cair no fim de semana, avança para segunda-feira
    while next_day.weekday() >= 5:  # 5=Sábado, 6=Domingo
        next_day += timedelta(days=1)
    return next_day


def update_related_appointments(todo, old_date, new_date):
    """
    Atualiza os compromissos associados a uma tarefa remarcada.
    Versão segura que verifica a existência dos campos.
    """
    related_appointments = Appointment.query.filter_by(todo_id=todo.id).all()

    for appointment in related_appointments:
        # Verificação de segurança para campos
        has_data_original = hasattr(appointment, 'data_original')
        has_remarcada_count = hasattr(appointment, 'remarcada_count')

        # Guardar a data original na primeira remarcação (com segurança)
        if has_data_original and not appointment.data_original:
            appointment.data_original = old_date

        # Limpar marcações anteriores no conteúdo do compromisso
        clean_content = limpar_marcacoes_remarcacao(appointment.content)

        # Incrementar contador de remarcações com verificação de segurança
        if has_remarcada_count:
            appointment.remarcada_count = (appointment.remarcada_count or 0) + 1
            remarcada_count = appointment.remarcada_count
        else:
            # Estimativa do contador baseado no conteúdo
            remarcada_count = 1
            if "[Remarcada]" in appointment.content:
                remarcada_count = 2
            # Verifica se há um formato como [Remarcada 3x]
            import re
            match = re.search(r'\[Remarcada (\d+)x\]', appointment.content)
            if match:
                try:
                    remarcada_count = int(match.group(1)) + 1
                except:
                    remarcada_count = 2

        # Atualizar conteúdo com nova marcação
        if remarcada_count > 1:
            appointment.content = f"[Remarcada {remarcada_count}x] {clean_content}"
        else:
            appointment.content = f"[Remarcada] {clean_content}"

        # Atualizar data do compromisso
        appointment.appointment_date = new_date