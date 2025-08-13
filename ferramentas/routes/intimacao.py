from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime
import locale
from io import BytesIO
import traceback
import logging
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Spacer
from num2words import num2words

def horario_por_extenso(horario):
    horas, minutos = map(int, horario.split(':'))
    horas_ext = num2words(horas, lang='pt_BR')
    if minutos == 0:
        return f"{horas_ext} horas"
    else:
        minutos_ext = num2words(minutos, lang='pt_BR')
        return f"{horas_ext} horas e {minutos_ext} minutos"

# Try to set locale for date formatting (Brazilian Portuguese)
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
    except:
        pass  # Fallback if locale formatting fails

# Register Times New Roman fonts if available
try:
    # Common font locations
    font_files = [
        # Windows
        ("TimesNewRoman", "C:/Windows/Fonts/times.ttf"),
        ("TimesNewRoman-Bold", "C:/Windows/Fonts/timesbd.ttf"),
        ("TimesNewRoman-Italic", "C:/Windows/Fonts/timesi.ttf"),
        ("TimesNewRoman-BoldItalic", "C:/Windows/Fonts/timesbi.ttf"),
        # macOS
        ("TimesNewRoman", "/Library/Fonts/Times New Roman.ttf"),
        ("TimesNewRoman-Bold", "/Library/Fonts/Times New Roman Bold.ttf"),
        ("TimesNewRoman-Italic", "/Library/Fonts/Times New Roman Italic.ttf"),
        ("TimesNewRoman-BoldItalic", "/Library/Fonts/Times New Roman Bold Italic.ttf"),
        # Linux (msttcorefonts)
        ("TimesNewRoman", "/usr/share/fonts/truetype/msttcorefonts/times.ttf"),
        ("TimesNewRoman-Bold", "/usr/share/fonts/truetype/msttcorefonts/timesbd.ttf"),
        ("TimesNewRoman-Italic", "/usr/share/fonts/truetype/msttcorefonts/timesi.ttf"),
        ("TimesNewRoman-BoldItalic", "/usr/share/fonts/truetype/msttcorefonts/timesbi.ttf"),
    ]
    registered = set()
    for font_name, font_path in font_files:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            registered.add(font_name)
    # Register family if at least regular and bold exist
    if "TimesNewRoman" in registered and "TimesNewRoman-Bold" in registered:
        from reportlab.pdfbase.pdfmetrics import registerFontFamily
        registerFontFamily('TimesNewRoman',
                           normal='TimesNewRoman',
                           bold='TimesNewRoman-Bold',
                           italic='TimesNewRoman-Italic' if "TimesNewRoman-Italic" in registered else 'TimesNewRoman',
                           boldItalic='TimesNewRoman-BoldItalic' if "TimesNewRoman-BoldItalic" in registered else 'TimesNewRoman-Bold')
        base_font = 'TimesNewRoman'
        bold_font = 'TimesNewRoman-Bold'
    else:
        base_font = 'Times-Roman'
        bold_font = 'Times-Bold'
except Exception as e:
    base_font = 'Times-Roman'
    bold_font = 'Times-Bold'

intimacao_bp = Blueprint('intimacao', __name__, template_folder='../templates', static_folder='../static')

def header_logo(canvas, doc):
    logo_path = "static/images/logolacheski.png"
    if os.path.exists(logo_path):
        width = 180
        height = 80
        from reportlab.lib.pagesizes import A4
        page_width, page_height = A4
        x = (page_width - width) / 2  # Center horizontally
        y = page_height - height - 10  # 10 pts below the top
        canvas.drawImage(logo_path, x, y, width=width, height=height, preserveAspectRatio=True, mask='auto')

def gerar_pdf_reportlab(
    vara, processo, cliente, testemunha, cpf_testemunha, telefone_testemunha,
    data_audiencia, hora_audiencia, endereco_testemunha=None, oab_escolhida=None
):
    try:
        dt_aud = datetime.strptime(data_audiencia, "%Y-%m-%d")
        data_aud_texto = dt_aud.strftime("%d/%m/%Y")
    except Exception:
        data_aud_texto = data_audiencia

    try:
        hr_aud = datetime.strptime(hora_audiencia, "%H:%M")
        hora_aud_texto = hr_aud.strftime("%H:%M")
    except Exception:
        hora_aud_texto = hora_audiencia

    hoje = datetime.now()
    try:
        data_hoje = hoje.strftime("%d de %B de %Y").lower()
    except:
        meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
        data_hoje = f"{hoje.day} de {meses[hoje.month - 1]} de {hoje.year}"

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=28.35 * 2.5, leftMargin= 28.35 * 2.5,
                            topMargin=100, bottomMargin=72)

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        'TituloCentral',
        parent=styles['Heading1'],
        fontName=bold_font,
        alignment=TA_CENTER,
        fontSize=15,
        leading=24,
        spaceAfter=18
    )
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontName=base_font,
        alignment=TA_JUSTIFY,
        fontSize=12,
        leading=18,
        spaceAfter=18
    )
    bold_style = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontName=bold_font,
        alignment=TA_JUSTIFY,
        fontSize=12,
        leading=18,
        spaceAfter=18
    )
    center_style = ParagraphStyle(
        'Center',
        parent=styles['Normal'],
        fontName=base_font,
        alignment=TA_CENTER,
        fontSize=12,
        leading=18,
        spaceAfter=18
    )
    bold_center_style = ParagraphStyle(
        'BoldCenter',
        parent=styles['Normal'],
        fontName=bold_font,
        alignment=TA_CENTER,
        fontSize=12,
        leading=18,
        spaceAfter=18
    )
    assinatura_style = ParagraphStyle(
        'Assinatura',
        parent=styles['Normal'],
        fontName=bold_font,
        alignment=TA_CENTER,
        fontSize=12,
        leading=18,
        spaceBefore=24
    )

    story = []

    # NÃO adicione o logo aqui! Ele será desenhado pelo header_logo

    # Title
    story.append(Paragraph(f"RESPEITÁVEL JUÍZO DA {vara.upper()}", titulo_style))
    story.append(Spacer(1, 24))
    story.append(Paragraph(f"Autos de n° {processo}", bold_style))
    story.append(Spacer(1, 24))

    # Cliente
    story.append(Paragraph(
        f"<b>{cliente.upper()}</b>, já devidamente qualificado nos autos em epígrafe, vem, por intermédio de seus advogados subscritos, respeitosamente perante Vossa Excelência, com fulcro no §3º do art. 852-H da Consolidação das Leis do Trabalho, requerer a",
        normal_style))
    story.append(Spacer(1, 12))

    # Document type
    story.append(Paragraph("INTIMAÇÃO PESSOAL DE TESTEMUNHA", bold_center_style))
    story.append(Paragraph("pelos motivos de fato e de direito a seguir aduzidos.", normal_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("DA NEGATIVA DA TESTEMUNHA", bold_center_style))
    story.append(Paragraph(
        f"A parte Reclamante ponderou inicialmente que o depoimento pessoal da sr(a) <b>{testemunha.upper()}</b>, inscrito(a) no CPF sob o no {cpf_testemunha}, seria realizado de livre e espontânea vontade. "
        f"Entretanto, conforme se pode extrair do print de tela obtido do aplicativo WhatsApp anexo (documento único), a mesma não está disposta a participar da audiência.",
        normal_style))
    story.append(Paragraph(
        "Ocorre que, nos termos do art. 852-H da CLT, a testemunha é obrigada a depor, independentemente de sua vontade pessoal. Não comparecendo quando intimada, o juiz pode, inclusive, determinar sua condução coercitiva – neste caso, além do pagamento de multa, se sujeita ainda a responder pelo crime de desobediência, conforme preceitua os arts. 218 e 219 do Código de Processo Penal.",
        normal_style))
    story.append(Paragraph(
        "Considera-se indispensável este depoimento em razão de ambos, Reclamante e testemunha, terem trabalhado juntos à época em que vigorou o pacto laboral objeto da presente Reclamação, cumprindo a mesma carga horária, na mesma equipe.",
        normal_style))
    story.append(Spacer(1, 18))
    story.append(Paragraph("DOS PEDIDOS", bold_center_style))
    story.append(Paragraph(
        "Ante o exposto, requer a Vossa Excelência o acolhimento do presente requerimento para:",
        normal_style))

    h = horario_por_extenso(hora_aud_texto)
    texto_testemunha = (
        f"i. Que seja intimada a testemunha, <b>{testemunha.upper()}</b>, inscrito(a) no CPF sob o no {cpf_testemunha}"
    )
    if endereco_testemunha:
        texto_testemunha += f", residente e domiciliado(a) em {endereco_testemunha}"
    texto_testemunha += (
        f", podendo ser notificada através do seu telefone/WhatsApp {telefone_testemunha}, para comparecer na audiência designada para o dia {data_aud_texto}, às {hora_aud_texto} ({h});"
    )
    story.append(Paragraph(texto_testemunha, normal_style))

    story.append(Paragraph(
        "ii. Que seja a testemunha devidamente instruída que o seu comparecimento é obrigatório, e sua falta injustificada resultará em sua condução coercitiva, além de responsabilização penal pelo crime de desobediência.",
        normal_style))

    story.append(Spacer(1, 24))
    story.append(Paragraph("Termos em que,", bold_style))
    story.append(Paragraph("Pede o deferimento.", bold_style))
    story.append(Paragraph(f"Machadinho Do Oeste, {data_hoje}.", bold_style))

    # Assinatura dinâmica com escolha da OAB
    adv_principal = current_user.get_advogado_principal()
    if adv_principal:
        nome_adv = adv_principal.nome
        if oab_escolhida:
            assinatura = f"{nome_adv}<br/>OAB {oab_escolhida}"
        else:
            oabs = adv_principal.oabs if adv_principal.oabs else []
            oabs_str = " / ".join(
                [f"OAB {oab['numero']}" if isinstance(oab, dict) and 'numero' in oab else str(oab) for oab in oabs]
            )
            assinatura = f"{nome_adv}"
            if oabs_str:
                assinatura += f"<br/>{oabs_str}"
    else:
        assinatura = "Advogado não cadastrado"

    story.append(Paragraph(assinatura, assinatura_style))

    doc.build(story, onFirstPage=header_logo, onLaterPages=header_logo)
    buffer.seek(0)
    return buffer

def gerar_html_text(
    vara, processo, cliente, testemunha, cpf_testemunha, telefone_testemunha,
    data_audiencia, hora_audiencia, endereco_testemunha=None, oab_escolhida=None
):
    try:
        dt_aud = datetime.strptime(data_audiencia, "%Y-%m-%d")
        data_aud_texto = dt_aud.strftime("%d/%m/%Y")
    except Exception:
        data_aud_texto = data_audiencia

    try:
        hr_aud = datetime.strptime(hora_audiencia, "%H:%M")
        hora_aud_texto = hr_aud.strftime("%H:%M")
    except Exception:
        hora_aud_texto = hora_audiencia

    hoje = datetime.now()
    try:
        data_hoje = hoje.strftime("%d de %B de %Y").lower()
    except:
        meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                 "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
        data_hoje = f"{hoje.day} de {meses[hoje.month - 1]} de {hoje.year}"

    texto_testemunha = (
        f"i. Que seja intimada a testemunha, <b>{testemunha.upper()}</b>, inscrito(a) no CPF sob o no <b>{cpf_testemunha}</b>"
    )
    if endereco_testemunha:
        texto_testemunha += f", residente e domiciliado(a) em <b>{endereco_testemunha}</b>"
    texto_testemunha += (
        f", podendo ser notificada através do seu telefone/WhatsApp <b>{telefone_testemunha}</b>, para comparecer na audiência designada para o dia <b>{data_aud_texto}</b>, às <b>{hora_aud_texto}</b>;"
    )

    # Assinatura dinâmica com escolha da OAB (HTML)
    adv_principal = current_user.get_advogado_principal()
    if adv_principal:
        nome_adv = adv_principal.nome
        if oab_escolhida:
            assinatura = f"{nome_adv}<br>OAB {oab_escolhida}"
        else:
            oabs = adv_principal.oabs if adv_principal.oabs else []
            oabs_str = " / ".join(
                [f"OAB {oab['numero']}" if isinstance(oab, dict) and 'numero' in oab else str(oab) for oab in oabs]
            )
            assinatura = f"{nome_adv}"
            if oabs_str:
                assinatura += f"<br>{oabs_str}"
    else:
        assinatura = "Advogado não cadastrado"

    html = f"""
<div style="font-family: 'Times New Roman', Times, serif; font-size: 12pt; line-height:1.5;">
    <div style="text-align: center; font-weight: bold; font-size: 15pt; margin-bottom: 18pt;">
        <b>RESPEITÁVEL JUÍZO DA {vara.upper()}</b>
    </div>
    <p><b>Autos de n° {processo}</b></p>
    <p><b>{cliente.upper()}</b>, já devidamente qualificado nos autos em epígrafe, vem, por intermédio de seus advogados subscritos, respeitosamente perante Vossa Excelência, com fulcro no §3º do art. 852-H da Consolidação das Leis do Trabalho, requerer a</p>
    <p style="text-align:center"><b>INTIMAÇÃO PESSOAL DE TESTEMUNHA</b></p>
    <p>pelos motivos de fato e de direito a seguir aduzidos.</p>
    <p style="text-align:center"><b>DA NEGATIVA DA TESTEMUNHA</b></p>
    <p>
        A parte Reclamante ponderou inicialmente que o depoimento pessoal da sr(a) <b>{testemunha.upper()}</b>, inscrito(a) no CPF sob o no <b>{cpf_testemunha}</b>, seria realizado de livre e espontânea vontade. 
        Entretanto, conforme se pode extrair do print de tela obtido do aplicativo WhatsApp anexo (documento único), a mesma não está disposta a participar da audiência.
    </p>
    <p>
        Ocorre que, nos termos do art. 852-H da CLT, a testemunha é obrigada a depor, independentemente de sua vontade pessoal. Não comparecendo quando intimada, o juiz pode, inclusive, determinar sua condução coercitiva – neste caso, além do pagamento de multa, se sujeita ainda a responder pelo crime de desobediência, conforme preceitua os arts. 218 e 219 do Código de Processo Penal.
    </p>
    <p>
        Considera-se indispensável este depoimento em razão de ambos, Reclamante e testemunha, terem trabalhado juntos à época em que vigorou o pacto laboral objeto da presente Reclamação, cumprindo a mesma carga horária, na mesma equipe.
    </p>
    <p><b>DOS PEDIDOS</b></p>
    <p>
        Ante o exposto, requer a Vossa Excelência o acolhimento do presente requerimento para:
    </p>
    <p>
        {texto_testemunha}
    </p>
    <p>
        ii. Que seja a testemunha devidamente instruída que o seu comparecimento é obrigatório, e sua falta injustificada resultará em sua condução coercitiva, além de responsabilização penal pelo crime de desobediência.
    </p>
    <p>Termos em que,</p>
    <p>Pede o deferimento.</p>
    <p>Machadinho Do Oeste, {data_hoje}.</p>
    <p style="margin-top: 24pt; font-weight: bold;">
        {assinatura}
    </p>
</div>
""".strip()
    return html

@intimacao_bp.route("/intimacao", methods=["GET", "POST"])
@login_required
def pagina_intimacao():
    if request.method == "POST":
        try:
            data = request.get_json() if request.is_json else request.form

            vara = data.get("vara", "").strip()
            processo = data.get("processo", "").strip()
            cliente = data.get("cliente", "").strip()
            testemunha = data.get("testemunha", "").strip()
            cpf_testemunha = data.get("cpf_testemunha", "").strip()
            telefone_testemunha = data.get("telefone_testemunha", "").strip()
            endereco_testemunha = data.get("endereco_testemunha", "").strip() if "endereco_testemunha" in data else ""
            data_audiencia = data.get("data_audiencia", "").strip()
            hora_audiencia = data.get("hora_audiencia", "").strip()
            oab_escolhida = data.get("oab_escolhida", "").strip() if "oab_escolhida" in data else ""
            gerar_pdf = data.get("gerar_pdf", False) in (["true", "True", True, 1, "1"])

            if not vara or not processo or not cliente or not testemunha or not cpf_testemunha or not telefone_testemunha or not data_audiencia or not hora_audiencia:
                return jsonify({"success": False, "error": "Preencha todos os campos obrigatórios."}), 400

            if gerar_pdf:
                try:
                    pdf_io = gerar_pdf_reportlab(
                        vara, processo, cliente, testemunha, cpf_testemunha,
                        telefone_testemunha, data_audiencia, hora_audiencia,
                        endereco_testemunha, oab_escolhida
                    )

                    return send_file(
                        pdf_io,
                        as_attachment=True,
                        download_name="intimacao_testemunha.pdf",
                        mimetype='application/pdf'
                    )
                except Exception as e:
                    logging.error(f"PDF generation error: {str(e)}")
                    logging.error(traceback.format_exc())
                    return jsonify({"success": False, "error": f"Erro ao gerar PDF: {str(e)}"}), 500

            html = gerar_html_text(
                vara, processo, cliente, testemunha, cpf_testemunha,
                telefone_testemunha, data_audiencia, hora_audiencia,
                endereco_testemunha, oab_escolhida
            )
            return jsonify({"success": True, "texto": html})

        except Exception as e:
            logging.error(f"General error: {str(e)}")
            logging.error(traceback.format_exc())
            return jsonify({"success": False, "error": f"Erro no processamento: {str(e)}"}), 500

    # GET: Carregar OABs para escolha
    adv_principal = None
    oabs = []
    try:
        adv_principal = current_user.get_advogado_principal()
        if adv_principal and adv_principal.oabs:
            oabs = adv_principal.oabs
    except Exception:
        oabs = []
    return render_template("pagina_intimacao.html", oabs=oabs)