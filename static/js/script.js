document.addEventListener('DOMContentLoaded', function() {

    /**
     * Função genérica para lidar com a submissão de formulários que geram documentos.
     * @param {Event} e - O evento de submissão do formulário.
     */
    async function handleFormSubmit(e) {
        e.preventDefault(); // Impede o recarregamento da página

        const form = e.target;
        const statusMessage = form.querySelector('.status-message');
        const submitButton = form.querySelector('button[type="submit"]');

        // Desabilita o botão para evitar cliques duplos
        if (submitButton) submitButton.disabled = true;

        // Mostra mensagem de processamento
        statusMessage.textContent = 'Gerando documento, por favor aguarde...';
        statusMessage.className = 'status-message alert alert-info';

        try {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());

            const response = await fetch(form.dataset.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                // Se o backend retornar um erro, lança uma exceção com a mensagem
                throw new Error(result.error || 'Ocorreu um erro desconhecido no servidor.');
            }

            // --- LÓGICA DE DOWNLOAD DIRETO ---
            const downloadLink = document.createElement('a');
            downloadLink.href = result.download_url;
            downloadLink.download = result.filename;
            document.body.appendChild(downloadLink);
            downloadLink.click();
            document.body.removeChild(downloadLink);

            // --- MENSAGEM DE SUCESSO ATRASADA ---
            // Adiciona um pequeno atraso para que o usuário perceba o início do download
            // antes da mensagem de sucesso final aparecer.
            setTimeout(() => {
                statusMessage.textContent = `Documento "${result.filename}" gerado com sucesso!`;
                statusMessage.className = 'status-message alert alert-success';
            }, 500); // Atraso de 500ms

        } catch (error) {
            console.error('Erro ao gerar documento:', error);
            statusMessage.textContent = `Erro: ${error.message}`;
            statusMessage.className = 'status-message alert alert-danger';
        } finally {
            // Reabilita o botão após a operação
            if (submitButton) submitButton.disabled = false;
        }
    }

    /**
     * Aplica uma máscara de CPF/CNPJ a um campo de input.
     * @param {HTMLInputElement} input - O elemento do input.
     */
    function applyCpfMask(input) {
        input.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) { // CPF
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
            } else { // CNPJ
                value = value.replace(/^(\d{2})(\d)/, '$1.$2');
                value = value.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
                value = value.replace(/\.(\d{3})(\d)/, '.$1/$2');
                value = value.replace(/(\d{4})(\d)/, '$1-$2');
            }
            e.target.value = value.substring(0, 18); // Limita o tamanho para CNPJ
        });
    }

    // --- INICIALIZAÇÃO ---

    // Encontra todos os formulários que geram documentos e anexa o evento
    const generatorForms = document.querySelectorAll('.form');
    generatorForms.forEach(form => {
        // Garante que só formulários com data-action sejam processados
        if (form.dataset.action) {
            form.addEventListener('submit', handleFormSubmit);
        }

        // Anexa o evento ao botão de limpar campos específico de cada formulário
        const clearButton = form.querySelector('#limparCampos');
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                form.reset();
                const statusMessage = form.querySelector('.status-message');
                if (statusMessage) {
                    statusMessage.textContent = 'Preencha os dados e clique em \'Gerar\'';
                    statusMessage.className = 'status-message';
                }
            });
        }
    });

    // Encontra todos os campos com a máscara de CPF/CNPJ e a aplica
    const cpfFields = document.querySelectorAll('.cpf-mask');
    cpfFields.forEach(applyCpfMask);
});