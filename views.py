# views.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Artigo, Arquivo, db, Comentario
from flask import current_app

main_bp = Blueprint('main', __name__)



@main_bp.route('/ferramentas-juridicas')
@login_required
def ferramentas_juridicas():
    """Página de ferramentas jurídicas (a página atual que você já tem)"""
    return render_template('ferramentas_juridicas.html')

# Mantenha todas as suas rotas existentes abaixo
@main_bp.route('/procuracao')
def pagina_procuracao():
    return render_template('procuracao.html')

@main_bp.route('/')
@login_required
def index():
    return render_template('index.html')

@main_bp.route('/substabelecimento')
def pagina_substabelecimento():
    return render_template('substabelecimento.html')

from flask import request, redirect, url_for, flash
from flask_login import current_user

@main_bp.route('/artigos/novo', methods=['GET', 'POST'])
@login_required
def criar_artigo():
    if request.method == 'POST':
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        imagem = request.files.get('imagem_capa')
        imagem_existente = request.form.get('imagem_existente')

        artigo = Artigo(
            titulo=titulo,
            conteudo=conteudo,
            user_id=current_user.id
        )

        # Imagem de capa (opcional)
        if imagem and imagem.filename:
            from werkzeug.utils import secure_filename
            import os
            filename = secure_filename(imagem.filename)
            caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            imagem.save(caminho)
            artigo.imagem_capa = filename
        elif imagem_existente:
            artigo.imagem_capa = imagem_existente

        db.session.add(artigo)
        db.session.commit()  # Agora artigo.id está disponível

        # Processar anexos
        anexos = request.files.getlist('anexos[]')
        for anexo in anexos:
            if anexo and anexo.filename:
                from werkzeug.utils import secure_filename
                import os
                filename = secure_filename(anexo.filename)
                caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                anexo.save(caminho)
                arquivo = Arquivo(
                    nome=filename,
                    filename=filename,
                    path=caminho,
                    user_id=current_user.id,
                    artigo_id=artigo.id
                )
                db.session.add(arquivo)
        db.session.commit()
        flash('Artigo criado com sucesso!')
        return redirect(url_for('main.listar_artigos'))
    return render_template('criar_artigo.html')

@main_bp.route('/artigos')
@login_required
def listar_artigos():
    artigos = Artigo.query.filter_by(user_id=current_user.id).order_by(Artigo.criado_em.desc()).all()
    return render_template('listar_artigos.html', artigos=artigos)


@main_bp.route('/gerenciador')
@login_required # Adicione autenticação
def painel_gerenciador():
    # Busca os dados de ambas as tabelas
    arquivos = Arquivo.query.order_by(Arquivo.id.desc()).all()
    artigos = Artigo.query.order_by(Artigo.criado_em.desc()).all()

    # Renderiza o novo template unificado, passando ambos os contextos
    return render_template(
        'gerenciador.html',
        arquivos=arquivos,
        artigos=artigos,
        # Você ainda precisa da lógica para 'usuario_admin'
        usuario_admin=current_user.is_admin
    )

@main_bp.route('/artigos/<int:artigo_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_artigo(artigo_id):
    artigo = Artigo.query.get_or_404(artigo_id)
    if artigo.user_id != current_user.id:
        flash('Você não tem permissão para editar este artigo.', 'danger')
        return redirect(url_for('main.listar_artigos'))

    if request.method == 'POST':
        artigo.titulo = request.form['titulo']
        artigo.conteudo = request.form['conteudo']
        imagem = request.files.get('imagem_capa')
        if imagem and imagem.filename:
            from werkzeug.utils import secure_filename
            import os
            filename = secure_filename(imagem.filename)
            caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            imagem.save(caminho)
            artigo.imagem_capa = filename

        # Remover anexos marcados para remoção
        anexos_remover = request.form.getlist('anexos_remover[]')
        for anexo_id in anexos_remover:
            if anexo_id:
                anexo = Arquivo.query.get(int(anexo_id))
                if anexo and anexo.artigo_id == artigo.id:
                    db.session.delete(anexo)

        # Adicionar novos anexos
        anexos = request.files.getlist('anexos[]')
        for anexo in anexos:
            if anexo and anexo.filename:
                from werkzeug.utils import secure_filename
                import os
                filename = secure_filename(anexo.filename)
                caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                anexo.save(caminho)
                arquivo = Arquivo(
                    nome=filename,
                    filename=filename,
                    path=caminho,
                    user_id=current_user.id,
                    artigo_id=artigo.id
                )
                db.session.add(arquivo)

        db.session.commit()
        flash('Artigo atualizado com sucesso!')
        return redirect(url_for('main.listar_artigos'))

    anexos_existentes = artigo.anexos.all()  # ou artigo.anexos.all()
    return render_template('criar_artigo.html', artigo=artigo, anexos_existentes=anexos_existentes)

@main_bp.route('/artigos/<int:artigo_id>/excluir', methods=['POST', 'GET'])
@login_required
def excluir_artigo(artigo_id):
    artigo = Artigo.query.get_or_404(artigo_id)
    if artigo.user_id != current_user.id:
        flash('Você não tem permissão para excluir este artigo.', 'danger')
        return redirect(url_for('main.listar_artigos'))

    db.session.delete(artigo)
    db.session.commit()
    flash('Artigo excluído com sucesso!')
    return redirect(url_for('main.listar_artigos'))

@main_bp.route('/artigos/<int:artigo_id>')
@login_required
def visualizar_artigo(artigo_id):
    artigo = Artigo.query.get_or_404(artigo_id)
    comentarios = Comentario.query.filter_by(artigo_id=artigo.id).order_by(Comentario.criado_em.asc()).all()
    return render_template('visualizar_artigo.html', artigo=artigo, comentarios=comentarios)

@main_bp.route('/artigos/<int:artigo_id>/comentar', methods=['POST'])
@login_required
def comentar_artigo(artigo_id):
    artigo = Artigo.query.get_or_404(artigo_id)
    texto = request.form.get("comentario", "").strip()
    if texto:
        comentario = Comentario(
            texto=texto,
            artigo_id=artigo.id,
            user_id=current_user.id
        )
        db.session.add(comentario)
        db.session.commit()
        flash("Comentário adicionado com sucesso!", "success")
    else:
        flash("O comentário não pode estar em branco.", "danger")
    # Redireciona diretamente para a seção de comentários
    return redirect(url_for('main.visualizar_artigo', artigo_id=artigo.id) + "#comentarios")

@main_bp.route('/comentarios/<int:comentario_id>/editar', methods=['POST'])
@login_required
def editar_comentario(comentario_id):
    comentario = Comentario.query.get_or_404(comentario_id)
    if comentario.user_id != current_user.id and not getattr(current_user, "is_admin", False):
        flash("Você não tem permissão para editar este comentário.", "danger")
        return redirect(url_for('main.visualizar_artigo', artigo_id=comentario.artigo_id) + "#comentarios")
    texto = request.form.get("comentario", "").strip()
    if texto:
        comentario.texto = texto
        db.session.commit()
        flash("Comentário editado com sucesso!", "success")
    else:
        flash("O comentário não pode estar em branco.", "danger")
    return redirect(url_for('main.visualizar_artigo', artigo_id=comentario.artigo_id) + "#comentarios")

@main_bp.route('/comentarios/<int:comentario_id>/excluir', methods=['POST', 'GET'])
@login_required
def excluir_comentario(comentario_id):
    comentario = Comentario.query.get_or_404(comentario_id)
    if comentario.user_id != current_user.id and not getattr(current_user, "is_admin", False):
        flash("Você não tem permissão para excluir este comentário.", "danger")
        return redirect(url_for('main.visualizar_artigo', artigo_id=comentario.artigo_id) + "#comentarios")
    artigo_id = comentario.artigo_id
    db.session.delete(comentario)
    db.session.commit()
    flash("Comentário excluído com sucesso.", "success")
    # Redireciona para a seção de comentários
    return redirect(url_for('main.visualizar_artigo', artigo_id=artigo_id) + "#comentarios")