from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import Artigo, Arquivo, db, Comentario, LancamentoFinanceiro, Ticket
from datetime import datetime, date
from flask import current_app
from collections import defaultdict
from models import Appointment

main_bp = Blueprint('main', __name__)

@main_bp.route('/ferramentas-juridicas')
@login_required
def ferramentas_juridicas():
    """Página de ferramentas jurídicas (a página atual que você já tem)"""
    return render_template('ferramentas_juridicas.html')

def pagina_procuracao():
    return render_template('procuracao.html')

@main_bp.route('/')
@login_required
def index():
    hoje = date.today()
    previstos_vencidos = LancamentoFinanceiro.query.filter(
        LancamentoFinanceiro.user_id == current_user.id,
        LancamentoFinanceiro.tipo == 'Entrada',
        LancamentoFinanceiro.status == 'Previsto',
        LancamentoFinanceiro.data < hoje
    ).all()
    alterou = False
    for l in previstos_vencidos:
        data_antiga = l.data
        l.data = hoje
        # Garante que data_original está preenchida
        if not l.data_original:
            l.data_original = data_antiga
        # Remove o appointment antigo e cria um novo para a data remarcada
        appt_antigo = Appointment.query.filter_by(
            user_id=current_user.id,
            appointment_date=data_antiga
        ).filter(
            Appointment.content.like(f"%{l.descricao}%")
        ).first()
        if appt_antigo:
            remarcada_count = (appt_antigo.remarcada_count or 0) + 1
            db.session.delete(appt_antigo)
        else:
            remarcada_count = 1
        # Cria novo compromisso na data remarcada (hoje)
        appt_novo = Appointment(
            content=f"Receita prevista: {l.descricao} (R$ {l.valor}) [REMARCADA x{remarcada_count}]",
            appointment_date=hoje,
            data_original=l.data_original or data_antiga,
            appointment_time="09:00",
            priority="Normal",
            is_recurring=False,
            remarcada_count=remarcada_count,
            user_id=current_user.id
        )
        db.session.add(appt_novo)
        alterou = True
    if alterou:
        db.session.commit()
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

@main_bp.route('/financeiro', methods=['GET', 'POST'])
@login_required
def financeiro():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    categoria = request.args.get('categoria')

    query = LancamentoFinanceiro.query.filter_by(user_id=current_user.id)
    if start_date:
        query = query.filter(LancamentoFinanceiro.data >= start_date)
    if end_date:
        query = query.filter(LancamentoFinanceiro.data <= end_date)
    if categoria:
        query = query.filter_by(categoria=categoria)
    lançamentos = query.order_by(LancamentoFinanceiro.data.desc()).all()

    casos = Ticket.query.order_by(Ticket.title).all()

    # KPIs
    total_entrada = sum(l.valor for l in lançamentos if l.tipo == 'Entrada' and l.status == 'Recebido')
    total_saida = sum(l.valor for l in lançamentos if l.tipo == 'Saída')
    saldo = total_entrada - total_saida
    hoje = date.today()
    total_previsto = sum(l.valor for l in lançamentos if l.tipo == 'Entrada' and l.status == 'Previsto' and l.data >= hoje)
    total_inadimplente = sum(l.valor for l in lançamentos if l.tipo == 'Entrada' and l.status == 'Inadimplente')


    # Gráfico 1: Barras empilhadas - Receitas por Status para Cada Caso
    casos_nomes = []
    recebidos_por_caso = []
    inadimplentes_por_caso = []
    previstos_por_caso = []

    casos_dict = {}
    for caso in casos:
        casos_dict[caso.id] = caso.title

    # Inicializar todos os casos com 0
    for caso_id, caso_nome in casos_dict.items():
        casos_nomes.append(caso_nome)
        recebidos_por_caso.append(0)
        inadimplentes_por_caso.append(0)
        previstos_por_caso.append(0)

    caso_idx_map = {nome: idx for idx, nome in enumerate(casos_nomes)}

    for l in lançamentos:
        if l.tipo == "Entrada" and l.ticket and l.ticket.title:
            idx = caso_idx_map.get(l.ticket.title)
            if idx is not None:
                if l.status == "Recebido":
                    recebidos_por_caso[idx] += float(l.valor)
                elif l.status == "Inadimplente":
                    inadimplentes_por_caso[idx] += float(l.valor)
                elif l.status == "Previsto":
                    previstos_por_caso[idx] += float(l.valor)

    # Gráfico 2: Pizza - Distribuição do Total Inadimplente por Caso
    inadimplentes_dict = defaultdict(float)
    for l in lançamentos:
        if l.tipo == "Entrada" and l.status == "Inadimplente" and l.ticket and l.ticket.title:
            inadimplentes_dict[l.ticket.title] += float(l.valor)

    inadimplentes_casos_labels = list(inadimplentes_dict.keys())
    inadimplentes_casos_data = [inadimplentes_dict[k] for k in inadimplentes_casos_labels]

    # Gráfico mensal
    receitas_recebidas_por_mes = defaultdict(float)
    receitas_previstas_por_mes = defaultdict(float)
    receitas_inadimplente_por_mes = defaultdict(float)
    todos_meses = set()
    mes_dict = {
        '01': 'Jan', '02': 'Fev', '03': 'Mar', '04': 'Abr', '05': 'Mai', '06': 'Jun',
        '07': 'Jul', '08': 'Ago', '09': 'Set', '10': 'Out', '11': 'Nov', '12': 'Dez'
    }

    for l in lançamentos:
        mesref = l.data.strftime('%Y-%m')
        todos_meses.add(mesref)
        if l.tipo == 'Entrada':
            if l.status == 'Recebido':
                receitas_recebidas_por_mes[mesref] += float(l.valor)
            elif l.status == 'Previsto':
                receitas_previstas_por_mes[mesref] += float(l.valor)
            elif l.status == 'Inadimplente':
                receitas_inadimplente_por_mes[mesref] += float(l.valor)
    meses = sorted(list(todos_meses))
    meses_label = [f"{mes_dict[m.split('-')[1]]}/{m.split('-')[0]}" for m in meses]
    recebidos_data = [receitas_recebidas_por_mes.get(m, 0) for m in meses]
    previstos_data = [receitas_previstas_por_mes.get(m, 0) for m in meses]
    inadimplentes_data = [receitas_inadimplente_por_mes.get(m, 0) for m in meses]

    chart_data = {
        "meses": meses_label,
        "recebidosData": recebidos_data,
        "previstosData": previstos_data,
        "inadimplentesData": inadimplentes_data,
        "casosNomes": casos_nomes,
        "recebidosPorCaso": recebidos_por_caso,
        "inadimplentesPorCaso": inadimplentes_por_caso,
        "previstosPorCaso": previstos_por_caso,
        "inadimplentesCasosLabels": inadimplentes_casos_labels,
        "inadimplentesCasosData": inadimplentes_casos_data,
    }

    return render_template(
        'financeiro.html',
        lançamentos=lançamentos,
        total_entrada=total_entrada,
        total_saida=total_saida,
        saldo=saldo,
        total_previsto=total_previsto,
        total_inadimplente=total_inadimplente,
        chart_data=chart_data,
        casos=casos
    )


@main_bp.route('/financeiro/novo', methods=['POST'])
@login_required
def novo_lancamento():
    tipo = request.form['tipo']
    descricao = request.form['descricao']
    valor = request.form['valor']
    data_str = request.form['data']
    categoria = request.form['categoria']
    ticket_id = request.form.get('ticket_id')
    status = request.form.get('status')
    data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
    try:
        # Sempre salva data_original na criação
        lanc = LancamentoFinanceiro(
            tipo=tipo,
            descricao=descricao,
            valor=valor,
            data=data_obj,
            data_original=data_obj,
            categoria=categoria,
            user_id=current_user.id,
            ticket_id=ticket_id if ticket_id else None,
            status=status
        )
        db.session.add(lanc)
        db.session.commit()

        # Adiciona compromisso se previsto futuro
        if tipo == 'Entrada' and status == 'Previsto':
            appointment = Appointment(
                content=f"Receita prevista: {descricao} (R$ {valor})",
                appointment_date=data_obj,
                data_original=data_obj,
                appointment_time="09:00",
                priority="Normal",
                is_recurring=False,
                user_id=current_user.id,
                remarcada_count=0
            )
            db.session.add(appointment)
            db.session.commit()

        flash("Lançamento adicionado com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao adicionar lançamento: {e}", "danger")
    return redirect(url_for('main.financeiro'))



@main_bp.route('/financeiro/<int:lancamento_id>/excluir', methods=['POST'])
@login_required
def excluir_lancamento(lancamento_id):
    lanc = LancamentoFinanceiro.query.get_or_404(lancamento_id)
    if lanc.user_id != current_user.id and not getattr(current_user, "is_admin", False):
        flash('Você não tem permissão para excluir este lançamento.', 'danger')
        return redirect(url_for('main.financeiro'))
    db.session.delete(lanc)
    db.session.commit()
    flash("Lançamento removido com sucesso.", "success")
    return redirect(url_for('main.financeiro'))

@main_bp.route('/financeiro/atualizar-status/<int:lancamento_id>', methods=['POST'])
@login_required
def atualizar_status_lancamento(lancamento_id):
    data = request.get_json()
    novo_status = data.get('status')
    lanc = LancamentoFinanceiro.query.get_or_404(lancamento_id)
    if lanc.user_id != current_user.id:
        return jsonify(success=False), 403
    if novo_status not in ['Recebido', 'Inadimplente', 'Previsto']:
        return jsonify(success=False), 400
    lanc.status = novo_status
    db.session.commit()
    return jsonify(success=True)

@main_bp.route('/api/appointments/<int:ano>/<int:mes>')
@login_required
def api_appointments_mes(ano, mes):
    from models import Appointment
    from datetime import date

    # Primeiro e último dia do mês
    d1 = date(ano, mes, 1)
    if mes == 12:
        d2 = date(ano + 1, 1, 1)
    else:
        d2 = date(ano, mes + 1, 1)

    appointments = Appointment.query.filter_by(user_id=current_user.id)\
        .filter(Appointment.appointment_date >= d1)\
        .filter(Appointment.appointment_date < d2)\
        .all()
    return jsonify([a.to_dict() for a in appointments])


@main_bp.route('/api/appointments', methods=['POST'])
@login_required
def criar_appointment():
    data = request.get_json()
    content = data.get('content')
    appointment_date = data.get('appointment_date')
    appointment_time = data.get('appointment_time')
    priority = data.get('priority', 'Normal')
    recurring = data.get('recurring', False)

    from models import Appointment
    from datetime import datetime

    try:
        appt = Appointment(
            content=content,
            appointment_date=datetime.strptime(appointment_date, "%Y-%m-%d").date(),
            appointment_time=appointment_time,
            priority=priority,
            is_recurring=recurring,
            user_id=current_user.id
        )
        db.session.add(appt)
        db.session.commit()
        return jsonify(success=True, id=appt.id)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e)), 400