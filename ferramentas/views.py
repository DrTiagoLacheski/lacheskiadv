# ferramentas/views.py (Versão Corrigida e Implementada)

import os
import uuid
from flask import Blueprint, render_template, request, jsonify, url_for, current_app, send_from_directory, redirect, session, flash
# ALTERAÇÃO 1: Importar 'current_user' para saber quem está logado
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import Advogado
from ferramentas.untils.untils_advogado import get_advogado_by_id, get_advogados_colaboradores_disponiveis

from . import pdf_tools
# Importações relativas para funcionar dentro do pacote 'ferramentas'
from .procuracao import gerar_procuracao_pdf
from .contratos import gerar_contrato_honorarios_pdf
from .substabelecimento import gerar_substabelecimento_pdf
from .calctrabalhista import gerar_relatorio_trabalhista_pdf
# Importa as funções de pdf_tools
from .pdf_tools import merge_pdfs, convert_images_to_pdf, split_pdf, cleanup_files

ferramentas_bp = Blueprint('ferramentas', __name__,
                           template_folder='templates',
                           static_folder='static',
                           static_url_path='/ferramentas_static')



@ferramentas_bp.route('/recibo')
@login_required
def recibo():
    """Página de recibo (a página atual que você já tem)"""
    return render_template('recibo.html')



@ferramentas_bp.route('/')
@login_required
def index():
    """Rota para a página inicial das ferramentas."""
    return render_template('index_ferramentas.html')


# --- Rotas de Geração de Documentos ---

@ferramentas_bp.route('/procuracao/<tipo>')
@login_required
def pagina_procuracao(tipo):
    colaboradores = get_advogados_colaboradores_disponiveis(current_user)
    # Buscar todos os modelos cadastrados
    from models import ProcuracaoModelo
    modelos_procuracao = ProcuracaoModelo.query.order_by(ProcuracaoModelo.nome.asc()).all()
    return render_template(
        'procuracao_fisica.html' if tipo == 'fisica' else 'procuracao_juridica.html',
        colaboradores=colaboradores,
        modelos_procuracao=modelos_procuracao
    )


@ferramentas_bp.route('/gerar-procuracao', methods=['POST'])
@login_required
def gerar_procuracao_route():
    try:
        data = request.json
        advogado_id_raw = data.get('colaborador_id')
        advogado_id = None
        tipo_adv = None
        if advogado_id_raw:
            if str(advogado_id_raw).endswith("_admin"):
                advogado_id = int(str(advogado_id_raw).replace("_admin", ""))
                tipo_adv = "admin"
            else:
                advogado_id = int(advogado_id_raw)
                tipo_adv = "meu"
        advogado_colaborador = get_advogado_by_id(current_user, advogado_id, tipo=tipo_adv) if advogado_id else None
        # Passe advogado_colaborador para a função gerar_procuracao_pdf, adaptando a função se necessário
        arquivo = gerar_procuracao_pdf(data, current_user, advogado_colaborador=advogado_colaborador)
        return jsonify({
            'success': True,
            'filename': os.path.basename(arquivo),
            'download_url': url_for('ferramentas.download_file', filename=os.path.basename(arquivo))
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
    colaboradores = get_advogados_colaboradores_disponiveis(current_user)
    return render_template('contrato_honorarios.html', colaboradores=colaboradores)

@ferramentas_bp.route('/gerar-contrato-honorarios', methods=['POST'])
@login_required
def gerar_contrato_honorarios_route():
    """Endpoint da API para gerar o PDF do contrato de honorários."""
    try:
        data = request.json
        # ... (validações de campos permanecem iguais) ...
        required_fields = [
            'nome_completo', 'estado_civil', 'cpf', 'endereco',
            'objeto_contrato', 'condicoes_honorarios'
        ]
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'O campo {field.replace("_", " ")} é obrigatório!'}), 400

        cpf_limpo = ''.join(filter(str.isdigit, data.get('cpf', '')))
        if len(cpf_limpo) != 11:
            return jsonify({'success': False, 'error': 'CPF deve conter 11 dígitos.'}), 400

        # ALTERAÇÃO 5: Passa o 'current_user' para a função de geração do contrato.
        # (Assumindo que 'contratos.py' também será atualizado para usar o current_user)
        arquivo = gerar_contrato_honorarios_pdf(data, current_user)

        return jsonify({
            'success': True,
            'filename': os.path.basename(arquivo),
            'download_url': url_for('ferramentas.download_file', filename=os.path.basename(arquivo))
        })
    except Exception as e:
        current_app.logger.error("Ocorreu uma exceção em 'gerar_contrato_honorarios_route'", exc_info=True)
        return jsonify({'success': False, 'error': f'Ocorreu um erro ao gerar o contrato: {str(e)}'}), 500


# --- O RESTANTE DO ARQUIVO PERMANECE IGUAL ---

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

        # NOTA: Esta função também deveria receber 'current_user' para identificar o advogado principal.
        arquivo = gerar_substabelecimento_pdf(data, current_user)
        return jsonify({
            'success': True,
            'filename': os.path.basename(arquivo),
            'download_url': url_for('ferramentas.download_file', filename=os.path.basename(arquivo))
        })
    except Exception as e:
        current_app.logger.error("Ocorreu uma exceção em 'gerar_substabelecimento_route'", exc_info=True)
        return jsonify({'error': f'Ocorreu um erro ao gerar o substabelecimento: {str(e)}'}), 500


# ... (O restante das rotas de cálculo trabalhista e ferramentas PDF não precisam de alteração) ...
# ... (As rotas de download, preview, etc., também permanecem iguais) ...
@ferramentas_bp.route('/calculo-trabalhista')
@login_required
def pagina_calculo_trabalhista():
    return render_template('calctrabalhista.html')


@ferramentas_bp.route('/gerar-calculo-trabalhista', methods=['POST'])
@login_required
def gerar_calculo_trabalhista_route():
    """Endpoint da API para gerar o relatório trabalhista."""
    try:
        data = request.get_json()

        required_fields = [
            'data_inicio', 'data_termino', 'funcao_exercida', 'remuneracao',
            'nome_empresa', 'cnpj_empresa', 'regime_jornada', 'clausula_compensacao',
            'insalubridade', 'depositos_fgts', 'hora_extra',
            'natureza_demissao'
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
                'download_url': url_for('ferramentas.download_file', filename=os.path.basename(pdf_path)),
                'preview_url': url_for('ferramentas.view_pdf', filename=os.path.basename(pdf_path)) # Nova linha
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


@ferramentas_bp.route('/view/<path:filename>')
@login_required
def view_pdf(filename):
    """
    Renderiza a página do visualizador de PDF, passando o nome do arquivo
    que será carregado pelo JavaScript.
    """
    # Você precisará criar o template 'viewer.html' para esta rota.
    return render_template('viewer.html', filename=filename)


@ferramentas_bp.route('/get-pdf/<path:filename>')
@login_required
def get_pdf_file(filename):
    """
    Serve o arquivo PDF bruto para ser carregado pelo PDF.js no frontend.
    'as_attachment=False' é crucial para que o navegador possa exibi-lo inline.
    """
    pdf_directory = os.path.join(current_app.root_path, 'static', 'temp')

    return send_from_directory(
        directory=pdf_directory,
        path=filename,
        as_attachment=False  # Garante que o PDF seja exibido, não baixado
    )


@ferramentas_bp.route('/preview-split-pdf', methods=['POST'])
@login_required
def preview_split_pdf_route():
    """
    Gera uma pré-visualização do PDF dividido sem iniciar o download.
    Retorna uma URL para ser exibida em um iframe/card.
    """
    if 'pdf' not in request.files:
        return jsonify({'success': False, 'error': 'Nenhum arquivo PDF enviado.'}), 400

    file = request.files['pdf']
    page_ranges = request.form.get('page_ranges')

    if file.filename == '' or not page_ranges:
        return jsonify({'success': False, 'error': 'Dados insuficientes para a pré-visualização.'}), 400

    upload_folder = os.path.join(current_app.root_path, 'static', 'temp_uploads')
    output_folder = os.path.join(current_app.root_path, 'static', 'temp')
    os.makedirs(upload_folder, exist_ok=True)

    original_filename = f"original_{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    original_filepath = os.path.join(upload_folder, original_filename)
    file.save(original_filepath)

    try:
        preview_output_filename = f"preview_{uuid.uuid4().hex}.pdf"

        # --- CORREÇÃO APLICADA AQUI ---
        # 1. Capture o caminho real do arquivo retornado pela função.
        created_pdf_path = split_pdf(original_filepath, page_ranges, output_folder, preview_output_filename)

        # 2. Verifique se o caminho retornado é válido e se o arquivo existe.
        if not created_pdf_path or not os.path.exists(created_pdf_path):
            # Esta mensagem de erro é a que você estava vendo.
            raise ValueError("A divisão do PDF para pré-visualização falhou.")

        # 3. Use o nome do arquivo real que foi criado.
        final_preview_filename = os.path.basename(created_pdf_path)
        preview_url = url_for('ferramentas.get_pdf_file', filename=final_preview_filename)

        return jsonify({
            'success': True,
            'filename': final_preview_filename,
            'preview_url': preview_url
        })
    except ValueError as e:
        # Retorna o erro específico da validação (ex: páginas inválidas).
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar pré-visualização de PDF: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Ocorreu um erro inesperado ao gerar a pré-visualização.'}), 500
    finally:
        if os.path.exists(original_filepath):
            cleanup_files([original_filepath])



# --- Rota de Download ---
@ferramentas_bp.route('/download/<path:filename>')
@login_required
def download_file(filename):
    """Rota para fazer o download dos arquivos gerados."""
    directory = os.path.join(current_app.root_path, 'static', 'temp')
    return send_from_directory(
        directory=directory,
        path=filename,
        as_attachment=True
    )

# --- Rotas para Gerenciamento de Arquivos (Guidelines) ---
@ferramentas_bp.route('/upload_arquivo', methods=['POST'])
@login_required
def upload_arquivo():
    """Upload de arquivos para guidelines/materiais"""
    from models import Arquivo, db
    import os
    from werkzeug.utils import secure_filename
    
    if 'arquivo' not in request.files:
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('main.painel_gerenciador'))
    
    arquivo = request.files['arquivo']
    descricao = request.form.get('descricao', '')
    
    if arquivo.filename == '':
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('main.painel_gerenciador'))
    
    if arquivo:
        # Garante nome seguro do arquivo
        filename = secure_filename(arquivo.filename)
        
        # Cria diretório de uploads se não existir
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Salva arquivo
        filepath = os.path.join(upload_dir, filename)
        arquivo.save(filepath)
        
        # Cria registro no banco
        novo_arquivo = Arquivo(
            nome=arquivo.filename,
            filename=filename,
            descricao=descricao,
            path=filepath,
            tamanho=os.path.getsize(filepath),
            tipo_mime=arquivo.content_type,
            user_id=current_user.id
        )
        
        db.session.add(novo_arquivo)
        db.session.commit()
        
        flash('Arquivo enviado com sucesso!', 'success')
    
    return redirect(url_for('main.painel_gerenciador'))

@ferramentas_bp.route('/download_arquivo/<int:arquivo_id>')
@login_required
def download_arquivo(arquivo_id):
    """Download de arquivo por ID"""
    from models import Arquivo
    
    arquivo = Arquivo.query.get_or_404(arquivo_id)
    
    return send_from_directory(
        directory=os.path.dirname(arquivo.path),
        path=os.path.basename(arquivo.path),
        as_attachment=True,
        download_name=arquivo.nome
    )

@ferramentas_bp.route('/oabs')
@login_required
def exibir_oabs():
    """
    Rota para exibir as OABs de todos advogados do usuário logado.
    Mostra uma lista simples em HTML.
    """
    advogados = current_user.advogados.order_by(Advogado.nome).all()
    dados = []
    for adv in advogados:
        oabs = [oab["numero"] for oab in (adv.oabs or []) if oab.get("numero")]
        dados.append({
            "nome": adv.nome,
            "oabs": oabs
        })

    # Renderiza como HTML simples
    html = "<h2>OABs dos advogados do usuário</h2><ul>"
    for adv in dados:
        html += f"<li><strong>{adv['nome']}</strong>: " + ", ".join(adv["oabs"]) + "</li>"
    html += "</ul>"
    return html

    # Se quiser como JSON, troque para:
    # return jsonify(dados)

