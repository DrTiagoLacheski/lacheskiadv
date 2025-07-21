# unir/ferramentas/views.py

import os
from flask import Blueprint, render_template, request, jsonify, send_file, url_for, current_app
from flask_login import login_required
# Importações relativas para funcionar dentro do pacote 'ferramentas'
from .procuracao import gerar_procuracao_pdf
from .contratos import gerar_contrato_honorarios_pdf
from .substabelecimento import gerar_substabelecimento_pdf

# CORREÇÃO: Adicionado template_folder='templates' para que o Flask encontre os HTMLs
# nesta pasta (unir/ferramentas/templates/)
ferramentas_bp = Blueprint('ferramentas', __name__, template_folder='templates')


@ferramentas_bp.route('/index')
@login_required
def index():
    """Rota para a página inicial das ferramentas."""
    # Esta rota agora irá renderizar o index.html de unir/ferramentas/templates/
    return render_template('index_ferramentas.html')


# --- Rotas de Procuração ---
@ferramentas_bp.route('/procuracao')
@login_required
def pagina_procuracao():
    """Rota para a página de geração de procuração."""
    return render_template('procuracao.html')


@ferramentas_bp.route('/gerar-procuracao', methods=['POST'])
@login_required
def gerar_procuracao_route():
    """Endpoint da API para gerar o PDF da procuração."""
    try:
        data = request.json
        # ... (sua validação de campos)
        arquivo = gerar_procuracao_pdf(data)

        return jsonify({
            'success': True,
            'filename': os.path.basename(arquivo),
            # CORREÇÃO: Usar o endpoint correto 'ferramentas.download_file'
            'download_url': url_for('ferramentas.download_file', filename=os.path.basename(arquivo))
        })
    except Exception as e:
        current_app.logger.error("Ocorreu uma exceção em 'gerar_procuracao_route'", exc_info=True)
        return jsonify({'error': f'Ocorreu um erro ao gerar a procuração: {str(e)}'}), 500


# --- Rotas de Contrato de Honorários ---
@ferramentas_bp.route('/contrato-honorarios')
@login_required
def pagina_contrato_honorarios():
    """Rota para a página de geração de contrato de honorários."""
    return render_template('contrato_honorarios.html')


@ferramentas_bp.route('/gerar-contrato-honorarios', methods=['POST'])
@login_required
def gerar_contrato_honorarios_route():
    """Endpoint da API para gerar o PDF do contrato de honorários."""
    try:
        data = request.json
        # ... (sua validação de campos)
        arquivo = gerar_contrato_honorarios_pdf(data)
        return jsonify({
            'success': True,
            'filename': os.path.basename(arquivo),
            # CORREÇÃO: Usar o endpoint correto 'ferramentas.download_file'
            'download_url': url_for('ferramentas.download_file', filename=os.path.basename(arquivo))
        })
    except Exception as e:
        current_app.logger.error("Ocorreu uma exceção em 'gerar_contrato_honorarios_route'", exc_info=True)
        return jsonify({'error': f'Ocorreu um erro ao gerar o contrato: {str(e)}'}), 500


# --- Rotas de Substabelecimento ---
@ferramentas_bp.route('/substabelecimento')
@login_required
def pagina_substabelecimento():
    """Rota para a página de geração de substabelecimento."""
    return render_template('substabelecimento.html')


@ferramentas_bp.route('/gerar-substabelecimento', methods=['POST'])
@login_required
def gerar_substabelecimento_route():
    """Endpoint da API para gerar o PDF do substabelecimento."""
    try:
        data = request.json
        # ... (sua validação de campos)
        arquivo = gerar_substabelecimento_pdf(data)

        return jsonify({
            'success': True,
            'filename': os.path.basename(arquivo),
            # CORREÇÃO: Usar o endpoint correto 'ferramentas.download_file'
            'download_url': url_for('ferramentas.download_file', filename=os.path.basename(arquivo))
        })
    except Exception as e:
        current_app.logger.error("Ocorreu uma exceção em 'gerar_substabelecimento_route'", exc_info=True)
        return jsonify({'error': f'Ocorreu um erro ao gerar o substabelecimento: {str(e)}'}), 500


# --- Rota de Download ---
@ferramentas_bp.route('/download/<filename>')
@login_required
def download_file(filename):
    """Rota para fazer o download dos arquivos gerados."""
    return send_file(
        os.path.join(current_app.root_path, 'static/temp', filename),
        as_attachment=True,
        download_name=filename
    )