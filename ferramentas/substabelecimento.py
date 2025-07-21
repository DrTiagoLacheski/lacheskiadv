# substabelecimento.py
# Contém a lógica de negócio para a geração de SUBSTABELECIMENTOS.

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

def gerar_substabelecimento_pdf(dados):
    """
    Gera o ficheiro PDF do Substabelecimento.
    Retorna o caminho do ficheiro gerado.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    _header(pdf)
    
    pdf.set_margins(left=25, top=20, right=25)
    pdf.set_font("Times", size=11)
    pdf.ln(25)

    tipo_reserva = dados.get('tipo_reserva')
    if tipo_reserva == 'com_reserva':
        titulo = "SUBSTABELECIMENTO COM RESERVAS DE PODERES"
        texto_poderes = "O substabelecente, já qualificado, vem através deste instrumento, SUBSTABELECER COM RESERVA DE PODERES na pessoa do substabelecido, já qualificado, absolutamente todos os poderes conferidos pelo outorgante, já qualificado, para que o substabelecido possa cumprir e atuar como advogado inerentes da cláusula ad judicia et extra para o foro em geral e praticar todos os demais atos necessários ao fiel desempenho deste mandato."
    else: # sem_reserva
        titulo = "SUBSTABELECIMENTO SEM RESERVAS DE PODERES"
        texto_poderes = "O substabelecente, já qualificado, vem através deste instrumento, SUBSTABELECER SEM RESERVA DE PODERES na pessoa do substabelecido, já qualificado, todos os poderes que lhe foram conferidos pelo outorgante, também qualificado, para que o substabelecido possa cumprir e atuar como advogado inerentes da cláusula ad judicia et extra, o que implica na renúncia ao mandato originalmente conferido, para todos os fins de direito."

    pdf.set_font("Times", 'B', 12)
    pdf.cell(0, 10, titulo, align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(10)

    # --- Partes ---
    pdf.set_font("Times", 'B', 11)
    pdf.cell(0, 5, "SUBSTABELECENTE:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", '', 11)
    advogado = DADOS_ADVOGADOS["TIAGO"]
    texto_substabelecente = (
        f"{advogado['nome']}, brasileiro, casado, advogado, inscrito no CPF sob o n° {advogado['cpf']}, "
        f"RG n° {advogado['rg']}, {advogado['orgao_emissor']}, OAB/PR n° {advogado['oab'][0]}, e OAB/RO n° {advogado['oab'][1]}, "
        f"com endereço profissional situado na {ENDERECO_ADV}."
    )
    pdf.multi_cell(0, 5, texto_substabelecente)
    pdf.ln(5)

    pdf.set_font("Times", 'B', 11)
    pdf.cell(0, 5, "SUBSTABELECIDO:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", '', 11)
    texto_substabelecido_base = (
        f"{dados['nome_substabelecido'].upper()}, brasileiro(a), {dados['estado_civil_substabelecido']}, advogado(a), "
        f"inscrito(a) no CPF sob o n° {_formatar_cpf(dados['cpf_substabelecido'])}"
    )
    if dados.get('rg_substabelecido'):
        texto_substabelecido_base += f", portador(a) do RG n° {dados['rg_substabelecido']}"
    
    texto_substabelecido_final = (
        f", OAB/{dados['oab_uf_substabelecido'].upper()} n° {dados['oab_num_substabelecido']}, "
        f"com endereço profissional na {dados['endereco_substabelecido']}."
    )
    pdf.multi_cell(0, 5, texto_substabelecido_base + texto_substabelecido_final)
    pdf.ln(5)

    pdf.set_font("Times", 'B', 11)
    pdf.cell(0, 5, "OUTORGANTE:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", '', 11)
    texto_outorgante_base = (
        f"{dados['nome_outorgante'].upper()}, brasileiro(a), {dados['estado_civil_outorgante']}, "
        f"inscrito(a) no CPF sob o n° {_formatar_cpf(dados['cpf_outorgante'])}"
    )
    if dados.get('rg_outorgante'):
        texto_outorgante_base += f", portador(a) do RG n° {dados['rg_outorgante']}"

    texto_outorgante_final = f", residente e domiciliado(a) na {dados['endereco_outorgante']}."
    pdf.multi_cell(0, 5, texto_outorgante_base + texto_outorgante_final)
    pdf.ln(10)

    # --- Poderes Transferidos ---
    pdf.set_font("Times", 'B', 11)
    pdf.cell(0, 5, "PODERES TRANSFERIDOS:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", '', 11)
    pdf.multi_cell(0, 5, texto_poderes)
    pdf.ln(10)

    # --- Fechamento e Assinatura ---
    data_atual = datetime.now().strftime("%d de %B de %Y").lower()
    meses = {"january": "janeiro", "february": "fevereiro", "march": "março", "april": "abril", "may": "maio", "june": "junho", "july": "julho", "august": "agosto", "september": "setembro", "october": "outubro", "november": "novembro", "december": "dezembro"}
    for eng, pt in meses.items():
        data_atual = data_atual.replace(eng, pt)
    pdf.cell(0, 5, f"Machadinho D'Oeste - RO, {data_atual}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(20)

    pdf.cell(0, 5, "__________________________________________", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, advogado['nome'], align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, f"OAB/RO n° {advogado['oab'][1]}", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    nome_arquivo = f"Substabelecimento_{dados['nome_outorgante'].replace(' ', '_')}.pdf"
    caminho_arquivo = os.path.join('static/temp', nome_arquivo)
    pdf.output(caminho_arquivo)

    return caminho_arquivo
