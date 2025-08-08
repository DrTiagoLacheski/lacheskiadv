# utils_advogado.py
# Funções utilitárias para advogados disponíveis para o usuário (próprios + admin associado)

from models import User, Advogado

def get_advogados_disponiveis(usuario):
    """
    Retorna advogados próprios do usuário e, se for associado a um admin, advogados do admin também.
    Output: lista de dicts: {'advogado': Advogado, 'tipo': 'meu' ou 'admin'}
    """
    advogados_own = usuario.advogados.order_by(Advogado.nome).all()
    advogados_admin = []
    if usuario.admin_id:
        admin = usuario.admin
        if admin:
            advogados_admin = admin.advogados.order_by(Advogado.nome).all()
    advogados = [{"advogado": adv, "tipo": "meu"} for adv in advogados_own]
    advogados += [{"advogado": adv, "tipo": "admin"} for adv in advogados_admin]
    return advogados

def get_advogado_by_id(usuario, advogado_id, tipo=None):
    """
    Busca o advogado pelo id, distinguindo entre próprio e admin (se tipo for passado).
    Retorna o objeto Advogado ou None.
    """
    if tipo == "admin":
        if usuario.admin_id:
            admin = usuario.admin
            if admin:
                return admin.advogados.filter_by(id=advogado_id).first()
    else:
        return usuario.advogados.filter_by(id=advogado_id).first()
    return None

def get_advogados_colaboradores_disponiveis(usuario):
    """
    Retorna advogados colaboradores disponíveis para o usuário:
    - Se admin: retorna seus próprios advogados + principais dos associados
    - Se não-admin: retorna advogados do admin (principal + colaboradores)
    """
    advs = []
    if usuario.is_admin:
        # Advogados do próprio admin
        advs += usuario.advogados.order_by(Advogado.nome).all()
        # Advogados principais dos associados
        for associado in usuario.associados:
            principal = associado.advogados.filter_by(is_principal=True).first()
            if principal:
                advs.append(principal)
    elif usuario.admin_id and usuario.admin:
        admin = usuario.admin
        advs = admin.advogados.order_by(Advogado.nome).all()
    return advs