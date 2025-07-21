# procuracao.py
# Contém a lógica de negócio para a geração de PROCURAÇÕES.

import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
from config import DADOS_ADVOGADOS, ENDERECO_ADV

def _header(pdf):
    """Função auxiliar para adicionar o cabeçalho com a logo ao PDF."""
    logo_width = 60
    page_width = pdf.w
    x_pos = (page_width - logo_width) / 2
    logo_path = 'static/images/logolacheski.png'
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=x_pos, y=8, w=logo_width)
    else:
        print(f"AVISO: Ficheiro de logo não encontrado em '{logo_path}'")

def _formatar_cpf(cpf_num):
    """Função auxiliar para formatar o número do CPF."""
    cpf_num = ''.join(filter(str.isdigit, cpf_num))
    if len(cpf_num) != 11:
        return cpf_num
    return f"{cpf_num[:3]}.{cpf_num[3:6]}.{cpf_num[6:9]}-{cpf_num[9:]}"

def gerar_procuracao_pdf(dados_cliente):
    """
    Gera o ficheiro PDF da procuração com base nos dados do cliente.
    Retorna o caminho do ficheiro gerado.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    _header(pdf)
    
    pdf.set_margins(left=30, top=30, right=20)
    pdf.set_font("Times", size=12)
    pdf.ln(20)

    # Outorgante
    pdf.set_font("Times", 'B', 12)
    pdf.cell(0, 7, "OUTORGANTE:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", size=12)

    # Construção do texto do outorgante com RG opcional
    texto_outorgante_base = (
        f"{dados_cliente['nome_completo'].upper()}, brasileiro(a), {dados_cliente['estado_civil']}, "
        f"{dados_cliente['profissao']}, devidamente inscrito(a) no CPF n.º {_formatar_cpf(dados_cliente['cpf'])}"
    )
    
    if dados_cliente.get('rg'):
        texto_outorgante_base += f", portador(a) do RG n.º {dados_cliente['rg']}"

    texto_outorgante_final = f", residente e domiciliado(a) à {dados_cliente['endereco']}"
    texto_outorgante = texto_outorgante_base + texto_outorgante_final

    pdf.set_x(37.5)
    pdf.multi_cell(0, 7, texto_outorgante)
    pdf.ln(5)

    # Outorgado
    pdf.set_font("Times", 'B', 12)
    pdf.cell(0, 7, "OUTORGADO:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", size=12)
    advogado = DADOS_ADVOGADOS["TIAGO"]
    partes = [
        f"{advogado['nome']}", "brasileiro, casado", advogado["profissao"],
        f"inscrito no CPF sob o n.º {advogado['cpf']}",
        f"RG n.º {advogado['rg']}, {advogado['orgao_emissor']}",
        f"OAB/PR n.º {advogado['oab'][0]}, e OAB/RO n.º {advogado['oab'][1]}"
    ]
    texto_outorgado = ", ".join(partes) + f", com endereço profissional situado na {ENDERECO_ADV}."
    pdf.set_x(37.5)
    pdf.multi_cell(0, 7, texto_outorgado)
    pdf.ln(5)

    # Poderes
    pdf.set_font("Times", 'B', 12)
    pdf.cell(0, 7, "PROCURAÇÃO GERAL:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", size=12)
    poderes = "O outorgante nomeia os outorgados seus procuradores, concedendo-lhes os poderes inerentes da cláusula ad judicia et extra para o foro em geral, podendo promover quaisquer medidas judiciais ou administrativas, oferecer defesa, interpor recursos, ajuizar ações e conduzir os respectivos processos, solicitar, providenciar e ter acesso a documentos de qualquer natureza, sendo o presente instrumento de mandato oneroso e contratual, podendo substabelecer este a outrem, com ou sem reserva de poderes, a fim de praticar todos os demais atos necessários ao fiel desempenho deste mandato, além de reconhecer a procedência do pedido, transigir, desistir, renunciar ao direito sobre o qual se funda a ação, receber, dar quitação, firmar compromisso e assinar declaração de hipossuficiência econômica."
    pdf.set_x(37.5)
    pdf.multi_cell(0, 7, poderes)
    pdf.ln(10)

    # Data e assinatura
    data_atual = datetime.now().strftime("%d de %B de %Y").lower()
    meses = {
        "january": "janeiro", "february": "fevereiro", "march": "março",
        "april": "abril", "may": "maio", "june": "junho",
        "july": "julho", "august": "agosto", "september": "setembro",
        "october": "outubro", "november": "novembro", "december": "dezembro"
    }
    for eng, pt in meses.items():
        data_atual = data_atual.replace(eng, pt)
    pdf.set_font("Times", size=12)
    pdf.cell(0, 7, f"Machadinho D'Oeste, {data_atual}.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(15)
    pdf.cell(0, 7, "___________________________", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.cell(0, 7, "OUTORGANTE", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    # Salva o ficheiro temporário
    nome_arquivo = f"Procuracao_{dados_cliente['nome_completo'].replace(' ', '_')}.pdf"
    caminho_arquivo = os.path.join('static/temp', nome_arquivo)
    pdf.output(caminho_arquivo)

    return caminho_arquivo
