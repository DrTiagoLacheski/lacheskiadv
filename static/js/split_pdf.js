document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('splitForm');
    if (!form) return;

    // --- Elementos da Interface ---
    const statusMessage = document.getElementById('statusMessage');
    const submitButton = form.querySelector('button[type="submit"]');
    const fileInput = document.getElementById('pdf-file');
    const pageRangesInput = document.getElementById('page_ranges');

    // Elementos da pré-visualização do ARQUIVO ORIGINAL
    const originalPreviewIcon = document.getElementById('original-preview-icon');
    const originalPreviewCard = document.getElementById('original-preview-card');
    const originalPreviewFrame = document.getElementById('original-preview-frame');

    // Elementos da pré-visualização do RESULTADO
    const resultPreviewIcon = document.getElementById('result-preview-icon');
    const resultPreviewCard = document.getElementById('result-preview-card');
    const resultPreviewFrame = document.getElementById('result-preview-frame');

    let originalFileObjectUrl = null;
    let resultFilePreviewUrl = null;

    // --- Funções Auxiliares ---
    const escapeHTML = (str) => str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    function setStatus(message, type) {
        statusMessage.innerHTML = message;
        statusMessage.className = `status-message alert alert-${type}`;
    }

    /**
     * Configura a lógica de hover para mostrar um card de pré-visualização interativo.
     * @param {HTMLElement} icon - O elemento do ícone que dispara o evento.
     * @param {HTMLElement} card - O card de preview a ser mostrado/escondido.
     * @param {HTMLElement} frame - O iframe dentro do card.
     * @param {function(): string} getUrlCallback - Função que retorna a URL a ser carregada no iframe.
     */
    function setupPreviewHover(icon, card, frame, getUrlCallback) {
        if (!icon || !card || !frame) return;

        // --- NOVO: Seleciona os controles dentro do card ---
        const closeButton = card.querySelector('.close-card');
        const openNewTabLink = card.querySelector('.open-in-new');

        let hideTimeoutId;

        const hideCard = () => {
            card.style.display = 'none';
            card.style.visibility = 'hidden';
            frame.src = 'about:blank'; // Limpa o iframe para parar o carregamento
        };

        const showCard = (event) => {
            clearTimeout(hideTimeoutId);

            const url = getUrlCallback();
            if (!url) return;

            // --- NOVO: Atualiza o link de "abrir em nova aba" ---
            if (openNewTabLink) {
                openNewTabLink.href = url;
            }

            if (card.style.display !== 'block') {
                card.style.visibility = 'hidden';
                card.style.display = 'flex'; // Usar flex para o layout interno
                card.style.left = '-9999px';
                frame.src = `${url}#view=FitH&toolbar=0&navpanes=0`;

                setTimeout(() => {
                    const cardWidth = card.offsetWidth;
                    const cardHeight = card.offsetHeight;
                    const viewportWidth = window.innerWidth;
                    const viewportHeight = window.innerHeight;
                    const margin = 20;

                    let finalLeft = event.clientX + margin;
                    let finalTop = event.clientY + margin;

                    if (finalLeft + cardWidth > viewportWidth) {
                        finalLeft = event.clientX - cardWidth - margin;
                    }
                    if (finalTop + cardHeight > viewportHeight) {
                        finalTop = event.clientY - cardHeight - margin;
                    }
                    if (finalLeft < 0) finalLeft = margin;
                    if (finalTop < 0) finalTop = margin;

                    card.style.left = `${finalLeft}px`;
                    card.style.top = `${finalTop}px`;
                    card.style.visibility = 'visible';
                }, 50);
            }
        };

        // Eventos para o ÍCONE
        icon.addEventListener('mouseenter', showCard);
        icon.addEventListener('mouseleave', () => {
            hideTimeoutId = setTimeout(hideCard, 300);
        });

        // Eventos para o CARD
        card.addEventListener('mouseenter', () => clearTimeout(hideTimeoutId));
        card.addEventListener('mouseleave', () => {
            hideTimeoutId = setTimeout(hideCard, 300);
        });

        // --- NOVO: Evento para o botão de fechar ---
        if (closeButton) {
            closeButton.addEventListener('click', (e) => {
                e.stopPropagation(); // Impede que o evento se propague
                hideCard();
            });
        }
    }

    // --- Lógica de Eventos da UI ---

    // 1. Quando um arquivo é selecionado
    fileInput.addEventListener('change', () => {
        if (originalFileObjectUrl) {
            URL.revokeObjectURL(originalFileObjectUrl);
        }
        if (resultPreviewIcon) resultPreviewIcon.style.display = 'none';

        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            document.querySelector('.file-name').textContent = escapeHTML(file.name);
            document.getElementById('file-input-container').classList.add('has-file');
            originalFileObjectUrl = URL.createObjectURL(file);
            if (originalPreviewIcon) originalPreviewIcon.style.display = 'inline-block';
        } else {
            document.querySelector('.file-name').textContent = 'Clique para selecionar o PDF';
            document.getElementById('file-input-container').classList.remove('has-file');
            originalFileObjectUrl = null;
            if (originalPreviewIcon) originalPreviewIcon.style.display = 'none';
        }
    });

    // 2. Quando o usuário termina de digitar as páginas
    pageRangesInput.addEventListener('blur', async () => {
        const pages = pageRangesInput.value.trim();
        if (fileInput.files.length === 0 || !pages) {
            if (resultPreviewIcon) resultPreviewIcon.style.display = 'none';
            return;
        }

        resultPreviewIcon.innerHTML = '<i class="spinner-border spinner-border-sm"></i>';
        resultPreviewIcon.style.display = 'inline-block';

        const formData = new FormData();
        formData.append('pdf', fileInput.files[0]);
        formData.append('page_ranges', pages);

        try {
            const response = await fetch('/ferramentas/preview-split-pdf', {
                method: 'POST',
                body: formData,
            });
            const result = await response.json();

            if (response.ok && result.success) {
                resultFilePreviewUrl = result.preview_url;
                resultPreviewIcon.innerHTML = '<i class="bi bi-eye-fill"></i>';
            } else {
                throw new Error(result.error || 'Falha ao gerar pré-visualização.');
            }
        } catch (error) {
            console.error('Erro na pré-visualização:', error);
            resultPreviewIcon.innerHTML = '<i class="bi bi-exclamation-triangle-fill text-danger"></i>';
        }
    });

    // 3. Configura os hovers para os dois ícones
    setupPreviewHover(originalPreviewIcon, originalPreviewCard, originalPreviewFrame, () => originalFileObjectUrl);
    setupPreviewHover(resultPreviewIcon, resultPreviewCard, resultPreviewFrame, () => resultFilePreviewUrl);


    // 4. Evento de submissão final do formulário
    form.addEventListener('submit', async function(event) {
        event.preventDefault();

        if (fileInput.files.length === 0) {
            setStatus('Erro: Por favor, selecione um arquivo PDF.', 'danger');
            return;
        }
        const pageRangesValue = pageRangesInput.value.trim();
        if (!pageRangesValue) {
            setStatus('Erro: Por favor, indique as páginas ou intervalos para extrair.', 'danger');
            return;
        }

        submitButton.disabled = true;
        setStatus('Dividindo o arquivo PDF, por favor aguarde...', 'info');

        const formData = new FormData(form);

        try {
            const response = await fetch(form.dataset.action, {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok && result.success) {
                const downloadLink = document.createElement('a');
                downloadLink.href = result.download_url;
                downloadLink.download = result.filename;
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);

                setTimeout(() => {
                    setStatus(`PDF <strong>"${escapeHTML(result.filename)}"</strong> dividido com sucesso! O download foi iniciado.`, 'success');
                }, 500);

            } else {
                throw new Error(result.error || 'Ocorreu um erro desconhecido no servidor.');
            }
        } catch (error) {
            console.error('Erro na submissão:', error);
            setStatus(`Erro: ${error.message}`, 'danger');
        } finally {
            submitButton.disabled = false;
        }
    });
});