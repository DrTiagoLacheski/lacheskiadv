document.addEventListener('DOMContentLoaded', function() {
    // Elementos do DOM
    const loginForm = document.getElementById('loginForm');
    const limparBtn = document.getElementById('limparLogin');
    const loginMessage = document.getElementById('loginMessage');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    // Função para exibir mensagem de erro
    function showError(message) {
        loginMessage.textContent = message;
        loginMessage.classList.add('error');
        loginMessage.classList.remove('success'); // Garante que a classe de sucesso seja removida
    }

    // Função para exibir mensagem de sucesso/informação
    function showInfo(message) {
        loginMessage.textContent = message;
        loginMessage.classList.remove('error');
        loginMessage.classList.add('success');
    }

    // Função para limpar mensagens
    function clearMessages() {
        loginMessage.textContent = 'Informe as suas credenciais de acesso';
        loginMessage.classList.remove('error', 'success');
    }

    // Limpar campos do formulário
    if (limparBtn) {
        limparBtn.addEventListener('click', function() {
            loginForm.reset();
            clearMessages();
            usernameInput.focus();
        });
    }

    // Evento de submissão do formulário
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            // 1. Prevenir o comportamento padrão de submissão do formulário, que recarrega a página.
            e.preventDefault();

            // Validação básica no lado do cliente
            const username = usernameInput.value.trim();
            const password = passwordInput.value.trim();

            if (!username || !password) {
                showError('Por favor, preencha todos os campos');
                return;
            }

            // Mostra uma mensagem de "a processar"
            showInfo('A autenticar...');

            // 2. Usar a API Fetch para enviar os dados para o servidor como JSON
            fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                // Converte o objeto JavaScript para uma string JSON
                body: JSON.stringify({
                    username: username,
                    password: password
                }),
            })
            .then(response => response.json()) // Converte a resposta do servidor para JSON
            .then(data => {
                // 3. Processar a resposta do servidor
                if (data.success) {
                    // Se o login for bem-sucedido, redireciona para a URL fornecida pelo backend
                    showInfo('Login bem-sucedido! A redirecionar...');
                    window.location.href = data.redirect_url;
                } else {
                    // Se o login falhar, mostra a mensagem de erro retornada pelo servidor
                    showError(data.error || 'Ocorreu um erro desconhecido.');
                }
            })
            .catch(error => {
                // Lida com erros de rede ou outros problemas com a requisição
                console.error('Erro na requisição de login:', error);
                showError('Não foi possível conectar ao servidor.');
            });
        });
    }

    // Foco automático no campo de utilizador
    if (usernameInput) {
        usernameInput.focus();
    }

    // Limpar mensagens quando o utilizador começa a digitar
    [usernameInput, passwordInput].forEach(input => {
        if (input) {
            input.addEventListener('input', function() {
                if (loginMessage.classList.contains('error')) {
                    clearMessages();
                }
            });
        }
    });
});
