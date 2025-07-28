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

/**
 * Retorna a jornada de trabalho padrão em horas com base no regime selecionado.
 * @param {string} regime O valor do select 'regime_jornada'.
 * @returns {number} As horas diárias padrão.
 */
function getHorasPadrao(regime) {
    // Nota: 44h semanais em 6 dias são 7.33h (7h20min).
    // Para 12x36, a hora extra é o que excede a 12ª hora no dia de trabalho.
    switch (regime) {
        case '5x2_40h':
            return 8;
        case '6x1_44h':
            return 7.33; // 44 / 6
        case '12x36':
            return 12;
        case '36h':
            return 6; // 36 / 6
        case '30h':
            return 5; // 30 / 6
        case '25h':
            return 4.16; // 25 / 6
        case '20h':
            return 3.33; // 20 / 6
        default:
            return 8; // Padrão
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

    if (feriadosDomingosSelect && dataGroup && listaDatas && btnAdicionarData) {
        feriadosDomingosSelect.addEventListener('change', function () {
            dataGroup.style.display = this.value === 'sim' ? 'block' : 'none';
        });

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

            const info = document.createElement('span');
            info.style.fontSize = '0.95em';

            const inputHoras = document.createElement('input');
                inputHoras.type = 'number';
                inputHoras.name = 'horas_feriado_domingo[]';
                inputHoras.min = '0';
                inputHoras.max = '24';
                inputHoras.step = '0.25';
                inputHoras.placeholder = 'Horas';
                inputHoras.required = true;
                inputHoras.style.width = '70px';

            input.addEventListener('change', function () {
                const data = new Date(this.value + 'T00:00:00');
                const diaSemana = data.getDay();
                if (diaSemana === 0) {
                    info.textContent = 'Domingo';
                } else {
                    info.textContent = 'Feriado';
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
            div.appendChild(btnRemover);
            listaDatas.appendChild(div);
        });
    }


        // Aplicar máscaras
        aplicarMascaraCpfCnpj(document.getElementById('cpf_reclamante'), 'cpf');
        aplicarMascaraCpfCnpj(document.getElementById('cnpj_empresa'), 'cnpj');
        aplicarMascaraRg(document.getElementById('rg_reclamante'));
        document.getElementById('remuneracao').addEventListener('input', aplicarMascaraMoeda);
        document.getElementById('remuneracao_informal_valor').addEventListener('input', aplicarMascaraMoeda);
        document.getElementById('ferias_vencidas').dispatchEvent(new Event('change'));
        document.getElementById('remuneracao_informal').dispatchEvent(new Event('change'));
        document.getElementById('hora_extra').dispatchEvent(new Event('change'));
        document.getElementById('feriados_domingos').dispatchEvent(new Event('change'));

        // Lógica da Remuneração Informal
        selectInformal.addEventListener('change', function () {
            const detalhes = document.getElementById('remuneracao_informal_detalhes');
            detalhes.style.display = this.value === 'sim' ? 'block' : 'none';
        });

        // Lógica para mostrar/esconder a seção de horas extras
        selectHoraExtra.addEventListener('change', function () {
            item10.style.display = this.value === 'sim' ? 'block' : 'none';
        });

        /**
         * Calcula as horas extras para uma linha específica da grade de jornada.
         * @param {HTMLElement} row O elemento da linha (.jornada-row).
         */
        function calcularHorasExtras(row) {
            const inicioExpediente = row.querySelector('[name^="inicio_expediente_"]').value;
            const fimExpediente = row.querySelector('[name^="fim_expediente_"]').value;
            const resultadoInput = row.querySelector('[name^="horas_extra_"]'); // Corrigido

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

        // Adiciona listeners para cada linha da grade de jornada
        document.querySelectorAll('.jornada-row').forEach(row => {
            const inputs = row.querySelectorAll('.time-input, .he-resultado');
            const checkbox = row.querySelector('.dia-ativo');

            // Habilita/desabilita a linha com base no checkbox
            checkbox.addEventListener('change', function () {
                inputs.forEach(input => {
                    input.disabled = !this.checked;
                });
                if (!this.checked) {
                    inputs.forEach(input => input.value = '');
                } else {
                    calcularHorasExtras(row);
                }
            });

            // Recalcula ao alterar qualquer horário
            row.querySelectorAll('.time-input').forEach(input => {
                input.addEventListener('change', () => calcularHorasExtras(row));
            });
        });

        // Recalcula tudo se o regime de jornada for alterado
        regimeJornadaSelect.addEventListener('change', function () {
            document.querySelectorAll('.jornada-row').forEach(row => {
                if (row.querySelector('.dia-ativo').checked) {
                    calcularHorasExtras(row);
                }
            });
        });

        // Lógica do botão "Copiar para todos"
        btnAplicarParaTodos.addEventListener('click', function () {
            const todasAsLinhas = Array.from(document.querySelectorAll('.jornada-row'));
            let primeiraLinhaAtiva = null;

            for (const linha of todasAsLinhas) {
                if (linha.querySelector('.dia-ativo').checked) {
                    primeiraLinhaAtiva = linha;
                    break;
                }
            }

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
                // Aplica somente para as outras linhas que também estiverem ativas
                if (linhaDestino !== primeiraLinhaAtiva && linhaDestino.querySelector('.dia-ativo').checked) {
                    linhaDestino.querySelector('[name^="inicio_expediente_"]').value = valoresFonte.inicioExp;
                    linhaDestino.querySelector('[name^="inicio_intervalo_"]').value = valoresFonte.inicioPausa;
                    linhaDestino.querySelector('[name^="fim_intervalo_"]').value = valoresFonte.fimPausa;
                    linhaDestino.querySelector('[name^="fim_expediente_"]').value = valoresFonte.fimExp;
                    calcularHorasExtras(linhaDestino); // Recalcula para a linha atualizada
                }
            });
        });

        // Lógica do Botão de Limpar
        btnLimpar.addEventListener('click', function () {
            form.reset();
            // Dispara eventos para garantir que as seções colapsem
            selectInformal.dispatchEvent(new Event('change'));
            selectHoraExtra.dispatchEvent(new Event('change'));
            // Reseta o estado dos checkboxes e campos da jornada
            document.querySelectorAll('.jornada-row').forEach(row => {
                row.querySelectorAll('input').forEach(input => {
                    if (input.type !== 'checkbox') input.value = '';
                    input.disabled = true;
                });
            });
        });

        // Define o estado inicial da página ao carregar
        selectInformal.dispatchEvent(new Event('change'));
        selectHoraExtra.dispatchEvent(new Event('change'));
    }
)
    ;

    document.getElementById('feriados_domingos').addEventListener('change', function () {
        const dataGroup = document.getElementById('feriados_domingos_data_group');
        dataGroup.style.display = this.value === 'sim' ? 'block' : 'none';
    });