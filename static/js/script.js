document.addEventListener('DOMContentLoaded', function() {
    // Seletores genéricos para funcionar em todas as páginas
    const forms = document.querySelectorAll('form.form');
    const clearButtons = document.querySelectorAll('#limparCampos');
    const modal = document.getElementById('downloadModal');
    const closeModalButton = modal ? modal.querySelector('.close') : null;
    const openFileButton = document.getElementById('abrirArquivo');
    // ATUALIZAÇÃO: Seleciona todos os campos de CPF pela classe
    const cpfInputs = document.querySelectorAll('.cpf-mask');

    // Função para aplicar a máscara de CPF
    function formatCPF(event) {
        let value = event.target.value.replace(/\D/g, ''); // Remove tudo que não é dígito
        
        // Aplica a máscara: 000.000.000-00
        if (value.length > 9) {
            value = value.replace(/^(\d{3})(\d{3})(\d{3})(\d{2}).*/, '$1.$2.$3-$4');
        } else if (value.length > 6) {
            value = value.replace(/^(\d{3})(\d{3})(\d{1,3}).*/, '$1.$2.$3');
        } else if (value.length > 3) {
            value = value.replace(/^(\d{3})(\d{1,3}).*/, '$1.$2');
        }
        
        event.target.value = value;
    }

    // ATUALIZAÇÃO: Aplica a máscara a todos os campos de CPF encontrados
    cpfInputs.forEach(input => {
        input.addEventListener('input', formatCPF);
    });

    // Função genérica para lidar com a submissão de formulários via Fetch
    async function handleFormSubmit(event) {
        event.preventDefault(); // Previne o recarregamento da página

        const form = event.target;
        const url = form.dataset.action;
        const statusMessage = form.querySelector('#statusMessage');

        if (!url) {
            console.error('Formulário sem o atributo data-action.');
            return;
        }

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // ATUALIZAÇÃO: Limpa a máscara de todos os campos de CPF antes de enviar
        for (const key in data) {
            if (key.includes('cpf')) {
                data[key] = data[key].replace(/\D/g, '');
            }
        }

        statusMessage.textContent = 'A gerar documento, por favor aguarde...';
        statusMessage.className = 'status-message processing';

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (response.ok && result.success) {
                statusMessage.textContent = 'Documento gerado com sucesso!';
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
    }

    // Função para exibir o modal de download
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

    // Adiciona o listener de submissão a cada formulário encontrado
    forms.forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });

    // Adiciona o listener para os botões de limpar
    clearButtons.forEach(button => {
        button.addEventListener('click', () => {
            const form = button.closest('form');
            if (form) {
                form.reset();
                const statusMessage = form.querySelector('#statusMessage');
                if (statusMessage) {
                    statusMessage.textContent = 'Preencha os dados e clique em gerar.';
                    statusMessage.className = 'status-message';
                }
            }
        });
    });

    // Adiciona o listener para fechar o modal
    if (closeModalButton) {
        closeModalButton.onclick = () => { modal.style.display = 'none'; };
    }
    window.onclick = (event) => {
        if (event.target == modal) { modal.style.display = 'none'; }
    };
});
