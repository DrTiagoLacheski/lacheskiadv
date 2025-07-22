// static/js/index.js
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
    const addAppointmentBtn = document.getElementById('add-appointment-btn');
    const deleteModalBtn = document.getElementById('delete-appointment-modal-btn');

    let selectedDate = new Date();

    // --- FUNÇÕES ---

    const formatDate = (dateObj) => {
        const y = dateObj.getFullYear();
        const m = String(dateObj.getMonth() + 1).padStart(2, '0');
        const d = String(dateObj.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    };

    const fetchAppointments = async (dateStr) => {
        appointmentList.innerHTML = `<p class="text-muted">A carregar...</p>`;
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

    const renderAppointments = (appointments) => {
        appointmentList.innerHTML = '';
        if (appointments.length === 0) {
            appointmentList.innerHTML = '<p class="text-muted">Nenhum compromisso para este dia.</p>';
            return;
        }
        appointments.forEach(apt => {
            const aptEl = document.createElement('div');
            aptEl.className = 'appointment-item d-flex justify-content-between align-items-center';
            aptEl.innerHTML = `
                <p class="mb-0"><strong>${apt.time}</strong> - ${apt.content}</p>
                <div class="appointment-actions">
                    <button class="btn btn-sm btn-outline-secondary edit-btn" 
                            data-id="${apt.id}" data-time="${apt.time}" data-content="${apt.content}"
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
        const firstDayOfMonth = new Date(year, month, 1).getDay();
        const lastDateOfMonth = new Date(year, month + 1, 0).getDate();
        const lastDayOfPrevMonth = new Date(year, month, 0).getDate();
        monthYearEl.innerText = `${meses[month]} ${year}`;
        let daysHTML = "";
        for (let i = firstDayOfMonth; i > 0; i--) {
            daysHTML += `<div class="prev-date">${lastDayOfPrevMonth - i + 1}</div>`;
        }
        for (let i = 1; i <= lastDateOfMonth; i++) {
            const today = new Date();
            let classes = [];
            if (i === today.getDate() && year === today.getFullYear() && month === today.getMonth()) {
                classes.push('today');
            }
            if (i === selectedDate.getDate() && year === selectedDate.getFullYear() && month === selectedDate.getMonth()) {
                classes.push('selected');
            }
            daysHTML += `<div class="${classes.join(' ')}">${i}</div>`;
        }
        const totalDaysDisplayed = firstDayOfMonth + lastDateOfMonth;
        const nextDays = (7 - (totalDaysDisplayed % 7)) % 7;
        for (let i = 1; i <= nextDays; i++) {
            daysHTML += `<div class="next-date">${i}</div>`;
        }
        daysEl.innerHTML = daysHTML;
        attachClickEventsToDays();
    };

    prevMonthBtn.addEventListener('click', () => {
        month--;
        if (month < 0) { month = 11; year--; }
        renderCalendar();
    });

    nextMonthBtn.addEventListener('click', () => {
        month++;
        if (month > 11) { month = 0; year++; }
        renderCalendar();
    });

    toggleEditModeBtn.addEventListener('click', () => {
        appointmentsCard.classList.toggle('edit-mode-active');
        const icon = toggleEditModeBtn.querySelector('i');
        if (appointmentsCard.classList.contains('edit-mode-active')) {
            icon.classList.replace('bi-gear-fill', 'bi-check-circle-fill');
        } else {
            icon.classList.replace('bi-check-circle-fill', 'bi-gear-fill');
        }
    });

    appointmentList.addEventListener('click', (e) => {
        const target = e.target.closest('button');
        if (!target || !target.closest('.appointment-actions')) return;
        const id = target.dataset.id;
        if (target.classList.contains('delete-btn')) {
            if (confirm('Tem certeza de que deseja excluir este compromisso?')) {
                fetch(`/api/appointments/${id}`, { method: 'DELETE' })
                .then(() => fetchAppointments(formatDate(selectedDate)));
            }
        }
    });

    appointmentModalEl.addEventListener('show.bs.modal', (e) => {
        const triggerButton = e.relatedTarget;
        if (triggerButton && triggerButton.classList.contains('edit-btn')) {
            modalTitle.innerText = 'Editar Compromisso';
            appointmentIdInput.value = triggerButton.dataset.id;
            appointmentTimeInput.value = triggerButton.dataset.time;
            appointmentContentInput.value = triggerButton.dataset.content;
            deleteModalBtn.style.display = 'inline-block';
        } else {
            modalTitle.innerText = 'Adicionar Compromisso';
            form.reset();
            appointmentIdInput.value = '';
            deleteModalBtn.style.display = 'none';
        }
    });
    
    deleteModalBtn.addEventListener('click', () => {
        const id = appointmentIdInput.value;
        if (id && confirm('Tem certeza de que deseja excluir este compromisso?')) {
            fetch(`/api/appointments/${id}`, { method: 'DELETE' })
            .then(response => {
                if (response.ok) {
                    appointmentModal.hide();
                    fetchAppointments(formatDate(selectedDate));
                } else {
                    alert('Não foi possível excluir o compromisso.');
                }
            });
        }
    });

    saveBtn.addEventListener('click', async () => {
        const id = appointmentIdInput.value;
        const time = appointmentTimeInput.value;
        const content = appointmentContentInput.value;
        const date = formatDate(selectedDate);
        const url = id ? `/api/appointments/${id}` : '/api/appointments';
        const method = id ? 'PUT' : 'POST';

        try {
            await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ content, time, date })
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