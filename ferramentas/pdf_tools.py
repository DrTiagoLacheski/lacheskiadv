# pdf_tools.py
# Contém a lógica para manipular arquivos PDF.

import os
import re
from pypdf import PdfReader, PdfWriter
from fpdf import FPDF
from PIL import Image  # <--- IMPORTANTE: Adicionado para ler as dimensões da imagem


# --- FUNÇÃO AUXILIAR PARA INTERPRETAR PÁGINAS ---
def parse_page_ranges(page_string, max_pages):
    """Interpreta uma string de páginas (ex: '1, 3-5, 8') e retorna uma lista de índices (base 0)."""
    pages_to_extract = set()
    parts = page_string.replace(" ", "").split(',')
    for part in parts:
        if not part:
            continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start > end:
                    start, end = end, start  # Inverte se estiver fora de ordem
                for i in range(start, end + 1):
                    if 1 <= i <= max_pages:
                        pages_to_extract.add(i - 1)
            except ValueError:
                raise ValueError(f"Intervalo inválido: '{part}'")
        else:
            try:
                page_num = int(part)
                if 1 <= page_num <= max_pages:
                    pages_to_extract.add(page_num - 1)
            except ValueError:
                raise ValueError(f"Número de página inválido: '{part}'")
    return sorted(list(pages_to_extract))


# --- FUNÇÃO PRINCIPAL PARA DIVIDIR PDF ---
def split_pdf(pdf_path, page_string, output_dir, output_filename_user):
    """
    Extrai páginas de um PDF com base em uma string de seleção.
    """
    if not os.path.exists(pdf_path):
        print(f"Erro: Arquivo de entrada não encontrado: {pdf_path}")
        return None

    try:
        reader = PdfReader(pdf_path)
        writer = PdfWriter()

        total_pages = len(reader.pages)
        pages_to_extract_indices = parse_page_ranges(page_string, total_pages)

        if not pages_to_extract_indices:
            raise ValueError("Nenhuma página válida foi selecionada para extração.")

        for index in pages_to_extract_indices:
            writer.add_page(reader.pages[index])

        # Lógica para nome do arquivo
        base_name = re.sub(r'[^a-zA-Z0-9_\- ]', '_',
                           output_filename_user) if output_filename_user else "Documento_Dividido"
        output_filename = f"{base_name}.pdf" if not base_name.lower().endswith('.pdf') else base_name
        output_path = os.path.join(output_dir, output_filename)

        counter = 1
        original_path = output_path
        while os.path.exists(output_path):
            name, ext = os.path.splitext(original_path)
            output_path = f"{name}_{counter}{ext}"
            counter += 1

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"PDF dividido com sucesso: {output_path}")
        return output_path

    except Exception as e:
        print(f"Erro ao dividir PDF: {e}")
        raise e


def merge_pdfs(file_paths, output_dir, output_filename_user):
    """
    Une múltiplos arquivos PDF em um único arquivo.
    """
    if not file_paths or len(file_paths) < 2:
        return None
    merger = PdfWriter()
    try:
        for pdf_path in file_paths:
            if os.path.exists(pdf_path):
                merger.append(pdf_path)
        base_name = re.sub(r'[^a-zA-Z0-9_\- ]', '_',
                           output_filename_user) if output_filename_user else "Documento_Unido"
        output_filename = f"{base_name}.pdf" if not base_name.lower().endswith('.pdf') else base_name
        output_path = os.path.join(output_dir, output_filename)
        counter = 1
        original_path = output_path
        while os.path.exists(output_path):
            name, ext = os.path.splitext(original_path)
            output_path = f"{name}_{counter}{ext}"
            counter += 1
        merger.write(output_path)
        return output_path
    except Exception as e:
        print(f"Ocorreu um erro ao unir os PDFs: {e}")
        return None
    finally:
        merger.close()


# --- FUNÇÃO DE CONVERSÃO DE IMAGEM (CORRIGIDA) ---
def convert_images_to_pdf(image_paths, output_dir, output_filename_user):
    """
    Converte uma lista de arquivos de imagem em um único arquivo PDF,
    ajustando cada imagem para caber na página A4 sem cortes e mantendo a proporção.
    """
    if not image_paths:
        return None
    try:
        # Lógica para nome do arquivo (sem alterações)
        base_name = re.sub(r'[^a-zA-Z0-9_\- ]', '_',
                           output_filename_user) if output_filename_user else "Documento_Convertido"
        output_filename = f"{base_name}.pdf" if not base_name.lower().endswith('.pdf') else base_name
        output_path = os.path.join(output_dir, output_filename)
        counter = 1
        original_path = output_path
        while os.path.exists(output_path):
            name, ext = os.path.splitext(original_path)
            output_path = f"{name}_{counter}{ext}"
            counter += 1

        pdf = FPDF(orientation='P', unit='mm', format='A4')

        # Dimensões úteis da página A4 (210x297mm) com margens de 10mm de cada lado
        page_width_mm = 210 - 20
        page_height_mm = 297 - 20

        for image_path in image_paths:
            if not os.path.exists(image_path):
                continue

            # Usa Pillow para obter as dimensões da imagem em pixels
            with Image.open(image_path) as img:
                img_width_px, img_height_px = img.size

            # Calcula a proporção da imagem
            aspect_ratio = img_width_px / img_height_px

            # Determina as novas dimensões em mm para caber na página, mantendo a proporção
            if aspect_ratio > 1:  # Imagem é paisagem (mais larga que alta)
                new_width = page_width_mm
                new_height = new_width / aspect_ratio
                # Se, mesmo assim, a altura for maior que a da página, recalcula com base na altura
                if new_height > page_height_mm:
                    new_height = page_height_mm
                    new_width = new_height * aspect_ratio
            else:  # Imagem é retrato (mais alta que larga) ou quadrada
                new_height = page_height_mm
                new_width = new_height * aspect_ratio
                # Se, mesmo assim, a largura for maior que a da página, recalcula com base na largura
                if new_width > page_width_mm:
                    new_width = page_width_mm
                    new_height = new_width / aspect_ratio

            # Calcula a posição para centralizar a imagem na página
            x_pos = (210 - new_width) / 2
            y_pos = (297 - new_height) / 2

            pdf.add_page()
            pdf.image(image_path, x=x_pos, y=y_pos, w=new_width, h=new_height)

        if not pdf.pages:
            return None

        pdf.output(output_path)
        return output_path
    except Exception as e:
        print(f"Ocorreu um erro durante a conversão das imagens para PDF: {e}")
        # Lança a exceção para que a rota possa capturá-la e informar o usuário
        raise e


def cleanup_files(file_paths):
    """
    Exclui uma lista de arquivos. Usado para limpar os uploads temporários.
    """
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"Erro ao remover o arquivo {path}: {e}")
