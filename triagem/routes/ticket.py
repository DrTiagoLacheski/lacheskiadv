# triagem/routes/ticket.py
# VERSÃO CORRIGIDA E PADRONIZADA - DELEGADO POR ID

import os
import shutil
import uuid
from datetime import datetime, date as dt_date
from functools import wraps

from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, send_from_directory, current_app, abort, jsonify)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import User
from models import db, Ticket, Comment, Attachment, TodoItem, Appointment
from triagem.Utils.utils_ticket import ensure_todo_appointments
from triagem.Utils.utils_ticket import reschedule_overdue_todos


ticket_bp = Blueprint(
    'ticket',
    __name__,
    static_folder='../static',
    static_url_path='/ticket_static',
    template_folder='../templates'
)

# --- DECORADOR DE AUTORIZAÇÃO (LÓGICA CENTRALIZADA E CORRIGIDA) ---
def ticket_permission_required(f):
    """
    Permite acesso ao ticket para: admin, autor, ou usuário associado designado como delegado.
    """
    @wraps(f)
    def decorated_function(ticket_id, *args, **kwargs):
        ticket = Ticket.query.get_or_404(ticket_id)
        if not (
            current_user.is_admin
            or ticket.user_id == current_user.id
            or (ticket.delegado_id and ticket.delegado_id == current_user.id)
        ):
            flash('Você não tem permissão para acessar este caso.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(ticket, *args, **kwargs)
    return decorated_function

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _generate_ticket_code(user):
    initials = user.username[:3].upper()
    user_ticket_count = Ticket.query.filter_by(user_id=user.id).count()
    next_seq = user_ticket_count + 1
    while True:
        ticket_code = f"{initials}-{next_seq:04d}"
        if not Ticket.query.filter_by(ticket_code=ticket_code).first():
            return ticket_code
        next_seq += 1

# Rota para criar um novo ticket
@ticket_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if not current_user.is_admin:
        flash('Apenas administradores podem criar casos.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    if request.method == 'POST':
        title = request.form['title']
        description = ''
        case_number = request.form['case_number']
        priority = request.form['priority']
        ticket_code = _generate_ticket_code(current_user)
        delegado_username = request.form['delegado']
        delegado_user = User.query.filter_by(username=delegado_username).first()
        delegado_id = delegado_user.id if delegado_user else None

        new_ticket = Ticket(
            title=title.upper(),
            description=description,
            case_number=case_number,
            priority=priority,
            user_id=current_user.id,
            delegado_id=delegado_id,
            ticket_code=ticket_code
        )
        db.session.add(new_ticket)
        db.session.commit()

        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            for file in files:
                if file and allowed_file(file.filename):
                    original_filename = secure_filename(file.filename)
                    _, ext = os.path.splitext(original_filename)
                    secure_name = f"{uuid.uuid4().hex}{ext}"
                    relative_path = f"{new_ticket.id}/{secure_name}"

                    full_upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(new_ticket.id))
                    os.makedirs(full_upload_path, exist_ok=True)
                    file.save(os.path.join(full_upload_path, secure_name))

                    attachment = Attachment(
                        filename=original_filename,
                        path=relative_path,
                        ticket_id=new_ticket.id,
                        user_id=current_user.id
                    )
                    db.session.add(attachment)
            db.session.commit()
        flash('Ticket criado com sucesso!')
        return redirect(url_for('ticket.view_ticket', ticket_id=new_ticket.id))

    associados = current_user.associados.order_by(User.username).all() if current_user.is_admin else []
    return render_template('create_ticket.html', associados=associados)

@ticket_bp.route('/<int:ticket_id>/add_attachment', methods=['POST'])
@login_required
@ticket_permission_required
def add_ticket_attachment(ticket):
    if 'ticket_attachments' not in request.files or not request.files.getlist('ticket_attachments'):
        flash('Nenhum arquivo selecionado', 'warning')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))
    files = request.files.getlist('ticket_attachments')
    for file in files:
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            _, ext = os.path.splitext(original_filename)
            secure_name = f"{uuid.uuid4().hex}{ext}"
            relative_path = f"{ticket.id}/{secure_name}"

            full_upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(ticket.id))
            os.makedirs(full_upload_path, exist_ok=True)
            file.save(os.path.join(full_upload_path, secure_name))

            attachment = Attachment(
                filename=original_filename,
                path=relative_path,
                ticket_id=ticket.id,
                user_id=current_user.id
            )
            db.session.add(attachment)
    db.session.commit()
    flash('Anexo(s) adicionado(s) com sucesso!', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

@ticket_bp.route('/<int:ticket_id>/rename_attachment', methods=['POST'])
@login_required
@ticket_permission_required
def rename_attachment(ticket):
    attachment_id = request.form.get('attachment_id')
    new_name = request.form.get('new_name')
    if not attachment_id or not new_name:
        flash('Dados inválidos para renomear.', 'danger')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

    attachment = Attachment.query.get_or_404(attachment_id)
    if attachment.ticket_id != ticket.id:
        flash('Operação não permitida.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    try:
        _, old_ext = os.path.splitext(attachment.filename)
        new_display_name = f"{secure_filename(new_name)}{old_ext}"
        attachment.filename = new_display_name
        db.session.commit()
        flash('Nome do anexo atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao renomear o anexo: {e}', 'danger')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

@ticket_bp.route('/attachment/<int:attachment_id>/download')
@login_required
def download_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    ticket = attachment.ticket
    if not (
        current_user.is_admin
        or ticket.user_id == current_user.id
        or (ticket.delegado_id and ticket.delegado_id == current_user.id)
    ):
        flash('Você não tem permissão para acessar este anexo.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    return send_from_directory(
        directory=current_app.config['UPLOAD_FOLDER'],
        path=attachment.path,
        as_attachment=True,
        download_name=attachment.filename
    )

from flask import send_file

@ticket_bp.route('/<int:ticket_id>/download_zip')
@login_required
@ticket_permission_required
def download_ticket_zip(ticket):
    # Garante a ordem final de exibição dos anexos!
    attachments = ticket.attachments.order_by(Attachment.position.asc()).all()
    if not attachments:
        flash('Não há anexos para baixar.', 'warning')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

    import zipfile
    import io
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for attachment in attachments:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment.path)
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=attachment.filename)
    zip_buffer.seek(0)

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'anexos_ticket_{ticket.id}.zip'
    )

@ticket_bp.route('/attachment/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    ticket_id = attachment.ticket_id

    if not current_user.is_admin:
        flash('Apenas administradores podem deletar anexos.', 'danger')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket_id))

    if not (current_user.is_admin or attachment.ticket.user_id == current_user.id):
        flash('Você não tem permissão para deletar este anexo.', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment.path)
        if os.path.exists(file_path):
            os.remove(file_path)
        db.session.delete(attachment)
        db.session.commit()
        flash('Anexo deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar anexo: {str(e)}', 'danger')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket_id))

@ticket_bp.route('/<int:ticket_id>')
@login_required
@ticket_permission_required
def view_ticket(ticket):
    reschedule_overdue_todos()
    comments = ticket.comments.order_by(Comment.created_at).all()
    todos = ticket.todos.order_by(TodoItem.position.asc()).all()
    return render_template('ticket.html', ticket=ticket, comments=comments, todos=todos)

@ticket_bp.route('/<int:ticket_id>/edit', methods=['GET', 'POST'])
@login_required
@ticket_permission_required
def edit_ticket(ticket):
    associados = []
    # Proíbe delegado de acessar edição
    if ticket.delegado_id and ticket.delegado_id == current_user.id and not current_user.is_admin and ticket.user_id != current_user.id:
        flash('Delegados não podem editar o caso.', 'danger')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

    if current_user.is_admin:
        associados = current_user.associados.all()
    if request.method == 'POST':
        ticket.title = request.form['title'].upper()
        ticket.case_number = request.form['case_number']
        ticket.description = request.form.get('description', ticket.description)
        ticket.priority = request.form['priority']
        ticket.updated_at = datetime.utcnow()
        # Atualiza o delegado via id
        delegado_username = request.form['delegado']
        delegado_user = User.query.filter_by(username=delegado_username).first()
        ticket.delegado_id = delegado_user.id if delegado_user else None
        db.session.commit()
        flash('Caso atualizado com sucesso!', 'success')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))
    return render_template('edit_ticket.html', ticket=ticket, associados=associados)

@ticket_bp.route('/<int:ticket_id>/comment', methods=['POST'])
@login_required
@ticket_permission_required
def add_comment(ticket):
    content = request.form['content']
    comment = Comment(content=content, user_id=current_user.id, ticket_id=ticket.id)
    db.session.add(comment)
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Comentário adicionado com sucesso!', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

@ticket_bp.route('/<int:ticket_id>/update_status', methods=['POST'])
@login_required
@ticket_permission_required
def update_status(ticket):
    ticket.status = request.form['status']
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'Status atualizado para {ticket.status}', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

@ticket_bp.route('/<int:ticket_id>/update_report', methods=['POST'])
@login_required
@ticket_permission_required
def update_report(ticket):
    if not current_user.is_admin:
        flash('Apenas administradores podem deletar casos.', 'danger')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

    ticket.description = request.form['description']
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Relatório atualizado com sucesso!', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

@ticket_bp.route('/<int:ticket_id>/delete', methods=['POST'])
@login_required
@ticket_permission_required
def delete_ticket(ticket):
    if not current_user.is_admin:
        flash('Apenas administradores podem deletar casos.', 'danger')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

    from models import Attachment, TodoItem, Appointment, Comment
    try:
        for attachment in ticket.attachments:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment.path)
            if os.path.exists(file_path):
                os.remove(file_path)

        for attachment in ticket.attachments:
            db.session.delete(attachment)

        for todo in ticket.todos:
            appointment = Appointment.query.filter_by(todo_id=todo.id).first()
            if appointment:
                db.session.delete(appointment)

        orphan_appointments = Appointment.query.filter(
            (Appointment.source == 'triagem') &
            (Appointment.content.like(f"%Ticket #{ticket.id}%"))
        ).all()
        for app in orphan_appointments:
            db.session.delete(app)

        for comment in ticket.comments:
            for attachment in comment.attachments:
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment.path)
                if os.path.exists(file_path):
                    os.remove(file_path)
                db.session.delete(attachment)
            db.session.delete(comment)

        ticket_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(ticket.id))
        if os.path.isdir(ticket_upload_dir):
            shutil.rmtree(ticket_upload_dir)

        db.session.delete(ticket)
        db.session.commit()
        flash('Caso e todos os seus anexos, tarefas e compromissos foram deletados com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar o caso: {e}', 'danger')
        current_app.logger.error(f"Erro ao deletar o ticket {ticket.id}: {e}")
    return redirect(url_for('dashboard.dashboard'))

@ticket_bp.route('/<int:ticket_id>/update_priority', methods=['POST'])
@login_required
@ticket_permission_required
def update_priority(ticket):
    ticket.priority = request.form['priority']
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Prioridade atualizada com sucesso!', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))

@ticket_bp.route('/<int:ticket_id>/reorder_attachments', methods=['POST'])
@login_required
@ticket_permission_required
def reorder_attachments(ticket):
    new_order = request.get_json()
    if not new_order:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400
    for item in new_order:
        attachment = Attachment.query.get(item.get('id'))
        if attachment and attachment.ticket_id == ticket.id:
            attachment.position = item.get('position')
    db.session.commit()
    return jsonify({'success': True})

@ticket_bp.route('/<int:ticket_id>/todos/add', methods=['POST'])
@login_required
@ticket_permission_required
def add_todo(ticket):
    data = request.get_json()
    content = data.get('content')
    priority = data.get('priority', 'Normal')  # NOVO
    date_str = data.get('date')
    if not content:
        return jsonify({'success': False, 'error': 'Content is required'}), 400


    todo_date = None
    if date_str:
        try:
            todo_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Data inválida'}), 400
        if todo_date < datetime.utcnow().date():
            return jsonify({'success': False, 'error': 'A data não pode ser no passado.'}), 400

    last_todo = TodoItem.query.filter_by(ticket_id=ticket.id).order_by(TodoItem.position.desc()).first()
    next_position = (last_todo.position + 1) if last_todo else 0

    new_todo = TodoItem(content=content, ticket_id=ticket.id, date=todo_date, priority=priority)  # NOVO

    db.session.add(new_todo)
    db.session.flush()

    if todo_date:
        admin_user_id = ticket.author.id if ticket.author.is_admin else None
        delegado_user = ticket.delegado if ticket.delegado_id else None

        user_ids = set()
        if admin_user_id:
            user_ids.add(admin_user_id)
        if delegado_user:
            user_ids.add(delegado_user.id)
        user_ids.add(current_user.id)

        for uid in user_ids:
            appointment = Appointment(
                content=f"Tarefa: {content} (Caso #{ticket.id})",
                appointment_date=todo_date,
                appointment_time="--:--",
                user_id=uid,
                priority=priority,  # NOVO
                todo_id=new_todo.id,
                source='triagem'
            )
            db.session.add(appointment)
    db.session.commit()

    return jsonify({
        'success': True,
        'todo': {
            'id': new_todo.id,
            'content': new_todo.content,
            'is_completed': new_todo.is_completed,
            'date': new_todo.date.strftime("%Y-%m-%d") if new_todo.date else None,
            'priority': new_todo.priority
        }
    }), 201

@ticket_bp.route('/todos/<int:todo_id>/update', methods=['POST'])
@login_required
def update_todo(todo_id):
    todo = TodoItem.query.get_or_404(todo_id)
    ticket = todo.ticket
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    data = request.get_json()
    is_completed = data.get('is_completed')
    if is_completed is None:
        return jsonify({'success': False, 'error': 'is_completed is required'}), 400

    todo.is_completed = is_completed

    if todo.date:
        appointment = Appointment.query.filter_by(
            appointment_date=todo.date,
            user_id=current_user.id,
            todo_id=todo.id
        ).first()
        if appointment:
            if is_completed:
                appointment.content = f"Tarefa concluída: {todo.content} (Ticket #{ticket.id})"
                if not appointment.appointment_time:
                    appointment.appointment_time = "--:--"
            else:
                appointment.content = f"Tarefa: {todo.content} (Ticket #{ticket.id})"

    db.session.commit()
    return jsonify({'success': True})

@ticket_bp.route('/todos/<int:todo_id>/delete', methods=['POST'])
@login_required
def delete_todo(todo_id):
    todo = TodoItem.query.get_or_404(todo_id)
    ticket = todo.ticket
    if not (current_user.is_admin):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    db.session.delete(todo)
    db.session.commit()
    return jsonify({'success': True})

@ticket_bp.route('/<int:ticket_id>/reorder_todos', methods=['POST'])
@login_required
@ticket_permission_required
def reorder_todos(ticket):
    new_order = request.get_json()
    if not new_order:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400

    try:
        for item_data in new_order:
            todo_item = TodoItem.query.get(item_data.get('id'))
            if todo_item and todo_item.ticket_id == ticket.id:
                todo_item.position = item_data.get('position')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao reordenar tarefas: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@ticket_bp.route('/<int:ticket_id>/sync_todo_appointments', methods=['POST'])
@login_required
@ticket_permission_required
def sync_todo_appointments(ticket):
    ensure_todo_appointments(ticket)
    flash("Tarefas do ticket sincronizadas no calendário!", "success")
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))


