from flask import Blueprint, request, render_template, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Advogado
from ferramentas.untils.utils_habilitacao import gerar_pdf_habilitacao

habilitacao_bp = Blueprint('habilitacao', __name__)

@habilitacao_bp.route('/habilitacao-processual', methods=['GET', 'POST'])
@login_required
def pagina_habilitacao():
    advogado = Advogado.query.filter_by(user_id=current_user.id, is_principal=True).first()
    oabs = advogado.oabs if advogado and advogado.oabs else []
    ro_idx = next((i for i, o in enumerate(oabs) if o.get("uf", "").upper() == "RO"), 0)

    if request.method == 'POST':
        endereco = request.form.get('endereco', '')
        numero_processo = request.form.get('numero_processo', '')
        nome_cliente = request.form.get('nome_cliente', '')
        oab_idx = int(request.form.get('oab_idx', 0))
        # Seleciona a OAB escolhida
        if oabs and 0 <= oab_idx < len(oabs):
            advogado.oabs = [oabs[oab_idx]]
        buf = gerar_pdf_habilitacao(endereco, numero_processo, nome_cliente, advogado)
        filename = f"habilitacao_{numero_processo.replace('/', '-')}.pdf"
        return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=filename)

    return render_template('req_habilitacao.html', oabs=oabs, ro_idx=ro_idx)