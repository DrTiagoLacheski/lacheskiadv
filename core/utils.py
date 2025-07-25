# core/utils.py

import os
import shutil
import logging


def clean_temp_folder(app):
    """
    Limpa o conteúdo da pasta de arquivos temporários ('static/temp').
    Esta função é chamada na inicialização do servidor.
    """
    temp_dir = os.path.join(app.root_path, 'static', 'temp')
    app.logger.info(f"Verificando pasta temporária para limpeza em: {temp_dir}")

    try:
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
            app.logger.info("Pasta temporária antiga removida com sucesso.")

        os.makedirs(temp_dir, exist_ok=True)
        app.logger.info("Pasta temporária limpa e pronta para uso.")
    except Exception as e:
        app.logger.error(f"Falha ao limpar a pasta temporária: {e}")