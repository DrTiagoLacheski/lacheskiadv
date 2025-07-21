# views.py
from flask import Blueprint, render_template

from triagem.auth import login_required

main_bp = Blueprint('main', __name__)



@main_bp.route('/ferramentas-juridicas')
def ferramentas_juridicas():
    """Página de ferramentas jurídicas (a página atual que você já tem)"""
    return render_template('ferramentas_juridicas.html')

# Mantenha todas as suas rotas existentes abaixo
@main_bp.route('/procuracao')
def pagina_procuracao():
    return render_template('procuracao.html')

@main_bp.route('/')

def index():
    return render_template('index.html')


@main_bp.route('/contrato-honorarios')
def pagina_contrato_honorarios():
    return render_template('contrato_honorarios.html')

@main_bp.route('/substabelecimento')
def pagina_substabelecimento():
    return render_template('substabelecimento.html')

