// Content Script - Roda na pagina do SEFAZ-MA
console.log('SEFAZ Auto Login - Extensao carregada');
console.log('URL da pagina:', window.location.href);
console.log('Origin:', window.location.origin);

// Funcao auxiliar
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Listener para mensagens do frontend (postMessage) - MODO ORIGINAL
window.addEventListener('message', async (event) => {
    console.log('Mensagem recebida (postMessage):', event.data);
    
    // Auto Login SEFAZ (modo original mantido para compatibilidade)
    if (event.data.type === 'SEFAZ_AUTO_LOGIN') {
        console.log('Auto login solicitado (modo original)');
        
        const { cpf, senha, linkRecibo } = event.data;
        
        await sleep(1000);
        
        // Executar login original
        const campoUsuario = document.querySelector('input[name="identificacao"]');
        if (campoUsuario) {
            campoUsuario.value = cpf;
            campoUsuario.dispatchEvent(new Event('input', { bubbles: true }));
            console.log('CPF preenchido (modo original)');
        }
        
        const campoSenha = document.querySelector('input[name="senha"]');
        if (campoSenha) {
            campoSenha.value = senha;
            campoSenha.dispatchEvent(new Event('input', { bubbles: true }));
            console.log('Senha preenchida (modo original)');
        }
        
        await sleep(500);
        
        const botaoEntrar = document.querySelector('button[type="submit"]');
        if (botaoEntrar) {
            botaoEntrar.click();
            console.log('Login iniciado (modo original)');
            
            if (linkRecibo) {
                await aguardarLoginEAbrirRecibo(linkRecibo);
            }
        }
    }
});

// Funcao original mantida para compatibilidade
async function aguardarLoginEAbrirRecibo(linkRecibo) {
    console.log('Aguardando login (modo original)...');
    
    let tentativas = 0;
    const maxTentativas = 40;
    
    const intervalo = setInterval(() => {
        tentativas++;
        
        const formularioLogin = document.querySelector('input[name="identificacao"]');
        const paginaPrincipal = document.querySelector('#principal, .menu-principal, #menu');
        
        if (!formularioLogin || paginaPrincipal) {
            clearInterval(intervalo);
            console.log('Login completado (modo original)');
            
            if (window.opener && linkRecibo) {
                try {
                    window.opener.postMessage({
                        type: 'SEFAZ_LOGIN_COMPLETO',
                        linkRecibo: linkRecibo
                    }, '*');
                    console.log('Gatilho enviado (modo original)');
                } catch (error) {
                    console.error('Erro ao enviar gatilho:', error);
                }
            }
        }
        
        if (tentativas >= maxTentativas) {
            clearInterval(intervalo);
            console.error('Timeout login (modo original)');
        }
    }, 500);
}

// Listener para mensagens da extensao (modo visual)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Mensagem da extensao recebida:', request);
    
    if (request.action === 'executarConsulta') {
        console.log('Acao executarConsulta detectada, iniciando...');
        
        // Executar de forma assincrona
        handleConsultaVisual(request.dados)
            .then(result => {
                console.log('Consulta concluida com sucesso:', result);
                sendResponse({
                    success: true,
                    data: result
                });
            })
            .catch(error => {
                console.error('Consulta falhou:', error);
                sendResponse({
                    success: false,
                    error: error.message || 'Erro desconhecido'
                });
            });
        
        return true; // Indicar resposta assincrona
    }
    
    return false;
});

// Funcao principal para executar consulta visual
async function handleConsultaVisual(dados) {
    console.log('Iniciando consulta visual com dados:', dados);
    
    try {
        // Aguardar pagina carregar completamente
        await waitForPageLoad();
        
        // Fazer login se necessario
        if (isLoginPage()) {
            console.log('Pagina de login detectada');
            await doLogin(dados);
            await waitForPageLoad();
        }
        
        // Navegar para consulta
        console.log('Navegando para consulta...');
        await navigateToConsulta();
        await waitForPageLoad();
        
        // Preencher formulario
        console.log('Preenchendo formulario...');
        await fillConsultaForm(dados);
        
        // Submeter e aguardar resultados
        console.log('Submetendo consulta...');
        await submitConsulta();
        await waitForResults();
        
        // Extrair resultados
        console.log('Extraindo resultados...');
        const resultados = await extractResults();
        
        console.log('Consulta concluida:', resultados);
        return resultados;
        
    } catch (error) {
        console.error('Erro na consulta visual:', error);
        throw error;
    }
}

// Aguardar pagina carregar
function waitForPageLoad() {
    return new Promise((resolve) => {
        if (document.readyState === 'complete') {
            setTimeout(resolve, 1000);
        } else {
            window.addEventListener('load', () => {
                setTimeout(resolve, 1000);
            });
        }
    });
}

// Verificar se e pagina de login
function isLoginPage() {
    return window.location.href.includes('login.do') || 
           document.querySelector('#matricula') !== null;
}

// Fazer login
async function doLogin(dados) {
    console.log('Executando login...');
    
    // Aguardar campo de matricula
    const matriculaField = await waitForElement('#matricula');
    matriculaField.value = dados.cpf_socio || '';
    
    // Aguardar campo de senha
    const senhaField = await waitForElement('#senha');
    senhaField.value = dados.senha || '';
    
    // Clicar no botao de login
    const loginBtn = await waitForElement('input[type="submit"], button[type="submit"]');
    loginBtn.click();
    
    console.log('Login submetido');
}

// Navegar para consulta
async function navigateToConsulta() {
    // Tentar encontrar link de consulta
    const links = document.querySelectorAll('a');
    for (let link of links) {
        if (link.textContent.toLowerCase().includes('conta corrente') ||
            link.href.includes('consultaContaCorrente')) {
            link.click();
            return;
        }
    }
    
    // Se nao encontrou, tentar URL direta
    window.location.href = 'https://sefaznet.sefaz.ma.gov.br/sefaznet/consultaContaCorrente.do';
}

// Preencher formulario de consulta
async function fillConsultaForm(dados) {
    // Aguardar campo de inscricao estadual
    const ieField = await waitForElement('input[name*="inscricao"], #inscricaoEstadual');
    ieField.value = dados.inscricao_estadual || '';
    
    // Trigger change event
    ieField.dispatchEvent(new Event('change', { bubbles: true }));
}

// Submeter consulta
async function submitConsulta() {
    const submitBtn = await waitForElement('input[value*="Consultar"], button[type="submit"]');
    submitBtn.click();
}

// Aguardar resultados
function waitForResults() {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('Timeout aguardando resultados'));
        }, 30000);
        
        const checkResults = () => {
            if (document.querySelector('table') || 
                document.querySelector('.resultado') ||
                document.querySelector('#resultado')) {
                clearTimeout(timeout);
                resolve();
            } else {
                setTimeout(checkResults, 500);
            }
        };
        
        checkResults();
    });
}

// Extrair resultados
async function extractResults() {
    const tables = document.querySelectorAll('table');
    const results = [];
    
    for (let table of tables) {
        const data = extractTableData(table);
        if (data.length > 0) {
            results.push(data);
        }
    }
    
    return {
        tabelas: results,
        url: window.location.href,
        timestamp: new Date().toISOString()
    };
}

// Extrair dados da tabela
function extractTableData(table) {
    const rows = table.querySelectorAll('tr');
    const data = [];
    
    for (let row of rows) {
        const cells = row.querySelectorAll('td, th');
        if (cells.length > 0) {
            const rowData = Array.from(cells).map(cell => cell.textContent.trim());
            data.push(rowData);
        }
    }
    
    return data;
}

// Aguardar elemento aparecer
function waitForElement(selector) {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error(`Timeout aguardando elemento: ${selector}`));
        }, 10000);
        
        const checkElement = () => {
            const element = document.querySelector(selector);
            if (element) {
                clearTimeout(timeout);
                resolve(element);
            } else {
                setTimeout(checkElement, 100);
            }
        };
        
        checkElement();
    });
}

console.log('Content script carregado com sucesso');