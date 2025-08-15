from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from io import BytesIO
from datetime import datetime

def gerar_pdf_habilitacao(endereco, numero_processo, nome_cliente, advogado):
    # Margens ABNT: sup: 3cm, inf: 2cm, esq: 3cm, dir: 2cm
    margem_sup = 3 * cm
    margem_inf = 2 * cm
    margem_esq = 3 * cm
    margem_dir = 2 * cm

    width, height = A4

    hoje = datetime.now().strftime('%d de %B de %Y')
    oab_num = ""
    oab_uf = ""
    if advogado.oabs and len(advogado.oabs) > 0:
        oab_num = advogado.oabs[0].get("numero", "")
        oab_uf = advogado.oabs[0].get("uf", "RO")

    # =========================
    # Geração com Platypus
    # =========================
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
    import os

    pdf_buffer = BytesIO()
    # topMargin=0 para colar a logo no topo, e só depois inicia margens ABNT
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        topMargin=0,
        bottomMargin=margem_inf,
        leftMargin=margem_esq,
        rightMargin=margem_dir,
    )

    styles = getSampleStyleSheet()
    style_body = ParagraphStyle(
        'corpo',
        parent=styles['Normal'],
        fontName="Times-Roman",
        fontSize=12,
        leading=18,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
    )
    style_body_recuo = ParagraphStyle(
        'corpo_recuo',
        parent=style_body,
        firstLineIndent=1.25*cm,
    )

    style_header = ParagraphStyle(
        'cabecalho',
        parent=styles['Normal'],
        fontName="Times-Bold",
        fontSize=12,
        alignment=TA_JUSTIFY,
        spaceAfter=24,
    )

    style_centro = ParagraphStyle(
        'centro',
        parent=style_body,
        alignment=TA_CENTER
    )

    # Caminho da logo (ajuste para o caminho real do seu projeto)
    logo_path = os.path.join("static", "images", "logolacheski.png")
    story = []

    if os.path.isfile(logo_path):
        # Logo centralizada e colada no topo, largura máxima 6cm, altura menor (ex: 1.2cm)
        story.append(Image(logo_path, width=6 * cm, height=3 * cm, hAlign='CENTER'))
        # Spacer de 1.5cm para iniciar as margens ABNT após a logo
        story.append(Spacer(1, 1.5 * cm))
    else:
        # Se não há logo, respeite a margem ABNT do topo
        story.append(Spacer(1, 3 * cm))

    # Agora o restante do conteúdo, já dentro das margens ABNT
    story.extend([
        Paragraph(f" {endereco.upper()}.", style_header),
        Spacer(1, 1.2 * cm),
        Paragraph(
            f"<b>{nome_cliente.upper()}</b>, já devidamente qualificado nos autos da presente ação, vem, por meio de seu advogado que a esta subscreve, "
            f"requerer habilitação do advogado <b>{advogado.nome.upper()}</b>, brasileiro, advogado, {advogado.estado_civil}, inscrito no CPF n° {advogado.cpf} "
            f"e regularmente inscrito na Ordem Dos Advogados Brasileiros – OAB, com endereço profissional na {advogado.endereco_profissional}, "
            "vem através deste, <b>REQUERER HABILITAÇÃO</b> nos autos da presente ação, conforme procuração em anexo.",
            style_body_recuo),
        Spacer(1, 0.8 * cm),
        Paragraph("Nestes termos,<br/>pede-se deferimento,", style_body),
        Spacer(1, 0.8 * cm),
        Paragraph(f"Machadinho D´ Oeste - RO, {hoje}", style_body),
        Spacer(1, 1 * cm),
        Paragraph(f"<b>{advogado.nome.upper()}</b><br/>OAB/{oab_uf} n° {oab_num}", style_centro),
    ])

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer