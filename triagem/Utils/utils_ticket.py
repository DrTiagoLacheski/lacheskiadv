from models import Appointment, User, TodoItem, db
from datetime import date as dt_date

def ensure_todo_appointments(ticket):
    """
    Para cada tarefa com data do ticket que não tem Appointment registrado,
    cria Appointment para admin, delegado e criador da tarefa.
    """
    todos = ticket.todos.filter(TodoItem.date.isnot(None)).all()
    for todo in todos:
        admin_user_id = ticket.author.id if ticket.author.is_admin else None
        delegado_user = None
        if ticket.delegado:
            delegado_user = User.query.filter_by(username=ticket.delegado).first()

        user_ids = set()
        if admin_user_id:
            user_ids.add(admin_user_id)
        if delegado_user:
            user_ids.add(delegado_user.id)
        user_ids.add(todo.ticket.author.id)

        for uid in user_ids:
            exists = Appointment.query.filter_by(user_id=uid, todo_id=todo.id).first()
            if not exists:
                appointment = Appointment(
                    content=f"Tarefa: {todo.content} (Caso #{ticket.id})",
                    appointment_date=todo.date,
                    appointment_time="--:--",
                    user_id=uid,
                    priority='Normal',
                    todo_id=todo.id,
                    source='triagem'
                )
                db.session.add(appointment)
    db.session.commit()


def reschedule_overdue_todos():
    """
    Para cada tarefa vencida, não concluída e não remarcada:
    - Atualiza a data da tarefa para hoje
    - Remove appointments antigos
    - Cria novos appointments com a nova data para admin, delegado e autor
    """
    today = dt_date.today()
    overdue_todos = TodoItem.query.filter(
        TodoItem.date < today,
        TodoItem.is_completed == False,
        (TodoItem.was_rescheduled == False)
    ).all()
    for todo in overdue_todos:
        ticket = todo.ticket

        # Apaga todos os appointments antigos vinculados à tarefa
        old_apps = Appointment.query.filter_by(todo_id=todo.id, appointment_date=todo.date).all()
        for app in old_apps:
            db.session.delete(app)

        # Remarca tarefa para hoje
        todo.date = today
        todo.was_rescheduled = True

        # Cria novos appointments para hoje
        admin_user_id = ticket.author.id if ticket.author.is_admin else None
        delegado_user = None
        if ticket.delegado:
            delegado_user = User.query.filter_by(username=ticket.delegado).first()

        user_ids = set()
        if admin_user_id:
            user_ids.add(admin_user_id)
        if delegado_user:
            user_ids.add(delegado_user.id)
        user_ids.add(ticket.author.id)

        for uid in user_ids:
            appointment = Appointment(
                content=f"Tarefa: {todo.content} (Caso #{ticket.id}) [Remarcada]",
                appointment_date=today,
                appointment_time="--:--",
                user_id=uid,
                priority='Normal',
                todo_id=todo.id,
                source='triagem'
            )
            db.session.add(appointment)
    if overdue_todos:
        db.session.commit()