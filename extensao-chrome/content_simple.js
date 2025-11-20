// Content Script - Roda na pagina do SEFAZ-MA
console.log('SEFAZ Auto Login - Extensao carregada');
console.log('URL da pagina:', window.location.href);
console.log('Origin:', window.location.origin);

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