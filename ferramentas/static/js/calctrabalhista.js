// --- MÁSCARAS E FUNÇÕES UTILITÁRIAS ---

function aplicarMascaraMoeda(e) {
    let v = e.target.value.replace(/\D/g, '');
    v = (v / 100).toFixed(2) + '';
    v = v.replace('.', ',');
    v = v.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
    e.target.value = 'R$ ' + v;
}

function aplicarMascaraCpfCnpj(input, tipo) {
    input.addEventListener('input', function (e) {
        let v = e.target.value.replace(/\D/g, '');
        if (tipo === 'cpf') {
            v = v.slice(0, 11);
            v = v.replace(/(\d{3})(\d)/, '$1.$2');
            v = v.replace(/(\d{3})(\d)/, '$1.$2');
            v = v.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
        } else if (tipo === 'cnpj') {
            v = v.slice(0, 14);
            v = v.replace(/(\d{2})(\d)/, '$1.$2');
            v = v.replace(/(\d{3})(\d)/, '$1.$2');
            v = v.replace(/(\d{3})(\d)/, '$1/$2');
            v = v.replace(/(\d{4})(\d{1,2})$/, '$1-$2');
        }
        e.target.value = v;
    });
}

function aplicarMascaraRg(input) {
    input.addEventListener('input', function (e) {
        let v = e.target.value.replace(/\D/g, '').slice(0, 9);
        v = v.replace(/(\d{2})(\d)/, '$1.$2');
        v = v.replace(/(\d{3})(\d)/, '$1.$2');
        v = v.replace(/(\d{3})(\d{1})$/, '$1-$2');
        e.target.value = v;
    });
}

function getHorasPadrao(regime) {
    switch (regime) {
        case '5x2_40h': return 8;
        case '6x1_44h': return 7.33; // 44 / 6
        case '12x36': return 12;
        case '36h': return 6; // 36 / 6
        case '30h': return 5; // 30 / 6
        case '25h': return 4.16; // 25 / 6
        case '20h': return 3.33; // 20 / 6
        default: return 8;
    }
}

// --- LÓGICA PRINCIPAL DO FORMULÁRIO ---
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('calcTrabalhistaForm');
    const selectInformal = document.getElementById('remuneracao_informal');
    const selectHoraExtra = document.getElementById('hora_extra');
    const regimeJornadaSelect = document.getElementById('regime_jornada');
    const item10 = document.getElementById('item_10');
    const btnLimpar = document.getElementById('limparCampos');
    const btnAplicarParaTodos = document.getElementById('aplicarParaTodos');
    const feriadosDomingosSelect = document.getElementById('feriados_domingos');
    const dataGroup = document.getElementById('feriados_domingos_data_group');
    const listaDatas = document.getElementById('datas_feriados_domingos_lista');
    const btnAdicionarData = document.getElementById('adicionarDataFeriadoDomingo');

    // Máscaras
    aplicarMascaraCpfCnpj(document.getElementById('cpf_reclamante'), 'cpf');
    aplicarMascaraCpfCnpj(document.getElementById('cnpj_empresa'), 'cnpj');
    aplicarMascaraRg(document.getElementById('rg_reclamante'));
    document.getElementById('remuneracao').addEventListener('input', aplicarMascaraMoeda);
    document.getElementById('remuneracao_informal_valor').addEventListener('input', aplicarMascaraMoeda);

    // Seções dinâmicas
    function toggleDetalhesInformal() {
        const detalhes = document.getElementById('remuneracao_informal_detalhes');
        detalhes.style.display = selectInformal.value === 'sim' ? 'block' : 'none';
    }
    function toggleItem10() {
        item10.style.display = selectHoraExtra.value === 'sim' ? 'block' : 'none';
    }
    function toggleFeriadosDomingos() {
        dataGroup.style.display = feriadosDomingosSelect.value === 'sim' ? 'block' : 'none';
    }

    selectInformal.addEventListener('change', toggleDetalhesInformal);
    selectHoraExtra.addEventListener('change', toggleItem10);
    feriadosDomingosSelect.addEventListener('change', toggleFeriadosDomingos);

    // Inicial
    toggleDetalhesInformal();
    toggleItem10();
    toggleFeriadosDomingos();

    // Adição de datas de feriados/domingos
    if (btnAdicionarData) {
        btnAdicionarData.addEventListener('click', function () {
            const div = document.createElement('div');
            div.className = 'data-feriado-domingo-item';
            div.style.display = 'flex';
            div.style.alignItems = 'center';
            div.style.gap = '8px';

            const input = document.createElement('input');
            input.type = 'date';
            input.name = 'datas_feriados_domingos[]';
            input.required = true;

            const inputTipo = document.createElement('input');
            inputTipo.type = 'hidden';
            inputTipo.name = 'tipo_feriado_domingo[]';

            const info = document.createElement('span');
            info.style.fontSize = '0.95em';

            const setTipoInfo = () => {
                if (input.value) {
                    const data = new Date(input.value + 'T00:00:00');
                    const tipo = data.getDay() === 0 ? 'Domingo' : 'Feriado'; // 0 = Domingo
                    info.textContent = tipo;
                    inputTipo.value = tipo;
                } else {
                    info.textContent = '';
                    inputTipo.value = '';
                }
            };

            const inputHoras = document.createElement('input');
            inputHoras.type = 'number';
            inputHoras.name = 'horas_feriado_domingo[]';
            inputHoras.min = '0';
            inputHoras.max = '24';
            inputHoras.step = '0.25';
            inputHoras.placeholder = 'Horas';
            inputHoras.required = true;
            inputHoras.style.width = '70px';

            setTipoInfo();

            input.addEventListener('change', function () {
                const data = new Date(this.value + 'T00:00:00');
                const tipo = data.getDay() === 0 ? 'Domingo' : 'Feriado';
                info.textContent = tipo;
                inputTipo.value = tipo;
            });

            input.addEventListener('input', function () {
                if (this.value) {
                    const data = new Date(this.value + 'T00:00:00');
                    const tipo = data.getDay() === 0 ? 'Domingo' : 'Feriado';
                    info.textContent = tipo;
                    inputTipo.value = tipo;
                }
            });

            const btnRemover = document.createElement('button');
            btnRemover.type = 'button';
            btnRemover.textContent = 'Remover';
            btnRemover.className = 'btn btn-outline-secondary btn-sm';
            btnRemover.onclick = () => div.remove();

            div.appendChild(input);
            div.appendChild(inputHoras);
            div.appendChild(info);
            div.appendChild(inputTipo);
            div.appendChild(btnRemover);
            listaDatas.appendChild(div);
        });
    }

    // Cálculo de horas extras
    function calcularHorasExtras(row) {
        const inicioExpediente = row.querySelector('[name^="inicio_expediente_"]').value;
        const fimExpediente = row.querySelector('[name^="fim_expediente_"]').value;
        const resultadoInput = row.querySelector('[name^="horas_extra_"]');

        if (!inicioExpediente || !fimExpediente) {
            resultadoInput.value = "00:00:00";
            return;
        }

        function decimalParaHoraMinSeg(decimal) {
            const totalSegundos = Math.round(decimal * 3600);
            const horas = Math.floor(totalSegundos / 3600);
            const minutos = Math.floor((totalSegundos % 3600) / 60);
            const segundos = totalSegundos % 60;
            return (
                String(horas).padStart(2, '0') + ':' +
                String(minutos).padStart(2, '0') + ':' +
                String(segundos).padStart(2, '0')
            );
        }

        const inicio = new Date(`1970-01-01T${inicioExpediente}`);
        const fim = new Date(`1970-01-01T${fimExpediente}`);
        let diffHoras = (fim - inicio) / (1000 * 60 * 60);
        if (diffHoras < 0) diffHoras += 24;

        const inicioPausa = row.querySelector('[name^="inicio_intervalo_"]').value;
        const fimPausa = row.querySelector('[name^="fim_intervalo_"]').value;
        let pausaHoras = 0;
        if (inicioPausa && fimPausa) {
            const pausaInicio = new Date(`1970-01-01T${inicioPausa}`);
            const pausaFim = new Date(`1970-01-01T${fimPausa}`);
            pausaHoras = (pausaFim - pausaInicio) / (1000 * 60 * 60);
            if (pausaHoras < 0) pausaHoras = 0;
        }

        const horasTrabalhadas = diffHoras - pausaHoras;
        const horasPadrao = getHorasPadrao(regimeJornadaSelect.value);
        const horasExtras = Math.max(0, horasTrabalhadas - horasPadrao);

        resultadoInput.value = decimalParaHoraMinSeg(horasExtras);
    }

    // Configura grade de jornada
    document.querySelectorAll('.jornada-row').forEach(row => {
        const checkbox = row.querySelector('.dia-ativo');
        const inputs = row.querySelectorAll('.time-input');
        // Ativa/desativa inputs
        checkbox.addEventListener('change', function () {
            if (this.checked) {
                inputs.forEach(input => input.disabled = false);
            } else {
                inputs.forEach(input => {
                    input.disabled = true;
                    input.value = '';
                });
            }
            calcularHorasExtras(row);
        });
        // Calcula horas extras ao alterar horários
        inputs.forEach(input => {
            input.addEventListener('change', () => calcularHorasExtras(row));
        });
    });

    // Recalcula tudo se regime de jornada mudar
    regimeJornadaSelect.addEventListener('change', function () {
        document.querySelectorAll('.jornada-row').forEach(row => {
            calcularHorasExtras(row);
        });
    });

    // Botão "Aplicar para todos"
    if (btnAplicarParaTodos) {
        btnAplicarParaTodos.addEventListener('click', function () {
            const todasAsLinhas = Array.from(document.querySelectorAll('.jornada-row'));
            let primeiraLinhaAtiva = todasAsLinhas.find(linha => linha.querySelector('.dia-ativo').checked);

            if (!primeiraLinhaAtiva) {
                alert('Por favor, ative e preencha os horários do primeiro dia de trabalho.');
                return;
            }

            const valoresFonte = {
                inicioExp: primeiraLinhaAtiva.querySelector('[name^="inicio_expediente_"]').value,
                inicioPausa: primeiraLinhaAtiva.querySelector('[name^="inicio_intervalo_"]').value,
                fimPausa: primeiraLinhaAtiva.querySelector('[name^="fim_intervalo_"]').value,
                fimExp: primeiraLinhaAtiva.querySelector('[name^="fim_expediente_"]').value,
            };

            todasAsLinhas.forEach(linhaDestino => {
                if (linhaDestino !== primeiraLinhaAtiva && linhaDestino.querySelector('.dia-ativo').checked) {
                    linhaDestino.querySelector('[name^="inicio_expediente_"]').value = valoresFonte.inicioExp;
                    linhaDestino.querySelector('[name^="inicio_intervalo_"]').value = valoresFonte.inicioPausa;
                    linhaDestino.querySelector('[name^="fim_intervalo_"]').value = valoresFonte.fimPausa;
                    linhaDestino.querySelector('[name^="fim_expediente_"]').value = valoresFonte.fimExp;
                    calcularHorasExtras(linhaDestino);
                }
            });
        });
    }

    // Botão Limpar
    if (btnLimpar) {
        btnLimpar.addEventListener('click', function () {
            form.reset();
            toggleDetalhesInformal();
            toggleItem10();
            toggleFeriadosDomingos();
            document.querySelectorAll('.jornada-row').forEach(row => {
                row.querySelectorAll('input').forEach(input => {
                    if (input.type !== 'checkbox') input.value = '';
                    input.disabled = true;
                });
            });
        });
    }
});

// Submit do formulário
document.getElementById('calcTrabalhistaForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const form = e.target;
    const dados = {};
    new FormData(form).forEach((v, k) => { dados[k] = v; });

    fetch('/ferramentas/gerar-calculo-trabalhista', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    })
    .then(res => res.json())
    .then(res => {
        if (res.success && res.download_url) {
            const a = document.createElement('a');
            a.href = res.download_url;
            a.download = res.filename || 'relatorio.pdf';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        } else {
            alert(res.error || 'Erro ao gerar relatório.');
        }
    })
    .catch(() => alert('Erro ao gerar relatório.'));
});