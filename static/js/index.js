// static/js/calendar.js

document.addEventListener('DOMContentLoaded', function() {
    // --- CONSTANTES ---
    const SELECTORS = {
        MONTH_YEAR: '#month-year',
        DAYS: '#calendar-days',
        PREV_BTN: '#prev-month-btn',
        NEXT_BTN: '#next-month-btn',
        APPOINTMENTS_CARD: '#appointments-card',
        TOGGLE_EDIT_BTN: '#toggle-edit-mode-btn',
        APPOINTMENT_LIST: '#appointment-list',
        APPOINTMENT_MODAL: '#appointmentModal',
        MODAL_TITLE: '#modalTitle',
        SAVE_BTN: '#save-appointment-btn',
        DELETE_ALL_BTN: '#delete-all-btn',
        DELETE_MODAL_BTN: '#delete-appointment-modal-btn',
        FORM: '#appointment-form',
        FORM_ID: '#appointment-id',
        FORM_TIME: '#appointment-time',
        FORM_CONTENT: '#appointment-content',
        FORM_PRIORITY: '#appointment-priority',
        FORM_RECURRING: '#appointment-recurring',
        ADD_BTN: '#add-appointment-btn',
    };

    const CSS_CLASSES = {
        EDIT_MODE: 'edit-mode-active',
        TODAY: 'today',
        SELECTED: 'selected',
        URGENT: 'urgent-day',
        IMPORTANT: 'important-day',
        HAS_APPOINTMENT: 'has-appointment',
        RECURRING: 'recurring-day',
        RECURRING_PREFIX: 'recurring-',
    };

    const MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];

    // --- ELEMENTOS DO DOM ---
    const dom = {
        monthYearEl: document.querySelector(SELECTORS.MONTH_YEAR),
        daysEl: document.querySelector(SELECTORS.DAYS),
        prevMonthBtn: document.querySelector(SELECTORS.PREV_BTN),
        nextMonthBtn: document.querySelector(SELECTORS.NEXT_BTN),
        appointmentsCard: document.querySelector(SELECTORS.APPOINTMENTS_CARD),
        toggleEditModeBtn: document.querySelector(SELECTORS.TOGGLE_EDIT_BTN),
        appointmentList: document.querySelector(SELECTORS.APPOINTMENT_LIST),
        appointmentModalEl: document.querySelector(SELECTORS.APPOINTMENT_MODAL),
        modalTitle: document.querySelector(SELECTORS.MODAL_TITLE),
        saveBtn: document.querySelector(SELECTORS.SAVE_BTN),
        deleteAllBtn: document.querySelector(SELECTORS.DELETE_ALL_BTN),
        deleteModalBtn: document.querySelector(SELECTORS.DELETE_MODAL_BTN),
        form: document.querySelector(SELECTORS.FORM),
        appointmentIdInput: document.querySelector(SELECTORS.FORM_ID),
        appointmentTimeInput: document.querySelector(SELECTORS.FORM_TIME),
        appointmentContentInput: document.querySelector(SELECTORS.FORM_CONTENT),
        appointmentPriorityInput: document.querySelector(SELECTORS.FORM_PRIORITY),
        appointmentRecurringInput: document.querySelector(SELECTORS.FORM_RECURRING),
        addAppointmentBtn: document.querySelector(SELECTORS.ADD_BTN),
    };

    const appointmentModal = new bootstrap.Modal(dom.appointmentModalEl);

    // --- ESTADO DA APLICAÇÃO ---
    const state = {
        date: new Date(),
        get month() { return this.date.getMonth(); },
        set month(m) { this.date.setMonth(m); },
        get year() { return this.date.getFullYear(); },
        set year(y) { this.date.setFullYear(y); },
        selectedDate: new Date(),
        urgentDays: [],
        importantDays: [],
        activeDays: [],
        recurringDays: {},
    };

    // --- FUNÇÕES DE UTILIDADE ---
    const formatDate = (dateObj) => {
        const y = dateObj.getFullYear();
        const m = String(dateObj.getMonth() + 1).padStart(2, '0');
        const d = String(dateObj.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    };

    const fetchCalendarData = async (endpoint, expectObject = false) => {
        try {
            const response = await fetch(`/api/appointments/${endpoint}/${state.year}/${state.month + 1}`);
            if (!response.ok) throw new Error(`Erro ao buscar ${endpoint}`);
            return await response.json();
        } catch (error) {
            console.error(error);
            return expectObject ? {} : [];
        }
    };

    const fetchAppointments = async (dateStr) => {
        dom.appointmentList.innerHTML = `<p class="text-muted">A carregar...</p>`;
        try {
            const response = await fetch(`/api/appointments/${dateStr}`);
            if (!response.ok) throw new Error(`Erro do servidor: ${response.status}`);
            const appointments = await response.json();
            renderAppointments(appointments);
        } catch (error) {
            dom.appointmentList.innerHTML = `<p class="text-danger">Erro ao carregar compromissos.</p>`;
            console.error('Falha na busca de compromissos:', error);
        }
    };

    const renderAppointments = (appointments) => {
        dom.appointmentList.innerHTML = '';
        if (appointments.length === 0) {
            dom.appointmentList.innerHTML = '<p class="text-muted">Nenhum compromisso para este dia.</p>';
            return;
        }
        appointments.forEach(apt => {
            const aptEl = document.createElement('div');
            const priority = apt.priority || 'Normal';
            let baseClass = `appointment-item d-flex justify-content-between align-items-center priority-${priority.toLowerCase()}`;
            const sourceClass = apt.source === 'financeiro' ? 'from-financeiro' :
                apt.source === 'triagem' ? 'from-triagem' : '';
            const isRemarcada = apt.content && apt.content.includes('REMARCADA');
            const remarcadaClass = isRemarcada ? 'remarcada' : '';

            aptEl.className = `${baseClass} ${sourceClass} ${remarcadaClass}`.trim();

            const recurringIcon = apt.recurring ? '<i class="bi bi-arrow-repeat me-2" title="Repete mensalmente"></i>' : '';

            let ticketLink = '';
            if (apt.ticket_id && apt.ticket_title) {
                ticketLink = `<a href="/ticket/${apt.ticket_id}" class="link-primary fw-bold" title="Ver caso">${apt.ticket_title}</a>`;
            }

            aptEl.innerHTML = `
        <p class="mb-0">
            ${recurringIcon}
            <strong>${apt.time}</strong> - 
            ${ticketLink ? ticketLink + " - " : ""}
            ${apt.content}
        </p>
        <div class="appointment-actions">
            <button class="btn btn-sm btn-outline-secondary edit-btn" data-id="${apt.id}" data-time="${apt.time}" data-content="${apt.content}" data-priority="${priority}" data-recurring="${apt.recurring}" data-bs-toggle="modal" data-bs-target="#appointmentModal">
                <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger delete-btn" data-id="${apt.id}">
                <i class="bi bi-trash"></i>
            </button>
        </div>`;
            dom.appointmentList.appendChild(aptEl);
        });
    };

    const renderCalendar = async () => {
        [
            state.urgentDays,
            state.importantDays,
            state.activeDays,
            state.recurringDays
        ] = await Promise.all([
            fetchCalendarData('urgent-days'),
            fetchCalendarData('important-days'),
            fetchCalendarData('active-days'),
            fetchCalendarData('recurring-days', true)
        ]);

        const firstDayOfMonth = new Date(state.year, state.month, 1).getDay();
        const lastDateOfMonth = new Date(state.year, state.month + 1, 0).getDate();
        const lastDayOfPrevMonth = new Date(state.year, state.month, 0).getDate();

        dom.monthYearEl.innerText = `${MESES[state.month]} ${state.year}`;
        let daysHTML = "";

        // Dias do mês anterior
        for (let i = firstDayOfMonth; i > 0; i--) {
            daysHTML += `<div class="prev-date">${lastDayOfPrevMonth - i + 1}</div>`;
        }

        // Dias do mês atual
        for (let i = 1; i <= lastDateOfMonth; i++) {
            const today = new Date();
            const classes = [];
            if (i === today.getDate() && state.year === today.getFullYear() && state.month === today.getMonth()) {
                classes.push(CSS_CLASSES.TODAY);
            }
            if (i === state.selectedDate.getDate() && state.year === state.selectedDate.getFullYear() && state.month === state.selectedDate.getMonth()) {
                classes.push(CSS_CLASSES.SELECTED);
            }

            if (state.urgentDays.includes(i)) classes.push(CSS_CLASSES.URGENT);
            else if (state.importantDays.includes(i)) classes.push(CSS_CLASSES.IMPORTANT);
            else if (state.activeDays.includes(i)) classes.push(CSS_CLASSES.HAS_APPOINTMENT);

            const recurringPriority = state.recurringDays[i];
            if (recurringPriority) {
                classes.push(CSS_CLASSES.RECURRING, `${CSS_CLASSES.RECURRING_PREFIX}${recurringPriority.toLowerCase()}`);
            }
            daysHTML += `<div class="${classes.join(' ')}">${i}</div>`;
        }

        // Dias do mês seguinte
        const cellsUsed = firstDayOfMonth + lastDateOfMonth;
        for (let i = 1; i <= 42 - cellsUsed; i++) {
            daysHTML += `<div class="next-date">${i}</div>`;
        }

        dom.daysEl.innerHTML = daysHTML;
        dom.daysEl.querySelectorAll('div:not(.prev-date):not(.next-date)').forEach(dayEl => {
            dayEl.addEventListener('click', () => {
                const day = parseInt(dayEl.innerText);
                state.selectedDate = new Date(state.year, state.month, day);
                fetchAppointments(formatDate(state.selectedDate));
                renderCalendar();
            });
        });
    };

    // --- EVENTOS ---
    const setupEventListeners = () => {
        dom.prevMonthBtn.addEventListener('click', () => {
            state.date.setMonth(state.month - 1);
            renderCalendar();
        });

        dom.nextMonthBtn.addEventListener('click', () => {
            state.date.setMonth(state.month + 1);
            renderCalendar();
        });

        dom.toggleEditModeBtn.addEventListener('click', () => {
            dom.appointmentsCard.classList.toggle(CSS_CLASSES.EDIT_MODE);
            const icon = dom.toggleEditModeBtn.querySelector('i');
            icon.classList.toggle('bi-gear-fill');
            icon.classList.toggle('bi-check-circle-fill');
        });

        dom.deleteAllBtn.addEventListener('click', () => {
            const dateStr = formatDate(state.selectedDate);
            if (confirm('Tem certeza que deseja excluir TODOS os compromissos deste dia? Esta ação não pode ser desfeita.')) {
                fetch(`/api/appointments/delete-all/${dateStr}`, { method: 'DELETE' })
                    .then(response => {
                        if (!response.ok) throw new Error('Falha ao excluir');
                        fetchAppointments(dateStr);
                        renderCalendar();
                    })
                    .catch(error => {
                        console.error('Erro na exclusão em massa:', error);
                        alert('Ocorreu um erro ao excluir os compromissos.');
                    });
            }
        });

        dom.appointmentList.addEventListener('click', (e) => {
            const button = e.target.closest('.delete-btn');
            if (!button) return;

            const id = button.dataset.id;
            if (confirm('Tem certeza de que deseja excluir este compromisso?')) {
                fetch(`/api/appointments/${id}`, { method: 'DELETE' })
                    .then(() => {
                        fetchAppointments(formatDate(state.selectedDate));
                        renderCalendar();
                    });
            }
        });

        dom.appointmentModalEl.addEventListener('show.bs.modal', (e) => {
            const triggerButton = e.relatedTarget;
            dom.form.reset();
            const isEditMode = triggerButton && triggerButton.classList.contains('edit-btn');
            dom.modalTitle.innerText = isEditMode ? 'Editar Compromisso' : 'Adicionar Compromisso';
            dom.deleteModalBtn.style.display = isEditMode ? 'inline-block' : 'none';

            if (isEditMode) {
                dom.appointmentIdInput.value = triggerButton.dataset.id;
                dom.appointmentTimeInput.value = triggerButton.dataset.time;
                dom.appointmentContentInput.value = triggerButton.dataset.content;
                dom.appointmentPriorityInput.value = triggerButton.dataset.priority || 'Normal';
                dom.appointmentRecurringInput.checked = (triggerButton.dataset.recurring === 'true');
            } else {
                dom.appointmentIdInput.value = "";
                dom.appointmentTimeInput.value = "";
                dom.appointmentContentInput.value = "";
                dom.appointmentPriorityInput.value = "Normal";
                dom.appointmentRecurringInput.checked = false;
            }
        });

        dom.saveBtn.addEventListener('click', async () => {
            const id = dom.appointmentIdInput.value;
            const body = {
                content: dom.appointmentContentInput.value,
                appointment_time: dom.appointmentTimeInput.value,
                appointment_date: formatDate(state.selectedDate),
                priority: dom.appointmentPriorityInput.value,
                recurring: dom.appointmentRecurringInput.checked,
            };

            const url = id ? `/api/appointments/${id}` : '/api/appointments';
            const method = id ? 'PUT' : 'POST';

            try {
                const response = await fetch(url, {
                    method,
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(body),
                });
                if (!response.ok) throw new Error('Falha ao salvar');
                appointmentModal.hide();
                fetchAppointments(body.appointment_date);
                renderCalendar();
            } catch (error) {
                console.error("Erro ao salvar:", error);
                alert("Não foi possível salvar o compromisso.");
            }
        });

        dom.deleteModalBtn.addEventListener('click', () => {
            const id = dom.appointmentIdInput.value;
            if (!id) return;
            if (confirm('Tem certeza de que deseja excluir este compromisso?')) {
                fetch(`/api/appointments/${id}`, {method: 'DELETE'})
                    .then(response => {
                        if (!response.ok) throw new Error('Falha ao excluir');
                        appointmentModal.hide();
                        fetchAppointments(formatDate(state.selectedDate));
                        renderCalendar();
                    })
                    .catch(() => alert('Não foi possível excluir o compromisso.'));
            }
        });

        // Botão para adicionar novo compromisso (modal em branco, data selecionada)
        dom.addAppointmentBtn.addEventListener('click', () => {
            dom.form.reset();
            dom.appointmentIdInput.value = "";
            dom.appointmentTimeInput.value = "";
            dom.appointmentContentInput.value = "";
            dom.appointmentPriorityInput.value = "Normal";
            dom.appointmentRecurringInput.checked = false;
            appointmentModal.show();
        });
    };

    // --- INICIALIZAÇÃO ---
    const initializePage = async () => {
        setupEventListeners();
        await fetchAppointments(formatDate(state.selectedDate));
        await renderCalendar();
    };

    initializePage();
});