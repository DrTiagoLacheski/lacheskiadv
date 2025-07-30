from datetime import datetime, timedelta

from datetime import datetime, timedelta


def calcular_meses_proporcionais_clt(data_inicio, data_termino):
    """
    Calcula o número de meses proporcionais de férias ou 13º salário após o último período aquisitivo completo,
    conforme a CLT brasileira (Art. 130 e 146).

    - Cada período aquisitivo é de 12 meses, após o qual o empregado tem direito às férias integrais.
    - Meses proporcionais são contados apenas após o último período de 12 meses completo.
    - Para o mês contar como proporcional, o empregado deve ter trabalhado pelo menos 15 dias nele.

    Args:
        data_inicio (str): Data de início do contrato no formato 'YYYY-MM-DD'
        data_termino (str): Data de término do contrato no formato 'YYYY-MM-DD'

    Returns:
        int: Número de meses proporcionais a serem considerados para férias proporcionais ou 13º proporcional.
    """
    try:
        dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        dt_termino = datetime.strptime(data_termino, "%Y-%m-%d")
        if dt_inicio > dt_termino:
            return 0

        # Calcula quantos períodos de 12 meses completos existem entre dt_inicio e dt_termino
        total_anos = 0
        dt_periodo = dt_inicio
        while True:
            dt_fim_periodo = dt_periodo.replace(year=dt_periodo.year + 1)
            if dt_fim_periodo <= dt_termino:
                total_anos += 1
                dt_periodo = dt_fim_periodo
            else:
                break

        # O novo dt_periodo é o início do período aquisitivo incompleto (restante)
        data_atual = dt_periodo
        meses = 0
        while data_atual <= dt_termino:
            # Define o próximo mês
            if data_atual.month == 12:
                proximo_mes = datetime(data_atual.year + 1, 1, 1)
            else:
                proximo_mes = datetime(data_atual.year, data_atual.month + 1, 1)
            fim_mes = proximo_mes - timedelta(days=1)
            inicio_periodo = data_atual
            fim_periodo = min(dt_termino, fim_mes)
            dias_trabalhados = (fim_periodo - inicio_periodo).days + 1
            if dias_trabalhados >= 15:
                meses += 1
            data_atual = proximo_mes

        return meses

    except Exception:
        return 0
        
    except (ValueError, TypeError) as e:
        return 0

def dias_trabalho_formatados(dados):
    ordem_dias = [
        ("segunda", "segunda-feira"),
        ("terca", "terça-feira"),
        ("quarta", "quarta-feira"),
        ("quinta", "quinta-feira"),
        ("sexta", "sexta-feira"),
        ("sabado", "sábado"),
        ("domingo", "domingo"),
    ]
    dias_ativos = []
    for chave, nome in ordem_dias:
        if dados.get(f'dia_ativo_{chave}'):
            dias_ativos.append(nome)
    if not dias_ativos:
        return "dias não informados"
    idx_ativos = [i for i, (chave, _) in enumerate(ordem_dias) if dados.get(f'dia_ativo_{chave}')]
    if idx_ativos == list(range(idx_ativos[0], idx_ativos[-1]+1)):
        return f"{dias_ativos[0]} a {dias_ativos[-1]}"
    else:
        if len(dias_ativos) == 1:
            return dias_ativos[0]
        return ", ".join(dias_ativos[:-1]) + " e " + dias_ativos[-1]

FERIADOS_NACIONAIS_FIXOS = [
    (1, 1, "Confraternização Universal"),
    (21, 4, "Tiradentes"),
    (1, 5, "Dia do Trabalho"),
    (7, 9, "Independência do Brasil"),
    (12, 10, "Nossa Senhora Aparecida"),
    (2, 11, "Finados"),
    (15, 11, "Proclamação da República"),
    (25, 12, "Natal"),
]

def nome_feriado_simples(data_str):
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d")
        for dia, mes, nome in FERIADOS_NACIONAIS_FIXOS:
            if dt.day == dia and dt.month == mes:
                return nome
        return None
    except Exception:
        return None

def letra_item(idx):
    return chr(ord('a') + idx) + ")"

def calcular_meses_trabalhados_ano_demissao(data_inicio, data_termino):
    """
    Calcula os meses trabalhados no ano da demissão seguindo as regras da CLT brasileira.
    
    Esta função específica considera apenas o período trabalhado no ano da demissão,
    aplicando a regra dos 15 dias da CLT.
    
    Args:
        data_inicio (str): Data de início no formato 'YYYY-MM-DD'
        data_termino (str): Data de término no formato 'YYYY-MM-DD'
    
    Returns:
        int: Número de meses proporcionais trabalhados no ano da demissão
    """
    try:
        dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        dt_termino = datetime.strptime(data_termino, "%Y-%m-%d")
        
        ano_demissao = dt_termino.year
        
        # Define o início do período no ano da demissão
        # Se o funcionário começou antes do ano da demissão, considera 01/01 do ano da demissão
        dt_inicio_ano = max(dt_inicio, datetime(ano_demissao, 1, 1))
        
        # Se o início for posterior ao término, retorna 0
        if dt_inicio_ano > dt_termino:
            return 0
        
        # Usa a função auxiliar para calcular os meses proporcionais
        return calcular_meses_proporcionais_clt(
            dt_inicio_ano.strftime("%Y-%m-%d"), 
            dt_termino.strftime("%Y-%m-%d")
        )
        
    except (ValueError, TypeError) as e:
        return 0

def paragrafo_contrato(dados):
    funcao = dados.get('funcao_exercida', 'FUNÇÃO NÃO INFORMADA').upper()
    registro = dados.get('registro_ctps', '').strip().lower()
    registro_str = "com registro em CTPS" if registro == "sim" else "sem registro em CTPS"
    data_inicio = dados.get('data_inicio', '')
    data_termino = dados.get('data_termino', '')
    data_inicio_fmt = ""
    data_termino_fmt = ""
    try:
        if data_inicio:
            data_inicio_fmt = datetime.strptime(data_inicio, "%Y-%m-%d").strftime("%d/%m/%Y")
        if data_termino:
            data_termino_fmt = datetime.strptime(data_termino, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        data_inicio_fmt = data_inicio
        data_termino_fmt = data_termino

    remuneracao = dados.get('remuneracao', '0,00')
    try:
        # Remove R$ e espaços
        valor_limpo = str(remuneracao).replace('R$', '').strip()
        # Se tem vírgula, assume formato brasileiro (ex: 1.234,56)
        if ',' in valor_limpo:
            # Remove pontos (milhares) e converte vírgula para ponto
            valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
        # Se só tem ponto, pode ser formato americano (ex: 1234.56) ou brasileiro com milhares (ex: 1.234)
        elif '.' in valor_limpo:
            # Se tem mais de 3 dígitos após o ponto, provavelmente é formato americano
            partes = valor_limpo.split('.')
            if len(partes) == 2 and len(partes[1]) <= 2:
                # Formato americano: 1234.56
                pass  # já está correto
            else:
                # Formato brasileiro sem vírgula: 1.234 (sem centavos)
                valor_limpo = valor_limpo.replace('.', '')
        valor = float(valor_limpo)
        remuneracao_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        remuneracao_fmt = f"R$ {remuneracao}"

    natureza_demissao = dados.get('natureza_demissao', '').strip().lower().replace('_', ' ')
    if "justa" in natureza_demissao:
        demissao = "demitido por justa causa"
    elif natureza_demissao == "pedido demissão":
        demissao = "pediu demissão"
    elif natureza_demissao == "sem justa causa":
        demissao = "demitido sem justa causa"
    elif natureza_demissao == "rescisao indireta":
        demissao = "rescisão indireta"
    else:
        demissao = natureza_demissao if natureza_demissao else ""

    depositos_fgts = dados.get('depositos_fgts', '').replace('_', ' ')

    inicio_expediente_seg = dados.get('inicio_expediente_segunda', '--:--')
    inicio_intervalo_seg = dados.get('inicio_intervalo_segunda', '--:--')
    fim_intervalo_seg = dados.get('fim_intervalo_segunda', '--:--')
    fim_expediente_seg = dados.get('fim_expediente_segunda', '--:--')
    inicio_expediente_sab = dados.get('inicio_expediente_sabado', '--:--')
    inicio_intervalo_sab = dados.get('inicio_intervalo_sabado', '--:--')
    fim_intervalo_sab = dados.get('fim_intervalo_sabado', '--:--')
    fim_expediente_sab = dados.get('fim_expediente_sabado', '--:--')

    def horario_str(inicio, intervalo_ini, intervalo_fim, fim):
        if intervalo_ini not in [None, "", "--:--"] and intervalo_fim not in [None, "", "--:--"]:
            return f"iniciava às {inicio}, com intervalo entre {intervalo_ini} e {intervalo_fim}, encerrando às {fim}"
        else:
            return f"iniciava às {inicio} e encerrava às {fim}"

    expediente_seg_sex = horario_str(inicio_expediente_seg, inicio_intervalo_seg, fim_intervalo_seg, fim_expediente_seg)
    expediente_sab = horario_str(inicio_expediente_sab, inicio_intervalo_sab, fim_intervalo_sab, fim_expediente_sab)

    if (inicio_expediente_sab, inicio_intervalo_sab, fim_intervalo_sab, fim_expediente_sab) == \
       (inicio_expediente_seg, inicio_intervalo_seg, fim_intervalo_seg, fim_expediente_seg):
        expediente_str = f"Expediente de segunda a sábado {expediente_seg_sex}, de forma habitual."
    else:
        expediente_str = (
            f"Expediente de segunda a sexta-feira {expediente_seg_sex}, "
            f"e aos sábados {expediente_sab}, de forma habitual."
        )

    dias_trabalho = dias_trabalho_formatados(dados)

    datas_feriados = dados.get('datas_feriados_domingos[]') or []
    tipos_feriados = dados.get('tipo_feriado_domingo[]') or []
    nomes_feriado_domingo = dados.get('nome_feriado_domingo[]') or []

    if isinstance(datas_feriados, str): datas_feriados = [datas_feriados]
    if isinstance(tipos_feriados, str): tipos_feriados = [tipos_feriados]
    if isinstance(nomes_feriado_domingo, str): nomes_feriado_domingo = [nomes_feriado_domingo]

    dias_unicos = set()
    nomes_completos_feriados = []
    for i, data in enumerate(datas_feriados):
        nome_feriado = nomes_feriado_domingo[i].strip() if i < len(nomes_feriado_domingo) and nomes_feriado_domingo[i] else ""
        tipo = tipos_feriados[i].strip() if i < len(tipos_feriados) and tipos_feriados[i] else ""
        data_fmt = ""
        try:
            data_fmt = datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            data_fmt = data
        chave_unica = (nome_feriado.lower(), tipo.lower(), data_fmt)
        if chave_unica in dias_unicos:
            continue
        dias_unicos.add(chave_unica)
        feriado_oficial = nome_feriado_simples(data)
        nome_para_exibir = feriado_oficial or nome_feriado or tipo
        if feriado_oficial and tipo and feriado_oficial.lower() != tipo.lower():
            nomes_completos_feriados.append(f"{feriado_oficial} ({tipo}, {data_fmt})")
        elif nome_feriado and tipo and nome_feriado.lower() != tipo.lower():
            nomes_completos_feriados.append(f"{nome_feriado} ({tipo}, {data_fmt})")
        elif nome_para_exibir:
            nomes_completos_feriados.append(f"{nome_para_exibir} ({data_fmt})")
        else:
            nomes_completos_feriados.append(f"{data_fmt}")

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

    # Busca as férias atrasadas do campo correto (similar às férias vencidas)
    qtd_ferias_atrasadas = dados.get('qtd_ferias_atrasadas', '')
    ferias_atrasadas_legacy = dados.get('ferias_atrasadas', '')

    # Se o campo antigo contém um número, usa ele
    if ferias_atrasadas_legacy and ferias_atrasadas_legacy.strip() and ferias_atrasadas_legacy != "0":
        try:
            float(ferias_atrasadas_legacy)
            qtd_ferias_atrasadas = ferias_atrasadas_legacy
        except (ValueError, TypeError):
            pass

    # Usa a quantidade de férias atrasadas se existe e é válida
    ferias_atrasadas = qtd_ferias_atrasadas if (qtd_ferias_atrasadas and qtd_ferias_atrasadas.strip() and qtd_ferias_atrasadas != "0") else ""

    ferias_proporcionais = dados.get('ferias_proporcionais', '')
    meses_proporcionais = calcular_meses_proporcionais_clt(data_inicio, data_termino) if data_inicio and data_termino else None

    itens = []
    idx = 0

    if funcao and funcao != 'FUNÇÃO NÃO INFORMADA':
        itens.append(f"{letra_item(idx)} O reclamante foi contratado pela reclamada para exercer a função de <b>{funcao}</b>.")
        idx += 1
    if registro_str and registro_str != "sem registro em CTPS":
        itens.append(f"{letra_item(idx)} Com a devida formalização do vínculo ({registro_str}).")
        idx += 1
    if depositos_fgts and depositos_fgts.strip() and depositos_fgts.lower() != "não informado":
        itens.append(f"{letra_item(idx)} {depositos_fgts} FGTS.")
        idx += 1
    if data_inicio_fmt or data_termino_fmt:
        itens.append(f"{letra_item(idx)} O vínculo iniciou em {data_inicio_fmt or 'data não informada'} e se encerrou em {data_termino_fmt or 'data não informada'}.")
        idx += 1
    if remuneracao_fmt and remuneracao_fmt != "R$ 0,00":
        itens.append(f"{letra_item(idx)} A remuneração era de {remuneracao_fmt}.")
        idx += 1
    if natureza_demissao and demissao != "":
        itens.append(f"{letra_item(idx)} O reclamante foi {demissao}.")
        idx += 1
    if dias_trabalho and dias_trabalho != "dias não informados":
        itens.append(f"{letra_item(idx)} Trabalhava de {dias_trabalho};")
        idx += 1
    if expediente_str and expediente_str.strip():
        itens.append(f"{letra_item(idx)} {expediente_str}")
        idx += 1

    if nomes_completos_feriados:
        qtd = len(nomes_completos_feriados)
        plural = "feriados/domingos" if qtd > 1 else "feriado/domingo"
        artigo = "eles" if qtd > 1 else "ele"
        feriado_str = (
            f"O reclamante atesta ter trabalhado em {qtd} {plural} e não recebeu por {artigo}, "
            f"são {artigo}: {', '.join(nomes_completos_feriados)}."
        )
        itens.append(f"{letra_item(idx)} {feriado_str}")
        idx += 1

    # Item exclusivo: férias vencidas + férias atrasadas + meses trabalhados no ano da demissão
    tem_ferias_vencidas_validas = tem_ferias_vencidas and qtd_ferias_vencidas and qtd_ferias_vencidas.strip() and qtd_ferias_vencidas != "0"
    tem_ferias_atrasadas_validas = ferias_atrasadas and ferias_atrasadas.strip() and ferias_atrasadas != "0"

    if tem_ferias_vencidas_validas or tem_ferias_atrasadas_validas or meses_proporcionais is not None:
        texto_ferias = ""

        # Férias vencidas (quantidade de férias)
        if tem_ferias_vencidas_validas:
            texto_ferias += f"Possui registro de férias vencidas não usufruídas ({qtd_ferias_vencidas} quantidade de férias vencidas)."

        # Férias atrasadas (dias)
        if tem_ferias_atrasadas_validas:
            if texto_ferias: texto_ferias += " "
            texto_ferias += f"Possui registro de férias atrasadas não usufruídas ({ferias_atrasadas})."

        # Meses trabalhados no ano da demissão
        if meses_proporcionais is not None:
            if texto_ferias: texto_ferias += " "
            texto_ferias += f"O total de meses proporcionais para cálculo de férias ou 13º salário é {meses_proporcionais}."

        itens.append(f"{letra_item(idx)} {texto_ferias}")
        idx += 1
    if ferias_proporcionais and ferias_proporcionais.strip() and ferias_proporcionais != "0":
        itens.append(f"{letra_item(idx)} Férias proporcionais devidas: {ferias_proporcionais}.")
        idx += 1

    texto = "3. Detalhes do Contrato de Trabalho<br/><br/>" + "<br/><br/>".join(itens)
    return texto