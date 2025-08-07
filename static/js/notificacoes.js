// Este script verifica compromissos próximos e mostra um aviso!

function showAppointmentAlert(appointment) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning fixed-top text-center';
    alertDiv.style.zIndex = 9999;
    alertDiv.innerHTML = `
        <strong>Compromisso próximo:</strong> 
        ${appointment.time} - ${appointment.content}
        <button type="button" class="btn-close ms-2" data-bs-dismiss="alert" aria-label="Fechar"></button>
    `;
    document.body.appendChild(alertDiv);

    // Auto-fechar após 60 segundos
    setTimeout(() => alertDiv.remove(), 60000);
}

function checkUpcomingAppointments() {
    fetch('/api/notificacoes/compromissos_proximos')
        .then(response => response.json())
        .then(appointments => {
            appointments.forEach(showAppointmentAlert);
        });
}

// Checa ao carregar e a cada minuto
document.addEventListener('DOMContentLoaded', function() {
    checkUpcomingAppointments();
    setInterval(checkUpcomingAppointments, 60000);
});