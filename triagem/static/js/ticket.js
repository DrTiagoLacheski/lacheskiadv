// static/js/ticket.js

document.addEventListener('DOMContentLoaded', function() {
    const ticketContainer = document.getElementById('ticket-container');
    if (!ticketContainer) {
        console.error('Elemento #ticket-container não encontrado. O script não pode continuar.');
        return;
    }

    // URLs do data-set
    const reorderUrl = ticketContainer.dataset.reorderUrl;
    const renameUrl = ticketContainer.dataset.renameUrl;
    const addTodoUrl = ticketContainer.dataset.addTodoUrl;
    const updateTodoUrlBase = ticketContainer.dataset.updateTodoUrlBase;
    const deleteTodoUrlBase = ticketContainer.dataset.deleteTodoUrlBase;
    const reorderTodosUrl = ticketContainer.dataset.reorderTodosUrl;

    // ---- REORDENAÇÃO DE ANEXOS ----
    const attachmentsList = document.getElementById('attachmentsList');
    if (attachmentsList && typeof Sortable !== 'undefined') {
        new Sortable(attachmentsList, {
            animation: 150,
            ghostClass: 'sortable-ghost',
            filter: '.btn, a, form, .editable-filename, .rename-form',
            preventOnFilter: true,
            onEnd: function() {
                const items = attachmentsList.querySelectorAll('.attachment-item');
                const newOrder = Array.from(items).map((item, index) => ({
                    id: parseInt(item.dataset.id),
                    position: index
                }));
                fetch(reorderUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newOrder)
                }).then(response => response.json())
                  .then(data => {
                      if (!data.success) console.error('Erro ao reordenar anexos');
                  });
            }
        });
    }

    // ---- EDIÇÃO DE NOME DE ANEXO ----
    if (attachmentsList) {
        const toggleEditMode = (filenameSpan, showEditForm) => {
            const form = filenameSpan.nextElementSibling;
            if (showEditForm) {
                filenameSpan.classList.add('d-none');
                form.classList.remove('d-none');
                const input = form.querySelector('input');
                input.focus();
                input.select();
            } else {
                filenameSpan.classList.remove('d-none');
                form.classList.add('d-none');
            }
        };

        attachmentsList.addEventListener('click', (e) => {
            if (e.target.closest('.editable-filename')) {
                toggleEditMode(e.target.closest('.editable-filename'), true);
            }
        });

        attachmentsList.addEventListener('submit', (e) => {
            const form = e.target.closest('.rename-form');
            if (form) {
                e.preventDefault();
                const attachmentId = form.dataset.attachmentId;
                const newName = form.querySelector('input').value.trim();
                if (!newName) return alert('O nome não pode ser vazio.');
                form.querySelector('input').disabled = true;
                fetch(renameUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `attachment_id=${attachmentId}&new_name=${encodeURIComponent(newName)}`
                })
                .then(response => {
                    if (response.ok) window.location.reload();
                    else throw new Error('Falha ao renomear o arquivo.');
                })
                .catch(error => {
                    console.error('Erro ao renomear:', error);
                    alert('Ocorreu um erro ao tentar renomear.');
                    form.querySelector('input').disabled = false;
                });
            }
        });

        attachmentsList.addEventListener('focusout', (e) => {
            if (e.target.closest('.rename-form input')) {
                toggleEditMode(e.target.closest('.rename-form').previousElementSibling, false);
            }
        });

        attachmentsList.addEventListener('keydown', (e) => {
            if (e.target.closest('.rename-form input') && e.key === 'Escape') {
                toggleEditMode(e.target.closest('.rename-form').previousElementSibling, false);
            }
        });
    }

    // ---- UPLOAD AUTOMÁTICO DE ANEXOS ----
    const addAttachmentForm = document.getElementById('addAttachmentForm');
    if (addAttachmentForm) {
        const fileInput = document.getElementById('ticket_attachments');
        const statusDiv = document.getElementById('attachment-upload-status');
        fileInput.addEventListener('change', async () => {
            if (fileInput.files.length === 0) return;
            const fileCount = fileInput.files.length;
            statusDiv.textContent = `Enviando ${fileCount} arquivo(s)...`;
            statusDiv.className = 'form-text mt-2 text-info';
            const formData = new FormData(addAttachmentForm);
            try {
                const response = await fetch(addAttachmentForm.action, { method: 'POST', body: formData });
                if (response.ok) window.location.reload();
                else throw new Error(`Falha no envio. Código: ${response.status}`);
            } catch (error) {
                statusDiv.textContent = `Erro: ${error.message}`;
                statusDiv.className = 'form-text mt-2 text-danger';
                console.error('Erro no upload do anexo:', error);
            }
        });
    }

    // ---- CHECKLIST DE TAREFAS (TO-DO) ----
    const todoListContainer = document.getElementById('todoListContainer');
    const addTodoForm = document.getElementById('addTodoForm');
    let newTodoContentInput = null;
    let newTodoDateInput = null;
    let newTodoTimeInput = null;
    let newTodoPriorityInput = null;

    if (addTodoForm) {
        newTodoContentInput = document.getElementById('newTodoContent');
        newTodoDateInput = document.getElementById('newTodoDate');
        newTodoTimeInput = document.getElementById('newTodoTime');
        newTodoPriorityInput = document.getElementById('newTodoPriority');
        // Definir min para hoje no campo de data
        if (newTodoDateInput) {
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            newTodoDateInput.min = `${yyyy}-${mm}-${dd}`;
            newTodoDateInput.value = '';
        }
        if (newTodoTimeInput) {
            newTodoTimeInput.value = '';
        }
    }

    // --- REORDENAÇÃO DA CHECKLIST ---
    if (todoListContainer && typeof Sortable !== 'undefined') {
        new Sortable(todoListContainer, {
            animation: 150,
            handle: '.todo-item',
            ghostClass: 'sortable-ghost',
            onEnd: function() {
                const items = todoListContainer.querySelectorAll('.todo-item');
                const newOrder = Array.from(items).map((item, index) => ({
                    id: parseInt(item.dataset.id),
                    position: index
                }));

                fetch(reorderTodosUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newOrder)
                }).then(response => {
                    if (!response.ok) {
                        console.error('Falha ao reordenar as tarefas.');
                    }
                });
            }
        });
    }

    if (addTodoForm) {
        // Adicionar uma nova tarefa com data e horário opcional
        addTodoForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const content = newTodoContentInput.value.trim();
            const date = newTodoDateInput ? newTodoDateInput.value : '';
            const time = newTodoTimeInput ? newTodoTimeInput.value : '';
            const priority = newTodoPriorityInput ? newTodoPriorityInput.value : 'Normal';

            if (!content) return;
            if (date) {
                const selected = new Date(date + 'T00:00:00');
                const now = new Date();
                now.setHours(0, 0, 0, 0);
                if (selected < now) {
                    alert('A data da tarefa não pode ser no passado.');
                    return;
                }
            }
            // Monta o objeto, incluindo data e horário se existirem
            const body = { content, priority };
            if (date) body.date = date;
            if (time) body.time = time;

            try {
                const response = await fetch(addTodoUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });
                const contentType = response.headers.get("content-type");
                if (!response.ok) {
                    const text = await response.text();
                    throw new Error("Erro HTTP: " + response.status + " - " + text);
                }
                let result;
                if (contentType && contentType.includes("application/json")) {
                    result = await response.json();
                } else {
                    const text = await response.text();
                    throw new Error("Resposta não é JSON: " + text);
                }
                if (result.success) {
                    document.getElementById('no-todos-message')?.remove();
                    const todoItemEl = createTodoElement(result.todo);
                    todoListContainer.appendChild(todoItemEl);
                    newTodoContentInput.value = '';
                    if (newTodoDateInput) newTodoDateInput.value = '';
                    if (newTodoTimeInput) newTodoTimeInput.value = '';
                } else {
                    throw new Error(result.error || 'Falha ao adicionar tarefa.');
                }
            } catch (error) {
                console.error('Erro ao adicionar tarefa:', error);
                alert(error.message || 'Não foi possível adicionar a tarefa.');
            }
        });

        // Atualizar e Deletar tarefas
        todoListContainer.addEventListener('click', async (e) => {
            const todoItem = e.target.closest('.todo-item');
            if (!todoItem) return;

            const todoId = todoItem.dataset.id;

            // Checkbox
            if (e.target.matches('.form-check-input')) {
                const isCompleted = e.target.checked;
                todoItem.classList.toggle('completed', isCompleted);
                fetch(`${updateTodoUrlBase}/${todoId}/update`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({is_completed: isCompleted})
                })
                    .then(response => response.json())
                    .then(data => {
                        updateAppointmentStrike(todoId, isCompleted);
                    })
                    .catch(err => console.error("Falha ao atualizar tarefa:", err));
            }

            // Botão deletar
            if (e.target.closest('.delete-todo-btn')) {
                e.preventDefault();
                if (confirm('Tem certeza que deseja excluir esta tarefa?')) {
                    todoItem.style.opacity = '0.5';
                    try {
                        const response = await fetch(`${deleteTodoUrlBase}/${todoId}/delete`, { method: 'POST' });
                        const contentType = response.headers.get("content-type");
                        let result;
                        if (contentType && contentType.includes("application/json")) {
                            result = await response.json();
                        } else {
                            const text = await response.text();
                            throw new Error("Resposta não é JSON: " + text);
                        }
                        if (result.success) {
                            todoItem.remove();
                        } else {
                            throw new Error(result.error || 'Falha ao deletar tarefa.');
                        }
                    } catch (error) {
                        console.error('Erro ao deletar tarefa:', error);
                        alert('Não foi possível deletar a tarefa.');
                        todoItem.style.opacity = '1';
                    }
                }
            }
        });
    }

    // ---- FUNÇÕES AUXILIARES ----

    function createTodoElement(todo) {
        const div = document.createElement('div');
        div.className = 'todo-item';
        div.dataset.id = todo.id;
        div.innerHTML = `
        <input class="form-check-input" type="checkbox" id="todo-${todo.id}" ${todo.is_completed ? "checked" : ""}>
        <label class="form-check-label" for="todo-${todo.id}">
            ${escapeHTML(todo.content)}
            ${todo.date ? `<span class="badge bg-info text-dark ms-2">${formatDateBR(todo.date)}</span>` : ""}
            ${todo.time ? `<span class="badge bg-secondary text-dark ms-2">${escapeHTML(todo.time)}</span>` : ""}
            ${todo.priority ? `<span class="badge bg-warning text-dark ms-2">${escapeHTML(todo.priority)}</span>` : ""}
        </label>
        <button class="btn btn-xs btn-outline-danger delete-todo-btn">
            <i class="bi bi-x-lg"></i>
        </button>
    `;
        return div;
    }

    function escapeHTML(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
    }

    function formatDateBR(dateStr) {
        if (!dateStr) return '';
        const [y, m, d] = dateStr.split('-');
        return `${d}/${m}/${y}`;
    }

    function updateAppointmentStrike(todoId, isCompleted) {
        const appointmentEl = document.querySelector(`.appointment-item[data-todo-id='${todoId}']`);
        if (!appointmentEl) return;
        if (isCompleted) {
            appointmentEl.classList.add('completed');
        } else {
            appointmentEl.classList.remove('completed');
        }
    }
});