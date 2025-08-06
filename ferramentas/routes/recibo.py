from flask import Blueprint, request, render_template, send_file, current_app
from io import BytesIO
from models import Advogado
from flask_login import current_user
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from num2words import num2words
import os

recibo_bp = Blueprint(
    'recibo',
    __name__,
    template_folder='../templates',
    static_folder='../static',
    static_url_path='/ferramentas/static'
)


#Escvrever por extenso
def valor_reais_por_extenso(valor_str):
    """Recebe valor em string formato '2.500,00' ou '2500,00' e retorna por extenso em reais."""
    # Remove pontos e troca vírgula por ponto para float
    valor_str = valor_str.replace('.', '').replace(',', '.')
    try:
        valor = float(valor_str)
    except Exception:
        valor = 0.0
    reais = int(valor)
    centavos = int(round((valor - reais) * 100))
    extenso = num2words(reais, lang='pt_BR') + " reais"
    if centavos > 0:
        extenso += " e " + num2words(centavos, lang='pt_BR') + " centavos"
    return extenso


def get_advogado_principal(user_id):
    return Advogado.query.filter_by(user_id=user_id, is_principal=True).first()

def gerar_texto_recibo(advogado, valor, data, texto_complementar, is_juridica, nome_empresa, cnpj, sede):
    nome_adv = advogado.nome
    nacionalidade = "brasileiro"
    estado_civil = advogado.estado_civil
    cpf = advogado.cpf
    endereco_profissional = advogado.endereco_profissional
    oab_ro = advogado.oab_ro or ""
    valor_formatado_reais = f"R$ {valor}" if valor else ""
    valor_por_extenso = valor_reais_por_extenso(valor)
    data_formatada = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y") if data else ""
    cidade_uf = "Machadinho D´ Oeste - RO"
    data_declaracao = datetime.today().strftime("%d de %B de %Y")

    texto_principal = (
        f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp<b>EU, {nome_adv.upper()}</b>, {nacionalidade}, advogado, {estado_civil}, "
        f"inscrito no CPF n° {cpf} e regularmente inscrito na Ordem Dos Advogados "
        f"Brasileiros OAB, com endereço profissional na {endereco_profissional}, vem através deste, <b>DECLARAR QUE RECEBEU</b> "
        f"o valor TOTAL de <b>{valor_formatado_reais}</b> ({valor_por_extenso}) na data de {data_formatada} referente a "
        f"prestação de serviços de advocacia e assessoria jurídica, em especial para {texto_complementar.strip()} "
    )

    if is_juridica:
        texto_principal += (
            f", este recibo outorga plena quitação, tendo recebido da empresa <b>{nome_empresa}</b>, "
            f"inscrita no CNPJ {cnpj}, com sede na {sede}."
        )
    else:
        texto_principal += "."

    texto_fechamento = "Por ser expressão da verdade, firmo a presente <b>DECLARAÇÃO DE RECEBIMENTO</b>"

    return {
        "principal": texto_principal,
        "fechamento": texto_fechamento,
        "local_data": f"{cidade_uf}, {data_declaracao}",
        "nome_adv": nome_adv,
        "oab": f"OAB/RO nº {oab_ro}"
    }

@recibo_bp.route('/recibo', methods=['GET', 'POST'])
def gerar_recibo():
    if request.method == 'POST':
        valor = request.form.get('valor')
        data = request.form.get('data')
        texto_complementar = request.form.get('texto_complementar')
        is_juridica = request.form.get('isJuridica')
        nome_empresa = request.form.get('nome_empresa')
        cnpj = request.form.get('cnpj')
        sede = request.form.get('sede')

        advogado = get_advogado_principal(current_user.id)
        if not advogado:
            return "Advogado principal não cadastrado!", 400

        textos = gerar_texto_recibo(
            advogado, valor, data, texto_complementar,
            is_juridica, nome_empresa, cnpj, sede
        )

        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4,
                                leftMargin=25 * mm, rightMargin=25 * mm,
                                topMargin=0 * mm, bottomMargin=18 * mm)  # topMargin = 0

        styles = getSampleStyleSheet()
        styleTitle = ParagraphStyle(name='Title', parent=styles['Normal'], fontName='Times-Bold', fontSize=12,
                                    alignment=1, spaceAfter=16)
        styleBody = ParagraphStyle(name='Body', parent=styles['Normal'], fontName='Times-Roman', fontSize=12,
                                   leading=18, alignment=4, spaceAfter=12)
        styleCentered = ParagraphStyle(name='Centered', parent=styles['Normal'], fontName='Times-Roman', fontSize=12,
                                       alignment=1, spaceAfter=4)
        styleCenteredBold = ParagraphStyle(name='CenteredBold', parent=styleCentered, fontName='Times-Bold')

        story = []

        # Logo colada no topo, sem Spacer antes!
        logo_path = os.path.join(current_app.root_path, 'static', 'images', 'logolacheski.png')
        if os.path.exists(logo_path):
            story.append(Image(logo_path, width=58*mm, height=28*mm, hAlign='CENTER'))
            story.append(Spacer(1, 12 * mm))  # Espaço abaixo da logo
        else:
            story.append(Paragraph("LOGO NÃO ENCONTRADA", styleCentered))
            story.append(Spacer(1, 12 * mm))

        story.append(Paragraph("RECIBO DE HONORÁRIOS ADVOCATÍCIOS", styleTitle))
        story.append(Spacer(1, 10 * mm))
        story.append(Paragraph(textos['principal'], styleBody))
        story.append(Paragraph(textos['fechamento'], styleBody))
        story.append(Spacer(1, 20 * mm))
        story.append(Paragraph(textos['local_data'], styleCentered))
        story.append(Spacer(1, 20 * mm))
        story.append(Paragraph(textos['nome_adv'], styleCenteredBold))
        story.append(Paragraph(textos['oab'], styleCentered))

        doc.build(story)
        pdf_buffer.seek(0)
        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name="recibo_honorarios.pdf",
            mimetype="application/pdf"
        )

    return render_template('recibo.html')