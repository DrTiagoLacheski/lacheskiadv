# unir/ferramentas/views.py

import os
import uuid
# ALTERAÇÃO 1: Adicionar 'send_from_directory' à importação do Flask
from flask import Blueprint, render_template, request, jsonify, send_file, url_for, current_app, send_from_directory
from flask_login import login_required
from werkzeug.utils import secure_filename

from . import pdf_tools
# Importações relativas para funcionar dentro do pacote 'ferramentas'
from .procuracao import gerar_procuracao_pdf
from .contratos import gerar_contrato_honorarios_pdf
from .substabelecimento import gerar_substabelecimento_pdf
from .calctrabalhista import gerar_relatorio_trabalhista_pdf
# Importa as funções de pdf_tools
from .pdf_tools import merge_pdfs, convert_images_to_pdf, split_pdf, cleanup_files

# CORREÇÃO: Adicionado template_folder='templates' para que o Flask encontre os HTMLs
# nesta pasta (.../ferramentas/templates/)
ferramentas_bp = Blueprint('ferramentas', __name__,
                           template_folder='templates',
                           static_folder='static',  # Pasta estática relativa a este Blueprint
                           static_url_path='/ferramentas_static')


@ferramentas_bp.route('/')
@login_required
def index():
    """Rota para a página inicial."""
    return render_template('index_ferramentas.html')


# --- Rotas de Geração de Documentos ---
@ferramentas_bp.route('/procuracao')
@login_required
def pagina_procuracao():
    return render_template('procuracao.html')


@ferramentas_bp.route('/gerar-procuracao', methods=['POST'])
@login_required
def gerar_procuracao_route():
    """Endpoint da API para gerar o PDF da procuração."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'success': False,
                'error': 'Nenhum dado enviado no corpo da requisição'
            }), 400

        required_fields = ['nome_completo', 'profissao', 'cpf', 'endereco', 'estado_civil']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'O campo {field.replace("_", " ")} é obrigatório!',
                    'missing_field': field
                }), 400

        # Validação adicional do CPF
        cpf_limpo = ''.join(filter(str.isdigit, data['cpf']))
        if len(cpf_limpo) != 11:
            return jsonify({
                'success': False,
                'error': 'CPF deve conter exatamente 11 dígitos numéricos',
                'invalid_field': 'cpf'
            }), 400

        arquivo = gerar_procuracao_pdf(data)

        return jsonify({
            'success': True,
            'filename': os.path.basename(arquivo),
            'download_url': url_for('ferramentas.download_file', filename=os.path.basename(arquivo)),
            'file_path': arquivo  # Para debug
        })

    except Exception as e:
        current_app.logger.error(f"Erro em gerar_procuracao_route: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Erro interno ao processar a solicitação',
            'details': str(e)
        }), 500


@ferramentas_bp.route('/contrato-honorarios')
@login_required
def pagina_contrato_honorarios():
    return render_template('contrato_honorarios.html')


@ferramentas_bp.route('/gerar-contrato-honorarios', methods=['POST'])
@login_required
def gerar_contrato_honorarios_route():
    """Endpoint da API para gerar o PDF do contrato de honorários."""
    try:
        data = request.json
        required_fields = [
            'nome_completo', 'estado_civil', 'cpf', 'endereco',
            'objeto_contrato', 'condicoes_honorarios'
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'O campo {field.replace("_", " ")} é obrigatório!'}), 400

        arquivo = gerar_contrato_honorarios_pdf(data)
        return jsonify({
            'success': True,
            'filename': os.path.basename(arquivo),
            'download_url': url_for('ferramentas.download_file', filename=os.path.basename(arquivo))
        })
    except Exception as e:
        current_app.logger.error("Ocorreu uma exceção em 'gerar_contrato_honorarios_route'", exc_info=True)
        return jsonify({'error': f'Ocorreu um erro ao gerar o contrato: {str(e)}'}), 500


@ferramentas_bp.route('/substabelecimento')
@login_required
def pagina_substabelecimento():
    return render_template('substabelecimento.html')


@ferramentas_bp.route('/gerar-substabelecimento', methods=['POST'])
@login_required
def gerar_substabelecimento_route():
    """Endpoint da API para gerar o PDF do substabelecimento."""
    try:
        data = request.json
        required_fields = [
            'tipo_reserva', 'nome_substabelecido', 'estado_civil_substabelecido',
            'cpf_substabelecido', 'oab_num_substabelecido', 'oab_uf_substabelecido',
            'endereco_substabelecido', 'nome_outorgante', 'estado_civil_outorgante',
            'cpf_outorgante', 'endereco_outorgante'
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'O campo {field.replace("_", " ")} é obrigatório!'}), 400

        arquivo = gerar_substabelecimento_pdf(data)
        return jsonify({
            'success': True,
            'filename': os.path.basename(arquivo),
            'download_url': url_for('ferramentas.download_file', filename=os.path.basename(arquivo))
        })
    except Exception as e:
        current_app.logger.error("Ocorreu uma exceção em 'gerar_substabelecimento_route'", exc_info=True)
        return jsonify({'error': f'Ocorreu um erro ao gerar o substabelecimento: {str(e)}'}), 500


@ferramentas_bp.route('/calculo-trabalhista')
@login_required
def pagina_calculo_trabalhista():
    return render_template('calctrabalhista.html')


@ferramentas_bp.route('/gerar-calculo-trabalhista', methods=['POST'])
@login_required
def gerar_calculo_trabalhista_route():
    """Endpoint da API para gerar o relatório trabalhista."""
    try:
        data = request.json
        required_fields = [
            'data_inicio', 'data_termino', 'funcao_exercida', 'remuneracao',
            'nome_empresa', 'cnpj_empresa', 'regime_jornada', 'clausula_compensacao',
            'insalubridade', 'depositos_fgts', 'hora_extra', 'inicio_expediente',
            'inicio_intervalo', 'fim_intervalo', 'fim_expediente', 'natureza_demissao'
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'O campo {field.replace("_", " ")} é obrigatório!'}), 400

        arquivo = gerar_relatorio_trabalhista_pdf(data)
        return jsonify({
            'success': True,
            'filename': os.path.basename(arquivo),
            'download_url': url_for('ferramentas.download_file', filename=os.path.basename(arquivo))
        })
    except Exception as e:
        current_app.logger.error("Ocorreu uma exceção em 'gerar_calculo_trabalhista_route'", exc_info=True)
        return jsonify({'error': f'Ocorreu um erro ao gerar o relatório: {str(e)}'}), 500


# --- ROTAS DE FERRAMENTAS PDF ---

@ferramentas_bp.route('/ferramentas-pdf')
@login_required
def pagina_ferramentas_pdf():
    """Rota para a página de hub de ferramentas PDF."""
    return render_template('ferramentas-pdf.html')


@ferramentas_bp.route('/merge-pdf')
@login_required
def pagina_merge_pdf():
    """Rota para a página de união de PDFs."""
    return render_template('merge_pdf.html')


@ferramentas_bp.route('/merge-pdf-route', methods=['POST'])
@login_required
def merge_pdf_route():
    """
    Recebe os arquivos PDF, os une usando a lógica de pdf_tools
    e retorna um JSON para o frontend iniciar o download.
    """
    if 'pdfs' not in request.files:
        return jsonify({'success': False, 'error': 'Nenhum arquivo foi enviado.'}), 400

    files = request.files.getlist('pdfs')
    if len(files) < 2:
        return jsonify({'success': False, 'error': 'Por favor, selecione pelo menos dois arquivos PDF.'}), 400

    temp_upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'temp_uploads')
    output_dir = os.path.join(current_app.root_path, 'static', 'temp')
    os.makedirs(temp_upload_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    temp_file_paths = []
    try:
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                temp_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                temp_path = os.path.join(temp_upload_dir, temp_filename)
                file.save(temp_path)
                temp_file_paths.append(temp_path)

        output_filename_user = request.form.get('output_filename', '')
        output_path = pdf_tools.merge_pdfs(temp_file_paths, output_dir, output_filename_user)

        if not output_path:
            raise ValueError("A função de unir PDFs falhou e não retornou um caminho.")

        final_filename = os.path.basename(output_path)
        download_url = url_for('ferramentas.download_file', filename=final_filename)

        return jsonify({
            'success': True,
            'filename': final_filename,
            'download_url': download_url
        })

    except Exception as e:
        current_app.logger.error(f"Erro ao unir PDFs: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Ocorreu um erro no servidor: {str(e)}'}), 500

    finally:
        pdf_tools.cleanup_files(temp_file_paths)


@ferramentas_bp.route('/convert-image')
@login_required
def pagina_convert_image():
    """Rota para a página de conversão de imagem para PDF."""
    return render_template('convert_image.html')


@ferramentas_bp.route('/convert-image-route', methods=['POST'])
@login_required
def convert_image_route():
    """Endpoint da API para converter uma ou mais imagens em PDF."""
    if 'images' not in request.files:
        return jsonify({'error': 'Nenhum arquivo de imagem enviado.'}), 400

    files = request.files.getlist('images')
    output_filename_user = request.form.get('output_filename')

    if not files or files[0].filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado.'}), 400

    saved_files = []
    upload_folder = os.path.join(current_app.root_path, 'static', 'temp')
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}

    for file in files:
        if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            saved_files.append(filepath)
        else:
            cleanup_files(saved_files)
            return jsonify({'error': 'Todos os arquivos devem ser imagens válidas (PNG, JPG, GIF).'}), 400

    pdf_path = convert_images_to_pdf(saved_files, upload_folder, output_filename_user)
    cleanup_files(saved_files)

    if pdf_path:
        return jsonify({
            'success': True,
            'filename': os.path.basename(pdf_path),
            'download_url': url_for('ferramentas.download_file', filename=os.path.basename(pdf_path))
        })
    else:
        return jsonify({'error': 'Falha ao converter as imagens para PDF.'}), 500


@ferramentas_bp.route('/split-pdf')
@login_required
def pagina_split_pdf():
    """Rota para a página de divisão de PDF."""
    return render_template('split_pdf.html')


@ferramentas_bp.route('/split-pdf-route', methods=['POST'])
@login_required
def split_pdf_route():
    """Endpoint da API para dividir um arquivo PDF."""
    if 'pdf' not in request.files:
        return jsonify({'error': 'Nenhum arquivo PDF enviado.'}), 400

    file = request.files['pdf']
    page_ranges = request.form.get('page_ranges')
    output_filename_user = request.form.get('output_filename')

    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado.'}), 400
    if not page_ranges:
        return jsonify({'error': 'As páginas para extração não foram especificadas.'}), 400

    upload_folder = os.path.join(current_app.root_path, 'static', 'temp')
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    try:
        pdf_path = split_pdf(filepath, page_ranges, upload_folder, output_filename_user)
        cleanup_files([filepath])  # Limpa o arquivo original após a divisão
        if pdf_path:
            return jsonify({
                'success': True,
                'filename': os.path.basename(pdf_path),
                'download_url': url_for('ferramentas.download_file', filename=os.path.basename(pdf_path))
            })
        else:
            return jsonify({'error': 'Nenhuma página válida foi encontrada para extrair.'}), 400
    except ValueError as e:
        cleanup_files([filepath])
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        cleanup_files([filepath])
        current_app.logger.error(f"Erro ao dividir PDF: {e}", exc_info=True)
        return jsonify({'error': 'Ocorreu um erro inesperado ao dividir o PDF.'}), 500


# --- Rota de Download ---
# ALTERAÇÃO 2: Rota de download corrigida e padronizada
@ferramentas_bp.route('/download/<path:filename>')
@login_required
def download_file(filename):
    """Rota para fazer o download dos arquivos gerados."""
    # Define o diretório de onde os arquivos serão servidos.
    directory = os.path.join(current_app.root_path, 'static', 'temp')

    # Usa send_from_directory que é mais seguro e idiomático.
    # Ele lida com a junção de caminhos e verificações de segurança.
    return send_from_directory(
        directory=directory,
        path=filename,
        as_attachment=True
    )