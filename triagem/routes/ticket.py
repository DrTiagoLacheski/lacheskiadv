# triagem/routes/ticket.py
# VERSÃO FINAL COM NOMES DE ARQUIVO SEGUROS (UUID)

import os
import uuid  # <--- Adicionado para gerar nomes de arquivo seguros
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, send_from_directory, current_app, abort, jsonify)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Ticket, Comment, Attachment
import shutil

# Ajuste da definição do Blueprint para encontrar os templates corretamente
ticket_bp = Blueprint('ticket', __name__, template_folder='../../../templates')


def allowed_file(filename):
    """Verifica se a extensão do arquivo é permitida."""
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

        new_ticket = Ticket(
            title=title.upper(), description=description, case_number=case_number,
            priority=priority, user_id=current_user.id, delegado=delegado
        )
        db.session.add(new_ticket)
        db.session.commit()

        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            for file in files:
                if file and allowed_file(file.filename):
                    original_filename = secure_filename(file.filename)
                    # --- LÓGICA DE NOME SEGURO ---
                    _, ext = os.path.splitext(original_filename)
                    secure_name = f"{uuid.uuid4().hex}{ext}"
                    relative_path = f"{new_ticket.id}/{secure_name}"
                    # ---------------------------

                    full_upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(new_ticket.id))
                    os.makedirs(full_upload_path, exist_ok=True)
                    file.save(os.path.join(full_upload_path, secure_name))

                    attachment = Attachment(
                        filename=original_filename,  # Salva o nome ORIGINAL para exibição
                        path=relative_path,  # Salva o caminho com o nome SEGURO
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
def add_ticket_attachment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        abort(403)
    if 'ticket_attachments' not in request.files or not request.files.getlist('ticket_attachments'):
        flash('Nenhum arquivo selecionado', 'warning')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket_id))
    files = request.files.getlist('ticket_attachments')
    for file in files:
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            # --- LÓGICA DE NOME SEGURO ---
            _, ext = os.path.splitext(original_filename)
            secure_name = f"{uuid.uuid4().hex}{ext}"
            relative_path = f"{ticket.id}/{secure_name}"
            # ---------------------------

            full_upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(ticket.id))
            os.makedirs(full_upload_path, exist_ok=True)
            file.save(os.path.join(full_upload_path, secure_name))

            attachment = Attachment(
                filename=original_filename,  # Salva o nome ORIGINAL
                path=relative_path,  # Salva o caminho com o nome SEGURO
                ticket_id=ticket.id,
                user_id=current_user.id
            )
            db.session.add(attachment)
    db.session.commit()
    flash('Anexo(s) adicionado(s) com sucesso!', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket_id))


# Rota para renomear um anexo (agora muito mais simples e segura)
@ticket_bp.route('/<int:ticket_id>/rename_attachment', methods=['POST'])
@login_required
def rename_attachment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        abort(403)
    attachment_id = request.form.get('attachment_id')
    new_name = request.form.get('new_name')
    if not attachment_id or not new_name:
        flash('Dados inválidos para renomear.', 'danger')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket_id))
    attachment = Attachment.query.get_or_404(attachment_id)
    if attachment.ticket_id != ticket.id:
        abort(403)

    # Simplesmente atualiza o nome de exibição no banco de dados.
    # O arquivo físico com nome seguro não é alterado.
    try:
        _, old_ext = os.path.splitext(attachment.filename)
        # Garante que o novo nome seja seguro e mantenha a extensão original
        new_display_name = f"{secure_filename(new_name)}{old_ext}"
        attachment.filename = new_display_name
        db.session.commit()
        flash('Nome do anexo atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao renomear o anexo: {e}', 'danger')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket_id))


# Rota para download de anexos do ticket
@ticket_bp.route('/attachment/<int:attachment_id>/download')
@login_required
def download_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    ticket = attachment.ticket
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        abort(403)

    return send_from_directory(
        directory=current_app.config['UPLOAD_FOLDER'],
        path=attachment.path,  # Usa o caminho com o nome seguro para encontrar o arquivo
        as_attachment=True,
        download_name=attachment.filename  # Usa o nome original para o usuário
    )


# Rota para deletar um anexo de um ticket
@ticket_bp.route('/attachment/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    ticket_id = attachment.ticket_id
    if not (current_user.is_admin or attachment.ticket.user_id == current_user.id):
        abort(403)
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], attachment.path)
        if os.path.exists(file_path):
            os.remove(file_path)  # os.remove é preferível a os.unlink
        db.session.delete(attachment)
        db.session.commit()
        flash('Anexo deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar anexo: {str(e)}', 'danger')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket_id))



@ticket_bp.route('/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    comments = ticket.comments.order_by(Comment.created_at).all()
    return render_template('ticket.html', ticket=ticket, comments=comments)


@ticket_bp.route('/<int:ticket_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        flash('Você não tem permissão para editar este caso.', 'danger')
        return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))
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
def add_comment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    content = request.form['content']
    comment = Comment(content=content, user_id=current_user.id, ticket_id=ticket.id)
    db.session.add(comment)
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Comentário adicionado com sucesso!', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))


@ticket_bp.route('/<int:ticket_id>/update_status', methods=['POST'])
@login_required
def update_status(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = request.form['status']
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'Status atualizado para {ticket.status}', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))


@ticket_bp.route('/<int:ticket_id>/update_report', methods=['POST'])
@login_required
def update_report(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        abort(403)
    ticket.description = request.form['description']
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Relatório atualizado com sucesso!', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))


@ticket_bp.route('/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        flash('Você não tem permissão para deletar este ticket', 'danger')
        return redirect(url_for('dashboard.dashboard'))
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
        current_app.logger.error(f"Erro ao deletar o ticket {ticket_id}: {e}")
    return redirect(url_for('dashboard.dashboard'))


@ticket_bp.route('/<int:ticket_id>/update_priority', methods=['POST'])
@login_required
def update_priority(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        abort(403)
    ticket.priority = request.form['priority']
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Prioridade atualizada com sucesso!', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))


@ticket_bp.route('/<int:ticket_id>/reorder_attachments', methods=['POST'])
@login_required
def reorder_attachments(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403
    new_order = request.get_json()
    if not new_order:
        return jsonify({'success': False, 'error': 'Invalid data'}), 400
    for item in new_order:
        attachment = Attachment.query.get(item.get('id'))
        if attachment and attachment.ticket_id == ticket.id:
            attachment.position = item.get('position')
    db.session.commit()
    return jsonify({'success': True})