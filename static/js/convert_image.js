document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('convertForm');
    const statusMessage = document.getElementById('statusMessage');
    const submitButton = form.querySelector('button[type="submit"]');

    // Seletores para o input de múltiplos arquivos
    const fileInput = document.getElementById('image-files');
    const fileListDisplay = document.getElementById('file-list-display');
    const fileWrapper = document.getElementById('file-wrapper');

    // Atualiza a lista de arquivos na interface quando selecionados
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            // Cria uma lista mais limpa dos nomes dos arquivos
            let fileListHTML = '<strong>Imagens selecionadas:</strong><ul>';
            Array.from(fileInput.files).forEach(file => {
                // CORREÇÃO: Garante que tanto '<' quanto '>' sejam escapados para segurança.
                const safeName = file.name.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                fileListHTML += `<li>${safeName}</li>`;
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

        // Validação melhorada: verifica se a lista de arquivos está vazia
        if (fileInput.files.length === 0) {
            statusMessage.textContent = 'Erro: Por favor, selecione pelo menos um arquivo de imagem.';
            statusMessage.className = 'status-message alert alert-warning';
            return;
        }

        if (submitButton) submitButton.disabled = true;
        statusMessage.textContent = 'Convertendo imagens para PDF, por favor aguarde...';
        statusMessage.className = 'status-message alert alert-info';


        const formData = new FormData(form);

        try {
            const response = await fetch(form.dataset.action, {
                method: 'POST',
                body: formData, // Para FormData, o navegador define o Content-Type automaticamente. Não o defina manualmente.
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // --- LÓGICA DE DOWNLOAD DIRETO ---
                const downloadLink = document.createElement('a');
                downloadLink.href = result.download_url;
                downloadLink.download = result.filename;

                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);

                // --- MENSAGEM DE SUCESSO ATRASADA ---
                setTimeout(() => {
                    statusMessage.textContent = `PDF "${result.filename}" gerado com sucesso!`;
                    statusMessage.className = 'status-message alert alert-success';
                }, 500); // Atraso de 500ms para o usuário perceber o download

            } else {
                // Exibe o erro retornado pelo backend
                throw new Error(result.error || 'Ocorreu um erro desconhecido no servidor.');
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
            statusMessage.textContent = `Erro: ${error.message}`;
            statusMessage.className = 'status-message alert alert-danger';
        } finally {
            // Reabilita o botão no final da operação, seja sucesso ou falha.
            if (submitButton) submitButton.disabled = false;
        }
    });
});