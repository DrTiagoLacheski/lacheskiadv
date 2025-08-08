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

@admin_associado_bp.route('/criar-usuario-associado', methods=['GET', 'POST'])
@login_required
def criar_usuario_associado():
    if not current_user.is_admin:
        flash("Apenas administradores podem acessar esta página.", "danger")
        return redirect(url_for('main.index'))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not username or not email or not password:
            flash("Todos os campos são obrigatórios.", "warning")
            return redirect(url_for('admin_associado.criar_usuario_associado'))

        # Verifica se já existe
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Já existe um usuário com este nome ou email.", "danger")
            return redirect(url_for('admin_associado.criar_usuario_associado'))

        novo_user = User(
            username=username,
            email=email,
            is_admin=False,
            admin_id=current_user.id
        )
        novo_user.set_password(password)
        db.session.add(novo_user)
        db.session.flush()  # Para pegar o novo_user.id

        # Cria Advogado padrão vinculado ao novo usuário
        from models import Advogado
        advogado_default = Advogado(
            user_id=novo_user.id,
            nome=username,
            estado_civil="solteiro(a)",
            profissao="advogado",
            cpf="000.000.000-00",
            rg="",
            orgao_emissor="",
            oab_pr="",
            oab_ro="",
            oab_sp="",
            endereco_profissional="Não informado",
            is_principal=True
        )
        db.session.add(advogado_default)
        db.session.commit()
        flash(f"Usuário associado '{username}' criado com sucesso, com advogado padrão.", "success")
        return redirect(url_for('admin_associado.criar_usuario_associado'))

    return render_template("criar_usuario_associado.html")