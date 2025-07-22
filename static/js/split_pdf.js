document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('splitForm');
    const statusMessage = document.getElementById('statusMessage');
    
    const fileInput = document.getElementById('pdf-file');
    const fileNameDisplay = document.querySelector('#file-input-container .file-name');
    const fileInputContainer = document.getElementById('file-input-container');

    const modal = document.getElementById('downloadModal');
    const closeModalButton = modal ? modal.querySelector('.close') : null;
    const openFileButton = document.getElementById('abrirArquivo');

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileNameDisplay.textContent = fileInput.files[0].name;
            fileInputContainer.classList.add('has-file');
        } else {
            fileNameDisplay.textContent = 'Clique para selecionar o PDF';
            fileInputContainer.classList.remove('has-file');
        }
    });

    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        const url = form.dataset.action;
        const formData = new FormData(form);
        const file = formData.get('pdf');
        const pageRanges = formData.get('page_ranges');

        if (!file || file.size === 0) {
            statusMessage.textContent = 'Erro: Por favor, selecione um arquivo PDF.';
            statusMessage.className = 'status-message error';
            return;
        }
        if (!pageRanges.trim()) {
            statusMessage.textContent = 'Erro: Por favor, indique as páginas a serem extraídas.';
            statusMessage.className = 'status-message error';
            return;
        }

        statusMessage.textContent = 'Dividindo o arquivo PDF...';
        statusMessage.className = 'status-message processing';

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
            });
            const result = await response.json();

            if (response.ok && result.success) {
                statusMessage.textContent = 'Arquivo dividido com sucesso!';
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
