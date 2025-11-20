// Content Script Enhanced - v1.2.0
console.log('🔐 SEFAZ Auto Login v1.2.0 - Content Script carregado');
console.log('📍 URL:', window.location.href);
console.log('🌐 Origin:', window.location.origin);
console.log('⏰ Timestamp:', new Date().toISOString());

// Estado do content script
let contentState = {
    scriptReady: true,
    currentOperation: null,
    lastMessage: null,
    operationStartTime: null
};

// Listener robusto para mensagens da extensão
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    const timestamp = new Date().toISOString();
    const connectionId = request.connectionId || 'unknown';
    
    console.log(`📨 [${connectionId}] Mensagem recebida [${timestamp}]:`, {
        action: request.action,
        hasData: !!request.dados,
        sender: sender?.id
    });
    
    // Validar mensagem
    if (!request.action) {
        console.error(`❌ [${connectionId}] Mensagem sem ação`);
        sendResponse({ success: false, error: 'Mensagem inválida: sem ação' });
        return false;
    }
    
    contentState.lastMessage = request;
    contentState.operationStartTime = Date.now();
    
    switch (request.action) {
        case 'executarConsulta':
            console.log(`🎯 [${connectionId}] Executando consulta visual...`);
            contentState.currentOperation = 'consulta';
            
            handleConsultaVisual(request.dados, connectionId)
                .then(result => {
                    console.log(`✅ [${connectionId}] Consulta concluída:`, result);
                    sendResponse({
                        success: true,
                        data: result,
                        timestamp: new Date().toISOString(),
                        connectionId,
                        duration: Date.now() - contentState.operationStartTime
                    });
                })
                .catch(error => {
                    console.error(`❌ [${connectionId}] Erro na consulta:`, error);
                    sendResponse({
                        success: false,
                        error: error.message,
                        timestamp: new Date().toISOString(),
                        connectionId,
                        duration: Date.now() - contentState.operationStartTime
                    });
                })
                .finally(() => {
                    contentState.currentOperation = null;
                    contentState.operationStartTime = null;
                });
            
            return true; // Resposta assíncrona
            
        case 'getStatus':
            console.log(`📊 [${connectionId}] Status do content script`);
            sendResponse({
                success: true,
                data: {
                    state: contentState,
                    url: window.location.href,
                    ready: contentState.scriptReady,
                    timestamp: new Date().toISOString()
                },
                connectionId
            });
            return false; // Resposta síncrona
            
        default:
            console.warn(`❓ [${connectionId}] Ação desconhecida:`, request.action);
            sendResponse({
                success: false,
                error: 'Ação não reconhecida: ' + request.action,
                connectionId
            });
            return false;
    }
});

// Função principal para consulta visual
async function handleConsultaVisual(dados, connectionId) {
    try {
        console.log(`🎯 [${connectionId}] Iniciando consulta visual com dados:`, {
            cpf: dados.cpf_socio ? dados.cpf_socio.substring(0, 3) + '***' : 'N/A',
            ie: dados.inscricao_estadual || 'N/A',
            url: window.location.href
        });
        
        // Validar página
        await validatePage();
        console.log(`✅ [${connectionId}] Página validada`);
        
        // Aguardar página estar pronta
        await waitForPageReady();
        console.log(`✅ [${connectionId}] Página pronta`);
        
        // Executar login se necessário
        if (needsLogin()) {
            const loginResult = await executeLogin(dados, connectionId);
            console.log(`✅ [${connectionId}] Login executado:`, loginResult);
            
            // Aguardar redirecionamento
            await waitForLoginRedirect(connectionId);
            console.log(`✅ [${connectionId}] Redirecionamento concluído`);
        }
        
        // Navegar para consulta se necessário
        if (!window.location.href.includes('consultas/pj')) {
            await navigateToConsulta(connectionId);
            console.log(`✅ [${connectionId}] Navegação para consulta concluída`);
        }
        
        // Executar consulta específica
        const consultaResult = await executeConsulta(dados, connectionId);
        console.log(`✅ [${connectionId}] Consulta executada:`, consultaResult);
        
        return {
            success: true,
            data: consultaResult,
            url: window.location.href,
            timestamp: new Date().toISOString(),
            connectionId,
            steps: ['validation', 'login', 'navigation', 'query', 'extraction']
        };
        
    } catch (error) {
        console.error(`❌ [${connectionId}] Erro na consulta visual:`, error);
        throw new Error(`Consulta falhou: ${error.message}`);
    }
}

// Validar se estamos na página correta
async function validatePage() {
    const allowedDomains = ['sefaz.ma.gov.br', 'sefaznet.sefaz.ma.gov.br'];
    const currentDomain = window.location.hostname;
    
    if (!allowedDomains.some(domain => currentDomain.includes(domain))) {
        throw new Error(`Página inválida. Domínio: ${currentDomain}. Esperado: ${allowedDomains.join(' ou ')}`);
    }
    
    return true;
}

// Aguardar página estar completamente pronta
function waitForPageReady() {
    return new Promise((resolve) => {
        if (document.readyState === 'complete') {
            setTimeout(resolve, 1500); // Aguardar scripts carregarem
        } else {
            window.addEventListener('load', () => {
                setTimeout(resolve, 1500);
            });
        }
    });
}

// Verificar se precisa fazer login
function needsLogin() {
    const loginFields = document.querySelector('input[name="identificacao"], input[name="cpf"]');
    const loggedInIndicators = document.querySelector('#principal, .menu-principal, .user-menu, .logout');
    
    console.log('🔍 Verificando necessidade de login:', {
        hasLoginFields: !!loginFields,
        hasLoggedInIndicators: !!loggedInIndicators,
        url: window.location.href
    });
    
    return !!loginFields && !loggedInIndicators;
}

// Executar login automático
async function executeLogin(dados, connectionId) {
    console.log(`🔐 [${connectionId}] Executando login...`);
    
    if (!dados.cpf_socio || !dados.senha) {
        throw new Error('Dados de login incompletos (CPF/senha)');
    }
    
    // Aguardar campos aparecerem
    await waitForElement('input[name="identificacao"], input[name="cpf"]', 10000);
    
    // Preencher CPF
    const campoCpf = document.querySelector('input[name="identificacao"], input[name="cpf"]');
    if (!campoCpf) {
        throw new Error('Campo de CPF não encontrado');
    }
    
    campoCpf.value = dados.cpf_socio;
    campoCpf.dispatchEvent(new Event('input', { bubbles: true }));
    campoCpf.dispatchEvent(new Event('change', { bubbles: true }));
    console.log(`✅ [${connectionId}] CPF preenchido`);
    
    // Aguardar e preencher senha
    await sleep(300);
    const campoSenha = document.querySelector('input[name="senha"], input[type="password"]');
    if (!campoSenha) {
        throw new Error('Campo de senha não encontrado');
    }
    
    campoSenha.value = dados.senha;
    campoSenha.dispatchEvent(new Event('input', { bubbles: true }));
    campoSenha.dispatchEvent(new Event('change', { bubbles: true }));
    console.log(`✅ [${connectionId}] Senha preenchida`);
    
    // Aguardar e clicar no botão
    await sleep(500);
    const botaoLogin = document.querySelector('button[type="submit"], input[type="submit"], button:contains("Entrar")') ||
                      document.querySelector('button, input[value*="Entrar"]');
    
    if (!botaoLogin) {
        throw new Error('Botão de login não encontrado');
    }
    
    console.log(`🚀 [${connectionId}] Clicando no botão de login...`);
    botaoLogin.click();
    
    return { status: 'login_initiated', timestamp: new Date().toISOString() };
}

// Aguardar redirecionamento após login
async function waitForLoginRedirect(connectionId) {
    console.log(`⏳ [${connectionId}] Aguardando redirecionamento...`);
    
    return new Promise((resolve, reject) => {
        let attempts = 0;
        const maxAttempts = 60; // 30 segundos
        
        const interval = setInterval(() => {
            attempts++;
            
            // Verificar se login foi concluído
            const loginForm = document.querySelector('input[name="identificacao"], input[name="cpf"]');
            const loggedIn = document.querySelector('#principal, .menu-principal, .user-menu') ||
                           !window.location.href.includes('login') ||
                           window.location.href.includes('portal') ||
                           window.location.href.includes('cidadao');
            
            if (!loginForm || loggedIn) {
                clearInterval(interval);
                console.log(`✅ [${connectionId}] Login detectado, redirecionamento concluído`);
                setTimeout(resolve, 2000); // Aguardar estabilizar
                return;
            }
            
            // Verificar erros de login
            const errorElement = document.querySelector('.error, .alert, .msg-erro, .erro');
            if (errorElement && errorElement.textContent.toLowerCase().includes('erro')) {
                clearInterval(interval);
                reject(new Error(`Erro de login detectado: ${errorElement.textContent}`));
                return;
            }
            
            if (attempts >= maxAttempts) {
                clearInterval(interval);
                reject(new Error('Timeout aguardando redirecionamento do login (30s)'));
            }
        }, 500);
    });
}

// Navegar para página de consultas
async function navigateToConsulta(connectionId) {
    console.log(`🧭 [${connectionId}] Navegando para consultas PJ...`);
    
    const consultaUrl = 'https://sefaz.ma.gov.br/portal/cidadao/consultas/pj';
    window.location.href = consultaUrl;
    
    // Aguardar nova página carregar
    await waitForPageReady();
    
    return { navigated: true, url: window.location.href };
}

// Executar consulta específica
async function executeConsulta(dados, connectionId) {
    console.log(`📋 [${connectionId}] Executando consulta específica...`);
    
    // Aguardar formulário aparecer
    await waitForElement('form, input[type="text"]', 15000);
    console.log(`✅ [${connectionId}] Formulário de consulta encontrado`);
    
    // Preencher formulário
    await fillConsultaForm(dados, connectionId);
    
    // Submeter consulta
    await submitConsulta(connectionId);
    
    // Aguardar e extrair resultados
    const resultado = await waitForResults(connectionId);
    
    return resultado;
}

// Preencher formulário de consulta
async function fillConsultaForm(dados, connectionId) {
    console.log(`✏️ [${connectionId}] Preenchendo formulário...`);
    
    // Buscar campo de CPF/CNPJ
    const campoCpf = document.querySelector('input[name*="cpf"], input[id*="cpf"], input[placeholder*="CPF"]') ||
                     document.querySelector('input[name*="cnpj"], input[id*="cnpj"], input[placeholder*="CNPJ"]') ||
                     document.querySelector('input[type="text"]:first-of-type');
    
    if (campoCpf && dados.cpf_socio) {
        campoCpf.value = dados.cpf_socio;
        campoCpf.dispatchEvent(new Event('input', { bubbles: true }));
        campoCpf.dispatchEvent(new Event('change', { bubbles: true }));
        console.log(`✅ [${connectionId}] CPF preenchido no formulário`);
        await sleep(300);
    }
    
    // Preencher IE se disponível
    if (dados.inscricao_estadual) {
        const campoIe = document.querySelector('input[name*="ie"], input[id*="inscricao"], input[placeholder*="IE"]') ||
                       document.querySelector('input[name*="estadual"]');
        
        if (campoIe) {
            campoIe.value = dados.inscricao_estadual;
            campoIe.dispatchEvent(new Event('input', { bubbles: true }));
            campoIe.dispatchEvent(new Event('change', { bubbles: true }));
            console.log(`✅ [${connectionId}] IE preenchida`);
            await sleep(300);
        }
    }
    
    return true;
}

// Submeter consulta
async function submitConsulta(connectionId) {
    console.log(`🚀 [${connectionId}] Submetendo consulta...`);
    
    const submitButton = document.querySelector('button[type="submit"], input[type="submit"]') ||
                        document.querySelector('button:contains("Consultar"), button:contains("Buscar")') ||
                        document.querySelector('button, input[value*="Consultar"]');
    
    if (!submitButton) {
        throw new Error('Botão de consulta não encontrado');
    }
    
    submitButton.click();
    await sleep(1000);
    
    return { submitted: true, timestamp: new Date().toISOString() };
}

// Aguardar e extrair resultados
async function waitForResults(connectionId) {
    console.log(`⏳ [${connectionId}] Aguardando resultados...`);
    
    return new Promise((resolve, reject) => {
        let attempts = 0;
        const maxAttempts = 120; // 60 segundos
        
        const interval = setInterval(() => {
            attempts++;
            
            // Procurar indicadores de resultado
            const resultElements = document.querySelectorAll('table, .resultado, .dados-empresa, .info-empresa');
            const statusElements = document.querySelectorAll('*');
            
            // Procurar por texto de status
            let statusFound = null;
            for (let elem of statusElements) {
                const text = elem.textContent || '';
                if (text.match(/(ATIVO|SUSPENSO|BAIXADO|CANCELADO|IRREGULAR)/i)) {
                    statusFound = text.match(/(ATIVO|SUSPENSO|BAIXADO|CANCELADO|IRREGULAR)/i)[0];
                    break;
                }
            }
            
            // Verificar erros
            const errorElements = document.querySelectorAll('.error, .erro, .alert-danger, .msg-erro');
            for (let errorElem of errorElements) {
                if (errorElem.textContent.toLowerCase().includes('não encontrado') ||
                    errorElem.textContent.toLowerCase().includes('erro')) {
                    clearInterval(interval);
                    reject(new Error(`Erro na consulta: ${errorElem.textContent}`));
                    return;
                }
            }
            
            // Se encontrou resultados ou status
            if (resultElements.length > 0 || statusFound) {
                clearInterval(interval);
                console.log(`✅ [${connectionId}] Resultados encontrados`);
                
                const resultado = extractResultData(connectionId);
                resolve(resultado);
                return;
            }
            
            if (attempts >= maxAttempts) {
                clearInterval(interval);
                reject(new Error('Timeout aguardando resultados da consulta (60s)'));
            }
        }, 500);
    });
}

// Extrair dados dos resultados
function extractResultData(connectionId) {
    console.log(`📊 [${connectionId}] Extraindo dados dos resultados...`);
    
    const resultado = {
        timestamp: new Date().toISOString(),
        url: window.location.href,
        dados_extraidos: {},
        status_empresa: null,
        tabelas: []
    };
    
    // Extrair de tabelas
    const tabelas = document.querySelectorAll('table');
    tabelas.forEach((tabela, index) => {
        const dadosTabela = {};
        const linhas = tabela.querySelectorAll('tr');
        
        linhas.forEach(linha => {
            const colunas = linha.querySelectorAll('td, th');
            if (colunas.length >= 2) {
                const chave = colunas[0].textContent.trim();
                const valor = colunas[1].textContent.trim();
                if (chave && valor) {
                    dadosTabela[chave] = valor;
                }
            }
        });
        
        if (Object.keys(dadosTabela).length > 0) {
            resultado.tabelas.push(dadosTabela);
        }
    });
    
    // Extrair status da empresa
    const bodyText = document.body.textContent;
    const statusMatch = bodyText.match(/(ATIVO|SUSPENSO|BAIXADO|CANCELADO|IRREGULAR)/i);
    if (statusMatch) {
        resultado.status_empresa = statusMatch[1];
    }
    
    // Extrair outros dados relevantes
    const elementos = document.querySelectorAll('*');
    elementos.forEach(elem => {
        const text = elem.textContent || '';
        if (text.match(/\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}/)) { // CNPJ
            resultado.dados_extraidos.cnpj = text.match(/\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}/)[0];
        }
        if (text.match(/\d{9,}/)) { // IE
            resultado.dados_extraidos.inscricao_estadual = text.match(/\d{9,}/)[0];
        }
    });
    
    console.log(`📋 [${connectionId}] Dados extraídos:`, resultado);
    return resultado;
}

// Aguardar elemento aparecer
function waitForElement(selector, timeout = 10000) {
    return new Promise((resolve, reject) => {
        const element = document.querySelector(selector);
        if (element) {
            resolve(element);
            return;
        }
        
        const observer = new MutationObserver(() => {
            const element = document.querySelector(selector);
            if (element) {
                observer.disconnect();
                resolve(element);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        setTimeout(() => {
            observer.disconnect();
            reject(new Error(`Elemento ${selector} não encontrado em ${timeout}ms`));
        }, timeout);
    });
}

// Função auxiliar de sleep
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Listener para modo original (compatibilidade)
window.addEventListener('message', async (event) => {
    if (event.data.type === 'SEFAZ_AUTO_LOGIN') {
        console.log('✅ Modo original detectado:', event.data);
        
        const { cpf, senha, linkRecibo } = event.data;
        
        await sleep(1000);
        
        // Executar login original
        const campoUsuario = document.querySelector('input[name="identificacao"]');
        if (campoUsuario) {
            campoUsuario.value = cpf;
            campoUsuario.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        const campoSenha = document.querySelector('input[name="senha"]');
        if (campoSenha) {
            campoSenha.value = senha;
            campoSenha.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        await sleep(500);
        
        const botaoEntrar = document.querySelector('button[type="submit"]');
        if (botaoEntrar) {
            botaoEntrar.click();
            
            if (linkRecibo) {
                await aguardarLoginOriginal(linkRecibo);
            }
        }
    }
});

// Compatibilidade com modo original
async function aguardarLoginOriginal(linkRecibo) {
    let tentativas = 0;
    const maxTentativas = 40;
    
    const intervalo = setInterval(() => {
        tentativas++;
        
        const formularioLogin = document.querySelector('input[name="identificacao"]');
        const paginaPrincipal = document.querySelector('#principal, .menu-principal');
        
        if (!formularioLogin || paginaPrincipal) {
            clearInterval(intervalo);
            
            if (window.opener && linkRecibo) {
                try {
                    window.opener.postMessage({
                        type: 'SEFAZ_LOGIN_COMPLETO',
                        linkRecibo: linkRecibo
                    }, '*');
                } catch (error) {
                    console.error('❌ Erro ao enviar gatilho:', error);
                }
            }
        }
        
        if (tentativas >= maxTentativas) {
            clearInterval(intervalo);
        }
    }, 500);
}

console.log('✅ Content Script v1.2.0 pronto - Modo visual robusto + compatibilidade original');
