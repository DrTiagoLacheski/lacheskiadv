# Em triagem/routes/appointment.py

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, Appointment
from datetime import datetime

appointment_bp = Blueprint('appointment', __name__)


@appointment_bp.route('/api/appointments/<string:date_str>', methods=['GET'])
@login_required
def get_appointments(date_str):
    try:
        query_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        appointments = Appointment.query.filter_by(
            user_id=current_user.id,
            appointment_date=query_date
        ).order_by(Appointment.appointment_time).all()
        return jsonify([apt.to_dict() for apt in appointments])
    except ValueError:
        return jsonify({"error": "Formato de data inválido. Use AAAA-MM-DD"}), 400


@appointment_bp.route('/api/appointments', methods=['POST'])
@login_required
def add_appointment():
    data = request.get_json()
    if not data or not data.get('content') or not data.get('date') or not data.get('time'):
        return jsonify({"error": "Dados incompletos"}), 400

    try:
        new_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        new_appointment = Appointment(
            content=data['content'],
            appointment_date=new_date,
            appointment_time=data['time'],
            priority=data.get('priority', 'Normal'),
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
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.user_id != current_user.id:
        return jsonify({"error": "Não autorizado"}), 403

    data = request.get_json()
    appointment.content = data.get('content', appointment.content)
    appointment.appointment_time = data.get('time', appointment.appointment_time)
    appointment.priority = data.get('priority', appointment.priority)
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