document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('mergeForm');
    const statusMessage = document.getElementById('statusMessage');

    const fileInput = document.getElementById('pdf-files');
    const fileListDisplay = document.getElementById('file-list-display');
    const fileWrapper = document.getElementById('file-wrapper');

    // Evento para atualizar a lista de ficheiros selecionados (sem alterações)
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            let fileListHTML = '<strong>Ficheiros selecionados:</strong><ul>';
            Array.from(fileInput.files).forEach(file => {
                fileListHTML += `<li>${file.name} (${(file.size / 1024).toFixed(2)} KB)</li>`;
            });
            fileListHTML += '</ul>';
            fileListDisplay.innerHTML = fileListHTML;
            fileWrapper.classList.add('has-files');
        } else {
            fileListDisplay.innerHTML = 'Nenhum ficheiro selecionado.';
            fileWrapper.classList.remove('has-files');
        }
    });

    // Evento de submissão do formulário
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        const url = form.dataset.action;

        const formData = new FormData(form);
        const files = formData.getAll('pdfs');

        // Validação (sem alterações)
        if (files.length > 0 && files[0].size === 0) { // Checa se o primeiro ficheiro está vazio
            statusMessage.textContent = 'Erro: Nenhum ficheiro foi selecionado.';
            statusMessage.className = 'status-message error';
            return;
        }
        if (files.length < 2) {
            statusMessage.textContent = 'Erro: Selecione pelo menos dois ficheiros para unir.';
            statusMessage.className = 'status-message error';
            return;
        }

        statusMessage.textContent = 'A processar e unir os ficheiros...';
        statusMessage.className = 'status-message processing';

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok && result.success) {
                statusMessage.textContent = 'Ficheiros unidos com sucesso! A iniciar o download...';
                statusMessage.className = 'status-message success';

                // --- ALTERAÇÃO PRINCIPAL ---
                // Em vez de mostrar um modal, inicia o download diretamente
                // redirecionando o navegador para a URL de download.
                window.location.href = result.download_url;

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

});