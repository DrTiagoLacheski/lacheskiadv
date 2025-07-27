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
     * Mostra um card de preview automaticamente
     * @param {HTMLElement} card - O card de preview a ser mostrado
     * @param {HTMLElement} frame - O iframe dentro do card
     * @param {string} url - URL do PDF a ser carregado
     * @param {string} title - Título do card
     */
    function showPreviewCard(card, frame, url, title = 'Preview') {
        if (!card || !frame || !url) return;

        // Configura o card
        card.style.display = 'flex';
        card.style.visibility = 'visible';
        card.classList.add('loading');
        card.classList.remove('hiding');

        // Posicionamento automático no canto inferior direito
        card.style.position = 'fixed';
        card.style.bottom = '20px';
        card.style.right = '20px';
        card.style.width = '300px'; // Reduzido
        card.style.height = '400px'; // Reduzido

        // Atualiza o link de "abrir em nova aba"
        const openNewTabLink = card.querySelector('.open-in-new');
        if (openNewTabLink) {
            openNewTabLink.href = url;
        }

        // Adiciona título se não existir
        let cardHeader = card.querySelector('.card-header');
        if (!cardHeader) {
            cardHeader = document.createElement('div');
            cardHeader.className = 'card-header';
            card.insertBefore(cardHeader, card.firstChild);
        }
        cardHeader.textContent = title;

        // Adicionar controles de minimizar se não existirem
        setupCardControls(card);

        // Carrega o PDF
        frame.src = `${url}#view=FitH&toolbar=0&navpanes=0`;

        // Evento para quando o iframe carregar
        frame.onload = () => {
            card.classList.remove('loading');
            card.classList.add('loaded');
        };

        // Mostra o card com animação
        requestAnimationFrame(() => {
            card.classList.add('show');
        });
    }

    /**
     * Configura controles do card (minimizar/maximizar)
     * @param {HTMLElement} card - O card de preview
     */
    function setupCardControls(card) {
        let isMinimized = false;
        
        // Verificar se já existe botão de minimizar
        let minimizeBtn = card.querySelector('.minimize-card');
        if (!minimizeBtn) {
            const controls = card.querySelector('.card-controls');
            if (controls) {
                minimizeBtn = document.createElement('button');
                minimizeBtn.className = 'minimize-card';
                minimizeBtn.innerHTML = '−';
                minimizeBtn.title = 'Minimizar card';
                controls.insertBefore(minimizeBtn, controls.firstChild);
                
                // Event listener para minimizar/maximizar
                minimizeBtn.onclick = function(e) {
                    e.stopPropagation();
                    isMinimized = !isMinimized;
                    
                    if (isMinimized) {
                        card.classList.add('minimized');
                        minimizeBtn.innerHTML = '+';
                        minimizeBtn.title = 'Maximizar card';
                    } else {
                        card.classList.remove('minimized');
                        minimizeBtn.innerHTML = '−';
                        minimizeBtn.title = 'Minimizar card';
                    }
                };
            }
        }
        
        // Duplo clique no header para minimizar/maximizar
        const header = card.querySelector('.card-header');
        if (header && !header.hasMinimizeListener) {
            header.hasMinimizeListener = true;
            header.ondblclick = function() {
                if (minimizeBtn) minimizeBtn.click();
            };
            header.style.cursor = 'pointer';
            header.title = 'Duplo clique para minimizar/maximizar';
        }
    }

    /**
     * Esconde um card de preview
     * @param {HTMLElement} card - O card de preview a ser escondido
     * @param {HTMLElement} frame - O iframe dentro do card
     */
    function hidePreviewCard(card, frame) {
        if (!card || !frame) return;

        card.classList.remove('show');
        card.classList.add('hiding');

        setTimeout(() => {
            if (card.classList.contains('hiding')) {
                card.style.display = 'none';
                card.style.visibility = 'hidden';
                card.classList.remove('loading', 'loaded', 'hiding');
                frame.src = 'about:blank';
            }
        }, 300);
    }

    /**
     * Configura a lógica de hover para mostrar um card de pré-visualização interativo.
     * @param {HTMLElement} icon - O elemento do ícone que dispara o evento.
     * @param {HTMLElement} card - O card de preview a ser mostrado/escondido.
     * @param {HTMLElement} frame - O iframe dentro do card.
     * @param {function(): string} getUrlCallback - Função que retorna a URL a ser carregada no iframe.
     */
    function setupPreviewHover(icon, card, frame, getUrlCallback) {
        if (!icon || !card || !frame) {
            console.log('Preview hover setup failed - missing elements:', {icon, card, frame});
            return;
        }

        console.log('Setting up preview hover for:', icon.id);

        // --- NOVO: Seleciona os controles dentro do card ---
        const closeButton = card.querySelector('.close-card');
        const openNewTabLink = card.querySelector('.open-in-new');

        let hideTimeoutId;

        const hideCard = () => {
            clearTimeout(hideTimeoutId);
            
            // Se o card não está visível, não faz nada
            if (!card.classList.contains('show') || !cardVisible) {
                return;
            }
            
            cardVisible = false; // Reset da variável de controle
            card.classList.remove('show');
            card.classList.add('hiding');
            
            setTimeout(() => {
                // Verifica novamente se o card não foi reaberto
                if (card.classList.contains('hiding') && !card.classList.contains('show')) {
                    card.style.display = 'none';
                    card.style.visibility = 'hidden';
                    card.classList.remove('loading', 'loaded', 'hiding');
                    frame.src = 'about:blank';
                    // Remove classes do overlay (se existirem)
                    document.body.classList.remove('preview-active', 'overlay-visible');
                }
            }, 300);
        };

        const showCard = (event) => {
            clearTimeout(hideTimeoutId);

            const url = getUrlCallback();
            if (!url) return;

            // Se o card já está visível, não faz nada
            if (cardVisible) {
                return;
            }

            // Marca como visível imediatamente
            cardVisible = true;

            // --- Atualiza o link de "abrir em nova aba" ---
            if (openNewTabLink) {
                openNewTabLink.href = url;
            }

            // Remove qualquer estado anterior
            card.classList.remove('hiding');
            
            // Configura o card
            card.style.display = 'flex';
            card.style.visibility = 'visible';
            card.classList.add('loading');
            
            // NÃO adiciona overlay para evitar interferência com eventos do mouse

            // Calcula a posição e configura o card
            requestAnimationFrame(() => {
                const cardWidth = card.offsetWidth;
                const cardHeight = card.offsetHeight;
                const viewportWidth = window.innerWidth;
                const viewportHeight = window.innerHeight;
                const margin = 20;

                // Obter a posição do ícone para evitar sobreposição
                const iconRect = icon.getBoundingClientRect();
                
                let finalLeft = iconRect.right + margin; // Posiciona à direita do ícone
                let finalTop = iconRect.top;

                // Se não cabe à direita, posiciona à esquerda
                if (finalLeft + cardWidth > viewportWidth) {
                    finalLeft = iconRect.left - cardWidth - margin;
                }

                // Se não cabe na altura original, ajusta verticalmente
                if (finalTop + cardHeight > viewportHeight) {
                    finalTop = viewportHeight - cardHeight - margin;
                }

                // Garante que não saia da tela pela esquerda
                if (finalLeft < margin) {
                    finalLeft = margin;
                    // Se ainda assim sobrepõe o ícone, posiciona abaixo
                    finalTop = iconRect.bottom + margin;
                }

                // Define a posição final
                card.style.left = `${finalLeft}px`;
                card.style.top = `${finalTop}px`;
                
                // Carrega o PDF
                frame.src = `${url}#view=FitH&toolbar=0&navpanes=0`;

                // Evento para quando o iframe carregar
                frame.onload = () => {
                    card.classList.remove('loading');
                    card.classList.add('loaded');
                };
                
                // Mostra o card com animação
                requestAnimationFrame(() => {
                    card.classList.add('show');
                });
            });
        };

        // Variável para rastrear se o mouse está sobre o ícone ou card
        let mouseOverIcon = false;
        let mouseOverCard = false;
        let cardVisible = false;

        // Eventos para o ÍCONE
        icon.addEventListener('mouseenter', (event) => {
            console.log('Mouse entered icon:', icon.id);
            mouseOverIcon = true;
            clearTimeout(hideTimeoutId);
            
            // Só mostra o card se ele não estiver já visível
            if (!cardVisible) {
                console.log('Showing card for:', icon.id);
                showCard(event);
            }
        });

        // Mantém o estado enquanto o mouse está sobre o ícone
        icon.addEventListener('mousemove', () => {
            mouseOverIcon = true;
            clearTimeout(hideTimeoutId);
        });
        
        icon.addEventListener('mouseleave', () => {
            mouseOverIcon = false;
            
            // Delay maior para dar tempo de mover para o card
            hideTimeoutId = setTimeout(() => {
                if (!mouseOverIcon && !mouseOverCard) {
                    hideCard();
                }
            }, 500); // Aumentei para 500ms para dar mais tempo
        });

        // Eventos para o CARD
        card.addEventListener('mouseenter', () => {
            mouseOverCard = true;
            clearTimeout(hideTimeoutId);
            card.classList.remove('hiding');
        });
        
        card.addEventListener('mouseleave', () => {
            mouseOverCard = false;
            
            // Delay menor para o card, já que o usuário saiu explicitamente
            hideTimeoutId = setTimeout(() => {
                if (!mouseOverIcon && !mouseOverCard) {
                    hideCard();
                }
            }, 200);
        });

        // --- Evento para o botão de fechar ---
        if (closeButton) {
            closeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                clearTimeout(hideTimeoutId);
                mouseOverIcon = false;
                mouseOverCard = false;
                cardVisible = false;
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
        if (resultPreviewIcon) {
            resultPreviewIcon.style.display = 'none';
            resultPreviewIcon.classList.remove('has-content');
        }

        if (fileInput.files.length > 0) {
            const file = fileInput.files[0];
            document.querySelector('.file-name').textContent = escapeHTML(file.name);
            document.getElementById('file-input-container').classList.add('has-file');
            originalFileObjectUrl = URL.createObjectURL(file);
            
            // Mostra automaticamente o card de preview do arquivo original
            setTimeout(() => {
                showPreviewCard(originalPreviewCard, originalPreviewFrame, originalFileObjectUrl, 'PDF Original');
            }, 500); // Pequeno delay para dar tempo do arquivo ser processado
            
        } else {
            document.querySelector('.file-name').textContent = 'Clique para selecionar o PDF';
            document.getElementById('file-input-container').classList.remove('has-file');
            originalFileObjectUrl = null;
            hidePreviewCard(originalPreviewCard, originalPreviewFrame);
        }
    });

    // 2. Quando o usuário termina de digitar as páginas
    pageRangesInput.addEventListener('blur', async () => {
        const pages = pageRangesInput.value.trim();
        if (fileInput.files.length === 0 || !pages) {
            hidePreviewCard(resultPreviewCard, resultPreviewFrame);
            return;
        }

        // Mostra loading no card de resultado
        resultPreviewCard.style.display = 'flex';
        resultPreviewCard.style.visibility = 'visible';
        resultPreviewCard.classList.add('loading');
        resultPreviewCard.style.position = 'fixed';
        resultPreviewCard.style.bottom = '20px';
        resultPreviewCard.style.left = '20px'; // Lado esquerdo para não sobrepor o original
        resultPreviewCard.style.width = '380px';
        resultPreviewCard.style.height = '500px';

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
                showPreviewCard(resultPreviewCard, resultPreviewFrame, resultFilePreviewUrl, 'Resultado');
            } else {
                throw new Error(result.error || 'Falha ao gerar pré-visualização.');
            }
        } catch (error) {
            console.error('Erro na pré-visualização:', error);
            hidePreviewCard(resultPreviewCard, resultPreviewFrame);
            
            // Mostra erro no card
            resultPreviewCard.classList.remove('loading');
            resultPreviewCard.classList.add('error');
            resultPreviewFrame.style.display = 'none';
            
            let errorDiv = resultPreviewCard.querySelector('.error-message');
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'error-message';
                resultPreviewCard.appendChild(errorDiv);
            }
            errorDiv.textContent = 'Erro ao gerar pré-visualização';
        }
    });

    // 3. Adiciona eventos de fechar aos cards
    if (originalPreviewCard) {
        const closeButton = originalPreviewCard.querySelector('.close-card');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                hidePreviewCard(originalPreviewCard, originalPreviewFrame);
            });
        }
    }

    if (resultPreviewCard) {
        const closeButton = resultPreviewCard.querySelector('.close-card');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                hidePreviewCard(resultPreviewCard, resultPreviewFrame);
            });
        }
    }


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