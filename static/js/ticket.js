// static/js/ticket.js

document.addEventListener('DOMContentLoaded', function() {
    // Pega o contêiner principal que agora armazena as URLs e o ID do ticket
    const ticketContainer = document.getElementById('ticket-container');
    if (!ticketContainer) {
        console.error('Elemento #ticket-container não encontrado. O script não pode continuar.');
        return; // Sai se o contêiner não for encontrado
    }

    // Lê as URLs e o ID dos atributos data-*
    const ticketId = ticketContainer.dataset.ticketId;
    const reorderUrl = ticketContainer.dataset.reorderUrl;
    const renameUrl = ticketContainer.dataset.renameUrl;

    // ---- LÓGICA PARA REORDENAR ANEXOS ----
    const attachmentsList = document.getElementById('attachmentsList');
    if (attachmentsList) {
        // Verifica se a biblioteca Sortable.js foi carregada
        if (typeof Sortable === 'undefined') {
            console.error('A biblioteca Sortable.js não foi encontrada. A funcionalidade de arrastar e soltar estará desativada.');
        } else {
            new Sortable(attachmentsList, {
                animation: 150,
                ghostClass: 'sortable-ghost',
                filter: '.btn, a, form, .editable-filename',
                preventOnFilter: true,
                onEnd: function() {
                    const items = attachmentsList.querySelectorAll('.attachment-item');
                    const newOrder = Array.from(items).map((item, index) => ({
                        id: parseInt(item.dataset.id),
                        position: index
                    }));

                    fetch(reorderUrl, { // Usa a URL passada pelo data-*
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(newOrder)
                    }).then(response => response.json())
                      .then(data => {
                          if (!data.success) {
                              console.error('Erro ao reordenar anexos');
                          }
                      });
                }
            });
        }
    }


    // ---- LÓGICA DO MODAL DE RENOMEAR ----
    const renameModalEl = document.getElementById('renameAttachmentModal');
    if(renameModalEl) {
        const renameAttachmentForm = document.getElementById('renameAttachmentForm');
        const originalFilenameEl = document.getElementById('originalFilename');
        const newAttachmentNameInput = document.getElementById('newAttachmentNameInput');
        const renameAttachmentIdInput = document.getElementById('renameAttachmentIdInput');

        renameModalEl.addEventListener('show.bs.modal', function (event) {
            const triggerElement = event.relatedTarget;
            const attachmentId = triggerElement.getAttribute('data-attachment-id');
            const attachmentName = triggerElement.getAttribute('data-attachment-name');
            const nameWithoutExt = attachmentName.lastIndexOf('.') > 0 ? attachmentName.substring(0, attachmentName.lastIndexOf('.')) : attachmentName;

            originalFilenameEl.textContent = attachmentName;
            newAttachmentNameInput.value = nameWithoutExt;
            renameAttachmentIdInput.value = attachmentId;

            // Foca no campo de input após o modal estar totalmente visível
            setTimeout(() => newAttachmentNameInput.focus(), 500);
        });

        renameAttachmentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const attachmentId = renameAttachmentIdInput.value;
            const newName = newAttachmentNameInput.value.trim();

            if (!newName) {
                alert('O nome não pode ser vazio.');
                return;
            }

            fetch(renameUrl, { // Usa a URL passada pelo data-*
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `attachment_id=${attachmentId}&new_name=${encodeURIComponent(newName)}`
            })
            .then(response => {
                if (response.ok) { // Se a resposta foi bem-sucedida (status 200-299)
                    window.location.reload(); // Recarrega a página para ver a alteração
                } else {
                   throw new Error('Falha ao renomear o arquivo. Status: ' + response.status);
                }
            })
            .catch(error => {
                console.error('Erro na requisição para renomear o arquivo:', error);
                alert('Ocorreu um erro ao tentar renomear. Tente novamente.');
            });
        });
    }


    // ---- OUTROS SCRIPTS ----
    // Disponibiliza as funções globalmente para serem acessadas pelo onclick no HTML
    window.enableEdit = function() {
        document.getElementById('reportView').classList.add('d-none');
        document.getElementById('reportEditForm').classList.remove('d-none');
        document.getElementById('reportEdit').focus();
    }

    window.cancelEdit = function() {
        document.getElementById('reportView').classList.remove('d-none');
        document.getElementById('reportEditForm').classList.add('d-none');
    }
});