# calctrabalhista.py
# Contém a lógica de negócio para a geração do Relatório Trabalhista Preliminar.

import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import datetime
from flask import Blueprint, render_template, request, session, redirect, url_for

def _header(pdf, dados):
    adicionar_secao("DADOS DO RECLAMANTE", {
        "Nome": dados.get('nome_reclamante', 'Não informado'),
        "CPF": dados.get('cpf_reclamante', 'Não informado'),
        "RG": dados.get('rg_reclamante', 'Não informado'),
        "Estado civil": dados.get('estado_civil', 'Não informado'),
        "Endereço": dados.get('endereco_reclamante', 'Não informado')
    })
    """Função auxiliar para adicionar o cabeçalho com a logo ao PDF."""
    logo_width = 60
    page_width = pdf.w
    x_pos = (page_width - logo_width) / 2
    logo_path = 'static/images/logolacheski.png'
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=x_pos, y=8, w=logo_width)
    else:
        print(f"AVISO: Arquivo de logo não encontrado em '{logo_path}'")

def _formatar_data(data_str):
    """Função auxiliar para formatar a data para exibição (DD/MM/AAAA)."""
    try:
        return datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return "Data inválida"

def _formatar_moeda(valor_str):
    """Função auxiliar para formatar um valor como moeda (R$)."""
    try:
        valor = float(valor_str)
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "Valor inválido"

def gerar_relatorio_trabalhista_pdf(dados):
    """
    Gera o arquivo PDF do Relatório Trabalhista Preliminar.
    Retorna o caminho do arquivo gerado.
    """
    os.makedirs('static/temp', exist_ok=True)  # Garante que o diretório existe

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    _header(pdf, dados)
    
    pdf.set_margins(left=25, top=20, right=25)
    pdf.set_font("Times", size=11)
    
    pdf.ln(25) 

    # Título
    pdf.set_font("Times", 'B', 14)
    pdf.cell(0, 10, "RELATÓRIO TRABALHISTA PRELIMINAR", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    # Função auxiliar para adicionar seções e campos ao PDF
    def adicionar_secao(titulo, conteudo_dict):
        pdf.set_font("Times", 'B', 12)
        pdf.cell(0, 8, titulo, border='B', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4)
        for label, value in conteudo_dict.items():
            pdf.set_font("Times", 'B', 11)
            pdf.cell(65, 6, f"{label}:")
            pdf.set_font("Times", '', 11)
            pdf.multi_cell(0, 6, str(value), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)

    # Seção 1: Informações do Vínculo
    adicionar_secao("1. INFORMAÇÕES DO VÍNCULO", {
        "Data de Início": _formatar_data(dados.get('data_inicio')),
        "Data de Término": _formatar_data(dados.get('data_termino')),
        "Função Exercida": dados.get('funcao_exercida', 'Não informado'),
        "Última Remuneração": _formatar_moeda(dados.get('remuneracao'))
    })

    # Seção 2: Empresa Reclamada
    adicionar_secao("2. EMPRESA RECLAMADA", {
        "Nome da Empresa": dados.get('nome_empresa', 'Não informado'),
        "CNPJ": dados.get('cnpj_empresa', 'Não informado')
    })

    # Seção 3: Jornada de Trabalho
    adicionar_secao("3. JORNADA DE TRABALHO", {
        "Regime Contratado": dados.get('regime_jornada', 'Não informado').replace('_', ' ').capitalize(),
        "Horário de Trabalho": f"Das {dados.get('inicio_expediente', '--:--')} às {dados.get('fim_expediente', '--:--')}",
        "Intervalo": f"Das {dados.get('inicio_intervalo', '--:--')} às {dados.get('fim_intervalo', '--:--')}",
        "Realizava Horas Extras": dados.get('hora_extra', 'Não').capitalize(),
        "Cláusula de Compensação": dados.get('clausula_compensacao', 'Não').capitalize()
    })

    # Seção 4: Outras Informações Relevantes
    adicionar_secao("4. OUTRAS INFORMAÇÕES RELEVANTES", {
        "Adicional de Insalubridade": dados.get('insalubridade', 'Não se aplica'),
        "Depósitos de FGTS": f"Foram realizados? {dados.get('depositos_fgts', 'Não').capitalize()}",
        "Natureza da Demissão": dados.get('natureza_demissao', 'Não informado').replace('_', ' ').capitalize()
    })

    # Aviso Legal
    pdf.ln(10)
    pdf.set_font("Times", 'I', 9)
    aviso = (
        "AVISO IMPORTANTE: Este é um relatório preliminar gerado com base nas informações fornecidas pelo cliente. "
        "Os valores e direitos aqui apresentados são estimativas e estão sujeitos a confirmação através de "
        "análise documental e cálculos detalhados por um profissional. Este documento não substitui uma "
        "consulta jurídica completa nem constitui um parecer técnico final."
    )
    pdf.multi_cell(0, 5, aviso, align='J')
    pdf.ln(10)

    # Data e Assinatura
    data_atual = datetime.now().strftime("%d de %B de %Y").lower()
    meses = {
        "january": "janeiro", "february": "fevereiro", "march": "março", "april": "abril", 
        "may": "maio", "june": "junho", "july": "julho", "august": "agosto", 
        "september": "setembro", "october": "outubro", "november": "novembro", "december": "dezembro"
    }
    for eng, pt in meses.items():
        data_atual = data_atual.replace(eng, pt)
    pdf.set_font("Times", '', 11)
    pdf.cell(0, 7, f"Gerado em Machadinho D'Oeste - RO, {data_atual}.", align='C', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Salva o arquivo
    nome_cliente = dados.get('funcao_exercida', 'relatorio').replace(' ', '_')
    nome_arquivo = f"Relatorio_Trabalhista_{nome_cliente}.pdf"
    caminho_arquivo = os.path.join('static/temp', nome_arquivo)
    pdf.output(caminho_arquivo)

    return caminho_arquivo
