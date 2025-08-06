document.addEventListener('DOMContentLoaded', function() {
    // Máscara para campo valor
    var valorInput = document.getElementById('valor');
    if(valorInput){
        valorInput.addEventListener('input', function(e){
            let v = e.target.value.replace(/\D/g,'');
            v = (parseInt(v,10)||0).toString();
            if(v.length < 3) v = v.padStart(3, '0');
            v = v.replace(/(\d+)(\d{2})$/, '$1,$2');
            e.target.value = v.replace(/^0+/, '') || '0,00';
        });
    }

    // Quill setup
    let quillRecibo = new Quill('#quill-editor', {
        theme: 'snow',
        placeholder: 'Ex: Referente ao pagamento de honorários...',
        modules: {
            toolbar: [
                [{'header': [1, 2, false]}],
                ['bold', 'italic', 'underline', 'strike'],
                [{'list': 'ordered'}, {'list': 'bullet'}],
                ['link', 'blockquote', 'code-block'],
                ['clean']
            ]
        }
    });

    var reciboForm = document.getElementById('reciboForm');
    var statusMsg = document.getElementById('statusMessage');
    if(reciboForm){
        // Antes do submit, copia o conteúdo do Quill para o input hidden
        reciboForm.addEventListener('submit', function(e){
            document.getElementById('texto_complementar').value = quillRecibo.root.innerText; // usa texto limpo
            statusMsg.textContent = "Gerando PDF...";
            // NÃO faça e.preventDefault() aqui!
        });
        reciboForm.addEventListener('reset', function(e){
            statusMsg.textContent = "Preencha os dados e clique em 'Gerar Recibo'";
            setTimeout(function () {
                quillRecibo.setText('');
                showJuridicaFields(false);
            }, 50);
        });
    }

    // Pessoa Jurídica checkbox: mostra/esconde campos
    var juridicaCheck = document.getElementById('isJuridica');
    var juridicaFields = document.getElementById('juridicaFields');
    juridicaCheck.addEventListener('change', function () {
        showJuridicaFields(juridicaCheck.checked);
    });

    function showJuridicaFields(show) {
        if (show) {
            juridicaFields.classList.remove('hidden');
            document.getElementById('nome_empresa').setAttribute('required', 'required');
            document.getElementById('cnpj').setAttribute('required', 'required');
            document.getElementById('sede').setAttribute('required', 'required');
        } else {
            juridicaFields.classList.add('hidden');
            document.getElementById('nome_empresa').removeAttribute('required');
            document.getElementById('cnpj').removeAttribute('required');
            document.getElementById('sede').removeAttribute('required');
        }
    }
});