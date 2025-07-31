document.addEventListener('DOMContentLoaded', function () {
    // MODAL: Apenas receita
    const modal = document.getElementById('add-entry-modal');
    const closeButtons = modal.querySelectorAll('.close-button');
    const btnAddReceita = document.getElementById('add-receita-btn');
    const pillsReceita = document.getElementById('category-pills-receita');
    const hiddenCategoryInput = document.getElementById('categoria');
    const allPills = modal.querySelectorAll('.pill');
    const valorInput = document.getElementById('valor');
    const dataInput = document.getElementById('data');
    const statusSelect = document.getElementById('status-select');

    function openModal() {
        modal.style.display = 'block';
        // Categoria padrão selecionada
        let firstPill = pillsReceita.querySelector('.pill');
        if (firstPill) {
            pillsReceita.querySelectorAll('.pill').forEach(p => p.classList.remove('selected'));
            firstPill.classList.add('selected');
            hiddenCategoryInput.value = firstPill.dataset.value;
        }
        // Reset status to "Recebido" by default
        statusSelect.value = "Recebido";
        statusSelect.disabled = false;
    }

    btnAddReceita.addEventListener('click', function(e) { e.preventDefault(); openModal(); });

    closeButtons.forEach(btn => btn.addEventListener('click', function() {
        modal.style.display = 'none';
        document.getElementById('entry-form').reset();
        allPills.forEach(p => p.classList.remove('selected'));
        // Categoria padrão ao abrir novamente
        let firstPill = pillsReceita.querySelector('.pill');
        if (firstPill) {
            firstPill.classList.add('selected');
            hiddenCategoryInput.value = firstPill.dataset.value;
        }
    }));

    allPills.forEach(pill => {
        pill.addEventListener('click', function () {
            this.parentElement.querySelectorAll('.pill').forEach(p => p.classList.remove('selected'));
            this.classList.add('selected');
            hiddenCategoryInput.value = this.dataset.value;
        });
    });

    window.addEventListener('click', (e) => {
        if (e.target == modal) {
            modal.style.display = 'none';
            document.getElementById('entry-form').reset();
            allPills.forEach(p => p.classList.remove('selected'));
            let firstPill = pillsReceita.querySelector('.pill');
            if (firstPill) {
                firstPill.classList.add('selected');
                hiddenCategoryInput.value = firstPill.dataset.value;
            }
        }
    });

    // -------- STATUS AUTOMÁTICO --------
    if (dataInput) {
        dataInput.addEventListener('change', function () {
            const selectedDate = new Date(dataInput.value);
            const today = new Date();
            today.setHours(0,0,0,0); // Zera o horário para comparar só a data
            if (selectedDate > today) {
                statusSelect.value = "Previsto";
                statusSelect.disabled = true;
            } else {
                statusSelect.disabled = false;
                // Se estava previsto, volta para Recebido
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

        document.getElementById('entry-form').addEventListener('submit', function(e) {
            let valor = valorInput.value.replace(/\./g, '').replace(',', '.');
            valorInput.value = valor;
        });
    }

    // ----------- Caso associado clicável -----------
    // Transforma o nome do caso em link para visualizar o caso (se houver)
    // Substitui todas as células da tabela de lançamentos que possuem caso associado
    document.querySelectorAll('table tbody tr').forEach(function(row) {
        const casoCell = row.querySelector('td:nth-child(6)');
        if (casoCell && casoCell.textContent.trim() !== '-' && casoCell.textContent.trim() !== '') {
            // Recupera o nome do caso
            const casoName = casoCell.textContent.trim();
            // Recupera o select do formulário de novo lançamento para pegar os ids e nomes dos casos
            const select = document.getElementById('ticket_id');
            if (select) {
                let found = false;
                for (let i = 0; i < select.options.length; i++) {
                    if (select.options[i].text === casoName) {
                        // Monta a url para o caso (ajuste o endpoint se necessário)
                        // Exemplo Flask: url_for('main.visualizar_caso', caso_id=...)
                        // Aqui assume /casos/<id>
                        const casoId = select.options[i].value;
                        if (casoId) {
                            casoCell.innerHTML = `<a href="/ticket/${casoId}" style="color:#2557a7; text-decoration:underline" title="Ver caso">${casoName}</a>`;
                            found = true;
                            break;
                        }
                    }
                }
                if (!found) {
                    // Se não encontrou, mantem texto simples
                    casoCell.innerHTML = casoName;
                }
            }
        }
    });

    // -------- GRÁFICOS DE RECEITAS POR STATUS: RECEBIDO, PREVISTO, INADIMPLENTE --------
    if (typeof window.lancamentosChartData !== "undefined") {
        const {
            meses,
            recebidosData,
            previstosData,
            inadimplentesData,
            pagosLabels,
            pagosData,
            casoLabels,
            casoValores
        } = window.lancamentosChartData;

        // RECEITAS POR STATUS: barras agrupadas
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
                            label: 'Previsto',
                            data: previstosData,
                            backgroundColor: '#ffb347',
                            borderWidth: 1
                        },
                        {
                            label: 'Inadimplente',
                            data: inadimplentesData,
                            backgroundColor: '#dc3545',
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

        // PAGOS POR CASO: doughnut
        if (pagosLabels && pagosData) {
            let pagosColors = [
                '#3498db','#e74c3c','#f1c40f','#9b59b6','#bdc3c7',
                '#28a745','#dc3545','#ff9800','#00bcd4','#ffb347','#bada55'
            ];
            const ctx = document.getElementById('pagosPorCasoChart').getContext('2d');
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: pagosLabels,
                    datasets: [{ data: pagosData, backgroundColor: pagosColors }]
                },
                options: {
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    let v = ctx.parsed !== undefined ? ctx.parsed : ctx.raw;
                                    return ctx.label + ': R$ ' + v.toLocaleString('pt-BR', {minimumFractionDigits: 2});
                                }
                            }
                        }
                    },
                    cutout: '70%',
                }
            });

            let legendDiv = document.getElementById('pagos-legend');
            if (legendDiv && pagosLabels.length > 0) {
                legendDiv.innerHTML = '';
                pagosLabels.forEach(function(label, idx) {
                    let color = pagosColors[idx % pagosColors.length];
                    let span = document.createElement('span');
                    span.innerHTML = `<span class="chart-legend-dot" style="background:${color}"></span>${label}`;
                    legendDiv.appendChild(span);
                });
            }
        }

        // RENTABILIDADE POR CASO: barras horizontais
        if (casoLabels && casoValores) {
            const ctx = document.getElementById('rentabilidadeChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: casoLabels,
                    datasets: [{
                        label: 'Rentabilidade',
                        data: casoValores,
                        backgroundColor: casoValores.map(v => v >= 0 ? '#28a745' : '#dc3545'),
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(ctx) {
                                    let v = ctx.parsed.x !== undefined ? ctx.parsed.x : ctx.raw;
                                    return (v >= 0 ? 'Lucro: ' : 'Prejuízo: ') + 'R$ ' + Math.abs(v).toLocaleString('pt-BR', {minimumFractionDigits: 2});
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            title: { display: true, text: 'R$' }
                        }
                    }
                }
            });
        }
    }
});