from datetime import datetime
from .paragrafo_contrato import paragrafo_contrato, calcular_meses_proporcionais_clt

def calcular_ferias_proporcionais_clt(data_inicio, data_termino, ferias_vencidas=None):
    """
    Calcula férias proporcionais seguindo as regras da CLT brasileira.
    
    Conforme Art. 146 da CLT:
    - A cada 12 meses, o trabalhador tem direito a 30 dias de férias
    - Para cálculo proporcional: períodos de 15 dias ou mais no mês = mês completo
    - Períodos inferiores a 15 dias = desconsiderados
    
    Args:
        data_inicio (str): Data de início no formato 'YYYY-MM-DD'
        data_termino (str): Data de término no formato 'YYYY-MM-DD'
        ferias_vencidas (str/float/int): Quantidade de férias vencidas/atrasadas em dias
    
    Returns:
        dict: {
            'meses_proporcionais': int,
            'dias_ferias_proporcionais': float,
            'dias_ferias_vencidas': float,
            'total_dias_ferias': float,
            'texto_descricao': str
        }
    """
    try:
        meses = calcular_meses_proporcionais_clt(data_inicio, data_termino)
        
        # Cálculo de férias proporcionais: 30 dias ÷ 12 meses = 2.5 dias por mês
        dias_ferias_proporcionais = round((meses * 30) / 12, 1)
        
        # Processa férias vencidas/atrasadas
        dias_ferias_vencidas = 0.0
        if ferias_vencidas is not None and ferias_vencidas != "" and ferias_vencidas != "0":
            try:
                if isinstance(ferias_vencidas, str):
                    ferias_vencidas_limpo = ferias_vencidas.replace(',', '.').strip()
                    dias_ferias_vencidas = float(ferias_vencidas_limpo)
                else:
                    dias_ferias_vencidas = float(ferias_vencidas)
            except (ValueError, TypeError):
                dias_ferias_vencidas = 0.0
        
        # Total de dias de férias
        total_dias_ferias = dias_ferias_proporcionais + dias_ferias_vencidas
        
        # Texto descritivo
        texto_partes = []
        
        # Férias proporcionais
        if meses == 0:
            texto_partes.append("Não há direito a férias proporcionais (período inferior a 15 dias em qualquer mês trabalhado)")
        elif meses == 12:
            texto_partes.append(f"Férias proporcionais completas: 30 dias ({meses} meses trabalhados)")
        else:
            texto_partes.append(f"Férias proporcionais: {dias_ferias_proporcionais} dias ({meses} meses trabalhados conforme CLT Art. 146)")
        
        # Férias vencidas
        if dias_ferias_vencidas > 0:
            texto_partes.append(f"Férias vencidas/atrasadas: {dias_ferias_vencidas} dias")
        
        # Total
        if dias_ferias_vencidas > 0 and dias_ferias_proporcionais > 0:
            texto_partes.append(f"TOTAL DE FÉRIAS: {total_dias_ferias} dias")
        
        texto = " | ".join(texto_partes)
        
        return {
            'meses_proporcionais': meses,
            'dias_ferias_proporcionais': dias_ferias_proporcionais,
            'dias_ferias_vencidas': dias_ferias_vencidas,
            'total_dias_ferias': total_dias_ferias,
            'texto_descricao': texto
        }
        
    except Exception as e:
        return {
            'meses_proporcionais': 0,
            'dias_ferias_proporcionais': 0.0,
            'dias_ferias_vencidas': 0.0,
            'total_dias_ferias': 0.0,
            'texto_descricao': "Erro no cálculo de férias proporcionais"
        }

def calcular_13_salario_proporcional_clt(data_inicio, data_termino, salario):
    """
    Calcula 13º salário proporcional seguindo as regras da CLT brasileira.
    
    Conforme Art. 1º da Lei 4.090/62:
    - A cada 12 meses, o trabalhador tem direito a uma gratificação natalina
    - Para cálculo proporcional: períodos de 15 dias ou mais no mês = mês completo
    - Períodos inferiores a 15 dias = desconsiderados
    
    Args:
        data_inicio (str): Data de início no formato 'YYYY-MM-DD'
        data_termino (str): Data de término no formato 'YYYY-MM-DD'
        salario (str/float): Último salário do trabalhador
    
    Returns:
        dict: {
            'meses_proporcionais': int,
            'valor_proporcional': float,
            'texto_descricao': str
        }
    """
    try:
        # Calcula os meses proporcionais usando a regra da CLT
        meses = calcular_meses_proporcionais_clt(data_inicio, data_termino)
        
        # Converte salário para float
        if isinstance(salario, str):
            # Remove R$, pontos (separadores de milhares) e converte vírgula para ponto
            salario_limpo = salario.replace('R$', '').replace(' ', '').strip()
            # Se tem vírgula, assume que é o separador decimal brasileiro
            if ',' in salario_limpo:
                # Remove pontos (milhares) e converte vírgula para ponto
                salario_limpo = salario_limpo.replace('.', '').replace(',', '.')
            salario_float = float(salario_limpo)
        else:
            salario_float = float(salario)
        
        # Cálculo do 13º proporcional: (salário ÷ 12) × meses trabalhados
        valor_proporcional = round((salario_float / 12) * meses, 2)
        
        # Texto descritivo
        if meses == 0:
            texto = "Não há direito ao 13º salário proporcional (período inferior a 15 dias em qualquer mês trabalhado)"
        elif meses == 12:
            texto = f"13º salário integral: R$ {salario_float:,.2f} ({meses} meses trabalhados)".replace(",", "X").replace(".", ",").replace("X", ".")
        else:
            valor_formatado = f"R$ {valor_proporcional:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            texto = f"13º salário proporcional: {valor_formatado} ({meses}/12 meses conforme CLT)"
        
        return {
            'meses_proporcionais': meses,
            'valor_proporcional': valor_proporcional,
            'texto_descricao': texto
        }
        
    except Exception as e:
        return {
            'meses_proporcionais': 0,
            'valor_proporcional': 0.0,
            'texto_descricao': "Erro no cálculo do 13º salário proporcional"
        }

def calcular_direitos_proporcionais_completo(dados):
    """
    Calcula todos os direitos proporcionais de um trabalhador seguindo a CLT brasileira.
    
    Esta função unifica todos os cálculos proporcionais e pode ser usada
    nos formulários de cálculo trabalhista.
    
    Args:
        dados (dict): Dicionário com dados do trabalhador contendo:
            - data_inicio: Data de início do trabalho
            - data_termino: Data de término do trabalho  
            - remuneracao: Último salário
            - ferias_vencidas: Quantidade de férias vencidas/atrasadas em dias (opcional)
    
    Returns:
        dict: Todos os cálculos proporcionais organizados
    """
    data_inicio = dados.get('data_inicio', '')
    data_termino = dados.get('data_termino', '')
    salario = dados.get('remuneracao', '0')
    
    # Busca a quantidade de férias vencidas do campo correto
    qtd_ferias_vencidas = dados.get('qtd_ferias_vencidas', '')
    tem_ferias_vencidas = dados.get('ferias_vencidas', '') == 'Possui'
    
    # Para compatibilidade, também verifica o campo antigo 'ferias_vencidas' se contém número
    ferias_vencidas_legacy = dados.get('ferias_vencidas', '')
    if ferias_vencidas_legacy and ferias_vencidas_legacy not in ['Possui', 'Não há', '']:
        # Se o campo ferias_vencidas contém um número, usa ele
        try:
            float(ferias_vencidas_legacy)
            qtd_ferias_vencidas = ferias_vencidas_legacy
            tem_ferias_vencidas = True
        except (ValueError, TypeError):
            pass
    
    # Usa a quantidade se existe e é válida
    ferias_vencidas = qtd_ferias_vencidas if (tem_ferias_vencidas and qtd_ferias_vencidas) else None
    
    if not data_inicio or not data_termino:
        return {
            'erro': 'Datas de início e término são obrigatórias',
            'ferias_proporcionais': None,
            'decimo_terceiro': None,
            'meses_ano_demissao': 0
        }
    
    try:
        # Calcula férias proporcionais (incluindo férias vencidas se houver)
        ferias = calcular_ferias_proporcionais_clt(data_inicio, data_termino, ferias_vencidas)
        
        # Calcula 13º salário proporcional
        decimo_terceiro = calcular_13_salario_proporcional_clt(data_inicio, data_termino, salario)
        
        # Calcula meses trabalhados no ano da demissão
        from .paragrafo_contrato import calcular_meses_trabalhados_ano_demissao
        meses_ano_demissao = calcular_meses_trabalhados_ano_demissao(data_inicio, data_termino)
        
        return {
            'erro': None,
            'ferias_proporcionais': ferias,
            'decimo_terceiro': decimo_terceiro,
            'meses_ano_demissao': meses_ano_demissao,
            'observacoes_clt': [
                "✓ Cálculos seguem rigorosamente o Art. 146 da CLT",
                "✓ Regra dos 15 dias: período ≥ 15 dias = mês completo",
                "✓ Período < 15 dias = desconsiderado para fins proporcionais",
                "✓ Base legal: CLT Art. 146 e Lei 4.090/62 (13º salário)"
            ]
        }
        
    except Exception as e:
        return {
            'erro': f'Erro no cálculo: {str(e)}',
            'ferias_proporcionais': None,
            'decimo_terceiro': None,
            'meses_ano_demissao': 0
        }

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