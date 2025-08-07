from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Advogado

user_bp = Blueprint('user', __name__, url_prefix='/usuario')

@user_bp.route('/<int:user_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_usuario(user_id):
    usuario = User.query.get_or_404(user_id)
    # Permite editar apenas o próprio usuário ou admin
    if current_user.id != usuario.id and not current_user.is_admin:
        flash('Você não tem permissão para editar este usuário.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        senha = request.form.get('password')
        senha_confirmacao = request.form.get('password_confirm')
        # Validação mínima de senha
        if not senha or not senha_confirmacao:
            flash('Por favor, preencha os dois campos de senha.', 'danger')
            return redirect(url_for('user.editar_usuario', user_id=user_id))
        if senha != senha_confirmacao:
            flash('As senhas não conferem.', 'danger')
            return redirect(url_for('user.editar_usuario', user_id=user_id))
        if len(senha) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
            return redirect(url_for('user.editar_usuario', user_id=user_id))
        usuario.set_password(senha)
        db.session.commit()
        flash('Senha alterada com sucesso!', 'success')
        return redirect(url_for('dashboard.dashboard'))

    # Adiciona consulta dos advogados do usuário
    advogados = usuario.advogados.order_by(Advogado.id).all()

    # Se for admin, mostra advogados dos associados também
    associados_advogados = []
    if usuario.is_admin and current_user.id == usuario.id:
        associados = usuario.associados.order_by(User.id).all()
        for associado in associados:
            associados_advogados.append({
                "associado": associado,
                "advogados": associado.advogados.order_by(Advogado.id).all()
            })

    return render_template(
        'editar_usuario.html',
        usuario=usuario,
        advogados=advogados,
        associados_advogados=associados_advogados
    )

@user_bp.route('/editar-advogado/<int:advogado_id>', methods=['GET', 'POST'])
@login_required
def editar_advogado(advogado_id):
    advogado = Advogado.query.get_or_404(advogado_id)
    # Permite que somente o dono (advogado.user_id) ou admin edite
    if current_user.id != advogado.user_id and not current_user.is_admin:
        flash('Você não tem permissão para editar este advogado.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        advogado.nome = request.form.get('nome')
        advogado.estado_civil = request.form.get('estado_civil')
        advogado.profissao = request.form.get('profissao')
        advogado.cpf = request.form.get('cpf')
        advogado.rg = request.form.get('rg')
        advogado.orgao_emissor = request.form.get('orgao_emissor')
        advogado.oab_pr = request.form.get('oab_pr')
        advogado.oab_ro = request.form.get('oab_ro')
        advogado.oab_sp = request.form.get('oab_sp')
        advogado.endereco_profissional = request.form.get('endereco_profissional')
        # Corrige principal para bool
        advogado.is_principal = bool(int(request.form.get('is_principal', '0')))
        db.session.commit()
        flash('Dados do advogado atualizados com sucesso!', 'success')
        return redirect(url_for('user.editar_usuario', user_id=advogado.user_id))

    return render_template('editar_advogado.html', advogado=advogado)