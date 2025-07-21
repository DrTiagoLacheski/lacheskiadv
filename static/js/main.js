document.addEventListener('DOMContentLoaded', function() {
    // Confirmação antes de deletar
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja deletar este ticket?')) {
                e.preventDefault();
            }
        });
    });

    // Validação de arquivos antes de enviar
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const files = this.files;
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const fileSize = file.size / 1024 / 1024; // in MB
                if (fileSize > 16) {
                    alert('O arquivo ' + file.name + ' excede o tamanho máximo de 16MB');
                    this.value = ''; // clear the input
                    break;
                }

                const validExtensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'];
                const extension = file.name.split('.').pop().toLowerCase();
                if (!validExtensions.includes(extension)) {
                    alert('O arquivo ' + file.name + ' tem um tipo não permitido. Por favor, envie apenas PDF, DOC, JPG ou PNG.');
                    this.value = ''; // clear the input
                    break;
                }
            }
        });
    });
});