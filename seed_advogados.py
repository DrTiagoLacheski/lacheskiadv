# seed_advogados.py
# Este script sincroniza os dados dos advogados do config.py com o banco de dados.

from app import create_app, db
from models import Advogado
from ferramentas.config import DADOS_ADVOGADOS

# Cria uma instância da aplicação para ter o contexto correto do banco de dados
app = create_app()

def sync_advogados():
    """
    Sincroniza a tabela de advogados com os dados do arquivo de configuração.
    - Se um advogado (baseado no CPF) já existe, atualiza seus dados.
    - Se não existe, cria um novo registro.
    É seguro executar este script múltiplas vezes.
    """
    with app.app_context():
        print("Iniciando sincronização de advogados...")

        for key, adv_data in DADOS_ADVOGADOS.items():
            # Busca o advogado no banco de dados pelo CPF, que é um campo único.
            existing_adv = Advogado.query.filter_by(cpf=adv_data['cpf']).first()

            # Prepara um dicionário com todos os dados para o modelo
            data_for_model = {
                "nome": adv_data['nome'],
                "is_principal": adv_data.get('is_principal', False),
                "estado_civil": adv_data['estado_civil'],
                "profissao": adv_data['profissao'],
                "cpf": adv_data['cpf'],
                "rg": adv_data.get('rg'), # .get() para campos que podem não existir
                "orgao_emissor": adv_data.get('orgao_emissor'),
                "oab_pr": adv_data.get('oab', {}).get('pr'),
                "oab_ro": adv_data.get('oab', {}).get('ro'),
                "oab_sp": adv_data.get('oab', {}).get('sp'),
                "endereco_profissional": adv_data['endereco_profissional']
            }

            if existing_adv:
                # Se o advogado já existe, atualiza cada campo.
                print(f"Advogado '{adv_data['nome']}' já existe. Atualizando dados...")
                for attr, value in data_for_model.items():
                    setattr(existing_adv, attr, value)
            else:
                # Se não existe, cria um novo.
                print(f"Adicionando novo advogado: '{adv_data['nome']}'")
                novo_advogado = Advogado(**data_for_model)
                db.session.add(novo_advogado)

        # Salva todas as alterações (updates e inserts) no banco de dados
        db.session.commit()
        print("\nSincronização de advogados concluída com sucesso!")

if __name__ == '__main__':
    sync_advogados()