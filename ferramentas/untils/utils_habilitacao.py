from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
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

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    hoje = datetime.now().strftime('%d de %B de %Y')
    oab_num = ""
    oab_uf = ""
    if advogado.oabs and len(advogado.oabs) > 0:
        oab_num = advogado.oabs[0].get("numero", "")
        oab_uf = advogado.oabs[0].get("uf", "RO")

    # CABEÇALHO
    c.setFont("Times-Bold", 14)
    c.drawCentredString(width / 2, height - margem_sup,
        f"EXCELENTÍSSIMO (A) SENHOR (A) DOUTOR (A) JUIZ (A) DE DIREITO {endereco.upper()}.")

    # Corpo do texto
    c.setFont("Times-Roman", 12)
    # Conteúdo principal (justificado simulando com width)
    texto = (
        f"\n\n\n{nome_cliente.upper()}, já devidamente qualificado nos autos da presente ação, vem, por meio de seu advogado que a esta subscreve, "
        f"requerer habilitação do advogado {advogado.nome.upper()}, brasileiro, advogado, {advogado.estado_civil}, inscrito no CPF n° {advogado.cpf} "
        f"e regularmente inscrito na Ordem Dos Advogados Brasileiros – OAB, com endereço profissional na {advogado.endereco_profissional}, "
        "vem através deste, REQUERER HABILITAÇÃO nos autos da presente ação, conforme procuração em anexo.\n\n"
        "Nestes termos,\npede-se deferimento,\n\n"
        f"Machadinho D´ Oeste - RO, {hoje}\n\n\n"
        f"{advogado.nome.upper()}\n"
        f"OAB/{oab_uf} n° {oab_num}"
    )

    # Desenha o texto com margens ABNT
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        topMargin=margem_sup,
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
        parent=style_body,  # herda fonte/tamanho/etc do style_body
        alignment=TA_CENTER
    )

    story = [
        Paragraph(f" {endereco.upper()}.", style_header),
        Spacer(1, 1.2*cm),
        Paragraph(
            f"<b>{nome_cliente.upper()}</b>, já devidamente qualificado nos autos da presente ação, vem, por meio de seu advogado que a esta subscreve, "
            f"requerer habilitação do advogado <b>{advogado.nome.upper()}</b>, brasileiro, advogado, {advogado.estado_civil}, inscrito no CPF n° {advogado.cpf} "
            f"e regularmente inscrito na Ordem Dos Advogados Brasileiros – OAB, com endereço profissional na {advogado.endereco_profissional}, "
            "vem através deste, <b>REQUERER HABILITAÇÃO</b> nos autos da presente ação, conforme procuração em anexo.", style_body_recuo),
        Spacer(1, 0.8*cm),
        Paragraph("Nestes termos,<br/>pede-se deferimento,", style_body),
        Spacer(1, 0.8*cm),
        Paragraph(f"Machadinho D´ Oeste - RO, {hoje}", style_body),
        Spacer(1, 1*cm),
        Paragraph(f"<b>{advogado.nome.upper()}</b><br/>OAB/{oab_uf} n° {oab_num}", style_centro),
    ]

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer