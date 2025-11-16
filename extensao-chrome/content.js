// Content Script - Roda na página do SEFAZ-MA
console.log('🔐 SEFAZ Auto Login - Extensão carregada');
console.log('📍 URL da página:', window.location.href);
console.log('🌐 Origin:', window.location.origin);

// Escuta mensagens do sistema web
window.addEventListener('message', async (event) => {
    console.log('📨 Mensagem recebida (raw):', event);
    console.log('📦 event.data:', event.data);
    console.log('🌍 event.origin:', event.origin);
    
    // Validar origem (ajuste para seu domínio em produção)
    // if (event.origin !== "http://localhost:8000") return;
    
    if (event.data.type === 'SEFAZ_AUTO_LOGIN') {
        console.log('✅ Mensagem do tipo SEFAZ_AUTO_LOGIN identificada!');
        console.log('📨 Credenciais recebidas:', event.data);
        
        const { cpf, senha, linkRecibo } = event.data;
        
        // Aguardar um pouco para garantir que a página carregou
        await sleep(1000);
        
        // Preencher campo CPF
        const campoUsuario = document.querySelector('input[name="identificacao"]');
        if (campoUsuario) {
            campoUsuario.value = cpf;
            campoUsuario.dispatchEvent(new Event('input', { bubbles: true }));
            console.log('✅ CPF preenchido:', cpf);
        } else {
            console.error('❌ Campo de usuário não encontrado');
        }
        
        // Preencher campo Senha
        const campoSenha = document.querySelector('input[name="senha"]');
        if (campoSenha) {
            campoSenha.value = senha;
            campoSenha.dispatchEvent(new Event('input', { bubbles: true }));
            console.log('✅ Senha preenchida');
        } else {
            console.error('❌ Campo de senha não encontrado');
        }
        
        // Aguardar um pouco antes de clicar
        await sleep(500);
        
        // Clicar no botão Entrar
        const botaoEntrar = document.querySelector('button[type="submit"]');
        if (botaoEntrar) {
            console.log('✅ Botão Entrar encontrado, clicando...');
            botaoEntrar.click();
            console.log('✅ Botão Entrar clicado automaticamente');
            
            // Se tiver link do recibo, aguardar login e abrir
            if (linkRecibo) {
                console.log('🎯 Link do recibo CONFIRMADO:', linkRecibo);
                console.log('⏳ Iniciando monitoramento de login...');
                await aguardarLoginEAbrirRecibo(linkRecibo);
            } else {
                console.warn('⚠️ Nenhum link do recibo foi fornecido');
            }
        } else {
            console.log('⚠️ Botão Entrar não encontrado - usuário deve clicar manualmente');
        }
    }
});

// Função para aguardar login completar e abrir recibo
async function aguardarLoginEAbrirRecibo(linkRecibo) {
    console.log('🔍 Iniciando aguardo de login...');
    console.log('🔗 Link do recibo:', linkRecibo);
    console.log('📍 URL atual:', window.location.href);
    
    // Aguardar redirecionamento após login (página principal SEFAZ)
    let tentativas = 0;
    const maxTentativas = 40; // 20 segundos (500ms * 40)
    
    const intervalo = setInterval(() => {
        tentativas++;
        console.log(`🔄 Tentativa ${tentativas}/${maxTentativas} - URL: ${window.location.href}`);
        
        // Verificar se o formulário de login sumiu (login bem-sucedido)
        const formularioLogin = document.querySelector('input[name="identificacao"]');
        const paginaPrincipal = document.querySelector('#principal, .menu-principal, #menu');
        
        console.log('   📝 Formulário existe?', !!formularioLogin);
        console.log('   🏠 Página principal?', !!paginaPrincipal);
        
        // Login completou quando: formulário sumiu OU elementos da página principal aparecem
        if (!formularioLogin || paginaPrincipal) {
            clearInterval(intervalo);
            console.log('');
            console.log('🎉 ========================================');
            console.log('🎉 LOGIN COMPLETADO COM SUCESSO!');
            console.log('🎉 ========================================');
            console.log('📍 URL atual:', window.location.href);
            console.log('📝 Formulário sumiu?', !formularioLogin);
            console.log('🏠 Página principal carregada?', !!paginaPrincipal);
            console.log('');
            console.log('🔗 Link do recibo a enviar:', linkRecibo);
            console.log('🪟 window.opener existe?', !!window.opener);
            console.log('');
            
            // Notificar a janela pai (aplicação) que o login foi concluído
            if (window.opener && linkRecibo) {
                console.log('📣 ===== ENVIANDO GATILHO PARA APLICAÇÃO =====');
                console.log('📦 Tipo da mensagem: SEFAZ_LOGIN_COMPLETO');
                console.log('📦 Link do recibo:', linkRecibo);
                console.log('📤 Destino: window.opener (aplicação pai)');
                
                try {
                    window.opener.postMessage({
                        type: 'SEFAZ_LOGIN_COMPLETO',
                        linkRecibo: linkRecibo
                    }, '*');
                    
                    console.log('');
                    console.log('✅ ========================================');
                    console.log('✅ GATILHO ENVIADO COM SUCESSO!');
                    console.log('✅ ========================================');
                    console.log('✅ A aplicação deve abrir o recibo agora...');
                    console.log('');
                } catch (error) {
                    console.error('');
                    console.error('❌ ========================================');
                    console.error('❌ ERRO AO ENVIAR GATILHO!');
                    console.error('❌ ========================================');
                    console.error('❌ Erro:', error);
                    console.error('');
                }
            } else {
                console.error('');
                console.error('❌ ========================================');
                console.error('❌ NÃO FOI POSSÍVEL ENVIAR GATILHO!');
                console.error('❌ ========================================');
                if (!window.opener) {
                    console.error('❌ Motivo: window.opener não existe');
                    console.error('❌ A janela não foi aberta via window.open()');
                }
                if (!linkRecibo) {
                    console.error('❌ Motivo: linkRecibo está vazio/null');
                }
                console.error('');
            }
        }
        
        if (tentativas >= maxTentativas) {
            clearInterval(intervalo);
            console.error('❌ Timeout aguardando login - URL ainda é:', window.location.href);
        }
    }, 500);
}

// Função auxiliar para aguardar
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Notificar que a extensão está pronta
console.log('✅ Extensão SEFAZ pronta para receber credenciais');
