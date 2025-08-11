from flask import Blueprint, send_file, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import db, Appointment
import json
from io import BytesIO
import zipfile
from datetime import datetime

calendar_export_import_bp = Blueprint(
    "calendar_export_import",
    __name__,
    template_folder='../templates',
    static_folder='../static'
)

@calendar_export_import_bp.route('/export_calendar_appointments', methods=['GET'])
@login_required
def export_calendar_appointments():
    """
    Exporta todos os compromissos criados diretamente pelo usuário no calendário,
    ou seja, source == None ou source == ''.
    """
    appointments = Appointment.query.filter_by(user_id=current_user.id)\
        .filter((Appointment.source == None) | (Appointment.source == '')).all()
    data = []
    for a in appointments:
        data.append({
            "id": a.id,
            "content": a.content,
            "date": a.appointment_date.strftime('%Y-%m-%d'),
            "time": a.appointment_time,
            "priority": a.priority,
            "is_recurring": a.is_recurring,
        })
    mem_zip = BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('calendar_appointments.json', json.dumps(data, ensure_ascii=False, indent=2))
    mem_zip.seek(0)
    return send_file(
        mem_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name='calendar_appointments.zip'
    )

@calendar_export_import_bp.route('/import_calendar_appointments', methods=['GET', 'POST'])
@login_required
def import_calendar_appointments():
    """
    Importa compromissos do calendário a partir de um arquivo ZIP contendo calendar_appointments.json.
    """
    if request.method == 'POST':
        file = request.files.get('calendar_zip')
        if not file or not file.filename.endswith('.zip'):
            flash('Envie um arquivo .zip válido.', 'danger')
            return redirect(request.url)
        try:
            mem_zip = BytesIO(file.read())
            with zipfile.ZipFile(mem_zip, 'r') as zf:
                if 'calendar_appointments.json' not in zf.namelist():
                    flash('Arquivo calendar_appointments.json não encontrado no ZIP.', 'danger')
                    return redirect(request.url)
                json_data = zf.read('calendar_appointments.json').decode('utf-8')
                appointments_data = json.loads(json_data)
                imported_count = 0
                for a in appointments_data:
                    # Evita duplicatas simples usando content, date e time
                    exists = Appointment.query.filter_by(
                        user_id=current_user.id,
                        content=a.get("content"),
                        appointment_date=datetime.strptime(a.get("date"), "%Y-%m-%d").date(),
                        appointment_time=a.get("time"),
                        source=None
                    ).first()
                    if exists:
                        continue
                    appt = Appointment(
                        content=a.get("content"),
                        appointment_date=datetime.strptime(a.get("date"), "%Y-%m-%d").date(),
                        appointment_time=a.get("time"),
                        priority=a.get("priority", "Normal"),
                        is_recurring=a.get("is_recurring", False),
                        user_id=current_user.id,
                        source=None
                    )
                    db.session.add(appt)
                    imported_count += 1
                db.session.commit()
                flash(f'Importação concluída: {imported_count} compromisso(s) do calendário adicionados.', 'success')
                return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao importar compromissos do calendário: {e}", 'danger')
            return redirect(url_for('main.index'))
    return '''
    <form method="POST" enctype="multipart/form-data">
        <h4>Importar Agendamentos do Calendário (.ZIP)</h4>
        <input type="file" name="calendar_zip" accept=".zip" required>
        <button type="submit" class="btn btn-primary">Importar</button>
    </form>
    '''