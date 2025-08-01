document.addEventListener('DOMContentLoaded', function () {
    // MODAL: Apenas receita
    const modal = document.getElementById('add-entry-modal');
    const closeButtons = modal ? modal.querySelectorAll('.close-button') : [];
    const btnAddReceita = document.getElementById('add-receita-btn');
    const pillsReceita = document.getElementById('category-pills-receita');
    const hiddenCategoryInput = document.getElementById('categoria');
    const allPills = modal ? modal.querySelectorAll('.pill') : [];
    const valorInput = document.getElementById('valor');
    const dataInput = document.getElementById('data');
    const statusSelect = document.getElementById('status-select');
    const entryForm = document.getElementById('entry-form');

    function openModal() {
        if (!modal) return;
        modal.style.display = 'block';
        let firstPill = pillsReceita ? pillsReceita.querySelector('.pill') : null;
        if (firstPill) {
            pillsReceita.querySelectorAll('.pill').forEach(p => p.classList.remove('selected'));
            firstPill.classList.add('selected');
            hiddenCategoryInput.value = firstPill.dataset.value;
        }
        if (statusSelect) {
            statusSelect.value = "Recebido";
            statusSelect.disabled = false;
        }
    }

    if (btnAddReceita) {
        btnAddReceita.addEventListener('click', function(e) { e.preventDefault(); openModal(); });
    }

    closeButtons.forEach(btn => btn.addEventListener('click', function() {
        if (!modal) return;
        modal.style.display = 'none';
        if (entryForm) entryForm.reset();
        allPills.forEach(p => p.classList.remove('selected'));
        let firstPill = pillsReceita ? pillsReceita.querySelector('.pill') : null;
        if (firstPill) {
            firstPill.classList.add('selected');
            hiddenCategoryInput.value = firstPill.dataset.value;
        }
    }));

    allPills.forEach(pill => {
        pill.addEventListener('click', function () {
            if (!this.parentElement) return;
            this.parentElement.querySelectorAll('.pill').forEach(p => p.classList.remove('selected'));
            this.classList.add('selected');
            hiddenCategoryInput.value = this.dataset.value;
        });
    });

    window.addEventListener('click', (e) => {
        if (modal && e.target == modal) {
            modal.style.display = 'none';
            if (entryForm) entryForm.reset();
            allPills.forEach(p => p.classList.remove('selected'));
            let firstPill = pillsReceita ? pillsReceita.querySelector('.pill') : null;
            if (firstPill) {
                firstPill.classList.add('selected');
                hiddenCategoryInput.value = firstPill.dataset.value;
            }
        }
    });

    // -------- STATUS AUTOMÁTICO --------
    if (dataInput && statusSelect) {
        dataInput.addEventListener('change', function () {
            const selectedDate = new Date(dataInput.value);
            const today = new Date();
            today.setHours(0,0,0,0);
            if (selectedDate > today) {
                statusSelect.value = "Previsto";
                statusSelect.disabled = true;
            } else {
                statusSelect.disabled = false;
                if (statusSelect.value === "Previsto") {
                    statusSelect.value = "Recebido";
                }
            }
        });
    }

    // -------- MÁSCARA DE DINHEIRO NO INPUT DE VALOR --------
    if (valorInput) {
        valorInput.type = 'text';

        valorInput.addEventListener('input', function(e) {
            let v = e.target.value.replace(/\D/g, '');
            v = (parseInt(v, 10) || 0).toString();
            while (v.length < 3) v = '0' + v;
            let reais = v.slice(0, v.length - 2);
            let centavos = v.slice(-2);
            reais = reais.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
            e.target.value = reais + ',' + centavos;
        });

        valorInput.addEventListener('blur', function(e) {
            let v = e.target.value.replace(/\D/g, '');
            v = (parseInt(v, 10) || 0).toString();
            while (v.length < 3) v = '0' + v;
            let reais = v.slice(0, v.length - 2);
            let centavos = v.slice(-2);
            reais = reais.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
            e.target.value = reais + ',' + centavos;
        });

        if (entryForm) {
            entryForm.addEventListener('submit', function(e) {
                let valor = valorInput.value.replace(/\./g, '').replace(',', '.');
                valorInput.value = valor;
            });
        }
    }

    // ----------- Caso associado clicável -----------
    document.querySelectorAll('table tbody tr').forEach(function(row) {
        const casoCell = row.querySelector('td:nth-child(6)');
        if (casoCell && casoCell.textContent.trim() !== '-' && casoCell.textContent.trim() !== '') {
            const casoName = casoCell.textContent.trim();
            const select = document.getElementById('ticket_id');
            if (select) {
                let found = false;
                for (let i = 0; i < select.options.length; i++) {
                    if (select.options[i].text === casoName) {
                        const casoId = select.options[i].value;
                        if (casoId) {
                            casoCell.innerHTML = `<a href="/casos/${casoId}" style="color:#2557a7; text-decoration:underline" title="Ver caso">${casoName}</a>`;
                            found = true;
                            break;
                        }
                    }
                }
                if (!found) {
                    casoCell.innerHTML = casoName;
                }
            }
        }
    });

    // -------- GRÁFICOS --------
    if (typeof window.lancamentosChartData !== "undefined") {
        const {
            meses,
            recebidosData,
            previstosData,
            inadimplentesData,
            casosNomes,
            recebidosPorCaso,
            inadimplentesPorCaso,
            previstosPorCaso,
            inadimplentesCasosLabels,
            inadimplentesCasosData
        } = window.lancamentosChartData;

        // Gráfico por status mensal
        if (meses && recebidosData && previstosData && inadimplentesData) {
            const ctx = document.getElementById('receitasStatusChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: meses,
                    datasets: [
                        {
                            label: 'Recebido',
                            data: recebidosData,
                            backgroundColor: '#28a745',
                            borderWidth: 1
                        },
                        {
                            label: 'Inadimplente',
                            data: inadimplentesData,
                            backgroundColor: '#dc3545',
                            borderWidth: 1
                        },
                        {
                            label: 'Previsto',
                            data: previstosData,
                            backgroundColor: '#ffb347',
                            borderWidth: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    let v = ctx.parsed.y !== undefined ? ctx.parsed.y : ctx.raw;
                                    return ctx.dataset.label + ': R$ ' + v.toLocaleString('pt-BR', {minimumFractionDigits: 2});
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: { display: true, text: 'Valores (R$)' }
                        }
                    }
                }
            });
        }

        // 1. Gráfico de Barras Empilhadas por Caso
        if (casosNomes && recebidosPorCaso && inadimplentesPorCaso && previstosPorCaso) {
            const ctx = document.getElementById('receitasPorCasoEmpilhadoChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: casosNomes,
                    datasets: [
                        {
                            label: 'Recebido',
                            data: recebidosPorCaso,
                            backgroundColor: '#28a745'
                        },
                        {
                            label: 'Inadimplente',
                            data: inadimplentesPorCaso,
                            backgroundColor: '#dc3545'
                        },
                        {
                            label: 'Previsto',
                            data: previstosPorCaso,
                            backgroundColor: '#ffb347'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    let v = ctx.parsed.y !== undefined ? ctx.parsed.y : ctx.raw;
                                    return ctx.dataset.label + ': R$ ' + v.toLocaleString('pt-BR', {minimumFractionDigits: 2});
                                }
                            }
                        }
                    },
                    scales: {
                        x: { stacked: true },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            title: { display: true, text: 'Valores (R$)' }
                        }
                    }
                }
            });
        }

        // 2. Gráfico de Pizza dos inadimplentes por caso
        if (inadimplentesCasosLabels && inadimplentesCasosData) {
            const ctx = document.getElementById('inadimplentesPorCasoPie').getContext('2d');
            new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: inadimplentesCasosLabels,
                    datasets: [{
                        data: inadimplentesCasosData,
                        backgroundColor: [
                            '#dc3545', '#ff7675', '#e17055', '#fdcb6e', '#fd79a8',
                            '#636e72', '#00b894', '#0984e3', '#00cec9', '#6c5ce7'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    let v = ctx.parsed !== undefined ? ctx.parsed : ctx.raw;
                                    let total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                    let percent = total > 0 ? ((v / total) * 100).toLocaleString('pt-BR', {minimumFractionDigits: 1}) : "0.0";
                                    return ctx.label + ': R$ ' + v.toLocaleString('pt-BR', {minimumFractionDigits: 2}) + ` (${percent}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
    }

    // --- EDIÇÃO INLINE DO STATUS NA TABELA ---
    document.querySelectorAll('.status-cell').forEach(function(cell) {
        const span = cell.querySelector('.status-label');
        const select = cell.querySelector('.status-edit');
        const lancamentoId = cell.getAttribute('data-lancamento-id');

        if (!span || !select || !lancamentoId) return;

        // Ao clicar no status, mostra o select
        span.addEventListener('click', function() {
            span.style.display = 'none';
            select.style.display = '';
            select.focus();
        });

        // Ao perder o foco ou mudar, envia o update via AJAX
        function finishEdit() {
            const novoStatus = select.value;
            fetch(`/financeiro/atualizar-status/${lancamentoId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
                body: JSON.stringify({ status: novoStatus })
            })
            .then(resp => resp.json())
            .then(data => {
                if (data.success) {
                    // Atualiza visual
                    let statusClass = '';
                    if (novoStatus === 'Recebido') statusClass = 'status-recebido';
                    else if (novoStatus === 'Inadimplente') statusClass = 'status-inadimplente';
                    else statusClass = 'status-previsto';
                    span.innerHTML = `<span class="status ${statusClass}">${novoStatus}</span>`;
                } else {
                    alert('Erro ao atualizar status!');
                }
                span.style.display = '';
                select.style.display = 'none';
            })
            .catch(() => {
                alert('Erro ao atualizar status!');
                span.style.display = '';
                select.style.display = 'none';
            });
        }

        select.addEventListener('change', finishEdit);
        select.addEventListener('blur', finishEdit);
    });

    // --- ENVIO AJAX PARA ADICIONAR NO CALENDÁRIO AO CRIAR NOVO PREVISTO FUTURO ---
    if (entryForm) {
        entryForm.addEventListener('submit', function(e) {
            const tipo = entryForm.querySelector('[name="tipo"]') ? entryForm.querySelector('[name="tipo"]').value : "Entrada";
            const status = statusSelect ? statusSelect.value : "";
            const dataStr = dataInput ? dataInput.value : "";
            const descricao = entryForm.querySelector('#descricao') ? entryForm.querySelector('#descricao').value : "";
            const valor = valorInput ? valorInput.value : "";
            if (
                tipo === "Entrada" &&
                status === "Previsto" &&
                dataStr &&
                new Date(dataStr) > new Date()
            ) {
                // Após o submit padrão, faz uma requisição para adicionar ao calendário
                setTimeout(() => {
                    fetch("/api/appointments", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            content: `Receita prevista: ${descricao} (R$ ${valor})`,
                            appointment_date: dataStr,
                            appointment_time: "09:00",
                            priority: "Normal",
                            recurring: false
                        })
                    });
                }, 500); // pequeno delay para garantir lançamento criado
            }
        });
    }
});