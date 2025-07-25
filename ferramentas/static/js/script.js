document.addEventListener('DOMContentLoaded', function() {
    // --- VARIÁVEIS DO CALENDÁRIO ---
    const monthYearEl = document.getElementById('month-year');
    const daysEl = document.getElementById('calendar-days');
    const prevMonthBtn = document.getElementById('prev-month-btn');
    const nextMonthBtn = document.getElementById('next-month-btn');

    let date = new Date();
    let month = date.getMonth();
    let year = date.getFullYear();

    const meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];

    // --- VARIÁVEIS DOS COMPROMISSOS ---
    const appointmentsCard = document.getElementById('appointments-card');
    const toggleEditModeBtn = document.getElementById('toggle-edit-mode-btn');
    const appointmentList = document.getElementById('appointment-list');
    const appointmentModalEl = document.getElementById('appointmentModal');
    const appointmentModal = new bootstrap.Modal(appointmentModalEl);
    const modalTitle = document.getElementById('modalTitle');
    const saveBtn = document.getElementById('save-appointment-btn');
    const form = document.getElementById('appointment-form');
    const appointmentIdInput = document.getElementById('appointment-id');
    const appointmentTimeInput = document.getElementById('appointment-time');
    const appointmentContentInput = document.getElementById('appointment-content');
    const appointmentPriorityInput = document.getElementById('appointment-priority'); // Novo campo
    const addAppointmentBtn = document.getElementById('add-appointment-btn');
    const deleteModalBtn = document.getElementById('delete-appointment-modal-btn');

    let selectedDate = new Date();

    // --- FUNÇÕES AUXILIARES ---
    const formatDate = (dateObj) => {
        const y = dateObj.getFullYear();
        const m = String(dateObj.getMonth() + 1).padStart(2, '0');
        const d = String(dateObj.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    };

    const fetchAppointments = async (dateStr) => {
        appointmentList.innerHTML = `<p class="text-muted">Carregando...</p>`;
        try {
            const response = await fetch(`/api/appointments/${dateStr}`);
            if (!response.ok) throw new Error(`Erro do servidor: ${response.status}`);
            const appointments = await response.json();
            renderAppointments(appointments);
        } catch (error) {
            appointmentList.innerHTML = `<p class="text-danger">Erro ao carregar compromissos.</p>`;
            console.error('Falha na busca de compromissos:', error);
        }
    };

    // --- LÓGICA DE RENDERIZAÇÃO E EVENTOS ---

    const renderAppointments = (appointments) => {
        appointmentList.innerHTML = '';
        if (appointments.length === 0) {
            appointmentList.innerHTML = '<p class="text-muted">Nenhum compromisso para este dia.</p>';
            return;
        }
        appointments.forEach(apt => {
            const aptEl = document.createElement('div');
            // Adiciona a classe de prioridade ao item para estilização
            const priorityClass = `priority-${apt.priority.toLowerCase()}`;
            aptEl.className = `appointment-item d-flex justify-content-between align-items-center ${priorityClass}`;

            aptEl.innerHTML = `
                <p class="mb-0"><strong>${apt.time}</strong> - ${apt.content}</p>
                <div class="appointment-actions">
                    <button class="btn btn-sm btn-outline-secondary edit-btn" 
                            data-id="${apt.id}" data-time="${apt.time}" data-content="${apt.content}" data-priority="${apt.priority}"
                            data-bs-toggle="modal" data-bs-target="#appointmentModal">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${apt.id}">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            `;
            appointmentList.appendChild(aptEl);
        });
    };

    const attachClickEventsToDays = () => {
        const allDays = daysEl.querySelectorAll('div:not(.prev-date):not(.next-date)');
        allDays.forEach(dayEl => {
            dayEl.addEventListener('click', () => {
                const day = parseInt(dayEl.innerText);
                selectedDate = new Date(year, month, day);
                fetchAppointments(formatDate(selectedDate));
                renderCalendar();
            });
        });
    };

    const renderCalendar = () => {
        // ... (lógica do calendário permanece a mesma)
    };

    // ... (eventos dos botões do calendário permanecem os mesmos)

    toggleEditModeBtn.addEventListener('click', () => {
        // ... (lógica do modo de edição permanece a mesma)
    });

    appointmentList.addEventListener('click', (e) => {
        // ... (lógica de clique em editar/excluir permanece a mesma)
    });

    appointmentModalEl.addEventListener('show.bs.modal', (e) => {
        const triggerButton = e.relatedTarget;
        if (triggerButton && triggerButton.classList.contains('edit-btn')) {
            modalTitle.innerText = 'Editar Compromisso';
            appointmentIdInput.value = triggerButton.dataset.id;
            appointmentTimeInput.value = triggerButton.dataset.time;
            appointmentContentInput.value = triggerButton.dataset.content;
            appointmentPriorityInput.value = triggerButton.dataset.priority; // Preenche a prioridade
            deleteModalBtn.style.display = 'inline-block';
        } else {
            modalTitle.innerText = 'Adicionar Compromisso';
            form.reset();
            appointmentIdInput.value = '';
            deleteModalBtn.style.display = 'none';
        }
    });

    deleteModalBtn.addEventListener('click', () => {
        // ... (lógica de exclusão no modal permanece a mesma)
    });

    saveBtn.addEventListener('click', async () => {
        const id = appointmentIdInput.value;
        const time = appointmentTimeInput.value;
        const content = appointmentContentInput.value;
        const priority = appointmentPriorityInput.value; // Pega o valor da prioridade
        const date = formatDate(selectedDate);

        const url = id ? `/api/appointments/${id}` : '/api/appointments';
        const method = id ? 'PUT' : 'POST';

        try {
            await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                // Envia a prioridade no corpo da requisição
                body: JSON.stringify({ content, time, date, priority })
            });
            appointmentModal.hide();
            fetchAppointments(date);
        } catch(error) {
            console.error("Erro ao salvar:", error);
            alert("Não foi possível salvar o compromisso.");
        }
    });

    // --- INICIALIZAÇÃO ---
    fetchAppointments(formatDate(new Date()));
    renderCalendar();
});

// --- CÁLCULO TRABALHISTA --- (Adicione no final do arquivo)
document.getElementById('calcTrabalhistaForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    const statusMessage = document.getElementById('statusMessage');
    const modalMessage = document.getElementById('modalMessage');
    const downloadLink = document.getElementById('downloadLink');
    const modal = document.getElementById('downloadModal');

    statusMessage.textContent = 'Gerando relatório...';
    statusMessage.className = 'status-message processing';

    try {
        const response = await fetch(form.dataset.action, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(await response.text());
        }

        const result = await response.json();

        // Configura o modal de download
        downloadLink.href = result.download_url;
        downloadLink.download = result.filename;
        modalMessage.textContent = `Relatório "${result.filename}" gerado com sucesso!`;
        statusMessage.textContent = 'Relatório pronto para download!';
        statusMessage.className = 'status-message success';

        // Exibe o modal
        modal.style.display = 'block';
    } catch (error) {
        console.error('Erro:', error);
        statusMessage.textContent = `Erro ao gerar relatório: ${error.message}`;
        statusMessage.className = 'status-message error';
    }
});

// Fechar modal quando clicar no "X"
document.querySelector('.close')?.addEventListener('click', function() {
    document.getElementById('downloadModal').style.display = 'none';
});

// Botão "Abrir Arquivo" (opcional)
document.getElementById('abrirArquivo')?.addEventListener('click', function() {
    const downloadLink = document.getElementById('downloadLink');
    window.open(downloadLink.href, '_blank');
});