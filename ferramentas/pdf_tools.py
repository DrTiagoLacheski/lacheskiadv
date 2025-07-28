# ferramentas/pdf_tools.py (Versão com a nova funcionalidade)

import os
import re
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader


# --- FUNÇÃO AUXILIAR PARA INTERPRETAR PÁGINAS (COM LÓGICA MELHORADA) ---
def parse_page_ranges(page_string, max_pages):
    """
    Interpreta uma string de páginas (ex: '1, 3-5, 8, 10-') e retorna uma lista de índices (base 0).
    Suporta intervalos abertos como '10-' (da página 10 até o final) e '-5' (do início até a página 5).
    """
    pages_to_extract = set()
    # Remove espaços e divide a string por vírgulas
    parts = page_string.replace(" ", "").split(',')

    for part in parts:
        if not part:
            continue

        # Se a parte contém um hífen, é um intervalo
        if '-' in part:
            try:
                range_parts = part.split('-')
                start_str = range_parts[0]
                end_str = range_parts[1]

                # Define o início: se vazio (ex: '-5'), começa em 1. Senão, converte para int.
                start = int(start_str) if start_str else 1
                # Define o fim: se vazio (ex: '10-'), vai até a última página. Senão, converte para int.
                end = int(end_str) if end_str else max_pages

                # Garante que o intervalo seja válido (start <= end)
                if start > end:
                    start, end = end, start

                # Adiciona todas as páginas do intervalo ao conjunto
                for i in range(start, end + 1):
                    if 1 <= i <= max_pages:
                        pages_to_extract.add(i - 1)  # Converte para índice base 0

            except (ValueError, IndexError):
                # Captura erros de formatação como '3-a' ou '-'
                raise ValueError(f"Intervalo inválido: '{part}'")
        else:
            # Se não for um intervalo, é uma página única
            try:
                page_num = int(part)
                if 1 <= page_num <= max_pages:
                    pages_to_extract.add(page_num - 1) # Converte para índice base 0
            except ValueError:
                raise ValueError(f"Número de página inválido: '{part}'")

    # Retorna a lista de índices, ordenada
    return sorted(list(pages_to_extract))


# --- O RESTANTE DO ARQUIVO pdf_tools.py PERMANECE IGUAL ---

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
        from PIL import Image
        import os
        import re

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

        page_width, page_height = A4
        c = canvas.Canvas(output_path, pagesize=A4)

        for image_path in image_paths:
            if not os.path.exists(image_path):
                continue

            with Image.open(image_path) as img:
                img_width_px, img_height_px = img.size
                aspect_ratio = img_width_px / img_height_px

            # Calcula as dimensões para caber na página A4 (em pontos)
            margin = 28.35  # 10mm em pontos
            max_width = page_width - 2 * margin
            max_height = page_height - 2 * margin

            if aspect_ratio > 1:
                new_width = max_width
                new_height = new_width / aspect_ratio
                if new_height > max_height:
                    new_height = max_height
                    new_width = new_height * aspect_ratio
            else:
                new_height = max_height
                new_width = new_height * aspect_ratio
                if new_width > max_width:
                    new_width = max_width
                    new_height = new_width / aspect_ratio

            x_pos = (page_width - new_width) / 2
            y_pos = (page_height - new_height) / 2

            c.drawImage(ImageReader(image_path), x_pos, y_pos, width=new_width, height=new_height)
            c.showPage()

        if c.getPageNumber() == 1 and not os.path.exists(image_paths[0]):
            return None

        c.save()
        return output_path
    except Exception as e:
        print(f"Ocorreu um erro durante a conversão das imagens para PDF: {e}")
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