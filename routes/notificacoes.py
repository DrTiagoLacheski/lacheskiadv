from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from models import Appointment
from datetime import datetime

notificacoes_bp = Blueprint('notificacoes', __name__, url_prefix='/api/notificacoes')

@notificacoes_bp.route('/compromissos_proximos')
@login_required
def compromissos_proximos():
    now = datetime.now()
    today = now.date()
    appointments = Appointment.query.filter_by(
        user_id=current_user.id,
        appointment_date=today
    ).all()
    upcoming = []
    for a in appointments:
        if a.appointment_time and a.appointment_time != "--:--":
            try:
                appt_dt = datetime.combine(today, datetime.strptime(a.appointment_time, "%H:%M").time())
                # Está nos próximos 10 minutos?
                delta = (appt_dt - now).total_seconds()
                if 0 <= delta <= 600:
                    upcoming.append(a.to_dict())
            except Exception:
                pass
    return jsonify(upcoming)