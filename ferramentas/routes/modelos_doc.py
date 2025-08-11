from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, ProcuracaoModelo, User
from datetime import datetime
from jinja2 import Template
import re

admin_bp = Blueprint("admin", __name__, template_folder='../templates', static_folder='../static')

VARIAVEIS_PERMITIDAS = [
    "nome_completo",
    "estado_civil",
    "profissao",
    "cpf",
    "rg",
    "endereco",
    # Variáveis do advogado principal
    "adv_principal_nome",
    "adv_principal_estado_civil",
    "adv_principal_profissao",
    "adv_principal_cpf",
    "adv_principal_rg",
    "adv_principal_orgao_emissor",
    "adv_principal_endereco_profissional",
    "adv_principal_oabs",
    # Variáveis do colaborador
    "adv_colab_nome",
    "adv_colab_estado_civil",
    "adv_colab_profissao",
    "adv_colab_cpf",
    "adv_colab_rg",
    "adv_colab_orgao_emissor",
    "adv_colab_endereco_profissional",
    "adv_colab_oabs",
]

MODELO_PADRAO_FISICA = """OUTORGANTE: {{nome_completo | upper}}, brasileiro(a), {{estado_civil}}, {{profissao}}, devidamente inscrito(a) no CPF n.º {{cpf}}, {% if rg %}portador(a) do RG n.º {{rg}}, {% endif %}residente e domiciliado(a) à {{endereco}}.

OUTORGADO: {{adv_principal_nome | upper}}, brasileiro(a), {{adv_principal_estado_civil}}, {{adv_principal_profissao}}, inscrito(a) no CPF sob o n.º {{adv_principal_cpf}}, {% if adv_principal_rg %}portador(a) do RG n.º {{adv_principal_rg}}{% if adv_principal_orgao_emissor %}, {{adv_principal_orgao_emissor}}{% endif %}{% endif %}, {% if adv_principal_oabs %}{% for oab in adv_principal_oabs %}OAB n.º {{oab.numero}}{% if not loop.last %}, {% endif %}{% endfor %}{% endif %}, com endereço profissional situado na {{adv_principal_endereco_profissional}}.

{% if adv_colab_nome %}
OUTORGADO COLABORADOR: {{adv_colab_nome | upper}}, brasileiro(a), {{adv_colab_estado_civil}}, {{adv_colab_profissao}}, inscrito(a) no CPF sob o n.º {{adv_colab_cpf}}, {% if adv_colab_rg %}portador(a) do RG n.º {{adv_colab_rg}}{% if adv_colab_orgao_emissor %}, {{adv_colab_orgao_emissor}}{% endif %}{% endif %}, {% if adv_colab_oabs %}{% for oab in adv_colab_oabs %}OAB n.º {{oab.numero}}{% if not loop.last %}, {% endif %}{% endfor %}{% endif %}, com endereço profissional situado na {{adv_colab_endereco_profissional}}.
{% endif %}

PODERES: O outorgante nomeia os outorgados seus procuradores, concedendo-lhes os poderes inerentes da cláusula ad judicia et extra para o foro em geral, podendo promover quaisquer medidas judiciais ou administrativas, oferecer defesa, interpor recursos, ajuizar ações e conduzir os respectivos processos, solicitar, providenciar e ter acesso a documentos de qualquer natureza, sendo o presente instrumento de mandato oneroso e contratual, podendo substabelecer este a outrem, com ou sem reserva de poderes, a fim de praticar todos os demais atos necessários ao fiel desempenho deste mandato, além de reconhecer a procedência do pedido, transigir, desistir, renunciar ao direito sobre o qual se funda a ação, receber, dar quitação, firmar compromisso e assinar declaração de hipossuficiência econômica.
"""

def garantir_modelo_padrao():
    nome_padrao = "Modelo Padrão Pessoa Física"
    modelo_existente = ProcuracaoModelo.query.filter_by(nome=nome_padrao).first()
    if not modelo_existente:
        admin = User.query.filter_by(is_admin=True).first()
        modelo = ProcuracaoModelo(
            nome=nome_padrao,
            conteudo=MODELO_PADRAO_FISICA,
            criado_por=admin if admin else current_user,
            data_criacao=datetime.utcnow()
        )
        db.session.add(modelo)
        db.session.commit()

@admin_bp.route('/modelos-procuracao', methods=['GET', 'POST'])
@login_required
def gerenciar_modelos_procuracao():
    if not current_user.is_admin:
        flash('Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('dashboard.dashboard'))

    garantir_modelo_padrao()

    if request.method == 'POST':
        nome = request.form.get('nome')
        conteudo = request.form.get('conteudo')
        if not nome or not conteudo:
            flash('Preencha todos os campos.', 'warning')
        else:
            modelo = ProcuracaoModelo(
                nome=nome,
                conteudo=conteudo,
                criado_por=current_user,
                data_criacao=datetime.utcnow()
            )
            db.session.add(modelo)
            db.session.commit()
            flash('Modelo criado com sucesso!', 'success')
            return redirect(url_for('admin.gerenciar_modelos_procuracao'))

    modelos = ProcuracaoModelo.query.order_by(ProcuracaoModelo.data_criacao.desc()).all()
    return render_template('gerenciar_modelos_procuracao.html', modelos=modelos, variaveis=VARIAVEIS_PERMITIDAS)

@admin_bp.route('/editar-modelo/<int:modelo_id>', methods=['GET', 'POST'])
@login_required
def editar_modelo_procuracao(modelo_id):
    if not current_user.is_admin:
        flash('Apenas administradores podem editar modelos.', 'danger')
        return redirect(url_for('admin.gerenciar_modelos_procuracao'))

    modelo = ProcuracaoModelo.query.get_or_404(modelo_id)
    if request.method == 'POST':
        nome = request.form.get('nome')
        conteudo = request.form.get('conteudo')
        if not nome or not conteudo:
            flash('Preencha todos os campos.', 'warning')
        else:
            modelo.nome = nome
            modelo.conteudo = conteudo
            db.session.commit()
            flash('Modelo atualizado com sucesso!', 'success')
            return redirect(url_for('admin.gerenciar_modelos_procuracao'))

    return render_template(
        'editar_modelo_procuracao.html',
        modelo=modelo,
        variaveis=VARIAVEIS_PERMITIDAS
    )

@admin_bp.route('/excluir-modelo/<int:modelo_id>', methods=['POST'])
@login_required
def excluir_modelo_procuracao(modelo_id):
    if not current_user.is_admin:
        flash('Apenas administradores podem excluir modelos.', 'danger')
        return redirect(url_for('admin.gerenciar_modelos_procuracao'))
    modelo = ProcuracaoModelo.query.get_or_404(modelo_id)
    db.session.delete(modelo)
    db.session.commit()
    flash('Modelo excluído com sucesso.', 'success')
    return redirect(url_for('admin.gerenciar_modelos_procuracao'))

def format_modelo_for_preview(rendered):
    # Negrito para nomes dos participantes
    rendered = re.sub(r'(OUTORGANTE: )(.*?)(,)', r'\1<strong>\2</strong>\3', rendered)
    rendered = re.sub(r'(OUTORGADO: )(.*?)(,)', r'\1<strong>\2</strong>\3', rendered)
    rendered = re.sub(r'(OUTORGADO COLABORADOR: )(.*?)(,)', r'\1<strong>\2</strong>\3', rendered)
    # Quebras de linha
    rendered = rendered.replace('\n', '<br>')
    return rendered

def format_modelo_for_preview(rendered, mock_data):
    # Substitui as variáveis por seus valores de exemplo no preview (para amostra visual ao clicar nos botões)
    # Exemplo: "{{nome_completo}}" -> "João da Silva"
    # Para arrays como adv_principal_oabs, faz transformação adequada

    # Função auxiliar para tratar variáveis compostas (como OABs)
    def get_var_value(var):
        val = mock_data.get(var, "")
        if isinstance(val, list):
            # Exemplo para OABs
            return ", ".join([f'OAB n.º {oab["numero"]}' for oab in val if "numero" in oab])
        return str(val)

    # Substitui todas as variáveis simples (ex: {{nome_completo}})
    for var in mock_data:
        if isinstance(mock_data[var], list):
            # Para variáveis do tipo lista (OABs)
            pattern = r'{{\s*' + re.escape(var) + r'\s*}}'
            rendered = re.sub(pattern, get_var_value(var), rendered)
        else:
            pattern = r'{{\s*' + re.escape(var) + r'\s*}}'
            rendered = re.sub(pattern, str(mock_data[var]), rendered)

    # Substitui possíveis blocos {% for oab in adv_principal_oabs %}...{% endfor %}
    rendered = re.sub(r'{%.*?%}', '', rendered, flags=re.DOTALL)

    # Formata nomes dos participantes em negrito (apenas para preview visual)
    rendered = re.sub(r'(OUTORGANTE: )(.*?)(,)', r'\1<strong>\2</strong>\3', rendered)
    rendered = re.sub(r'(OUTORGADO: )(.*?)(,)', r'\1<strong>\2</strong>\3', rendered)
    rendered = re.sub(r'(OUTORGADO COLABORADOR: )(.*?)(,)', r'\1<strong>\2</strong>\3', rendered)
    # Quebras de linha
    rendered = rendered.replace('\n', '<br>')
    return rendered

@admin_bp.route('/preview-modelo', methods=['POST'])
@login_required
def preview_modelo_procuracao():
    conteudo = request.form.get('conteudo', '')
    mock_data = {
        'nome_completo': 'João da Silva',
        'estado_civil': 'Solteiro(a)',
        'profissao': 'Advogado',
        'cpf': '123.456.789-00',
        'rg': '12.345.678-9',
        'endereco': 'Rua das Flores, 100, Centro, Cidade/UF',
        # Advogado principal
        'adv_principal_nome': 'Maria Advogada',
        'adv_principal_estado_civil': 'Casada',
        'adv_principal_profissao': 'Advogada',
        'adv_principal_cpf': '999.888.777-66',
        'adv_principal_rg': '11.222.333-4',
        'adv_principal_orgao_emissor': 'SSP/SP',
        'adv_principal_endereco_profissional': 'Av. Central, 100, Cidade/UF',
        'adv_principal_oabs': [{'numero': '12345/SP'}, {'numero': '54321/RJ'}],
        # Advogado colaborador
        'adv_colab_nome': 'Carlos Colaborador',
        'adv_colab_estado_civil': 'Solteiro',
        'adv_colab_profissao': 'Advogado',
        'adv_colab_cpf': '111.222.333-44',
        'adv_colab_rg': '22.333.444-5',
        'adv_colab_orgao_emissor': 'SSP/RJ',
        'adv_colab_endereco_profissional': 'Rua Nova, 200, Cidade/UF',
        'adv_colab_oabs': [{'numero': '98765/SP'}],
    }
    try:
        # Renderização básica sem Jinja, apenas substituição das variáveis por seus exemplos
        rendered = format_modelo_for_preview(conteudo, mock_data)
    except Exception as e:
        rendered = f"<span style='color:red;'>Erro no modelo: {e}</span>"
    return jsonify({'preview': rendered})