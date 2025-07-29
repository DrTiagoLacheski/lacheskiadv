from datetime import datetime

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
    try:
        dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        dt_termino = datetime.strptime(data_termino, "%Y-%m-%d")
        ano_demissao = dt_termino.year
        dt_inicio_ano = max(dt_inicio, datetime(ano_demissao, 1, 1))
        if dt_inicio_ano > dt_termino:
            return 0
        meses = (dt_termino.year - dt_inicio_ano.year) * 12 + (dt_termino.month - dt_inicio_ano.month)
        if dt_termino.day >= 15:
            meses += 1
        return meses
    except Exception:
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
        valor = float(str(remuneracao).replace('R$', '').strip().replace('.', '').replace(',', '.'))
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

    ferias_vencidas = dados.get('ferias_vencidas', '')
    ferias_atrasadas = dados.get('ferias_atrasadas', '')
    ferias_proporcionais = dados.get('ferias_proporcionais', '')
    meses_ano_demissao = calcular_meses_trabalhados_ano_demissao(data_inicio, data_termino) if data_inicio and data_termino else None

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

    # Item exclusivo: férias vencidas + meses trabalhados no ano da demissão
    if (ferias_vencidas and ferias_vencidas.strip() and ferias_vencidas != "0") or meses_ano_demissao is not None:
        texto_ferias = ""
        if ferias_vencidas and ferias_vencidas.strip() and ferias_vencidas != "0":
            texto_ferias += f"{ferias_vencidas} registro de férias vencidas não usufruídas."
        if meses_ano_demissao is not None:
            if texto_ferias: texto_ferias += " "
            texto_ferias += f"O total de meses trabalhados no ano da demissão {meses_ano_demissao}."
        itens.append(f"{letra_item(idx)} {texto_ferias}")
        idx += 1

    if ferias_atrasadas and ferias_atrasadas.strip() and ferias_atrasadas != "0":
        itens.append(f"{letra_item(idx)}  {ferias_atrasadas} registro de férias atrasadas não usufruídas.")
        idx += 1
    if ferias_proporcionais and ferias_proporcionais.strip() and ferias_proporcionais != "0":
        itens.append(f"{letra_item(idx)} Férias proporcionais devidas: {ferias_proporcionais}.")
        idx += 1

    texto = "3. Detalhes do Contrato de Trabalho<br/><br/>" + "<br/><br/>".join(itens)
    return texto