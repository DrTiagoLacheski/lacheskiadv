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
    Versão atualizada para incluir todos os novos campos.
    """
    appointments = Appointment.query.filter_by(user_id=current_user.id) \
        .filter((Appointment.source == None) | (Appointment.source == '')).all()

    data = []
    for a in appointments:
        # Usar o métod to_dict() do modelo para garantir consistência e obter todos os campos
        appointment_dict = a.to_dict()

        # Adicionar campos extras que não estão em to_dict() mas são importantes para o export
        appointment_dict.update({
            "data_original": a.data_original.strftime('%Y-%m-%d') if a.data_original else None,
            "remarcada_count": a.remarcada_count or 0
        })

        data.append(appointment_dict)

    mem_zip = BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        # Adicionar metadados com versão para compatibilidade futura
        metadata = {
            "version": "2.0",
            "export_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": current_user.id,
            "username": current_user.username
        }
        zf.writestr('metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2))

        # Exportar dados dos compromissos
        zf.writestr('calendar_appointments.json', json.dumps(data, ensure_ascii=False, indent=2))

    mem_zip.seek(0)

    # Criar nome de arquivo com timestamp
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
    Versão atualizada para suportar todos os novos campos do modelo Appointment.
    """
    if request.method == 'POST':
        file = request.files.get('calendar_zip')
        if not file or not file.filename.endswith('.zip'):
            flash('Envie um arquivo .zip válido.', 'danger')
            return redirect(request.url)

        try:
            mem_zip = BytesIO(file.read())
            with zipfile.ZipFile(mem_zip, 'r') as zf:
                # Verificar se o arquivo de dados existe
                if 'calendar_appointments.json' not in zf.namelist():
                    flash('Arquivo calendar_appointments.json não encontrado no ZIP.', 'danger')
                    return redirect(request.url)

                # Verificar metadados (se existirem)
                version = "1.0"  # Versão padrão para arquivos antigos
                if 'metadata.json' in zf.namelist():
                    metadata = json.loads(zf.read('metadata.json').decode('utf-8'))
                    version = metadata.get('version', "1.0")

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
                        # Atualizar compromisso existente se configurado para isso
                        # (pode ser uma opção definida pelo usuário no futuro)
                        update_existing = request.form.get('update_existing') == 'true'

                        if update_existing:
                            existing.appointment_time = a.get("time")
                            existing.priority = a.get("priority", "Normal")
                            existing.is_recurring = a.get("recurring", False)

                            # Processar campos novos (somente se presentes no arquivo importado)
                            if "data_original" in a and a["data_original"]:
                                existing.data_original = datetime.strptime(a["data_original"], "%Y-%m-%d").date()

                            if "remarcada_count" in a:
                                existing.remarcada_count = a.get("remarcada_count", 0)

                            updated_count += 1
                        continue

                    # Criar novo compromisso
                    new_appointment = Appointment(
                        content=a.get("content"),
                        appointment_date=datetime.strptime(a.get("date"), "%Y-%m-%d").date(),
                        appointment_time=a.get("time"),
                        priority=a.get("priority", "Normal"),
                        is_recurring=a.get("recurring", False),
                        user_id=current_user.id,
                        source=None
                    )

                    # Processar campos adicionais da versão 2.0+
                    if version >= "2.0":
                        if a.get("data_original"):
                            new_appointment.data_original = datetime.strptime(a["data_original"], "%Y-%m-%d").date()

                        new_appointment.remarcada_count = a.get("remarcada_count", 0)

                    db.session.add(new_appointment)
                    imported_count += 1

                db.session.commit()

                # Mensagem de resultado
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