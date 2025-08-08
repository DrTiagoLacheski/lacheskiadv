# ferramentas/procuracao.py (Versão Corrigida)
# Contém a lógica de negócio para a geração de PROCURAÇÕES.

import os
from datetime import datetime

# Importa o modelo do banco de dados
from models import Advogado

# ... (outros imports do ReportLab e PIL permanecem iguais) ...
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib.units import cm
from PIL import Image as PILImage




def RG_valido(rg):
    """Retorna True se o RG tiver entre 7 e 10 dígitos numéricos (com ou sem hifens/pontos)."""
    if not rg:
        return False
    rg_digits = ''.join(filter(str.isdigit, str(rg)))
    # RG normalmente tem entre 7 e 10 dígitos
    return 7 <= len(rg_digits) <= 10


def oab_valida(oab):
    import re
    if not oab:
        return False
    oab = str(oab).strip()
    return bool(re.fullmatch(r"\d{4,6}/[A-Z]{2}", oab))



# --- FUNÇÕES AUXILIARES (permanecem iguais) ---
def _formatar_cpf_cnpj(num):
    # ... (código sem alteração) ...
    if not num:
        return ""
    num_only = ''.join(filter(str.isdigit, str(num)))
    if len(num_only) == 11:  # CPF
        return f"{num_only[:3]}.{num_only[3:6]}.{num_only[6:9]}-{num_only[9:]}"
    if len(num_only) == 14:  # CNPJ
        return f"{num_only[:2]}.{num_only[2:5]}.{num_only[5:8]}/{num_only[8:12]}-{num_only[12:]}"
    return num_only


def _get_qualificacao_advogado_parts(advogado):
    if not advogado:
        return None, None

    partes_core = [
        f"brasileiro(a), {advogado.estado_civil}",
        advogado.profissao,
        f"inscrito(a) no CPF sob o n.º {_formatar_cpf_cnpj(advogado.cpf)}",
    ]

    if advogado.rg:
        qualificacao_rg = f"portador(a) do RG n.º {advogado.rg}"
        if advogado.orgao_emissor:
            qualificacao_rg += f", {advogado.orgao_emissor}"
        partes_core.append(qualificacao_rg)

    # --- Lógica para OABs ---
    oabs_validas = [oab["numero"] for oab in (advogado.oabs or []) if oab_valida(oab.get("numero"))]
    if oabs_validas:
        partes_core.append(" e ".join([f"OAB n.º {num}" for num in oabs_validas]))

    qualificacao_sem_endereco = ", " + ", ".join(partes_core)
    endereco = advogado.endereco_profissional

    return qualificacao_sem_endereco, endereco


# --- FUNÇÃO PRINCIPAL DE GERAÇÃO DO PDF (COM A CORREÇÃO) ---

def gerar_procuracao_pdf(dados_cliente, current_user):
    """
    Gera o arquivo PDF da procuração com base nos dados do cliente usando ReportLab.
    Recebe 'current_user' para garantir que apenas os advogados corretos sejam usados.
    Retorna o caminho do arquivo gerado.
    """
    # ... (código de definição de nome de arquivo e estilos permanece igual) ...
    nome_arquivo_base = dados_cliente.get('razao_social') or dados_cliente.get('nome_completo') or "procuracao"
    nome_arquivo_seguro = "".join(c for c in nome_arquivo_base.replace(' ', '_') if c.isalnum() or c in ('_')).rstrip()
    nome_arquivo = f"Procuracao_{nome_arquivo_seguro}.pdf"
    caminho_arquivo = os.path.join('static/temp', nome_arquivo)

    doc = SimpleDocTemplate(
        caminho_arquivo,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=0.6 * cm,
        bottomMargin=2.5 * cm
    )
    styles = getSampleStyleSheet()
    style_justified_no_indent = ParagraphStyle(
        name='JustifiedNoIndent',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        alignment=TA_JUSTIFY,
        firstLineIndent=0
    )
    style_center = ParagraphStyle(
        name='Center',
        parent=styles['Normal'],
        fontName='Times-Roman',
        fontSize=12,
        alignment=TA_CENTER
    )
    story = []
    # ... (código da logo e do outorgante permanece igual) ...
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

    tipo_outorgante = dados_cliente.get('tipo_outorgante')
    texto_outorgante = ""
    if tipo_outorgante == 'juridica':
        texto_outorgante = (
            f"<b>{dados_cliente['razao_social'].upper()}</b>, pessoa jurídica de direito privado, "
            f"inscrita no CNPJ sob o n.º {_formatar_cpf_cnpj(dados_cliente['cnpj'])}, "
            f"com sede à {dados_cliente['endereco_sede']}, neste ato representada na forma de seu "
            f"contrato social por seu(sua) {dados_cliente['rep_qualificacao'].lower()}, "
            f"<b>{dados_cliente['rep_nome'].upper()}</b>, inscrito(a) no CPF sob o n.º "
            f"{_formatar_cpf_cnpj(dados_cliente['rep_cpf'])}."
        )
    else:
        qualificacao_pf = (
            f"brasileiro(a), {dados_cliente['estado_civil']}, {dados_cliente['profissao']}, "
            f"devidamente inscrito(a) no CPF n.º {_formatar_cpf_cnpj(dados_cliente['cpf'])}"
        )
        rg_valido = RG_valido(dados_cliente.get('rg'))
        if rg_valido:
            qualificacao_pf += f", portador(a) do RG n.º {dados_cliente['rg']}"
        qualificacao_pf += f", residente e domiciliado(a) à {dados_cliente['endereco']}."
        texto_outorgante = f"<b>{dados_cliente['nome_completo'].upper()}</b>, {qualificacao_pf}"

    texto_final_outorgante = f"OUTORGANTE: {texto_outorgante}"
    story.append(Paragraph(texto_final_outorgante, style_justified_no_indent))
    story.append(Spacer(1, 0.5 * cm))

    # --- Seção do Outorgado (Advogados) - LÓGICA CORRIGIDA ---

    # 1. Busca o advogado principal QUE PERTENCE AO USUÁRIO LOGADO
    advogado_principal = current_user.advogados.filter_by(is_principal=True).first()
    if not advogado_principal:
        raise ValueError(f"Nenhum advogado principal encontrado para o usuário '{current_user.username}'.")

    # 2. Busca o advogado colaborador, garantindo que ele também pertença ao usuário logado
    colaborador_id = dados_cliente.get('colaborador_id')
    advogado_colaborador = None
    if colaborador_id:
        # A busca é feita dentro da lista de advogados do próprio usuário
        advogado_colaborador = current_user.advogados.filter_by(id=colaborador_id).first()

    # O resto da lógica para montar o texto permanece a mesma
    texto_outorgado = ""
    if not advogado_colaborador or advogado_colaborador.id == advogado_principal.id:
        p_qual_core, p_endereco = _get_qualificacao_advogado_parts(advogado_principal)
        texto_outorgado = f"<b>{advogado_principal.nome.upper()}</b>{p_qual_core}, com endereço profissional situado na {p_endereco}."
    else:
        p_qual_core, p_endereco = _get_qualificacao_advogado_parts(advogado_principal)
        c_qual_core, c_endereco = _get_qualificacao_advogado_parts(advogado_colaborador)

        if p_endereco == c_endereco or not c_endereco:
            texto_outorgado = (
                f"<b>{advogado_principal.nome.upper()}</b>{p_qual_core} e "
                f"<b>{advogado_colaborador.nome.upper()}</b>{c_qual_core}, "
                f"ambos com endereço profissional situado na {p_endereco}."
            )
        else:
            texto_outorgado = (
                f"<b>{advogado_principal.nome.upper()}</b>{p_qual_core}, com endereço profissional situado na {p_endereco} e "
                f"<b>{advogado_colaborador.nome.upper()}</b>{c_qual_core}, com endereço profissional situado na {c_endereco}."
            )

    texto_final_outorgado = f"OUTORGADO: {texto_outorgado}"
    story.append(Paragraph(texto_final_outorgado, style_justified_no_indent))
    story.append(Spacer(1, 0.5 * cm))

    # ... (código da seção de poderes, data e assinatura permanece igual) ...
    poderes = "O outorgante nomeia os outorgados seus procuradores, concedendo-lhes os poderes inerentes da cláusula ad judicia et extra para o foro em geral, podendo promover quaisquer medidas judiciais ou administrativas, oferecer defesa, interpor recursos, ajuizar ações e conduzir os respectivos processos, solicitar, providenciar e ter acesso a documentos de qualquer natureza, sendo o presente instrumento de mandato oneroso e contratual, podendo substabelecer este a outrem, com ou sem reserva de poderes, a fim de praticar todos os demais atos necessários ao fiel desempenho deste mandato, além de reconhecer a procedência do pedido, transigir, desistir, renunciar ao direito sobre o qual se funda a ação, receber, dar quitação, firmar compromisso e assinar declaração de hipossuficiência econômica."
    texto_final_poderes = f"<b>PODERES:</b> {poderes}"
    story.append(Paragraph(texto_final_poderes, style_justified_no_indent))
    story.append(Spacer(1, 1 * cm))

    data_atual = datetime.now().strftime("%d de %B de %Y").lower()
    meses = {
        "january": "janeiro", "february": "fevereiro", "march": "março",
        "april": "abril", "may": "maio", "june": "junho",
        "july": "julho", "august": "agosto", "september": "setembro",
        "october": "outubro", "november": "novembro", "december": "dezembro"
    }
    for eng, pt in meses.items():
        data_atual = data_atual.replace(eng, pt)

    story.append(Paragraph(f"Machadinho D'Oeste, {data_atual}.", styles['Normal']))
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("___________________________", style_center))
    story.append(Paragraph("OUTORGANTE", style_center))

    doc.build(story)
    return caminho_arquivo