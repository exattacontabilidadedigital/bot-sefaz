// Content Script Simplificado - Cache Limpo 2025-11-20
console.log('🔐 SEFAZ Content Script carregado - CACHE LIMPO em:', window.location.href);
console.log('🧹 Nova versão carregada:', '1.2.1', new Date().toISOString());

// Listener para mensagens
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('📨 Mensagem recebida:', request.action);
    
    if (request.action === 'executarConsulta') {
        console.log('🎯 Executando consulta...');
        
        executeConsulta(request.dados, request.connectionId)
            .then(result => {
                console.log('✅ Consulta concluída');
                sendResponse({ success: true, data: result });
            })
            .catch(error => {
                console.error('❌ Erro na consulta:', error);
                sendResponse({ success: false, error: error.message });
            });
            
        return true; // Async response
    }
    
    return false;
});

// Função principal de consulta
async function executeConsulta(dados, connId) {
    try {
        console.log(`🔄 [${connId}] Iniciando automação...`);
        
        // Aguardar página carregar
        await sleep(2000);
        
        // Verificar se precisa login
        if (needsLogin()) {
            console.log(`🔐 [${connId}] Executando login...`);
            await doLogin(dados);
            await waitForRedirect();
        }
        
        // Ir para consultas se necessário
        if (!window.location.href.includes('consultas')) {
            console.log(`🧭 [${connId}] Navegando para consultas...`);
            window.location.href = 'https://sefaz.ma.gov.br/portal/cidadao/consultas/pj';
            await sleep(3000);
        }
        
        // Executar consulta
        console.log(`📋 [${connId}] Preenchendo formulário...`);
        await fillAndSubmit(dados);
        
        // Aguardar resultados
        console.log(`⏳ [${connId}] Aguardando resultados...`);
        const results = await waitForResults();
        
        return {
            success: true,
            data: results,
            timestamp: new Date().toISOString(),
            url: window.location.href
        };
        
    } catch (error) {
        throw new Error(`Automação falhou: ${error.message}`);
    }
}

// Verificar se precisa login
function needsLogin() {
    const loginField = document.querySelector('input[name="identificacao"]');
    const loggedIn = document.querySelector('#principal, .menu-principal');
    return !!loginField && !loggedIn;
}

// Executar login
async function doLogin(dados) {
    if (!dados.cpf_socio || !dados.senha) {
        throw new Error('Dados de login incompletos');
    }
    
    // Preencher CPF
    const cpfField = document.querySelector('input[name="identificacao"]');
    if (cpfField) {
        cpfField.value = dados.cpf_socio;
        cpfField.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    // Preencher senha
    const senhaField = document.querySelector('input[name="senha"]');
    if (senhaField) {
        senhaField.value = dados.senha;
        senhaField.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    await sleep(500);
    
    // Clicar entrar
    const submitBtn = document.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.click();
    } else {
        throw new Error('Botão de login não encontrado');
    }
}

// Aguardar redirecionamento
function waitForRedirect() {
    return new Promise((resolve, reject) => {
        let attempts = 0;
        const maxAttempts = 40;
        
        const check = () => {
            attempts++;
            const loginForm = document.querySelector('input[name="identificacao"]');
            const loggedIn = document.querySelector('#principal, .menu-principal') || 
                           window.location.href.includes('portal');
            
            if (!loginForm || loggedIn) {
                resolve();
            } else if (attempts >= maxAttempts) {
                reject(new Error('Timeout aguardando login'));
            } else {
                setTimeout(check, 500);
            }
        };
        
        setTimeout(check, 1000);
    });
}

// Preencher e submeter formulário
async function fillAndSubmit(dados) {
    // Aguardar formulário aparecer
    await sleep(2000);
    
    // Buscar campo CPF
    const cpfField = document.querySelector('input[name*="cpf"], input[type="text"]');
    if (cpfField && dados.cpf_socio) {
        cpfField.value = dados.cpf_socio;
        cpfField.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    // IE se disponível
    if (dados.inscricao_estadual) {
        const ieField = document.querySelector('input[name*="ie"], input[name*="inscricao"]');
        if (ieField) {
            ieField.value = dados.inscricao_estadual;
            ieField.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }
    
    await sleep(500);
    
    // Submeter
    const submitBtn = document.querySelector('button[type="submit"], input[type="submit"]');
    if (submitBtn) {
        submitBtn.click();
    } else {
        throw new Error('Botão de consulta não encontrado');
    }
}

// Aguardar resultados
function waitForResults() {
    return new Promise((resolve, reject) => {
        let attempts = 0;
        const maxAttempts = 60;
        
        const check = () => {
            attempts++;
            
            // Procurar resultados
            const tables = document.querySelectorAll('table');
            const status = document.body.textContent.match(/(ATIVO|SUSPENSO|BAIXADO|CANCELADO)/i);
            
            if (tables.length > 0 || status) {
                const result = {
                    timestamp: new Date().toISOString(),
                    url: window.location.href,
                    status: status ? status[1] : null,
                    tables: extractTables()
                };
                resolve(result);
            } else if (attempts >= maxAttempts) {
                reject(new Error('Timeout aguardando resultados'));
            } else {
                setTimeout(check, 1000);
            }
        };
        
        setTimeout(check, 2000);
    });
}

// Extrair dados de tabelas
function extractTables() {
    const tables = document.querySelectorAll('table');
    const data = [];
    
    tables.forEach((table, index) => {
        const rows = table.querySelectorAll('tr');
        const tableData = {};
        
        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length >= 2) {
                const key = cells[0].textContent.trim();
                const value = cells[1].textContent.trim();
                if (key && value) {
                    tableData[key] = value;
                }
            }
        });
        
        if (Object.keys(tableData).length > 0) {
            data.push(tableData);
        }
    });
    
    return data;
}

// Função auxiliar
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Compatibilidade com modo original
window.addEventListener('message', async (event) => {
    if (event.data.type === 'SEFAZ_AUTO_LOGIN') {
        console.log('✅ Modo original detectado');
        
        const { cpf, senha, linkRecibo } = event.data;
        
        await sleep(1000);
        
        const userField = document.querySelector('input[name="identificacao"]');
        if (userField) {
            userField.value = cpf;
            userField.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        const passField = document.querySelector('input[name="senha"]');
        if (passField) {
            passField.value = senha;
            passField.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        await sleep(500);
        
        const submitBtn = document.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.click();
        }
    }
});

console.log('✅ Content script simplificado pronto');