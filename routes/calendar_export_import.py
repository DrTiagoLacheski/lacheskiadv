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
    compatível com o modelo atual.
    """
    appointments = Appointment.query.filter_by(user_id=current_user.id) \
        .filter((Appointment.source == None) | (Appointment.source == '')).all()

    data = []
    for a in appointments:
        # Usar o mod to_dict() do modelo para garantir compatibilidade
        appointment_dict = a.to_dict()
        # Adicionar campos extras que possam não estar em to_dict()
        appointment_dict["data_original"] = a.data_original.strftime('%Y-%m-%d') if a.data_original else None
        appointment_dict["remarcada_count"] = a.remarcada_count or 0
        data.append(appointment_dict)

    mem_zip = BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        metadata = {
            "version": "2.0",
            "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": current_user.id,
            "username": current_user.username
        }
        zf.writestr('metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2))
        zf.writestr('calendar_appointments.json', json.dumps(data, ensure_ascii=False, indent=2))

    mem_zip.seek(0)
    filename = f'calendar_appointments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'

    return send_file(
        mem_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name=filename
    )


@calendar_export_import_bp.route('/import_calendar_appointments', methods=['GET', 'POST'])
@login_required
def import_calendar_appointments():
    """
    Importa compromissos do calendário a partir de um arquivo ZIP contendo calendar_appointments.json.
    Compatível com o modelo atual.
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

                # Carregar dados dos compromissos
                json_data = zf.read('calendar_appointments.json').decode('utf-8')
                appointments_data = json.loads(json_data)

                imported_count = 0
                updated_count = 0

                for a in appointments_data:
                    # Verificar se o compromisso já existe pelo content e data
                    existing = Appointment.query.filter_by(
                        user_id=current_user.id,
                        content=a.get("content"),
                        appointment_date=datetime.strptime(a.get("date"), "%Y-%m-%d").date()
                    ).first()

                    if existing:
                        update_existing = request.form.get('update_existing') == 'true'
                        if update_existing:
                            existing.appointment_time = a.get("time")
                            existing.priority = a.get("priority", "Normal")
                            existing.is_recurring = a.get("recurring", False)
                            # Campos extras
                            if a.get("data_original"):
                                existing.data_original = datetime.strptime(a["data_original"], "%Y-%m-%d").date()
                            if "remarcada_count" in a:
                                existing.remarcada_count = a.get("remarcada_count", 0)
                            updated_count += 1
                        continue

                    new_appointment = Appointment(
                        content=a.get("content"),
                        appointment_date=datetime.strptime(a.get("date"), "%Y-%m-%d").date(),
                        appointment_time=a.get("time"),
                        priority=a.get("priority", "Normal"),
                        is_recurring=a.get("recurring", False),
                        user_id=current_user.id,
                        source=None
                    )
                    # Campos extras
                    if a.get("data_original"):
                        new_appointment.data_original = datetime.strptime(a["data_original"], "%Y-%m-%d").date()
                    if "remarcada_count" in a:
                        new_appointment.remarcada_count = a.get("remarcada_count", 0)

                    db.session.add(new_appointment)
                    imported_count += 1

                db.session.commit()

                result_message = f'Importação concluída: {imported_count} compromisso(s) adicionados'
                if updated_count > 0:
                    result_message += f' e {updated_count} atualizado(s)'

                flash(result_message + '.', 'success')
                return redirect(url_for('main.index'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao importar compromissos: {str(e)}", exc_info=True)
            flash(f"Erro ao importar compromissos do calendário: {str(e)}", 'danger')
            return redirect(url_for('main.index'))

    # Formulário de importação com opções adicionais
    return '''
    <form method="POST" enctype="multipart/form-data" class="p-3">
        <h4>Importar Agendamentos do Calendário</h4>
        <div class="mb-3">
            <input type="file" name="calendar_zip" accept=".zip" required class="form-control">
        </div>
        <div class="mb-3 form-check">
            <input type="checkbox" name="update_existing" value="true" id="update_existing" class="form-check-input">
            <label for="update_existing" class="form-check-label">Atualizar compromissos existentes</label>
        </div>
        <button type="submit" class="btn btn-primary">Importar</button>
        <a href="/" class="btn btn-secondary">Cancelar</a>
    </form>
    '''