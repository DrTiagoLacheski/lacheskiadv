# triagem/routes/ticket.py
# VERSÃO CORRIGIDA E PADRONIZADA

import os
import shutil
import uuid
from datetime import datetime, date as dt_date
from functools import wraps

from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, send_from_directory, current_app, abort, jsonify)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from models import db, Ticket, Comment, Attachment, TodoItem, Appointment

# Especificamos o caminho para a pasta de templates deste blueprint.
ticket_bp = Blueprint(
    'ticket',
    __name__,
    static_folder='../static',         # relativo a routes/
    static_url_path='/ticket_static',  # URL pública será /ticket_static/...
    template_folder='../templates'
)

# --- DECORADOR DE AUTORIZAÇÃO (LÓGICA CENTRALIZADA E CORRIGIDA) ---
def ticket_permission_required(f):
    """
    Verifica se o usuário logado tem permissão para acessar o ticket.
    O usuário deve ser o autor do ticket ou um administrador.
    Este decorador busca o ticket e o passa como primeiro argumento para a função da rota.
    """
    @wraps(f)
    def decorated_function(ticket_id, *args, **kwargs):
        ticket = Ticket.query.get_or_404(ticket_id)
        if not (current_user.is_admin or ticket.user_id == current_user.id):
            # Em vez de um erro 403 genérico, redireciona com uma mensagem clara.
            flash('Você não tem permissão para acessar este caso.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        # Passa o objeto 'ticket' em vez de 'ticket_id' para a rota
        return f(ticket, *args, **kwargs)

    # CORREÇÃO: A função do decorador deve retornar a função interna 'decorated_function'.
    return decorated_function


def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _generate_ticket_code(user):
    """
    Gera um código de ticket único e legível para o usuário.
    Formato: INICIAIS-NUMERO (ex: ADM-0001)
    """
    initials = user.username[:3].upper()

    # Conta quantos tickets o usuário já criou para ter um ponto de partida
    user_ticket_count = Ticket.query.filter_by(user_id=user.id).count()

    # Loop para garantir a unicidade do código gerado
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
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        case_number = request.form['case_number']
        delegado = request.form['delegado']
        priority = request.form['priority']
        ticket_code = _generate_ticket_code(current_user)

        new_ticket = Ticket(
            title=title.upper(), description=description, case_number=case_number,
            priority=priority, user_id=current_user.id, delegado=delegado,
            ticket_code = ticket_code
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
    return render_template('create_ticket.html')


# Rota para adicionar anexos a um ticket existente
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


# Rota para renomear um anexo
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
    # Verificação extra para garantir que o anexo pertence ao ticket da URL
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


# Rota para download de anexos do ticket
@ticket_bp.route('/attachment/<int:attachment_id>/download')
@login_required
def download_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    ticket = attachment.ticket
    # A verificação manual é mantida aqui porque a rota não tem ticket_id
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        flash('Você não tem permissão para acessar este anexo.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    return send_from_directory(
        directory=current_app.config['UPLOAD_FOLDER'],
        path=attachment.path,
        as_attachment=True,
        download_name=attachment.filename
    )


# Rota para deletar um anexo de um ticket
@ticket_bp.route('/attachment/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    ticket_id = attachment.ticket_id
    # A verificação manual é mantida aqui porque a rota não tem ticket_id
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
    if request.method == 'POST':
        ticket.title = request.form['title'].upper()
        ticket.case_number = request.form['case_number']
        ticket.delegado = request.form['delegado']
        ticket.description = request.form['description']
        ticket.priority = request.form['priority']
        ticket.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Caso atualizado com sucesso!', 'success')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))
    return render_template('edit_ticket.html', ticket=ticket)


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
    ticket.description = request.form['description']
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Relatório atualizado com sucesso!', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))


@ticket_bp.route('/<int:ticket_id>/delete', methods=['POST'])
@login_required
@ticket_permission_required
def delete_ticket(ticket):
    try:
        ticket_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(ticket.id))
        if os.path.isdir(ticket_upload_dir):
            shutil.rmtree(ticket_upload_dir)
        db.session.delete(ticket)
        db.session.commit()
        flash('Caso e todos os seus anexos foram deletados com sucesso!', 'success')
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

    # Cria a tarefa normalmente
    new_todo = TodoItem(content=content, ticket_id=ticket.id, date=todo_date)
    db.session.add(new_todo)
    db.session.flush()  # Garante que new_todo.id esteja disponível

    # Se a tarefa tem data, cria um compromisso no calendário
    if todo_date:
        appointment = Appointment(
            content=f"Tarefa: {content} (Ticket #{ticket.id})",
            appointment_date=todo_date,
            appointment_time= "--:--",  # Horário não é obrigatório
            user_id=current_user.id,
            priority='Normal',
            todo_id = new_todo.id
        )
        db.session.add(appointment)

    db.session.commit()

    return jsonify({
        'success': True,
        'todo': {
            'id': new_todo.id,
            'content': new_todo.content,
            'is_completed': new_todo.is_completed,
            'date': new_todo.date.strftime("%Y-%m-%d") if new_todo.date else None
        }
    }), 201


# Rota para atualizar uma tarefa (requer verificação manual)
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


# Rota para deletar uma tarefa (requer verificação manual)
@ticket_bp.route('/todos/<int:todo_id>/delete', methods=['POST'])
@login_required
def delete_todo(todo_id):
    todo = TodoItem.query.get_or_404(todo_id)
    ticket = todo.ticket
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    db.session.delete(todo)
    db.session.commit()
    return jsonify({'success': True})


@ticket_bp.route('/<int:ticket_id>/reorder_todos', methods=['POST'])
@login_required
@ticket_permission_required
def reorder_todos(ticket):
    """Recebe a nova ordem das tarefas e atualiza no banco de dados."""
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


def reschedule_overdue_todos():
    today = dt_date.today()
    # Pega todas as tarefas com data anterior a hoje, não concluídas e não remarcadas
    overdue_todos = TodoItem.query.filter(
        TodoItem.date < today,
        TodoItem.is_completed == False,
        (TodoItem.was_rescheduled == False)  # só remarca uma vez!
    ).all()
    for todo in overdue_todos:
        # Remove Appointment correspondente
        app = Appointment.query.filter_by(
            content=f"Tarefa: {todo.content} (Ticket #{todo.ticket_id})",
            appointment_date=todo.date
        ).first()
        if app:
            db.session.delete(app)
        # Remarca tarefa
        todo.date = today
        todo.was_rescheduled = True
    if overdue_todos:
        db.session.commit()