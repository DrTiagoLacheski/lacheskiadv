# init_db.py
# Script para inicializar o banco de dados, criar usuários e perfis de advogado.

from app import create_app, db
from models import User, Advogado
from ferramentas.config import DADOS_ADVOGADOS

def initialize_database():
    """
    Cria usuários (admin e user) e perfis de advogado associados.
    Ajustado para funcionar com relacionamento correto de Advogado <-> User.
    """
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Iniciando script de inicialização do banco de dados...")

        # --- 1. Criar Usuário Admin ---
        owner_username = 'admin'
        owner_user = User.query.filter_by(username=owner_username).first()
        if not owner_user:
            print(f"Criando usuário admin: '{owner_username}'")
            owner_user = User(
                username=owner_username,
                email='admin@escritorio.com',
                is_admin=True
            )
            owner_user.set_password('asdf1234')
            db.session.add(owner_user)
            db.session.commit()
        else:
            print(f"Usuário admin '{owner_username}' já existe.")

        # --- 2. Criar Perfis de Advogado para Admin ---
        for key, adv_data in DADOS_ADVOGADOS.items():
            advogado_existente = Advogado.query.filter_by(cpf=adv_data['cpf']).first()
            if advogado_existente:
                print(f"Perfil de advogado para '{adv_data['nome']}' já existe. Pulando.")
                continue
            print(f"Criando perfil de advogado para '{adv_data['nome']}' e associando a '{owner_username}'.")
            novo_advogado = Advogado(
                user_id=owner_user.id,
                nome=adv_data['nome'],
                estado_civil=adv_data['estado_civil'],
                profissao=adv_data['profissao'],
                cpf=adv_data['cpf'],
                rg=adv_data.get('rg', ''),
                orgao_emissor=adv_data.get('orgao_emissor', ''),
                oab_pr=adv_data.get('oab', {}).get('pr', ''),
                oab_ro=adv_data.get('oab', {}).get('ro', ''),
                oab_sp=adv_data.get('oab', {}).get('sp', ''),
                endereco_profissional=adv_data['endereco_profissional'],
                is_principal=adv_data.get('is_principal', False)
            )
            db.session.add(novo_advogado)

        # --- 3. Criar Usuário Normal de Exemplo ---
        normal_username = 'user'
        normal_user = User.query.filter_by(username=normal_username).first()
        if not normal_user:
            print(f"Criando usuário normal: '{normal_username}'")
            normal_user = User(
                username=normal_username,
                email='user@exemplo.com',
                is_admin=False
            )
            normal_user.set_password('user')
            db.session.add(normal_user)
            db.session.flush()  # Para garantir que normal_user.id está disponível

            # Perfil principal
            default_advogado = Advogado(
                user_id=normal_user.id,
                nome="USUÁRIO PADRÃO",
                estado_civil="não informado",
                profissao="advogado",
                cpf="999.999.999-99",
                endereco_profissional="Endereço Padrão do Usuário",
                is_principal=True
            )
            db.session.add(default_advogado)

            # Perfil associado (exemplo)
            associate_advogado = Advogado(
                user_id=normal_user.id,
                nome="ASSOCIADO PADRÃO (TESTE)",
                estado_civil="não informado",
                profissao="advogado",
                cpf="888.888.888-88",
                endereco_profissional="Endereço do Associado de Teste",
                is_principal=False
            )
            db.session.add(associate_advogado)
        else:
            print(f"Usuário normal '{normal_username}' já existe.")

        db.session.commit()
        print("\nOperação de inicialização concluída com sucesso!")

if __name__ == '__main__':
    initialize_database()