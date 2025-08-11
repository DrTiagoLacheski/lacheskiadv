import os
import json
import zipfile
from io import BytesIO
from flask import Blueprint, current_app, send_file, flash, redirect, url_for, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Ticket, TodoItem, Comment, Attachment, User
from datetime import datetime

export_import_bp = Blueprint(
    "ticket_export_import",
    __name__,
    template_folder='../templates',
    static_folder='../static'
)

def ticket_permission_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(ticket_id, *args, **kwargs):
        ticket = Ticket.query.get_or_404(ticket_id)
        if not (current_user.is_admin or ticket.user_id == current_user.id or (ticket.delegado_id and ticket.delegado_id == current_user.id)):
            flash('Você não tem permissão para acessar este caso.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(ticket, *args, **kwargs)
    return decorated

def serialize_ticket(ticket):
    """
    Serializa o ticket para exportação, incluindo apenas campos serializáveis.
    """
    return {
        "id": ticket.id,
        "ticket_code": ticket.ticket_code,
        "title": ticket.title,
        "description": ticket.description,
        "case_number": ticket.case_number,
        "status": ticket.status,
        "priority": ticket.priority,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        "delegado_id": ticket.delegado_id,
        "delegado_username": ticket.delegado.username if ticket.delegado else None,
        "author_id": ticket.user_id,
        "author_username": ticket.author.username if ticket.author else None,
    }

@export_import_bp.route('/<int:ticket_id>/export_zip', methods=['GET'])
@login_required
@ticket_permission_required
def export_ticket_zip(ticket):
    # Exporta o ticket e anexos em um ZIP, modelo novo (delegado por ID e username)
    data = {
        "ticket": serialize_ticket(ticket),
        "todos": [
            {
                "content": todo.content,
                "is_completed": todo.is_completed,
                "date": todo.date.isoformat() if todo.date else None,
                "was_rescheduled": todo.was_rescheduled,
                "position": todo.position
            }
            for todo in ticket.todos
        ],
        "comments": [
            {
                "content": comment.content,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
                "attachments": [
                    {
                        "filename": att.filename,
                        "path": att.path
                    }
                    for att in comment.attachments
                ]
            }
            for comment in ticket.comments
        ],
        "attachments": [
            {
                "filename": att.filename,
                "path": att.path
            }
            for att in ticket.attachments
        ]
    }

    mem_zip = BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        # JSON principal
        zf.writestr('ticket.json', json.dumps(data, ensure_ascii=False, indent=2))
        # Anexos do ticket
        for att in ticket.attachments:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], att.path)
            if os.path.isfile(file_path):
                zf.writestr(f'attachments/{att.filename}', open(file_path, 'rb').read())
        # Anexos dos comentários (prefixo comment_{id}_)
        for comment in ticket.comments:
            for att in comment.attachments:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], att.path)
                if os.path.isfile(file_path):
                    zf.writestr(f'attachments/comment_{comment.id}_{att.filename}', open(file_path, 'rb').read())
    mem_zip.seek(0)
    return send_file(
        mem_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"ticket_{ticket.id}.zip"
    )

@export_import_bp.route('/import_zip', methods=['GET', 'POST'])
@login_required
def import_ticket_zip():
    if not current_user.is_admin:
        flash('Apenas administradores podem importar anexos.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        file = request.files.get('ticket_zip')
        if not file or not file.filename.endswith('.zip'):
            flash('Envie um arquivo .zip válido.', 'danger')
            return redirect(request.url)
        try:
            mem_zip = BytesIO(file.read())
            with zipfile.ZipFile(mem_zip, 'r') as zf:
                # Verifica se é pacote multi-ticket
                ticket_jsons = [name for name in zf.namelist() if name.startswith('ticket_') and name.endswith('.json')]
                if len(ticket_jsons) == 0 and 'ticket.json' in zf.namelist():
                    ticket_jsons = ['ticket.json']  # formato antigo, 1 ticket

                imported_count = 0
                for ticket_json_name in ticket_jsons:
                    json_data = zf.read(ticket_json_name).decode('utf-8')
                    data = json.loads(json_data)
                    t = data.get("ticket")

                    delegado_id = None
                    if t.get("delegado_id"):
                        delegado_id = t["delegado_id"]
                    elif t.get("delegado_username"):
                        delegado_user = User.query.filter_by(username=t["delegado_username"]).first()
                        delegado_id = delegado_user.id if delegado_user else None
                    elif t.get("delegado"):
                        delegado_user = User.query.filter_by(username=t["delegado"]).first()
                        delegado_id = delegado_user.id if delegado_user else None

                    from .ticket import _generate_ticket_code
                    new_ticket = Ticket(
                        title=t["title"],
                        description=t.get("description"),
                        case_number=t.get("case_number"),
                        status=t.get("status", "Em Análise"),
                        priority=t.get("priority", "Média"),
                        delegado_id=delegado_id,
                        user_id=current_user.id,
                        ticket_code=_generate_ticket_code(current_user)
                    )
                    db.session.add(new_ticket)
                    db.session.flush()

                    # Todos (agora com 'time' e 'priority')
                    for todo in data.get("todos", []):
                        new_todo = TodoItem(
                            content=todo["content"],
                            is_completed=todo.get("is_completed", False),
                            date=datetime.fromisoformat(todo["date"]).date() if todo.get("date") else None,
                            was_rescheduled=todo.get("was_rescheduled", False),
                            position=todo.get("position", 0),
                            ticket_id=new_ticket.id,
                            time=todo.get("time"),
                            priority=todo.get("priority", "Normal"),
                        )
                        db.session.add(new_todo)
                        db.session.flush()

                        if new_todo.date:
                            from models import Appointment
                            appointment = Appointment(
                                content=f"Tarefa: {new_todo.content} (Caso #{new_ticket.id})",
                                appointment_date=new_todo.date,
                                appointment_time=new_todo.time if new_todo.time else "--:--",
                                user_id=current_user.id,
                                priority=new_todo.priority,
                                todo_id=new_todo.id,
                                source='triagem'
                            )
                            db.session.add(appointment)

                    # Comentários
                    for comment in data.get("comments", []):
                        new_comment = Comment(
                            content=comment["content"],
                            created_at=datetime.fromisoformat(comment["created_at"]) if comment.get("created_at") else datetime.utcnow(),
                            user_id=current_user.id,
                            ticket_id=new_ticket.id
                        )
                        db.session.add(new_comment)

                    # Attachments do ticket e comentários
                    attachments_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(new_ticket.id))
                    os.makedirs(attachments_dir, exist_ok=True)
                    for att in data.get("attachments", []):
                        att_filename = att["filename"]
                        att_path_in_zip = f"attachments/ticket_{t['id']}_{att_filename}"
                        if att_path_in_zip in zf.namelist():
                            with open(os.path.join(attachments_dir, att_filename), 'wb') as f:
                                f.write(zf.read(att_path_in_zip))
                            new_attachment = Attachment(
                                filename=att_filename,
                                path=f"{new_ticket.id}/{att_filename}",
                                ticket_id=new_ticket.id,
                                user_id=current_user.id
                            )
                            db.session.add(new_attachment)
                    # Attachments dos comentários
                    for comment in data.get("comments", []):
                        for att in comment.get("attachments", []):
                            att_filename = att["filename"]
                            att_path_in_zip = f"attachments/ticket_{t['id']}_comment_{comment['id']}_{att_filename}"
                            if att_path_in_zip in zf.namelist():
                                with open(os.path.join(attachments_dir, att_filename), 'wb') as f:
                                    f.write(zf.read(att_path_in_zip))
                                new_attachment = Attachment(
                                    filename=att_filename,
                                    path=f"{new_ticket.id}/{att_filename}",
                                    ticket_id=new_ticket.id,
                                    user_id=current_user.id,
                                    comment_id=new_comment.id if 'new_comment' in locals() else None
                                )
                                db.session.add(new_attachment)

                    imported_count += 1

                db.session.commit()
                flash(f'{imported_count} ticket(s) importado(s) com sucesso!', 'success')
                return redirect(url_for('dashboard.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao importar ticket(s): {e}", 'danger')
            return redirect(url_for('dashboard.dashboard'))
    return '''
    <form method="POST" enctype="multipart/form-data">
        <h4>Importar Ticket(s) (ZIP)</h4>
        <input type="file" name="ticket_zip" accept=".zip" required>
        <button type="submit" class="btn btn-primary">Importar</button>
    </form>
    '''


@export_import_bp.route('/export_all_zip')
@login_required
def export_all_zip():
    mem_zip = BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        tickets = Ticket.query.all()
        for ticket in tickets:
            # Serializa cada ticket como no export individual

            data = {
                "ticket": serialize_ticket(ticket),
                "todos": [
                    {
                        "content": todo.content,
                        "is_completed": todo.is_completed,
                        "date": todo.date.isoformat() if todo.date else None,
                        "was_rescheduled": todo.was_rescheduled,
                        "position": todo.position,
                        "time": getattr(todo, 'time', None),
                        "priority": getattr(todo, 'priority', 'Normal'),
                    }
                    for todo in ticket.todos
                ],
                "comments": [
                    {
                        "content": comment.content,
                        "created_at": comment.created_at.isoformat() if comment.created_at else None,
                        "attachments": [
                            {
                                "filename": att.filename,
                                "path": att.path
                            }
                            for att in comment.attachments
                        ]
                    }
                    for comment in ticket.comments
                ],
                "attachments": [
                    {
                        "filename": att.filename,
                        "path": att.path
                    }
                    for att in ticket.attachments
                ]
            }
            zf.writestr(f"ticket_{ticket.id}.json", json.dumps(data, ensure_ascii=False, indent=2))

            # Anexos do ticket
            ticket_attach_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(ticket.id))
            for att in ticket.attachments:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], att.path)
                if os.path.isfile(file_path):
                    zf.writestr(f"attachments/ticket_{ticket.id}_{att.filename}", open(file_path, 'rb').read())
            # Anexos dos comentários
            for comment in ticket.comments:
                for att in comment.attachments:
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], att.path)
                    if os.path.isfile(file_path):
                        zf.writestr(f"attachments/ticket_{ticket.id}_comment_{comment.id}_{att.filename}", open(file_path, 'rb').read())
    mem_zip.seek(0)
    return send_file(
        mem_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name="todos_os_tickets.zip"
    )