document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('convertForm');
    const statusMessage = document.getElementById('statusMessage');
    
    // ATUALIZAÇÃO: Seletores para o novo input múltiplo
    const fileInput = document.getElementById('image-files');
    const fileListDisplay = document.getElementById('file-list-display');
    const fileWrapper = document.getElementById('file-wrapper');

    // Elementos do Modal
    const modal = document.getElementById('downloadModal');
    const closeModalButton = modal ? modal.querySelector('.close') : null;
    const openFileButton = document.getElementById('abrirArquivo');

    // Atualiza a lista de arquivos na interface quando selecionados
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            let fileListHTML = '<strong>Imagens selecionadas:</strong><ul>';
            Array.from(fileInput.files).forEach(file => {
                fileListHTML += `<li>${file.name}</li>`;
            });
            fileListHTML += '</ul>';
            fileListDisplay.innerHTML = fileListHTML;
            fileWrapper.classList.add('has-files');
        } else {
            fileListDisplay.innerHTML = 'Nenhum arquivo selecionado.';
            fileWrapper.classList.remove('has-files');
        }
    });

    // Evento de submissão do formulário
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        const url = form.dataset.action;

        const formData = new FormData(form);
        const files = formData.getAll('images');

        if (files[0].size === 0) {
            statusMessage.textContent = 'Erro: Por favor, selecione pelo menos um arquivo de imagem.';
            statusMessage.className = 'status-message error';
            return;
        }

        statusMessage.textContent = 'Convertendo imagens para PDF...';
        statusMessage.className = 'status-message processing';

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok && result.success) {
                statusMessage.textContent = 'Conversão concluída com sucesso!';
                statusMessage.className = 'status-message success';
                showDownloadModal(result.filename, result.download_url);
            } else {
                statusMessage.textContent = result.error || 'Ocorreu um erro desconhecido.';
                statusMessage.className = 'status-message error';
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
            statusMessage.textContent = 'Erro de conexão. Verifique a sua internet e tente novamente.';
            statusMessage.className = 'status-message error';
        }
    });

    // Funções do Modal
    function showDownloadModal(filename, downloadUrl) {
        if (!modal) return;
        const modalMessage = modal.querySelector('#modalMessage');
        const downloadLink = modal.querySelector('#downloadLink');
        modalMessage.textContent = `O seu ficheiro "${filename}" está pronto.`;
        downloadLink.href = downloadUrl;
        if (openFileButton) {
            openFileButton.onclick = () => window.open(downloadUrl, '_blank');
        }
        modal.style.display = 'block';
    }

    if (closeModalButton) {
        closeModalButton.onclick = () => { modal.style.display = 'none'; };
    }
    window.onclick = (event) => {
        if (event.target == modal) { modal.style.display = 'none'; }
    };
});
