from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User

admin_associado_bp = Blueprint(
    'admin_associado',
    __name__,
    url_prefix='/admin'
)

@admin_associado_bp.route('/criar-associado', methods=['GET', 'POST'])
@login_required
def criar_associado():
    if not current_user.is_admin:
        flash("Apenas administradores podem criar associados.", "danger")
        return redirect(url_for('main.index'))
    if request.method == "POST":
        user_id = request.form.get("user_id")
        user = User.query.filter_by(id=user_id, is_admin=False).first()
        if not user:
            flash("Usuário inválido.", "danger")
            return redirect(url_for('admin_associado.criar_associado'))
        user.admin_id = current_user.id
        db.session.commit()
        flash(f"O usuário {user.username} agora é seu associado.", "success")
        return redirect(url_for('admin_associado.criar_associado'))

    usuarios = User.query.filter_by(is_admin=False, admin_id=None).all()
    return render_template("criar_associado.html", usuarios=usuarios)