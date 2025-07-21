# contratos.py
# Contém a lógica de negócio para a geração de CONTRATOS DE HONORÁRIOS.

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

def gerar_contrato_honorarios_pdf(dados):
    """
    Gera o ficheiro PDF do Contrato de Honorários.
    Retorna o caminho do ficheiro gerado.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    _header(pdf)
    
    pdf.set_margins(left=25, top=20, right=25)
    
    pdf.set_font("Times", size=10)
    
    pdf.ln(25) 

    # --- Partes do Contrato ---
    pdf.set_font("Times", 'B', 10)
    pdf.cell(0, 5, "CONTRATANTE:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", '', 10)
    
    # ATUALIZAÇÃO: O texto do RG agora é condicional.
    texto_base = (
        f"{dados['nome_completo'].upper()}, brasileiro(a), {dados['estado_civil']}, "
        f"inscrito no CPF sob o n° {_formatar_cpf(dados['cpf'])}"
    )
    
    # Adiciona o RG apenas se ele foi fornecido.
    if dados.get('rg'):
        texto_base += f", portador do RG N° {dados['rg']}"

    texto_final = f", residente e domiciliado na {dados['endereco']}."
    
    texto_contratante = texto_base + texto_final
    
    pdf.multi_cell(0, 5, texto_contratante, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    advogado = DADOS_ADVOGADOS["TIAGO"]
    pdf.set_font("Times", 'B', 10)
    pdf.cell(0, 5, "CONTRATADO:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Times", '', 10)
    texto_contratado = (
        f"{advogado['nome']}, brasileiro, casado, advogado, inscrito no CPF sob o n° {advogado['cpf']}, "
        f"RG n° {advogado['rg']}, {advogado['orgao_emissor']}, OAB/PR n° {advogado['oab'][0]}, e OAB/RO n° {advogado['oab'][1]}, "
        f"com endereço profissional situado na {ENDERECO_ADV}."
    )
    pdf.multi_cell(0, 5, texto_contratado, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(5)

    # --- Cláusulas ---
    clausula_1 = (
        f"1 - O presente contrato tem por objeto a prestação de serviços de advocacia, por parte do Advogado "
        f"contratado, para o fim especial {dados['objeto_contrato']}."
    )
    pdf.multi_cell(0, 5, clausula_1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    clausula_2 = (
        "2 - Em caso de indeferimento ou inviabilidade da justiça gratuita, as custas e demais despesas "
        "judiciais e extrajudiciais correrão por conta exclusiva do(a) contratante. O(A) contratante "
        "obriga-se, ainda, a fornecer as informações e os documentos necessários ao ajuizamento da ação, "
        "bem como outros que porventura venham a ser necessários no curso dos mesmos."
    )
    pdf.multi_cell(0, 5, clausula_2, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    clausula_3 = (
        "3 - Os honorários profissionais devidos pelo contratante a favor do advogado contratado, corresponderão a "
        f"{dados['condicoes_honorarios']}"
    )
    pdf.multi_cell(0, 5, clausula_3, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    
    clausula_4 = (
        "4 - Os honorários serão devidos também na hipótese de haver acordo das partes; e/ou se obter êxito em "
        "resolver administrativamente e independente da propositura da ação. Considerar-se-ão vencidos e "
        "imediatamente exigíveis os honorários ora contratados, no caso de o CONTRATANTE vir a revogar ou "
        "cassar o mandato outorgado ao CONTRATADO ou a exigir o substabelecimento sem reservas, sem que este "
        "tenha, para isso, dado causa. Nesta hipótese, os honorários serão calculados pelo valor da causa, ou, "
        "caso publicada sentença ou acórdão, pelo valor da condenação, ou, ainda, acaso liquidado o processo, "
        "pelo valor arbitrado em sentença de liquidação."
    )
    pdf.multi_cell(0, 5, clausula_4, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)

    clausula_5 = (
        "5 - O contratado não se compromete a recorrer e buscar o duplo grau de jurisdição, se reserva ao "
        "direito de não recorrer da sentença ou acórdão, sem prévio aviso ao cliente, se este for o seu "
        "entendimento jurídico. Quando entender que não há possibilidade de reversão ou não preenche os "
        "requisitos para apreciação de legalidade por instância superior, já que esta não analisa questões de mérito."
    )
    pdf.multi_cell(0, 5, clausula_5, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    # --- Fechamento e Assinaturas ---
    fechamento = (
        "E, por assim estarem justos e contratados, assinam o presente em 02 (duas) vias, para um só efeito, "
        "na presença das testemunhas abaixo, elegendo o foro da Comarca de Machadinho Do Oeste - RO, para "
        "dirimir quaisquer dúvidas resultantes deste contrato."
    )
    pdf.multi_cell(0, 5, fechamento, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    data_atual = datetime.now().strftime("%d de %B de %Y").lower()
    meses = {
        "january": "janeiro", "february": "fevereiro", "march": "março", "april": "abril", 
        "may": "maio", "june": "junho", "july": "julho", "august": "agosto", 
        "september": "setembro", "october": "outubro", "november": "novembro", "december": "dezembro"
    }
    for eng, pt in meses.items():
        data_atual = data_atual.replace(eng, pt)
    pdf.cell(0, 5, f"Machadinho D'Oeste - RO, {data_atual}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(10)

    pdf.cell(0, 5, "__________________________________________", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, "CONTRATANTE", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    pdf.ln(8)
    
    pdf.cell(0, 5, "__________________________________________", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 5, "ADVOGADO", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Salva o ficheiro
    nome_arquivo = f"Contrato_Honorarios_{dados['nome_completo'].replace(' ', '_')}.pdf"
    caminho_arquivo = os.path.join('static/temp', nome_arquivo)
    pdf.output(caminho_arquivo)

    return caminho_arquivo
