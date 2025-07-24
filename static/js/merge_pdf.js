document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('mergeForm');
    if (!form) return; // Sai se o formulário não for encontrado

    // Elementos da interface
    const statusMessage = document.getElementById('statusMessage');
    const submitButton = form.querySelector('button[type="submit"]');
    const fileInput = document.getElementById('pdf-files');
    const fileListDisplay = document.getElementById('file-list-display');
    const fileWrapper = document.getElementById('file-wrapper');

    // Função para escapar HTML e prevenir XSS
    const escapeHTML = (str) => str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    // Evento para atualizar a lista de arquivos selecionados na UI
    fileInput.addEventListener('change', () => {
        const files = fileInput.files;
        if (files.length > 0) {
            let fileListHTML = '<strong>Arquivos selecionados:</strong><ul>';
            Array.from(files).forEach(file => {
                const safeName = escapeHTML(file.name);
                fileListHTML += `<li>${safeName} (${(file.size / 1024).toFixed(2)} KB)</li>`;
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
        event.preventDefault(); // Impede o envio padrão do formulário

        // Validação: verifica se pelo menos 2 arquivos foram selecionados
        if (fileInput.files.length < 2) {
            statusMessage.textContent = 'Erro: Por favor, selecione pelo menos dois arquivos PDF para unir.';
            statusMessage.className = 'status-message alert alert-warning';
            return;
        }

        // Desabilita o botão e mostra mensagem de processamento
        submitButton.disabled = true;
        statusMessage.textContent = 'Unindo os arquivos PDF, por favor aguarde...';
        statusMessage.className = 'status-message alert alert-info';

        const formData = new FormData(form);

        try {
            // Envia os dados para a rota do backend
            const response = await fetch(form.dataset.action, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // --- LÓGICA CORRETA PARA FORÇAR O DOWNLOAD ---
                const downloadLink = document.createElement('a');
                downloadLink.href = result.download_url;
                downloadLink.download = result.filename; // Atributo que força o download

                document.body.appendChild(downloadLink);
                downloadLink.click(); // Simula o clique para baixar
                document.body.removeChild(downloadLink); // Remove o link da página

                // Mostra mensagem de sucesso após um breve atraso
                setTimeout(() => {
                    statusMessage.innerHTML = `PDF <strong>"${escapeHTML(result.filename)}"</strong> unido com sucesso! O download foi iniciado.`;
                    statusMessage.className = 'status-message alert alert-success';
                }, 500);

            } else {
                // Se deu erro, mostra a mensagem retornada pelo servidor
                throw new Error(result.error || 'Ocorreu um erro desconhecido no servidor.');
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
            statusMessage.textContent = `Erro: ${error.message}`;
            statusMessage.className = 'status-message alert alert-danger';
        } finally {
            // Reabilita o botão no final da operação, seja sucesso ou falha
            submitButton.disabled = false;
        }
    });
});