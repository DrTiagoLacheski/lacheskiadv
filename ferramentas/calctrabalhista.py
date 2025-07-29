from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Frame, Table, TableStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
import os
from datetime import datetime
import locale
from PIL import Image
from flask import current_app

# --- CONFIGURAÇÕES GLOBAIS ---
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')

FOOTER_MARGIN = 30 * mm


# --- FUNÇÕES AUXILIARES DE FORMATAÇÃO ---
def _formatar_data(data_str):
    if not data_str: return "Não informado"
    try:
        return datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return data_str


def _formatar_moeda(valor_str):
    if not valor_str: return "Não informado"
    try:
        valor = float(str(valor_str).replace('R$', '').strip().replace('.', '').replace(',', '.'))
        return locale.currency(valor, symbol=True, grouping=True)
    except (ValueError, TypeError):
        return valor_str


def _formatar_texto(texto):
    if not texto: return "Não informado"
    return str(texto).replace('_', ' ').capitalize()


# --- FUNÇÕES DE DESENHO NO PDF ---

def _draw_header(c, width, height):
    logo_margin_top = 15 * mm
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'logolacheski.png')
    logo_height = 0
    if os.path.exists(logo_path):
        img = ImageReader(logo_path)
        img_width, img_height = img.getSize()
        max_logo_width = 50 * mm
        scale = max_logo_width / img_width
        logo_draw_width = max_logo_width
        logo_draw_height = img_height * scale
        x = (width - logo_draw_width) / 2
        y = height - logo_draw_height - logo_margin_top
        c.drawImage(
            logo_path,
            x, y,
            width=logo_draw_width,
            height=logo_draw_height,
            preserveAspectRatio=True,
            mask='auto'
        )
        logo_height = logo_draw_height + logo_margin_top
    else:
        logo_height = 30 * mm  # fallback se não houver logo

    c.setLineWidth(0.5)
    c.line(20 * mm, height - logo_height - 5 * mm, width - 20 * mm, height - logo_height - 5 * mm)
    return logo_height + 10 * mm  # altura total ocupada pelo cabeçalho



def _draw_footer(c, width):
    data_geracao = datetime.now().strftime("Gerado em %d de %B de %Y")
    c.saveState()
    c.setFont('Times-Italic', 8)
    c.setFillColor(colors.HexColor('#666666'))
    c.drawCentredString(width / 2, 20 * mm, data_geracao)
    c.drawCentredString(width / 2, 15 * mm, "Este é um documento preliminar e confidencial.")
    c.restoreState()


def _handle_page_break(c, y_pos, required_height):
    if y_pos - required_height < FOOTER_MARGIN:
        c.showPage()
        _draw_header(c, c._pagesize[0], c._pagesize[1])
        return c._pagesize[1] - 50 * mm
    return y_pos


def _adicionar_secao_rl(c, titulo, conteudo_dict, y_start):
    width = 170 * mm
    x_pos = 20 * mm

    style_title = ParagraphStyle('title', fontName='Times-Bold', fontSize=11, spaceAfter=6,
                                 textColor=colors.HexColor('#FFFFFF'), leading=14, backColor=colors.HexColor('#34495e'),
                                 paddingLeft=10, paddingTop=4, paddingBottom=4, borderRadius=3)
    style_label = ParagraphStyle('label', fontName='Times-Bold', fontSize=10, textColor=colors.HexColor('#2c3e50'))
    style_value = ParagraphStyle('value', fontName='Times-Roman', fontSize=10, textColor=colors.HexColor('#333333'))

    p_title = Paragraph(titulo, style_title)
    w_title, h_title = p_title.wrapOn(c, width, y_start)

    data = []
    if conteudo_dict:
        for label, value in conteudo_dict.items():
            if value:
                p_label = Paragraph(f"{label}:", style_label)
                p_value = Paragraph(str(value), style_value)
                data.append([p_label, p_value])

    table = Table(data, colWidths=[55 * mm, (width - 55 * mm)]) if data else None
    h_table = 0
    if table:
        table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
        w_table, h_table = table.wrapOn(c, width, y_start)

    total_height = h_title + h_table + 10 * mm
    y_pos = _handle_page_break(c, y_start, total_height)

    p_title.drawOn(c, x_pos, y_pos)
    y_pos -= (h_title + 2 * mm)

    if table:
        table.drawOn(c, x_pos, y_pos - h_table)
        y_pos -= h_table

    return y_pos - (6 * mm)


def _adicionar_secao_jornada_completa_rl(c, dados, y_start):
    width = 170 * mm
    x_pos = 20 * mm

    style_title = ParagraphStyle('title', fontName='Times-Bold', fontSize=11, spaceAfter=6,
                                 textColor=colors.HexColor('#FFFFFF'), leading=14, backColor=colors.HexColor('#34495e'),
                                 paddingLeft=10, paddingTop=4, paddingBottom=4, borderRadius=3)
    style_subtitle = ParagraphStyle('subtitle', fontName='Times-Roman', fontSize=10, spaceAfter=8,
                                    textColor=colors.HexColor('#333'))

    p_title = Paragraph("7. JORNADA DE TRABALHO E HORAS EXTRAS", style_title)
    w_title, h_title = p_title.wrapOn(c, width, y_start)

    regime_contratado = _formatar_texto(dados.get('regime_jornada'))
    p_regime = Paragraph(f"<b>Regime Contratado:</b> {regime_contratado}", style_subtitle)
    w_regime, h_regime = p_regime.wrapOn(c, width, y_start)

    h_conteudo = h_regime
    table = None
    p_info = None

    if dados.get('hora_extra') == 'sim':
        dias_semana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo']
        dia_map = {'segunda': 'Segunda', 'terca': 'Terça', 'quarta': 'Quarta', 'quinta': 'Quinta', 'sexta': 'Sexta',
                   'sabado': 'Sábado', 'domingo': 'Domingo'}
        dados_jornada = []
        for dia in dias_semana:
            if dados.get(f'dia_ativo_{dia}'):
                dados_jornada.append([dia_map[dia], dados.get(f'inicio_expediente_{dia}', '---'),
                                      dados.get(f'inicio_intervalo_{dia}', '---'),
                                      dados.get(f'fim_intervalo_{dia}', '---'),
                                      dados.get(f'fim_expediente_{dia}', '---'),
                                      dados.get(f'horas_extra_{dia}', '0.00')])

        if dados_jornada:
            header = [['Dia', 'Início', 'Pausa In.', 'Pausa Fim', 'Fim Exp.', 'H. Extras']]
            table = Table(header + dados_jornada, colWidths=[25 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm, 25 * mm],
                          repeatRows=1)
            table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e0e0')),
                                       ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#333')),
                                       ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                       ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
                                       ('FONTNAME', (0, 1), (-1, -1), 'Times-Roman'), ('FONTSIZE', (0, 0), (-1, -1), 9),
                                       ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]))
            w, h_table = table.wrapOn(c, width, y_start)
            h_conteudo += h_table
        else:
            p_info = Paragraph("<b>Horas Extras:</b> Nenhuma jornada detalhada foi informada.", style_subtitle)
            w_info, h_info = p_info.wrapOn(c, width, y_start)
            h_conteudo += h_info
    else:
        p_info = Paragraph("<b>Horas Extras:</b> Conforme informado, não havia realização de horas extras.",
                           style_subtitle)
        w_info, h_info = p_info.wrapOn(c, width, y_start)
        h_conteudo += h_info

    total_height = h_title + h_conteudo + 10 * mm
    y_pos = _handle_page_break(c, y_start, total_height)

    p_title.drawOn(c, x_pos, y_pos)
    y_pos -= (h_title + 4 * mm)

    p_regime.drawOn(c, x_pos, y_pos)
    y_pos -= h_regime

    if table:
        table.drawOn(c, x_pos, y_pos - h_table)
        y_pos -= h_table
    elif p_info:
        p_info.drawOn(c, x_pos, y_pos - h_info)
        y_pos -= h_info

    return y_pos - (6 * mm)


def _adicionar_aviso_legal(c, y_start):
    width = 170 * mm
    x_pos = 20 * mm
    aviso = (
        "<b>AVISO IMPORTANTE:</b> Este é um relatório preliminar gerado com base nas informações fornecidas pelo cliente. "
        "Os valores e direitos aqui apresentados são estimativas e estão sujeitos a confirmação através de "
        "análise documental e cálculos detalhados por um profissional. Este documento não substitui uma "
        "consulta jurídica completa nem constitui um parecer técnico final.")

    style = ParagraphStyle('aviso', fontName='Times-Italic', fontSize=9, alignment=TA_JUSTIFY,
                           textColor=colors.HexColor('#444444'), leading=12)
    p_aviso = Paragraph(aviso, style)
    w, h = p_aviso.wrapOn(c, width, y_start)

    y_pos = _handle_page_break(c, y_start, h + 8 * mm)
    p_aviso.drawOn(c, x_pos, y_pos - h)

    return y_pos - h - (8 * mm)


def _adicionar_secao_feriados_domingos(c, dados, y_start):
    width = 170 * mm
    x_pos = 20 * mm

    style_title = ParagraphStyle('title', fontName='Times-Bold', fontSize=11, spaceAfter=6,
                                 textColor=colors.HexColor('#FFFFFF'), leading=14, backColor=colors.HexColor('#34495e'),
                                 paddingLeft=10, paddingTop=4, paddingBottom=4, borderRadius=3)
    style_label = ParagraphStyle('label', fontName='Times-Bold', fontSize=10, textColor=colors.HexColor('#2c3e50'))
    style_value = ParagraphStyle('value', fontName='Times-Roman', fontSize=10, textColor=colors.HexColor('#333333'))

    p_title = Paragraph("8. FERIADOS E DOMINGOS TRABALHADOS", style_title)
    w_title, h_title = p_title.wrapOn(c, width, y_start)

    datas = dados.get('datas_feriados_domingos[]') or []
    horas = dados.get('horas_feriado_domingo[]') or []
    tipos = dados.get('tipo_feriado_domingo[]') or []

    # Garante que são listas
    if isinstance(datas, str):
        datas = [datas]
    if isinstance(horas, str):
        horas = [horas]
    if isinstance(tipos, str):
        tipos = [tipos]

    data = []
    for i, data_feriado in enumerate(datas):
        hora = horas[i] if i < len(horas) else ''
        tipo = tipos[i] if i < len(tipos) else ''
        label = f"Data: {_formatar_data(data_feriado)} ({tipo})"
        value = f"Horas: {hora}"
        data.append([Paragraph(label, style_label), Paragraph(value, style_value)])

    table = Table(data, colWidths=[70 * mm, (width - 70 * mm)]) if data else None
    h_table = 0
    if table:
        table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
        w_table, h_table = table.wrapOn(c, width, y_start)

    total_height = h_title + h_table + 10 * mm
    y_pos = _handle_page_break(c, y_start, total_height)

    p_title.drawOn(c, x_pos, y_pos)
    y_pos -= (h_title + 2 * mm)

    if table:
        table.drawOn(c, x_pos, y_pos - h_table)
        y_pos -= h_table

    return y_pos - (6 * mm)


# --- FUNÇÃO PRINCIPAL ---
def gerar_relatorio_trabalhista_pdf(dados):
    os.makedirs('static/temp', exist_ok=True)
    nome_arquivo = f"Relatorio_Trabalhista_{dados.get('nome_reclamante', 'cliente').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    caminho_arquivo = os.path.join('static/temp', nome_arquivo)

    c = canvas.Canvas(caminho_arquivo, pagesize=A4)
    width, height = A4

    header_height = _draw_header(c, width, height)
    y = height - header_height  # agora o conteúdo começa após a logo

    c.setFont("Times-Bold", 16)
    c.drawCentredString(width / 2, y, "RELATÓRIO TRABALHISTA PRELIMINAR")
    y -= (5 * mm)

    y = _adicionar_secao_rl(c, "1. DADOS DO RECLAMANTE", {
        "Nome": dados.get('nome_reclamante'), "CPF": dados.get('cpf_reclamante'),
        "RG": dados.get('rg_reclamante'), "Estado Civil": dados.get('estado_civil'),
        "Endereço": dados.get('endereco_reclamante')
    }, y)

    y = _adicionar_secao_rl(c, "2. EMPRESA RECLAMADA", {
        "Nome da Empresa": dados.get('nome_empresa'), "CNPJ": dados.get('cnpj_empresa')
    }, y)

    y = _adicionar_secao_rl(c, "3. DETALHES DO CONTRATO", {
        "Função Exercida": dados.get('funcao_exercida'),
        "Data de Início": _formatar_data(dados.get('data_inicio')),
        "Data de Término": _formatar_data(dados.get('data_termino')),
        "Registro em CTPS": _formatar_texto(dados.get('registro_ctps')),
        "Insalubridade": dados.get('insalubridade'), "Periculosidade": dados.get('periculosidade')
    }, y)

    y = _adicionar_secao_rl(c, "4. REMUNERAÇÃO", {
        "Remuneração Formal": _formatar_moeda(dados.get('remuneracao')),
        "Recebia Remuneração Informal?": _formatar_texto(dados.get('remuneracao_informal')),
        "Tipo de Remuneração Informal": dados.get('remuneracao_informal_tipo'),
        "Valor da Remuneração Informal": _formatar_moeda(dados.get('remuneracao_informal_valor'))
    }, y)

    y = _adicionar_secao_rl(c, "5. MOTIVO DA RESCISÃO", {
        "Natureza da Demissão": _formatar_texto(dados.get('natureza_demissao')),
        "Aplicação do Art. 477 da CLT": _formatar_texto(dados.get('aplica_art_477'))
    }, y)

    y = _adicionar_secao_rl(c, "6. VERBAS TRABALHISTAS", {
        "Depósitos de FGTS": _formatar_texto(dados.get('depositos_fgts')),
        "Férias Vencidas": _formatar_texto(dados.get('ferias_vencidas')),
        "Período de Férias Vencidas": dados.get('periodo_ferias_vencidas', '---')
    }, y)

    y = _adicionar_secao_jornada_completa_rl(c, dados, y)

    if dados.get('feriados_domingos') == 'sim':
        y = _adicionar_secao_feriados_domingos(c, dados, y)

    y = _adicionar_aviso_legal(c, y)

    _draw_footer(c, width)

    c.save()
    return caminho_arquivo