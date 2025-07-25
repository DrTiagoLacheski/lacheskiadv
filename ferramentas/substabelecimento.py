# ferramentas/substabelecimento.py
# Contém a lógica de negócio para a geração de SUBSTABELECIMENTOS.
# REFATORADO para usar a biblioteca ReportLab para formatação avançada.

import os
from datetime import datetime

# Importa os modelos e funções auxiliares necessários
from models import Advogado
from .procuracao import _formatar_cpf_cnpj, _get_qualificacao_advogado_parts

# Importações da biblioteca ReportLab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import cm

# Importação da Pillow para ler as dimensões da imagem
from PIL import Image as PILImage


def gerar_substabelecimento_pdf(dados):
    """
    Gera o ficheiro PDF do Substabelecimento usando ReportLab.
    Retorna o caminho do ficheiro gerado.
    """
    # 1. Definição do nome e caminho do arquivo de saída
    nome_outorgante_seguro = "".join(c for c in dados.get('nome_outorgante', 'sub').replace(' ', '_') if c.isalnum() or c in ('_')).rstrip()
    nome_arquivo = f"Substabelecimento_{nome_outorgante_seguro}.pdf"
    caminho_arquivo = os.path.join('static/temp', nome_arquivo)

    # 2. Configuração do Documento e Estilos
    doc = SimpleDocTemplate(
        caminho_arquivo,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=0.6 * cm,
        bottomMargin=2.0 * cm
    )

    styles = getSampleStyleSheet()
    style_justified_no_indent = ParagraphStyle(
        name='JustifiedNoIndent',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=16,
        alignment=TA_JUSTIFY
    )
    style_center = ParagraphStyle(
        name='Center',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        alignment=TA_CENTER
    )
    style_titulo_sub = ParagraphStyle(
        name='TituloSub',
        parent=style_center,
        fontName='Times-Bold',
        fontSize=14,
        spaceAfter=15
    )

    # 3. Construção do Conteúdo (A "Story" do ReportLab)
    story = []

    # --- LÓGICA DA LOGO ---
    logo_path = 'static/images/logolacheski.png'
    if os.path.exists(logo_path):
        try:
            with PILImage.open(logo_path) as img:
                img_width, img_height = img.size
            aspect_ratio = img_height / float(img_width)
            display_width = 6 * cm
            display_height = display_width * aspect_ratio
            logo = Image(logo_path, width=display_width, height=display_height)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 0.8 * cm))
        except Exception as e:
            print(f"AVISO: Ficheiro de logo não encontrado ou erro ao processar: {e}")

    # --- Título e Texto dos Poderes (definidos com base no tipo) ---
    tipo_reserva = dados.get('tipo_reserva')
    if tipo_reserva == 'com_reserva':
        titulo = "SUBSTABELECIMENTO COM RESERVAS DE PODERES"
        texto_poderes = "O substabelecente, já qualificado, vem através deste instrumento, SUBSTABELECER COM RESERVA DE PODERES na pessoa do substabelecido, já qualificado, absolutamente todos os poderes conferidos pelo outorgante, já qualificado, para que o substabelecido possa cumprir e atuar como advogado inerentes da cláusula ad judicia et extra para o foro em geral e praticar todos os demais atos necessários ao fiel desempenho deste mandato."
    else:  # Padrão para 'sem_reserva'
        titulo = "SUBSTABELECIMENTO SEM RESERVAS DE PODERES"
        texto_poderes = "O substabelecente, já qualificado, vem através deste instrumento, SUBSTABELECER SEM RESERVA DE PODERES na pessoa do substabelecido, já qualificado, todos os poderes que lhe foram conferidos pelo outorgante, também qualificado, para que o substabelecido possa cumprir e atuar como advogado inerentes da cláusula ad judicia et extra, o que implica na renúncia ao mandato originalmente conferido, para todos os fins de direito."

    story.append(Paragraph(titulo, style_titulo_sub))

    # --- Seção do Substabelecente (Advogado Principal do Sistema) ---
    advogado_principal = Advogado.query.filter_by(is_principal=True).first()
    if not advogado_principal:
        raise ValueError("Nenhum advogado principal (is_principal=True) encontrado no banco de dados para ser o substabelecente.")

    # Reutiliza a função de qualificação para montar o texto
    qual_core, endereco_prof = _get_qualificacao_advogado_parts(advogado_principal)
    texto_substabelecente = f"<b>{advogado_principal.nome.upper()}</b>{qual_core}, com endereço profissional situado na {endereco_prof}."
    story.append(Paragraph(f"SUBSTABELECENTE: {texto_substabelecente}", style_justified_no_indent))
    story.append(Spacer(1, 0.5 * cm))

    # --- Seção do Substabelecido (Dados do Formulário) ---
    texto_substabelecido = (
        f"<b>{dados['nome_substabelecido'].upper()}</b>, brasileiro(a), {dados['estado_civil_substabelecido']}, advogado(a), "
        f"inscrito(a) no CPF sob o n° {_formatar_cpf_cnpj(dados['cpf_substabelecido'])}, "
        f"OAB/{dados['oab_uf_substabelecido'].upper()} n° {dados['oab_num_substabelecido']}, "
        f"com endereço profissional na {dados['endereco_substabelecido']}."
    )
    story.append(Paragraph(f"SUBSTABELECIDO: {texto_substabelecido}", style_justified_no_indent))
    story.append(Spacer(1, 0.5 * cm))

    # --- Seção do Outorgante (Dados do Formulário) ---
    texto_outorgante = (
        f"<b>{dados['nome_outorgante'].upper()}</b>, brasileiro(a), {dados['estado_civil_outorgante']}, "
        f"inscrito(a) no CPF sob o n° {_formatar_cpf_cnpj(dados['cpf_outorgante'])}, "
        f"residente e domiciliado(a) na {dados['endereco_outorgante']}."
    )
    story.append(Paragraph(f"OUTORGANTE: {texto_outorgante}", style_justified_no_indent))
    story.append(Spacer(1, 0.8 * cm))

    # --- Seção dos Poderes Transferidos ---
    story.append(Paragraph(f"<b>PODERES TRANSFERIDOS: </b>{texto_poderes}", style_justified_no_indent))
    story.append(Spacer(1, 1 * cm))

    # --- Data e Assinatura ---
    data_atual = datetime.now().strftime("%d de %B de %Y").lower()
    meses = {"january": "janeiro", "february": "fevereiro", "march": "março", "april": "abril", "may": "maio", "june": "junho", "july": "julho", "august": "agosto", "september": "setembro", "october": "outubro", "november": "novembro", "december": "dezembro"}
    for eng, pt in meses.items():
        data_atual = data_atual.replace(eng, pt)

    story.append(Paragraph(f"Machadinho D'Oeste/RO, {data_atual}.", style_center))
    story.append(Spacer(1, 2 * cm))

    # Assinatura do advogado principal
    oab_principal = advogado_principal.oab_ro or advogado_principal.oab_pr or advogado_principal.oab_sp
    oab_uf_principal = "RO" if advogado_principal.oab_ro else ("PR" if advogado_principal.oab_pr else "SP")

    story.append(Paragraph("________________________________", style_center))
    story.append(Paragraph(f"{advogado_principal.nome.upper()}", style_center))
    if oab_principal:
        story.append(Paragraph(f"OAB/{oab_uf_principal} n° {oab_principal}", style_center))

    # 4. Geração do PDF
    doc.build(story)

    return caminho_arquivo