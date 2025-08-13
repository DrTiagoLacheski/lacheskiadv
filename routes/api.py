# Certifique-se de que este arquivo seja importado na sua aplicação principal

from flask import Blueprint, request, jsonify, abort
from flask_login import login_required, current_user
from models import db, Appointment

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/appointments/<int:appointment_id>/toggle-completion', methods=['PUT'])
@login_required
def toggle_appointment_completion(appointment_id):
    """
    Alterna o estado de conclusão de um compromisso.
    """

    if not current_user.is_admin:
        abort(403)

    try:
        appointment = Appointment.query.get_or_404(appointment_id)

        # Verificar permissão - usuário deve ser o dono do compromisso
        if appointment.user_id != current_user.id:
            return jsonify({"error": "Não autorizado"}), 403

        data = request.get_json()
        if data is None:
            return jsonify({"error": "Dados JSON inválidos"}), 400

        is_completed = data.get('is_completed', False)

        # Atualizar o estado de conclusão
        appointment.is_completed = is_completed

        db.session.commit()
        return jsonify(appointment.to_dict())

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao alternar conclusão do compromisso {appointment_id}: {str(e)}")
        return jsonify({"error": f"Erro ao processar: {str(e)}"}), 500


@api_bp.route('/diagnostic/appointment/<int:appointment_id>')
@login_required
def appointment_diagnostic(appointment_id):
    """Diagnóstico para problemas com compromissos"""
    if not current_user.is_admin:
        abort(403)

    try:
        appointment = Appointment.query.get_or_404(appointment_id)

        # Informações sobre o compromisso
        result = {
            'appointment': {
                'id': appointment.id,
                'user_id': appointment.user_id,
                'content': appointment.content,
                'date': str(appointment.appointment_date),
                'is_completed': appointment.is_completed,
                'has_is_completed_field': hasattr(appointment, 'is_completed'),
                'table_columns': [c.name for c in appointment.__table__.columns]
            },
            'current_user': {
                'id': current_user.id,
                'username': current_user.username,
                'is_admin': current_user.is_admin
            }
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500