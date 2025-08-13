from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Appointment
from datetime import datetime
from sqlalchemy import extract, or_

appointment_bp = Blueprint('appointment', __name__)

# Valores permitidos para prioridade
VALID_PRIORITIES = {'Normal', 'Importante', 'Urgente'}


@appointment_bp.route('/api/appointments/<string:date_str>', methods=['GET'])
@login_required
def get_appointments(date_str):
    """
    Busca compromissos para uma data específica, incluindo os recorrentes
    que já iniciaram.
    """
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        day_of_month = query_date.day

        # A consulta agora busca compromissos que são:
        # 1. Não recorrentes e na data exata.
        # OU
        # 2. Recorrentes, no mesmo dia do mês, E cuja data de início já passou.
        appointments = Appointment.query.filter(
            Appointment.user_id == current_user.id,
            or_(
                Appointment.appointment_date == query_date,
                (
                    (Appointment.is_recurring == True) &
                    (extract('day', Appointment.appointment_date) == day_of_month) &
                    # ALTERADO: Garante que a recorrência só apareça a partir da data de criação
                    (Appointment.appointment_date <= query_date)
                )
            )
        ).order_by(Appointment.appointment_time).all()

        return jsonify([apt.to_dict() for apt in appointments])
    except ValueError:
        return jsonify({"error": "Formato de data inválido. Use AAAA-MM-DD"}), 400


@appointment_bp.route('/api/appointments', methods=['POST'])
@login_required
def add_appointment():
    """
    Adiciona um novo compromisso, salvando seu estado de recorrência.
    """
    data = request.get_json()
    if not data or not data.get('content') or not data.get('date') or not data.get('time'):
        return jsonify({"error": "Dados incompletos"}), 400

    priority = data.get('priority', 'Normal')
    if priority not in VALID_PRIORITIES:
        priority = 'Normal'

    is_recurring = data.get('recurring', False)

    try:
        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        new_appointment = Appointment(
            content=data['content'],
            appointment_date=new_date,
            appointment_time=data['time'],
            priority=priority,
            is_recurring=is_recurring,
            user_id=current_user.id
        )
        db.session.add(new_appointment)
        db.session.commit()
        return jsonify(new_appointment.to_dict()), 201
    except ValueError:
        return jsonify({"error": "Formato de dados inválido."}), 400


@appointment_bp.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
@login_required
def update_appointment(appointment_id):
    """
    Atualiza um compromisso existente, incluindo seu estado de recorrência.
    """
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.user_id != current_user.id:
        return jsonify({"error": "Não autorizado"}), 403

    data = request.get_json()

    if 'priority' in data:
        appointment.priority = data['priority'] if data['priority'] in VALID_PRIORITIES else 'Normal'

    if 'recurring' in data:
        appointment.is_recurring = data.get('recurring', appointment.is_recurring)

    appointment.content = data.get('content', appointment.content)
    appointment.appointment_time = data.get('time', appointment.appointment_time)

    db.session.commit()
    return jsonify(appointment.to_dict())


@appointment_bp.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
@login_required
def delete_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.user_id != current_user.id:
        return jsonify({"error": "Não autorizado"}), 403

    db.session.delete(appointment)
    db.session.commit()
    return jsonify({"success": True})


@appointment_bp.route('/api/appointments/urgent-days/<int:year>/<int:month>', methods=['GET'])
@login_required
def get_urgent_days(year, month):
    """
    Encontra todos os dias com compromissos 'Urgente', incluindo os recorrentes
    que já iniciaram até o mês visualizado.
    """
    # Helper para criar a data do fim do mês visualizado
    next_m = month + 1
    next_y = year
    if next_m > 12:
        next_m = 1
        next_y += 1
    first_day_of_next_month = datetime(next_y, next_m, 1).date()

    # 1. Dias de compromissos urgentes NÃO recorrentes no mês/ano específico
    specific_urgent_days_query = db.session.query(
        extract('day', Appointment.appointment_date)
    ).filter(
        extract('year', Appointment.appointment_date) == year,
        extract('month', Appointment.appointment_date) == month,
        Appointment.user_id == current_user.id,
        Appointment.priority == 'Urgente',
        Appointment.is_recurring == False
    ).distinct()

    # 2. Dias de compromissos urgentes que SÃO recorrentes e já iniciaram
    recurring_urgent_days_query = db.session.query(
        extract('day', Appointment.appointment_date)
    ).filter(
        Appointment.user_id == current_user.id,
        Appointment.priority == 'Urgente',
        Appointment.is_recurring == True,
        # ALTERADO: Apenas considera recorrências que já iniciaram
        Appointment.appointment_date < first_day_of_next_month
    ).distinct()

    specific_days = {date[0] for date in specific_urgent_days_query.all()}
    recurring_days = {date[0] for date in recurring_urgent_days_query.all()}

    all_urgent_days = sorted(list(specific_days.union(recurring_days)))
    return jsonify(all_urgent_days)


@appointment_bp.route('/api/appointments/important-days/<int:year>/<int:month>', methods=['GET'])
@login_required
def get_important_days(year, month):
    """
    Encontra todos os dias com compromissos 'Importante', incluindo os recorrentes
    que já iniciaram até o mês visualizado.
    """
    # Helper para criar a data do fim do mês visualizado
    next_m = month + 1
    next_y = year
    if next_m > 12:
        next_m = 1
        next_y += 1
    first_day_of_next_month = datetime(next_y, next_m, 1).date()

    # 1. Dias de compromissos importantes NÃO recorrentes no mês/ano específico
    specific_important_days_query = db.session.query(
        extract('day', Appointment.appointment_date)
    ).filter(
        extract('year', Appointment.appointment_date) == year,
        extract('month', Appointment.appointment_date) == month,
        Appointment.user_id == current_user.id,
        Appointment.priority == 'Importante',
        Appointment.is_recurring == False
    ).distinct()

    # 2. Dias de compromissos importantes que SÃO recorrentes e já iniciaram
    recurring_important_days_query = db.session.query(
        extract('day', Appointment.appointment_date)
    ).filter(
        Appointment.user_id == current_user.id,
        Appointment.priority == 'Importante',
        Appointment.is_recurring == True,
        Appointment.appointment_date < first_day_of_next_month
    ).distinct()

    specific_days = {date[0] for date in specific_important_days_query.all()}
    recurring_days = {date[0] for date in recurring_important_days_query.all()}

    all_important_days = sorted(list(specific_days.union(recurring_days)))
    return jsonify(all_important_days)

# ALTERADO: A rota agora retorna um dicionário com a prioridade de cada dia recorrente
@appointment_bp.route('/api/appointments/recurring-days/<int:year>/<int:month>', methods=['GET'])
@login_required
def get_recurring_days(year, month):
    """
    Encontra todos os dias com compromissos recorrentes e retorna um dicionário
    mapeando o dia para sua prioridade mais alta.
    Ex: { "5": "Urgente", "15": "Normal" }
    """
    # Helper para criar a data do fim do mês visualizado
    next_m = month + 1
    next_y = year
    if next_m > 12:
        next_m = 1
        next_y += 1
    first_day_of_next_month = datetime(next_y, next_m, 1).date()

    # A consulta agora busca o dia e a prioridade
    recurring_appointments_query = db.session.query(
        extract('day', Appointment.appointment_date),
        Appointment.priority
    ).filter(
        Appointment.user_id == current_user.id,
        Appointment.is_recurring == True,
        Appointment.appointment_date < first_day_of_next_month
    ).all()

    # Lógica para determinar a prioridade mais alta para cada dia
    highest_priority_by_day = {}
    priority_order = {'Normal': 0, 'Importante': 1, 'Urgente': 2}

    for day, priority in recurring_appointments_query:
        # Se o dia ainda não está no dicionário ou a nova prioridade é maior, atualiza
        if day not in highest_priority_by_day or priority_order[priority] > priority_order[highest_priority_by_day[day]]:
            highest_priority_by_day[day] = priority

    return jsonify(highest_priority_by_day)

# ... (resto do arquivo, incluindo get_active_days) ...

@appointment_bp.route('/api/appointments/active-days/<int:year>/<int:month>', methods=['GET'])
@login_required
def get_active_days(year, month):
    """
    Encontra todos os dias com QUALQUER compromisso, incluindo os recorrentes
    que já iniciaram até o mês visualizado.
    """
    # Helper para criar a data do fim do mês visualizado
    next_m = month + 1
    next_y = year
    if next_m > 12:
        next_m = 1
        next_y += 1
    first_day_of_next_month = datetime(next_y, next_m, 1).date()

    # 1. Dias com compromissos NÃO recorrentes no mês/ano específico
    specific_days_query = db.session.query(
        extract('day', Appointment.appointment_date)
    ).filter(
        extract('year', Appointment.appointment_date) == year,
        extract('month', Appointment.appointment_date) == month,
        Appointment.user_id == current_user.id,
        Appointment.is_recurring == False
    ).distinct()

    # 2. Dias de TODOS os compromissos que SÃO recorrentes e já iniciaram
    recurring_days_query = db.session.query(
        extract('day', Appointment.appointment_date)
    ).filter(
        Appointment.user_id == current_user.id,
        Appointment.is_recurring == True,
        # ALTERADO: Apenas considera recorrências que já iniciaram
        Appointment.appointment_date < first_day_of_next_month
    ).distinct()

    specific_days = {date[0] for date in specific_days_query.all()}
    recurring_days = {date[0] for date in recurring_days_query.all()}

    all_active_days = sorted(list(specific_days.union(recurring_days)))
    return jsonify(all_active_days)

@appointment_bp.route('/api/appointments/delete-all/<string:date_str>', methods=['DELETE'])
@login_required
def delete_all_on_date(date_str):
    """
    Exclui todos os compromissos NÃO recorrentes de um usuário para uma data específica.
    Compromissos recorrentes não são afetados para não excluir a regra principal.
    """
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Deleta os compromissos que correspondem aos critérios
        num_deleted = Appointment.query.filter(
            Appointment.user_id == current_user.id,
            Appointment.appointment_date == query_date,
            Appointment.is_recurring == False
        ).delete(synchronize_session=False)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"{num_deleted} compromissos foram excluídos."
        })

    except ValueError:
        return jsonify({"error": "Formato de data inválido. Use AAAA-MM-DD"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erro interno ao processar a exclusão."}), 500


@appointment_bp.route('/api/appointments/completed-days/<int:year>/<int:month>', methods=['GET'])
@login_required
def get_completed_days(year, month):
    """
    Encontra todos os dias com compromissos marcados como concluídos.
    """
    # Configurar datas do período
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()

    # Buscar compromissos com tarefas concluídas
    from models import TodoItem
    completed_query = db.session.query(
        extract('day', Appointment.appointment_date)
    ).filter(
        Appointment.user_id == current_user.id,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date < end_date,
        Appointment.todo_id.isnot(None)
    ).join(TodoItem).filter(
        TodoItem.is_completed == True
    ).distinct()

    completed_days = [int(day[0]) for day in completed_query.all()]
    return jsonify(sorted(completed_days))


@appointment_bp.route('/api/appointments/rescheduled-days/<int:year>/<int:month>', methods=['GET'])
@login_required
def get_rescheduled_days(year, month):
    """
    Encontra todos os dias com compromissos remarcados.
    """
    # Configurar datas do período
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()

    # Buscar compromissos remarcados
    rescheduled_query = db.session.query(
        extract('day', Appointment.appointment_date)
    ).filter(
        Appointment.user_id == current_user.id,
        Appointment.appointment_date >= start_date,
        Appointment.appointment_date < end_date,
        or_(
            Appointment.data_original.isnot(None),
            Appointment.remarcada_count > 0
        )
    ).distinct()

    rescheduled_days = [int(day[0]) for day in rescheduled_query.all()]
    return jsonify(sorted(rescheduled_days))


# Adicione este endpoint ao arquivo appointment.py

@appointment_bp.route('/api/appointments/<int:appointment_id>/toggle-completion', methods=['PUT'])
@login_required
def toggle_appointment_completion(appointment_id):
    """
    Alterna o estado de conclusão de um compromisso (apenas para triagem).
    """
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.user_id != current_user.id:
        return jsonify({"error": "Não autorizado"}), 403

    data = request.get_json()
    is_completed = data.get('is_completed', False)

    # Atualizar o estado de conclusão
    appointment.is_completed = is_completed

    db.session.commit()
    return jsonify(appointment.to_dict())