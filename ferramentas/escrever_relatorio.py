from datetime import datetime
from .paragrafo_contrato import paragrafo_contrato

def paragrafo_reclamante(dados):
    nome = dados.get('nome_reclamante', 'NOME NÃO INFORMADO')
    nacionalidade = dados.get('nacionalidade', 'brasileiro(a)')
    estado_civil = dados.get('estado_civil', 'estado civil não informado')
    cpf = dados.get('cpf_reclamante', 'CPF não informado')
    rg = dados.get('rg_reclamante', 'RG não informado')
    orgao_emissor = dados.get('orgao_emissor_rg', '')
    uf_rg = dados.get('uf_rg', '')
    endereco = dados.get('endereco_reclamante', '')
    numero = dados.get('numero_endereco', '')
    bairro = dados.get('bairro_endereco', '')
    municipio = dados.get('municipio_endereco', '')
    uf = dados.get('uf_endereco', '')

    # Monta RG com órgão/UF se existirem
    rg_full = f"{rg}"
    if orgao_emissor and uf_rg:
        rg_full += f", {orgao_emissor}/{uf_rg}"
    elif orgao_emissor:
        rg_full += f", {orgao_emissor}"
    elif uf_rg:
        rg_full += f", {uf_rg}"

    # Monta endereço
    endereco_full = f"{endereco}"
    if numero:
        endereco_full += f", N°{numero}"
    if bairro:
        endereco_full += f", bairro {bairro}"
    if municipio and uf:
        endereco_full += f", no município de {municipio}/{uf}"
    elif municipio:
        endereco_full += f", no município de {municipio}"

    # Nome em negrito usando HTML, e título da seção antes do texto
    return (
        "1. Dados do Reclamante<br/><br/>"
        f"<b>{nome.upper()}</b>, {nacionalidade}, {estado_civil}, inscrito no CPF sob o n° {cpf}, "
        f"portador do RG N°{rg_full}, residente e domiciliado na {endereco_full}."
    )

def paragrafo_reclamada(dados):
    nome = dados.get('nome_empresa', 'NOME NÃO INFORMADO')
    natureza = dados.get('natureza_empresa', 'pessoa jurídica de direito privado')
    cnpj = dados.get('cnpj_empresa', 'CNPJ não informado')
    endereco = dados.get('endereco_empresa', '')
    numero = dados.get('numero_endereco_empresa', '')
    bairro = dados.get('bairro_endereco_empresa', '')
    municipio = dados.get('municipio_endereco_empresa', '')
    uf = dados.get('uf_endereco_empresa', '')

    # Monta endereço
    endereco_full = f"{endereco}"
    if numero:
        endereco_full += f", N°{numero}"
    if bairro:
        endereco_full += f", bairro {bairro}"
    if municipio and uf:
        endereco_full += f", no município de {municipio}/{uf}"
    elif municipio:
        endereco_full += f", no município de {municipio}"

    # Nome em negrito usando HTML, e título da seção antes do texto
    return (
        "2. Dados da Reclamada<br/><br/>"
        f"<b>{nome.upper()}</b>, {natureza}, inscrita no CNPJ sob o n° {cnpj}, com sede na {endereco_full}."
    )