// index.js - versão reorganizada (Option B) + correções de chip TRIAGEM
// - Estrutura apt-header / apt-body
// - Chip único para TODOS os itens de triagem:
//     * triagem-chip (urgente)
//     * triagem-chip-normal (não urgente)
// - Evita duplicação (removido uso de pseudo-elemento ::before no CSS para não urgentes)
//
// Observação: Certifique-se de que o CSS tenha as classes .triagem-chip e .triagem-chip-normal.
// Caso ainda exista bloco CSS que injete "TRIAGEM" via .apt-ticket::before, remova-o para não duplicar.
//
// Dependências: Bootstrap Modal (window.bootstrap)

document.addEventListener('DOMContentLoaded', () => {

  /* ================= CONST / SELECTORS ================= */
  const SELECTORS = {
    MONTH_YEAR:'#month-year',
    DAYS:'#calendar-days',
    PREV_BTN:'#prev-month-btn',
    NEXT_BTN:'#next-month-btn',
    APPOINTMENTS_CARD:'#appointments-card',
    TOGGLE_EDIT_BTN:'#toggle-edit-mode-btn',
    APPOINTMENT_LIST:'#appointment-list',
    APPOINTMENT_MODAL:'#appointmentModal',
    MODAL_TITLE:'#modalTitle',
    SAVE_BTN:'#save-appointment-btn',
    DELETE_ALL_BTN:'#delete-all-btn',
    DELETE_MODAL_BTN:'#delete-appointment-modal-btn',
    FORM:'#appointment-form',
    FORM_ID:'#appointment-id',
    FORM_TIME:'#appointment-time',
    FORM_CONTENT:'#appointment-content',
    FORM_PRIORITY:'#appointment-priority',
    FORM_RECURRING:'#appointment-recurring',
    ADD_BTN:'#add-appointment-btn',
    EXPORT_CALENDAR_BTN:'#export-calendar-btn',
    IMPORT_CALENDAR_BTN:'#import-calendar-btn',
    IMPORT_CALENDAR_INPUT:'#importCalendarInput',
    IMPORT_CALENDAR_FORM:'#importCalendarForm'
  };

  const LEGACY_CLASSES = {
    EDIT_MODE:'edit-mode-active',
    TODAY:'today',
    SELECTED:'selected',
    URGENT:'urgent-day',
    IMPORTANT:'important-day',
    HAS_APPOINTMENT:'has-appointment',
    RECURRING:'recurring-day',
    RECURRING_PREFIX:'recurring-',
    COMPLETED:'completed-task',
    RESCHEDULED:'rescheduled-task'
  };

  const MESES = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"];

  /* ================= DOM HANDLES ================= */
  const dom = {
    monthYearEl:document.querySelector(SELECTORS.MONTH_YEAR),
    daysEl:document.querySelector(SELECTORS.DAYS),
    prevMonthBtn:document.querySelector(SELECTORS.PREV_BTN),
    nextMonthBtn:document.querySelector(SELECTORS.NEXT_BTN),
    appointmentsCard:document.querySelector(SELECTORS.APPOINTMENTS_CARD),
    toggleEditModeBtn:document.querySelector(SELECTORS.TOGGLE_EDIT_BTN),
    appointmentList:document.querySelector(SELECTORS.APPOINTMENT_LIST),
    appointmentModalEl:document.querySelector(SELECTORS.APPOINTMENT_MODAL),
    modalTitle:document.querySelector(SELECTORS.MODAL_TITLE),
    saveBtn:document.querySelector(SELECTORS.SAVE_BTN),
    deleteAllBtn:document.querySelector(SELECTORS.DELETE_ALL_BTN),
    deleteModalBtn:document.querySelector(SELECTORS.DELETE_MODAL_BTN),
    form:document.querySelector(SELECTORS.FORM),
    appointmentIdInput:document.querySelector(SELECTORS.FORM_ID),
    appointmentTimeInput:document.querySelector(SELECTORS.FORM_TIME),
    appointmentContentInput:document.querySelector(SELECTORS.FORM_CONTENT),
    appointmentPriorityInput:document.querySelector(SELECTORS.FORM_PRIORITY),
    appointmentRecurringInput:document.querySelector(SELECTORS.FORM_RECURRING),
    addAppointmentBtn:document.querySelector(SELECTORS.ADD_BTN),
    exportCalendarBtn:document.querySelector(SELECTORS.EXPORT_CALENDAR_BTN),
    importCalendarBtn:document.querySelector(SELECTORS.IMPORT_CALENDAR_BTN),
    importCalendarInput:document.querySelector(SELECTORS.IMPORT_CALENDAR_INPUT),
    importCalendarForm:document.querySelector(SELECTORS.IMPORT_CALENDAR_FORM)
  };

  const appointmentModal = new bootstrap.Modal(dom.appointmentModalEl);

  /* ================= STATE ================= */
  const state = {
    date:new Date(),
    get month(){return this.date.getMonth();},
    set month(m){this.date.setMonth(m);},
    get year(){return this.date.getFullYear();},
    set year(y){this.date.setFullYear(y);},
    selectedDate:new Date(),
    urgentDays:[],
    importantDays:[],
    activeDays:[],
    recurringDays:{},
    completedDays:[],
    rescheduledDays:[],
    modalOpenedProgrammatically:false
  };

  /* ================= UTILS ================= */
  const formatDate = d => {
    const y=d.getFullYear();
    const m=String(d.getMonth()+1).padStart(2,'0');
    const day=String(d.getDate()).padStart(2,'0');
    return `${y}-${m}-${day}`;
  };
  const formatDateBR = str => {
    if(!str) return '';
    const [y,m,d]=str.split('-');
    return `${d}/${m}/${y}`;
  };
  const normalizePriority = val => {
    if(!val) return 'normal';
    const v=val.toString().trim().toLowerCase();
    if(['urgente','urgent'].includes(v)) return 'urgent';
    if(['importante','important'].includes(v)) return 'important';
    if(['remarcada','rescheduled','remarcado'].includes(v)) return 'rescheduled';
    if(['normal','padrao','padrão'].includes(v)) return 'normal';
    return 'normal';
  };
  const fetchCalendarData = async (endpoint, expectObject=false) => {
    try{
      const r=await fetch(`/api/appointments/${endpoint}/${state.year}/${state.month+1}`);
      if(!r.ok) throw new Error(endpoint);
      return await r.json();
    }catch(e){
      console.error("Falha fetch:",endpoint,e);
      return expectObject?{}:[];
    }
  };

  const fetchAppointments = async dateStr => {
    dom.appointmentList.innerHTML='<p class="text-muted">A carregar...</p>';
    try{
      const r=await fetch(`/api/appointments/${dateStr}`);
      if(!r.ok) throw new Error(r.status);
      const data=await r.json();
      renderAppointments(data);
    }catch(e){
      console.error("Erro ao carregar compromissos",e);
      dom.appointmentList.innerHTML='<p class="text-danger">Erro ao carregar compromissos.</p>';
    }
  };

  /* ================= RENDER APPOINTMENTS ================= */
  const renderAppointments = appointments => {
    dom.appointmentList.innerHTML='';
    if(!appointments.length){
      dom.appointmentList.innerHTML='<p class="text-muted">Nenhum compromisso para este dia.</p>';
      return;
    }

    appointments.forEach(apt=>{
      const el=document.createElement('div');
      el.className='appointment-item';

      const originalPriority=apt.priority||'Normal';
      const prio=normalizePriority(originalPriority);

      el.dataset.priority=prio;
      if(apt.source) el.dataset.origin=apt.source.toLowerCase();
      if(apt.is_completed) el.dataset.status='completed';
      if(apt.recurring) el.dataset.recurring='true';

      const isRemarcada =
        (apt.content && /remarcad/i.test(apt.content))
        || (apt.remarcada_count && apt.remarcada_count>0)
        || prio==='rescheduled';

      if(isRemarcada && prio!=='rescheduled'){
        el.dataset.rescheduled='true';
      }
      el.dataset.id=apt.id;

      // Ícones
      const iconRecurring = apt.recurring ? '<i class="bi bi-arrow-repeat" title="Recorrente"></i>' : '';
      const iconCompleted = apt.is_completed ? '<i class="bi bi-check-circle-fill" title="Concluída"></i>' : '';
      const iconsBlock = `<span class="apt-icons">${iconRecurring}${iconCompleted}</span>`;

      // Horário (editável)
      const displayTime = apt.time || '--:--';
      const timeSpan = `<span class="apt-time time-edit-link"
          role="button"
          tabindex="0"
          data-id="${apt.id}"
          data-time="${apt.time||''}"
          data-content="${encodeURIComponent(apt.content)}"
          data-priority="${originalPriority}"
          data-recurring="${apt.recurring}"
          aria-label="Editar horário ${displayTime}"
        >${displayTime}</span>`;

      // Chip TRIAGEM para qualquer origem triagem
      // - Urgente: classe triagem-chip (já existente no CSS)
      // - Não urgente: classe triagem-chip-normal (estilo suave)
      let triagemChip = '';
      if (el.dataset.origin === 'triagem') {
        if (prio === 'urgent') {
          triagemChip = '<span class="triagem-chip" aria-label="Triagem urgente">TRIAGEM</span>';
        } else {
          triagemChip = '<span class="triagem-chip-normal" aria-label="Triagem">TRIAGEM</span>';
        }
      }

      // Ticket
      const ticketHtml = (apt.ticket_id && apt.ticket_title)
        ? `<a href="/ticket/${apt.ticket_id}" class="apt-ticket-link" title="Abrir caso">${apt.ticket_title}</a>`
        : '';

      // Wrapper "meio" (chip + ticket)
      // Se houver ticket e chip, juntamos; se não, só o que existir
      const middleContent = [triagemChip, ticketHtml].filter(Boolean).join(' ');

      // Badges meta
      const remarcadaBadge = (apt.remarcada_count && apt.remarcada_count>0)
        ? `<span class="apt-badge rescheduled" title="Remarcada ${apt.remarcada_count} vezes">${apt.remarcada_count}x</span>`
        : (isRemarcada && prio!=='rescheduled' ? '<span class="apt-badge rescheduled" title="Remarcada">R</span>' : '');

      const dataOriginalBadge = apt.data_original
        ? `<span class="apt-badge warning" title="Data original ${formatDateBR(apt.data_original)}">${formatDateBR(apt.data_original)}</span>`
        : '';

      const meta = `<span class="apt-meta">${remarcadaBadge}${dataOriginalBadge}</span>`;

      // Header: icons | time | (chip+ticket) | meta
      const headerHTML = `
        <div class="apt-header">
          ${iconsBlock}
          ${timeSpan}
          <span class="apt-ticket">${middleContent}</span>
          ${meta}
        </div>
      `;

      // Corpo
      const contentHTML = `
        <div class="apt-body">
          <span class="apt-content">${apt.content}</span>
        </div>
      `;

      // Ações (edit / delete)
      const actionsHTML = `
        <div class="appointment-actions">
          <button class="btn btn-sm btn-outline-secondary edit-btn"
            data-id="${apt.id}"
            data-time="${apt.time||''}"
            data-content="${encodeURIComponent(apt.content)}"
            data-priority="${originalPriority}"
            data-recurring="${apt.recurring}"
            data-bs-toggle="modal"
            data-bs-target="#appointmentModal"
            title="Editar">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger delete-btn"
            data-id="${apt.id}"
            title="Excluir">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      `;

      el.innerHTML = headerHTML + contentHTML + actionsHTML;
      dom.appointmentList.appendChild(el);
    });

    // Listeners: horário (click / Enter / Space)
    dom.appointmentList.querySelectorAll('.time-edit-link').forEach(node=>{
      const openModal=()=>{
        const id=node.dataset.id;
        const time=node.dataset.time;
        const content=decodeURIComponent(node.dataset.content||'');
        const pr=node.dataset.priority||'Normal';
        const rec=node.dataset.recurring==='true';

        state.modalOpenedProgrammatically=true;
        dom.form.reset();
        dom.modalTitle.textContent='Editar Compromisso';
        dom.appointmentIdInput.value=id;
        dom.appointmentTimeInput.value=time;
        dom.appointmentContentInput.value=content;
        dom.appointmentPriorityInput.value=pr;
        dom.appointmentRecurringInput.checked=rec;
        dom.deleteModalBtn.style.display='inline-block';
        appointmentModal.show();
      };
      node.addEventListener('click',openModal);
      node.addEventListener('keydown',e=>{
        if(e.key==='Enter'||e.key===' '){
          e.preventDefault();
          openModal();
        }
      });
    });
  };

  /* ================= MODAL SHOW ================= */
  dom.appointmentModalEl.addEventListener('show.bs.modal', e=>{
    if(e.relatedTarget && !state.modalOpenedProgrammatically){
      const trg=e.relatedTarget;
      dom.form.reset();
      const isEdit=trg.classList.contains('edit-btn');
      dom.modalTitle.textContent = isEdit ? 'Editar Compromisso' : 'Adicionar Compromisso';
      dom.deleteModalBtn.style.display = isEdit ? 'inline-block' : 'none';
      if(isEdit){
        dom.appointmentIdInput.value=trg.dataset.id;
        dom.appointmentTimeInput.value=trg.dataset.time||'';
        dom.appointmentContentInput.value=decodeURIComponent(trg.dataset.content||'');
        dom.appointmentPriorityInput.value=trg.dataset.priority||'Normal';
        dom.appointmentRecurringInput.checked = (trg.dataset.recurring==='true');
      }
    }
    state.modalOpenedProgrammatically=false;
  });

  /* ================= RENDER CALENDAR ================= */
  const renderCalendar = async () => {
    // Lista de endpoints suportados pelo backend
    const supportedEndpoints = ['urgent-days', 'important-days', 'active-days', 'recurring-days'];

    // Obter dados apenas para endpoints suportados
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

    // Inicializar como arrays vazios para endpoints não implementados
    state.completedDays = [];
    state.rescheduledDays = [];

    const firstDay = new Date(state.year, state.month, 1).getDay();
    const lastDate = new Date(state.year, state.month + 1, 0).getDate();
    const lastPrev = new Date(state.year, state.month, 0).getDate();
    dom.monthYearEl.textContent = `${MESES[state.month]} ${state.year}`;

    let html = '';
    for (let i = firstDay; i > 0; i--) {
      const d = lastPrev - i + 1;
      html += `<div class="prev-date" data-outside="true" data-day="${d}" aria-hidden="true">${d}</div>`;
    }

    const today = new Date();
    for (let day = 1; day <= lastDate; day++) {
      const cellDate = new Date(state.year, state.month, day);
      const iso = formatDate(cellDate);
      const isToday = cellDate.toDateString() === today.toDateString();
      const isSelected = cellDate.toDateString() === state.selectedDate.toDateString();

      let p = null;
      if (state.urgentDays.includes(day)) p = 'urgent';
      else if (state.rescheduledDays.includes(day)) p = 'rescheduled';
      else if (state.importantDays.includes(day)) p = 'important';
      else if (state.activeDays.includes(day)) p = 'normal';

      const recurringRaw = state.recurringDays[day];
      let hasRecurring = false;
      if (!p && recurringRaw) {
        hasRecurring = true;
        p = normalizePriority(recurringRaw);
      } else if (recurringRaw) {
        hasRecurring = true;
      }

      const isCompleted = state.completedDays.includes(day);
      const isRescheduled = state.rescheduledDays.includes(day);

      const attrs = [
        `data-day="${day}"`,
        `data-date="${iso}"`,
        isToday ? 'data-today="true"' : '',
        isSelected ? 'data-selected="true"' : '',
        p ? `data-priority="${p}"` : '',
        hasRecurring ? 'data-recurring="true"' : '',
        isCompleted ? 'data-status="completed"' : '',
        isRescheduled ? 'data-rescheduled="true"' : ''
      ].filter(Boolean).join(' ');

      // Adicionar classe "current-day" para estilo especial do dia atual
      const legacy = [];
      if (isToday) legacy.push(LEGACY_CLASSES.TODAY, 'current-day');
      if (isSelected) legacy.push(LEGACY_CLASSES.SELECTED);
      if (p === 'urgent') legacy.push(LEGACY_CLASSES.URGENT);
      else if (p === 'important') legacy.push(LEGACY_CLASSES.IMPORTANT);
      else if (p === 'normal') legacy.push(LEGACY_CLASSES.HAS_APPOINTMENT);
      if (hasRecurring) legacy.push(LEGACY_CLASSES.RECURRING, LEGACY_CLASSES.RECURRING_PREFIX + (p || 'normal'));
      if (isCompleted) legacy.push(LEGACY_CLASSES.COMPLETED);
      if (isRescheduled) legacy.push(LEGACY_CLASSES.RESCHEDULED);

      let aria = `${day} de ${MESES[state.month]} de ${state.year}`;
      if (isToday) aria += ', hoje';
      if (p === 'urgent') aria += ', urgente';
      if (p === 'important') aria += ', importante';
      if (p === 'rescheduled') aria += ', remarcado';
      if (hasRecurring) aria += ', recorrente';
      if (isCompleted) aria += ', concluído';

      html += `<div class="${legacy.join(' ')}" ${attrs} aria-label="${aria}">${day}</div>`;
    }

    const used = firstDay + lastDate;
    for (let i = 1; i <= 42 - used; i++) {
      html += `<div class="next-date" data-outside="true" data-day="${i}" aria-hidden="true">${i}</div>`;
    }

    dom.daysEl.innerHTML = html;

    dom.daysEl.querySelectorAll('div:not([data-outside="true"])').forEach(cell => {
      cell.addEventListener('click', () => {
        const d = parseInt(cell.dataset.day, 10);
        state.selectedDate = new Date(state.year, state.month, d);
        fetchAppointments(formatDate(state.selectedDate));
        renderCalendar();
      });
    });
  };

  /* ================= EVENTS ================= */
  const setupEvents = () => {
    dom.prevMonthBtn.addEventListener('click',()=>{state.month=state.month-1;renderCalendar();});
    dom.nextMonthBtn.addEventListener('click',()=>{state.month=state.month+1;renderCalendar();});

    dom.toggleEditModeBtn.addEventListener('click',()=>{
      dom.appointmentsCard.classList.toggle(LEGACY_CLASSES.EDIT_MODE);
      const icon=dom.toggleEditModeBtn.querySelector('i');
      icon.classList.toggle('bi-gear-fill');
      icon.classList.toggle('bi-check-circle-fill');
    });

    dom.deleteAllBtn.addEventListener('click',()=>{
      const dateStr=formatDate(state.selectedDate);
      if(confirm('Tem certeza que deseja excluir TODOS os compromissos deste dia?')){
        fetch(`/api/appointments/delete-all/${dateStr}`,{method:'DELETE'})
          .then(r=>{
            if(!r.ok) throw new Error();
            fetchAppointments(dateStr);
            renderCalendar();
          })
          .catch(()=>alert('Erro ao excluir todos.'));
      }
    });

    // Delete individual
    dom.appointmentList.addEventListener('click',e=>{
      const btn=e.target.closest('.delete-btn');
      if(!btn) return;
      const id=btn.dataset.id;
      if(confirm('Excluir compromisso?')){
        fetch(`/api/appointments/${id}`,{method:'DELETE'})
          .then(()=>{fetchAppointments(formatDate(state.selectedDate));renderCalendar();});
      }
    });

    // Add (reset modal)
    dom.addAppointmentBtn.addEventListener('click',()=>{
      dom.form.reset();
      dom.modalTitle.textContent='Adicionar Compromisso';
      dom.appointmentIdInput.value='';
      dom.appointmentTimeInput.value='';
      dom.appointmentContentInput.value='';
      dom.appointmentPriorityInput.value='Normal';
      dom.appointmentRecurringInput.checked=false;
      dom.deleteModalBtn.style.display='none';
    });

    // Save
    dom.saveBtn.addEventListener('click',async ()=>{
      const id=dom.appointmentIdInput.value;
      const body={
        content:dom.appointmentContentInput.value,
        time:dom.appointmentTimeInput.value,
        appointment_date:formatDate(state.selectedDate),
        priority:dom.appointmentPriorityInput.value,
        recurring:dom.appointmentRecurringInput.checked
      };
      const url=id?`/api/appointments/${id}`:'/api/appointments';
      const method=id?'PUT':'POST';
      try{
        const r=await fetch(url,{
          method,
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify(body)
        });
        if(!r.ok) throw new Error();
        appointmentModal.hide();
        fetchAppointments(body.appointment_date);
        renderCalendar();
      }catch(e){
        console.error(e);
        alert('Não foi possível salvar.');
      }
    });

    dom.deleteModalBtn.addEventListener('click',()=>{
      const id=dom.appointmentIdInput.value;
      if(!id) return;
      if(confirm('Excluir este compromisso?')){
        fetch(`/api/appointments/${id}`,{method:'DELETE'})
          .then(r=>{
            if(!r.ok) throw new Error();
            appointmentModal.hide();
            fetchAppointments(formatDate(state.selectedDate));
            renderCalendar();
          })
          .catch(()=>alert('Erro ao excluir.'));
      }
    });

    // Toggle completed (somente triagem)
    dom.appointmentList.addEventListener('click', e => {
      const item = e.target.closest('.appointment-item');

      if (!item) return;
      if (e.target.closest('.apt-ticket-link')) return;
      if (e.target.closest('.appointment-actions, .edit-btn, .delete-btn, .time-edit-link')) return;
      if (item.dataset.origin === 'triagem') {
        const id = item.dataset.id;
        const isDone = item.dataset.status === 'completed';

        // Feedback visual durante a atualização
        item.style.opacity = '0.7';

        fetch(`/api/appointments/${id}/toggle-completion`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            // Adicionar CSRF token se estiver usando Flask-WTF
            'X-CSRFToken': getCsrfToken()
          },
          body: JSON.stringify({is_completed: !isDone}),
          // Importante: adicionar credentials para que cookies de sessão sejam enviados
          credentials: 'same-origin'
        })
            .then(r => {
              // Restaurar opacidade
              item.style.opacity = '1';

              if (!r.ok) {
                console.error(`Erro na resposta: ${r.status} ${r.statusText}`);
                throw new Error(`Erro ${r.status}: ${r.statusText}`);
              }

              return r.json();
            })
            .then(data => {
              console.log('Toggle realizado com sucesso:', data);

              if (isDone) {
                delete item.dataset.status;
                item.classList.remove('completed');
              } else {
                item.dataset.status = 'completed';
                item.classList.add('completed');
              }
              renderCalendar();
            })
            .catch(err => {
              console.error('Erro toggle completion:', err);
              item.style.opacity = '1';

              // Exibir mensagem de erro ao usuário
              const errorMsg = document.createElement('div');
              errorMsg.className = 'alert alert-danger mt-2 mb-2';
              errorMsg.textContent = 'Erro ao atualizar status. Tente novamente.';
              errorMsg.style.fontSize = '0.8rem';
              errorMsg.style.padding = '0.25rem 0.5rem';

              item.appendChild(errorMsg);
              setTimeout(() => errorMsg.remove(), 3000);
            });
      }
    });

// Função auxiliar para obter CSRF token, se estiver usando Flask-WTF
    function getCsrfToken() {
      const tokenElement = document.querySelector('meta[name="csrf-token"]');
      return tokenElement ? tokenElement.getAttribute('content') : '';
    }

    // Export / Import
    if(dom.exportCalendarBtn){
      dom.exportCalendarBtn.addEventListener('click',e=>{
        e.preventDefault();
        window.location.href='/export_calendar_appointments';
      });
    }
    if(dom.importCalendarBtn && dom.importCalendarInput && dom.importCalendarForm){
      dom.importCalendarBtn.addEventListener('click',e=>{
        e.preventDefault();
        dom.importCalendarInput.click();
      });
      dom.importCalendarInput.addEventListener('change',function(){
        if(this.files.length>0){
          dom.importCalendarForm.submit();
        }
      });
    }
  };

  /* ================= INIT ================= */
  (async ()=>{
    setupEvents();
    await fetchAppointments(formatDate(state.selectedDate));
    await renderCalendar();
  })();

});