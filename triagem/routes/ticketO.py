# triagem/routes/ticket.py
# VERSÃO FINAL COM CORREÇÃO DE CAMINHOS DE ARQUIVO

import os
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

# Rota para visualizar um ticket específico
@ticket_bp.route('/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    comments = ticket.comments.order_by(Comment.created_at).all()
    return render_template('ticket.html', ticket=ticket, comments=comments)


# Rota para editar os detalhes de um ticket
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
                    filename = secure_filename(file.filename)
                    # CORREÇÃO: Cria o caminho relativo sempre com a barra normal (/)
                    relative_path = f"{new_ticket.id}/{filename}"
                    full_upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(new_ticket.id))
                    os.makedirs(full_upload_path, exist_ok=True)
                    file.save(os.path.join(full_upload_path, filename))
                    attachment = Attachment(
                        filename=filename, path=relative_path,
                        ticket_id=new_ticket.id, user_id=current_user.id
                    )
                    db.session.add(attachment)
            db.session.commit()
        flash('Ticket criado com sucesso!')
        return redirect(url_for('ticket.view_ticket', ticket_id=new_ticket.id))
    return render_template('create_ticket.html')


# Rota para adicionar um comentário a um ticket
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


# Rota para atualizar o status de um ticket
@ticket_bp.route('/<int:ticket_id>/update_status', methods=['POST'])
@login_required
def update_status(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = request.form['status']
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f'Status atualizado para {ticket.status}', 'success')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket.id))


# Rota para atualizar a descrição (relatório) de um ticket
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


# Rota para deletar um ticket
@ticket_bp.route('/<int:ticket_id>/delete', methods=['POST'])
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if not (current_user.is_admin or ticket.user_id == current_user.id):
        flash('Você não tem permissão para deletar este ticket', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    try:
        # AJUSTE: Lógica para deletar a pasta de anexos do ticket
        ticket_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(ticket.id))
        if os.path.isdir(ticket_upload_dir):
            shutil.rmtree(ticket_upload_dir) # rmtree deleta a pasta e todo o seu conteúdo

        # Agora, deleta o ticket do banco de dados.
        # A configuração 'cascade' no models.py cuidará de deletar os registros de anexos e comentários.
        db.session.delete(ticket)
        db.session.commit()
        flash('Caso e todos os seus anexos foram deletados com sucesso!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar o caso: {e}', 'danger')
        current_app.logger.error(f"Erro ao deletar o ticket {ticket_id}: {e}")

    return redirect(url_for('dashboard.dashboard'))


# Rota para download de anexos do ticket
@ticket_bp.route('/attachment/<int:attachment_id>/download')
@login_required
def download_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    ticket = attachment.ticket
    if not (current_user.is_admin or ticket.user_id == current_user.id):
        abort(403)
    # CORREÇÃO: Garante que o caminho use a barra correta (/)
    safe_path = attachment.path.replace('\\', '/')
    return send_from_directory(
        directory=current_app.config['UPLOAD_FOLDER'],
        path=safe_path,
        as_attachment=True,
        download_name=attachment.filename
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
        # CORREÇÃO: Garante que o caminho use a barra correta (/) para encontrar o arquivo
        safe_path = attachment.path.replace('\\', '/')
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_path)
        if os.path.exists(file_path):
            os.unlink(file_path)
        db.session.delete(attachment)
        db.session.commit()
        flash('Anexo deletado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao deletar anexo: {str(e)}', 'danger')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket_id))


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
            filename = secure_filename(file.filename)
            # CORREÇÃO: Cria o caminho relativo sempre com a barra normal (/)
            relative_path = f"{ticket.id}/{filename}"
            full_upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(ticket.id))
            os.makedirs(full_upload_path, exist_ok=True)
            file.save(os.path.join(full_upload_path, filename))
            attachment = Attachment(
                filename=filename,
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
    _, old_ext = os.path.splitext(attachment.filename)
    new_filename = f"{secure_filename(new_name)}{old_ext}"
    upload_folder = current_app.config['UPLOAD_FOLDER']
    # CORREÇÃO: Garante que os caminhos usem a barra correta (/)
    safe_old_path = attachment.path.replace('\\', '/')
    old_physical_path = os.path.join(upload_folder, safe_old_path)
    new_relative_path = f"{ticket.id}/{new_filename}"
    new_physical_path = os.path.join(upload_folder, str(ticket.id), new_filename)
    try:
        if os.path.exists(old_physical_path):
            os.rename(old_physical_path, new_physical_path)
        attachment.filename = new_filename
        attachment.path = new_relative_path
        db.session.commit()
        flash('Nome do anexo atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao renomear o arquivo: {e}', 'danger')
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket_id))


# Rota para atualizar a prioridade de um ticket
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
    return redirect(url_for('ticket.view_ticket', ticket_id=ticket_id))


# Rota para reordenar anexos
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