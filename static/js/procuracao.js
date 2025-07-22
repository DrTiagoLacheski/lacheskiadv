document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('procuracaoForm');
    const statusMessage = document.getElementById('statusMessage');
    const modal = document.getElementById('downloadModal');
    const closeModal = document.querySelector('.close');
    const downloadLink = document.getElementById('downloadLink');
    const abrirArquivoBtn = document.getElementById('abrirArquivo');

    // Máscara e validação de CPF
    const cpfInput = document.getElementById('cpf');
    if (cpfInput) {
        cpfInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
            e.target.value = value;
        });
    }

    // Validação antes do envio
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Validação do CPF
        const cpf = document.getElementById('cpf').value.replace(/\D/g, '');
        if (cpf.length !== 11) {
            statusMessage.textContent = 'CPF deve conter 11 dígitos';
            statusMessage.className = 'status-message error';
            document.getElementById('cpf').focus();
            return;
        }

        statusMessage.textContent = 'Gerando procuração...';
        statusMessage.className = 'status-message processing';

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
                throw new Error(result.error || 'Erro ao gerar procuração');
            }

            // Configura o modal de download
            downloadLink.href = result.download_url;
            downloadLink.download = result.filename;
            document.getElementById('modalMessage').textContent =
                `Procuração "${result.filename}" gerada com sucesso!`;

            statusMessage.textContent = 'Procuração pronta para download!';
            statusMessage.className = 'status-message success';
            modal.style.display = 'block';

        } catch (error) {
            console.error('Erro:', error);
            statusMessage.textContent = `Erro: ${error.message}`;
            statusMessage.className = 'status-message error';
        }
    });

    // Fechar modal
    closeModal.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Abrir arquivo em nova aba
    abrirArquivoBtn.addEventListener('click', () => {
        if (downloadLink.href) {
            window.open(downloadLink.href, '_blank');
        }
    });

    // Fechar modal ao clicar fora
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
});