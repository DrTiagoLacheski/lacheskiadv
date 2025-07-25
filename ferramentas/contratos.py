# ferramentas/contratos.py
# Contém a lógica de negócio para a geração de CONTRATOS DE HONORÁRIOS.
# CORRIGIDO para usar o 'current_user' e garantir a separação de dados.

import os
from datetime import datetime

# Importa o modelo do banco de dados
from models import Advogado

# Importações da biblioteca ReportLab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import cm

# Importação da Pillow para ler as dimensões da imagem
from PIL import Image as PILImage

# Importa as funções auxiliares reutilizadas do módulo de procuração
from .procuracao import _formatar_cpf_cnpj, _get_qualificacao_advogado_parts

# ALTERAÇÃO 1: A função agora recebe 'current_user'
def gerar_contrato_honorarios_pdf(dados, current_user):
    """
    Gera o ficheiro PDF do Contrato de Honorários usando ReportLab.
    Recebe 'current_user' para garantir que apenas os advogados corretos sejam usados.
    Retorna o caminho do ficheiro gerado.
    """
    # 1. Definição do nome e caminho do arquivo de saída (sem alterações)
    nome_arquivo_base = dados.get('nome_completo') or "contrato_honorarios"
    nome_arquivo_seguro = "".join(c for c in nome_arquivo_base.replace(' ', '_') if c.isalnum() or c in ('_')).rstrip()
    nome_arquivo = f"Contrato_Honorarios_{nome_arquivo_seguro}.pdf"
    caminho_arquivo = os.path.join('static/temp', nome_arquivo)

    # 2. Configuração do Documento e Estilos (sem alterações)
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
        fontSize=10,
        leading=12,
        alignment=TA_JUSTIFY
    )
    style_center = ParagraphStyle(
        name='Center',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=10,
        alignment=TA_CENTER
    )
    style_titulo_contrato = ParagraphStyle(
        name='ContratoTitulo',
        parent=style_center,
        fontName='Times-Bold',
        fontSize=14,
        spaceAfter=10
    )

    # 3. Construção do Conteúdo (A "Story" do ReportLab)
    story = []

    # --- LÓGICA DA LOGO (sem alterações) ---
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
            story.append(Spacer(1, 1 * cm))
        except Exception as e:
            print(f"Erro ao processar a imagem da logo: {e}")


    # --- Seção do contratante(Cliente) (sem alterações) ---
    texto_rg = f", portador(a) do RG n.º {dados['rg']}" if dados.get('rg') else ""
    texto_contratante= (
        f"CONTRATANTE: <b>{dados['nome_completo'].upper()}</b>, brasileiro(a), {dados['estado_civil']}, "
        f"inscrito(a) no CPF sob o n.º {_formatar_cpf_cnpj(dados['cpf'])}{texto_rg}, "
        f"residente e domiciliado(a) na {dados['endereco']}."
    )
    story.append(Paragraph(texto_contratante, style_justified_no_indent))
    story.append(Spacer(1, 0.5 * cm))

    # --- ALTERAÇÃO 2: Seção do contratado(Advogados) com LÓGICA CORRIGIDA ---
    # Busca o advogado principal QUE PERTENCE AO USUÁRIO LOGADO
    advogado_principal = current_user.advogados.filter_by(is_principal=True).first()
    if not advogado_principal:
        raise ValueError(f"Nenhum advogado principal encontrado para o usuário '{current_user.username}'.")

    # Busca o advogado colaborador, garantindo que ele também pertença ao usuário logado
    colaborador_id = dados.get('colaborador_id')
    advogado_colaborador = None
    if colaborador_id:
        advogado_colaborador = current_user.advogados.filter_by(id=colaborador_id).first()

    # O resto da lógica para montar o texto permanece a mesma
    texto_contratado= ""
    if not advogado_colaborador or advogado_colaborador.id == advogado_principal.id:
        p_qual_core, p_endereco = _get_qualificacao_advogado_parts(advogado_principal)
        texto_contratado= f"<b>{advogado_principal.nome.upper()}</b>{p_qual_core}, com endereço profissional situado na {p_endereco}."
    else:
        p_qual_core, p_endereco = _get_qualificacao_advogado_parts(advogado_principal)
        c_qual_core, c_endereco = _get_qualificacao_advogado_parts(advogado_colaborador)
        if p_endereco == c_endereco or not c_endereco:
            texto_contratado= (
                f"<b>{advogado_principal.nome.upper()}</b>{p_qual_core} e "
                f"<b>{advogado_colaborador.nome.upper()}</b>{c_qual_core}, "
                f"ambos com endereço profissional situado na {p_endereco}."
            )
        else:
            texto_contratado= (
                f"<b>{advogado_principal.nome.upper()}</b>{p_qual_core}, com endereço profissional situado na {p_endereco} e "
                f"<b>{advogado_colaborador.nome.upper()}</b>{c_qual_core}, com endereço profissional situado na {c_endereco}."
            )

    texto_final_contratado= f"CONTRATADO: {texto_contratado}"
    story.append(Paragraph(texto_final_contratado, style_justified_no_indent))
    story.append(Spacer(1, 0.5 * cm))

    # --- Cláusulas (sem alterações na lógica) ---
    # Variáveis dinâmicas para singular/plural
    if advogado_colaborador and advogado_colaborador.id != advogado_principal.id:
        contratado_com_artigo = "do(s) contratado(s)"
        contratado_sem_artigo = "O(s) contratado(s)"
        contratado_sem_artigo_ao = "ao(s) contratado(s)"
        verbo_ter = "tenham"
        verbo_comprometer = "se comprometem"
        verbo_reservar = "se reservam"
        verbo_entender = "entenderem"
    else:
        contratado_com_artigo = "do contratado"
        contratado_sem_artigo = "o contratado"
        contratado_sem_artigo_ao = "ao contratado"
        verbo_ter = "tenha"
        verbo_comprometer = "se compromete"
        verbo_reservar = "se reserva"
        verbo_entender = "entender"

    clausulas = [
        f"1 - O presente contrato tem por objeto a prestação de serviços de advocacia, por parte {contratado_com_artigo}, para o fim especial de {dados['objeto_contrato']}.",
        f"2 -  Em caso de indeferimento ou inviabilidade da justiça gratuita, as custas e demais despesas judiciais e extrajudiciais correrão por conta exclusiva do(a) contratante. O(A) contratanteobriga-se, ainda, a fornecer as informações e os documentos necessários ao ajuizamento da ação, bem como outros que porventura venham a ser necessários no curso dos mesmos.",
        f"3 -  Os honorários profissionais devidos pelo(a) contratantea favor {contratado_com_artigo}, corresponderão a {dados['condicoes_honorarios']}.",
        f"4 -  Os honorários serão devidos também na hipótese de haver acordo das partes; e/ou se obter êxito em resolver administrativamente e independente da propositura da ação. Considerar-se-ão vencidos e imediatamente exigíveis os honorários ora contratados, no caso de o(a) contratantevir a revogar ou cassar o mandato outorgado {contratado_sem_artigo_ao} ou a exigir o substabelecimento sem reservas, sem que este(s) {verbo_ter}, para isso, dado causa. Nesta hipótese, os honorários serão calculados pelo valor da causa, ou, caso publicada sentença ou acórdão, pelo valor da condenação, ou, ainda, acaso liquidado o processo, pelo valor arbitrado em sentença de liquidação.",
        f"5 -  {contratado_sem_artigo} não {verbo_comprometer} a recorrer e buscar o duplo grau de jurisdição, {verbo_reservar} ao direito de não recorrer da sentença ou acórdão, sem prévio aviso ao cliente, se este for o seu entendimento jurídico. Quando {verbo_entender} que não há possibilidade de reversão ou não preenche os requisitos para apreciação de legalidade por instância superior, já que esta não analisa questões de mérito.",
    ]

    for clausula in clausulas:
        story.append(Paragraph(clausula, style_justified_no_indent))
        story.append(Spacer(1, 0.5 * cm))

    # Parágrafo de fechamento (sem alterações)
    texto_fechamento = "E, por assim estarem justos e contratados, assinam o presente em 02 (duas) vias, para um só efeito, na presença das testemunhas abaixo, elegendo o foro da Comarca de Machadinho D'Oeste/RO para dirimir quaisquer dúvidas resultantes deste contrato."
    story.append(Paragraph(texto_fechamento, style_justified_no_indent))
    story.append(Spacer(1, 0.5 * cm))


    # --- Data e Assinatura (sem alterações) ---
    data_atual = datetime.now().strftime("%d de %B de %Y").lower()
    meses = { "january": "janeiro", "february": "fevereiro", "march": "março", "april": "abril", "may": "maio", "june": "junho", "july": "julho", "august": "agosto", "september": "setembro", "october": "outubro", "november": "novembro", "december": "dezembro" }
    for eng, pt in meses.items():
        data_atual = data_atual.replace(eng, pt)

    story.append(Paragraph(f"Machadinho D'Oeste/RO, {data_atual}."))
    story.append(Spacer(1, 2 * cm))

    story.append(Paragraph("________________________________", style_center))
    story.append(Paragraph("CONTRATANTE", style_center))
    story.append(Spacer(1, 1 * cm))

    story.append(Paragraph("________________________________", style_center))
    story.append(Paragraph("CONTRATADO(S)", style_center))

    # 4. Geração do PDF
    doc.build(story)

    return caminho_arquivo