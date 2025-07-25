# init_db.py
# Este script cria usuários e associa perfis de advogado a eles.

from app import create_app, db
from models import User, Advogado
# A fonte de dados agora vem do config.py de ferramentas
from ferramentas.config import DADOS_ADVOGADOS


def initialize_database():
    """
    Cria os usuários (admin e user) e popula a tabela de advogados,
    associando os perfis corretos a cada um.
    """
    app = create_app()
    with app.app_context():
        print("Iniciando script de inicialização do banco de dados...")

        # --- 1. Criar o Usuário Dono da Conta (admin) ---
        owner_username = 'admin'
        owner_user = User.query.filter_by(username=owner_username).first()

        if not owner_user:
            print(f"Criando usuário dono da conta: '{owner_username}'")
            owner_user = User(
                username=owner_username,
                email='admin@escritorio.com',
                is_admin=True
            )
            owner_user.set_password('102030')  # Use uma senha forte em produção
            db.session.add(owner_user)
            db.session.commit()
        else:
            print(f"Usuário dono da conta '{owner_username}' já existe.")

        # --- 2. Sincronizar os Perfis de Advogado para a conta 'admin' ---
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

        # --- 3. Criar um Usuário Normal de Exemplo (user) com múltiplos perfis ---
        normal_username = 'user'
        normal_user = User.query.filter_by(username=normal_username).first()

        if not normal_user:
            print(f"Criando usuário normal de exemplo: '{normal_username}'")
            normal_user = User(
                username=normal_username,
                email='user@exemplo.com',
                is_admin=False
            )
            normal_user.set_password('user')

            # Cria um perfil de advogado principal para este usuário
            default_advogado = Advogado(
                nome="USUÁRIO PADRÃO",
                estado_civil="não informado",
                profissao="advogado",
                cpf="999.999.999-99",
                endereco_profissional="Endereço Padrão do Usuário",
                is_principal=True
            )

            # --- NOVO: Cria um perfil de advogado associado para este usuário ---
            associate_advogado = Advogado(
                nome="ASSOCIADO PADRÃO (TESTE)",
                estado_civil="não informado",
                profissao="advogado",
                cpf="888.888.888-88",  # CPF único para o associado de teste
                endereco_profissional="Endereço do Associado de Teste",
                is_principal=False  # Importante: este não é o principal
            )

            # Associa ambos os perfis ao usuário 'user'
            normal_user.advogados.append(default_advogado)
            normal_user.advogados.append(associate_advogado)

            db.session.add(normal_user)
        else:
            print(f"Usuário normal de exemplo '{normal_username}' já existe.")

        # --- 4. Salva todas as alterações no banco ---
        db.session.commit()
        print("\nOperação de inicialização concluída com sucesso!")


if __name__ == '__main__':
    initialize_database()