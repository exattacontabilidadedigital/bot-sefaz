// Content Script - Roda na pagina do SEFAZ-MA
console.log('SEFAZ Auto Login - Extensao carregada');
console.log('URL da pagina:', window.location.href);
console.log('Origin:', window.location.origin);

// Listener para mensagens da extensão (modo visual)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('📨 Mensagem da extensão recebida:', request);
    console.log('📤 Sender:', sender);
    
    if (request.action === 'executarConsulta') {
        console.log('🎯 Ação executarConsulta detectada, iniciando handleConsultaVisual...');
        
        // Executar de forma assíncrona
        handleConsultaVisual(request.dados)
            .then(result => {
                console.log('✅ handleConsultaVisual concluído com sucesso:', result);
                sendResponse({
                    success: true,
                    data: result
                });
            })
            .catch(error => {
                console.error('❌ handleConsultaVisual falhou:', error);
                sendResponse({
                    success: false,
                    error: error.message || 'Erro desconhecido no content script'
                });
            });
        
        return true; // Manter canal aberto para resposta assíncrona
    }
    
    console.log('❓ Ação não reconhecida:', request.action);
    return false;
});

// Executar consulta no modo visual
async function handleConsultaVisual(dados) {
    try {
        console.log('🎯 Iniciando consulta visual:', dados);
        
        // Verificar se estamos na página correta
        if (!window.location.href.includes('sefaz.ma.gov.br')) {
            throw new Error('Página SEFAZ não detectada. URL: ' + window.location.href);
        }
        
        // Aguardar página carregar completamente
        await waitForPageReady();
        console.log('✅ Página carregada, iniciando login...');
        
        // Executar login
        const loginResult = await executeLogin(dados);
        console.log('✅ Login executado:', loginResult);
        
        // Aguardar redirecionamento e navegar para consulta
        await waitForLoginRedirect();
        console.log('✅ Redirecionamento concluído, executando consulta...');
        
        // Executar consulta específica
        const consultaResult = await executeConsulta(dados);
        console.log('✅ Consulta executada:', consultaResult);
        
        return {
            login: loginResult,
            consulta: consultaResult,
            timestamp: new Date().toISOString(),
            url: window.location.href
        };
        
    } catch (error) {
        console.error('❌ Erro na consulta visual:', error);
        throw error;
    }
}

// Aguardar página estar pronta
function waitForPageReady() {
    return new Promise((resolve) => {
        if (document.readyState === 'complete') {
            setTimeout(resolve, 1000); // Aguardar mais um pouco
        } else {
            window.addEventListener('load', () => {
                setTimeout(resolve, 1000);
            });
        }
    });
}

// Executar login automático
async function executeLogin(dados) {
    console.log('🔐 Executando login...');
    
    // Preencher campo CPF
    const campoUsuario = document.querySelector('input[name="identificacao"]');
    if (campoUsuario) {
        campoUsuario.value = dados.cpf_socio;
        campoUsuario.dispatchEvent(new Event('input', { bubbles: true }));
        console.log('✅ CPF preenchido');
    } else {
        throw new Error('Campo de usuário não encontrado');
    }
    
    // Preencher campo Senha
    const campoSenha = document.querySelector('input[name="senha"]');
    if (campoSenha) {
        campoSenha.value = dados.senha;
        campoSenha.dispatchEvent(new Event('input', { bubbles: true }));
        console.log('✅ Senha preenchida');
    } else {
        throw new Error('Campo de senha não encontrado');
    }
    
    // Aguardar um pouco antes de clicar
    await sleep(500);
    
    // Clicar no botão Entrar
    const botaoEntrar = document.querySelector('button[type="submit"]');
    if (botaoEntrar) {
        console.log('✅ Clicando no botão Entrar...');
        botaoEntrar.click();
    } else {
        throw new Error('Botão Entrar não encontrado');
    }
    
    return { status: 'login_initiated' };
}

// Aguardar redirecionamento após login
async function waitForLoginRedirect() {
    console.log('⏳ Aguardando redirecionamento após login...');
    
    return new Promise((resolve, reject) => {
        let tentativas = 0;
        const maxTentativas = 40; // 20 segundos
        
        const interval = setInterval(() => {
            tentativas++;
            
            // Verificar se formulário de login sumiu
            const formularioLogin = document.querySelector('input[name="identificacao"]');
            const paginaPrincipal = document.querySelector('#principal, .menu-principal, #menu');
            
            if (!formularioLogin || paginaPrincipal) {
                clearInterval(interval);
                console.log('✅ Login completado, redirecionamento detectado');
                setTimeout(resolve, 1000); // Aguardar mais um pouco
                return;
            }
            
            if (tentativas >= maxTentativas) {
                clearInterval(interval);
                reject(new Error('Timeout aguardando redirecionamento do login'));
            }
        }, 500);
    });
}

// Executar consulta específica
async function executeConsulta(dados) {
    console.log('📋 Executando consulta específica...');
    
    // Navegar para página de consultas PJ se necessário
    if (!window.location.href.includes('consultas/pj')) {
        console.log('🧭 Navegando para consultas PJ...');
        window.location.href = 'https://sefaz.ma.gov.br/portal/cidadao/consultas/pj';
        await waitForPageReady();
    }
    
    // Aguardar formulário de consulta carregar
    await waitForConsultaForm();
    
    // Preencher dados da consulta
    await fillConsultaForm(dados);
    
    // Submeter consulta
    await submitConsulta();
    
    // Aguardar e capturar resultados
    const resultado = await waitForConsultaResults();
    
    return resultado;
}

// Aguardar formulário de consulta aparecer
function waitForConsultaForm() {
    return new Promise((resolve, reject) => {
        let tentativas = 0;
        const maxTentativas = 20;
        
        const interval = setInterval(() => {
            tentativas++;
            
            const form = document.querySelector('form') || 
                         document.querySelector('#consultaForm') ||
                         document.querySelector('input[type="text"]');
            
            if (form) {
                clearInterval(interval);
                console.log('✅ Formulário de consulta encontrado');
                resolve();
                return;
            }
            
            if (tentativas >= maxTentativas) {
                clearInterval(interval);
                reject(new Error('Formulário de consulta não encontrado'));
            }
        }, 500);
    });
}

// Preencher formulário de consulta
async function fillConsultaForm(dados) {
    console.log('✏️ Preenchendo formulário de consulta...');
    
    // Procurar e preencher campo CPF
    const campoCpf = document.querySelector('input[name*="cpf"], input[id*="cpf"], input[placeholder*="CPF"]') ||
                     document.querySelector('input[type="text"]:first-of-type');
    
    if (campoCpf) {
        campoCpf.value = dados.cpf_socio;
        campoCpf.dispatchEvent(new Event('input', { bubbles: true }));
        campoCpf.dispatchEvent(new Event('change', { bubbles: true }));
        console.log('✅ CPF preenchido no formulário de consulta');
    }
    
    // Preencher IE se fornecida
    if (dados.inscricao_estadual) {
        const campoIe = document.querySelector('input[name*="ie"], input[id*="inscricao"], input[placeholder*="IE"]');
        if (campoIe) {
            campoIe.value = dados.inscricao_estadual;
            campoIe.dispatchEvent(new Event('input', { bubbles: true }));
            campoIe.dispatchEvent(new Event('change', { bubbles: true }));
            console.log('✅ IE preenchida no formulário de consulta');
        }
    }
    
    await sleep(500); // Aguardar processamento
}

// Submeter consulta
async function submitConsulta() {
    console.log('🚀 Submetendo consulta...');
    
    const botaoSubmit = document.querySelector('button[type="submit"], input[type="submit"], button:contains("Consultar")') ||
                       document.querySelector('button, input[type="button"]');
    
    if (botaoSubmit) {
        botaoSubmit.click();
        console.log('✅ Consulta submetida');
    } else {
        throw new Error('Botão de submit não encontrado');
    }
}

// Aguardar e capturar resultados
async function waitForConsultaResults() {
    console.log('⏳ Aguardando resultados da consulta...');
    
    return new Promise((resolve, reject) => {
        let tentativas = 0;
        const maxTentativas = 60; // 30 segundos
        
        const interval = setInterval(() => {
            tentativas++;
            
            // Procurar por elementos que indicam resultado
            const resultados = document.querySelector('.resultado, .resultados, table, .dados-empresa') ||
                             document.querySelector('*:contains("ATIVO"), *:contains("SUSPENSO"), *:contains("BAIXADO")');
            
            // Verificar por mensagens de erro
            const erro = document.querySelector('.erro, .error, .alert-danger') ||
                        document.querySelector('*:contains("erro"), *:contains("não encontrado")');
            
            if (resultados) {
                clearInterval(interval);
                console.log('✅ Resultados encontrados');
                
                // Extrair dados dos resultados
                const dadosExtraidos = extractResultData();
                resolve(dadosExtraidos);
                return;
            }
            
            if (erro) {
                clearInterval(interval);
                const mensagemErro = erro.textContent || 'Erro na consulta';
                reject(new Error(`Erro na consulta: ${mensagemErro}`));
                return;
            }
            
            if (tentativas >= maxTentativas) {
                clearInterval(interval);
                reject(new Error('Timeout aguardando resultados da consulta'));
            }
        }, 500);
    });
}

// Extrair dados dos resultados
function extractResultData() {
    console.log('📊 Extraindo dados dos resultados...');
    
    const resultado = {
        timestamp: new Date().toISOString(),
        url: window.location.href,
        dados_extraidos: {}
    };
    
    // Tentar extrair dados de tabelas
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
            resultado.dados_extraidos[`tabela_${index + 1}`] = dadosTabela;
        }
    });
    
    // Tentar extrair texto relevante
    const textoRelevante = document.body.textContent.match(/(ATIVO|SUSPENSO|BAIXADO|CANCELADO)/gi);
    if (textoRelevante) {
        resultado.status_encontrado = textoRelevante[0];
    }
    
    console.log('📋 Dados extraídos:', resultado);
    return resultado;
}

// Escuta mensagens do sistema web (modo original mantido para compatibilidade)
window.addEventListener('message', async (event) => {
    console.log('📨 Mensagem recebida (modo original):', event);
    
    if (event.data.type === 'SEFAZ_AUTO_LOGIN') {
        console.log('✅ Modo original de login detectado');
        
        const { cpf, senha, linkRecibo } = event.data;
        
        await sleep(1000);
        
        // Executar login original
        const campoUsuario = document.querySelector('input[name="identificacao"]');
        if (campoUsuario) {
            campoUsuario.value = cpf;
            campoUsuario.dispatchEvent(new Event('input', { bubbles: true }));
            console.log('✅ CPF preenchido (modo original)');
        }
        
        const campoSenha = document.querySelector('input[name="senha"]');
        if (campoSenha) {
            campoSenha.value = senha;
            campoSenha.dispatchEvent(new Event('input', { bubbles: true }));
            console.log('✅ Senha preenchida (modo original)');
        }
        
        await sleep(500);
        
        const botaoEntrar = document.querySelector('button[type="submit"]');
        if (botaoEntrar) {
            botaoEntrar.click();
            console.log('✅ Login iniciado (modo original)');
            
            if (linkRecibo) {
                await aguardarLoginEAbrirRecibo(linkRecibo);
            }
        }
    }
});

// Função original mantida para compatibilidade
async function aguardarLoginEAbrirRecibo(linkRecibo) {
    console.log('🔍 Aguardando login (modo original)...');
    
    let tentativas = 0;
    const maxTentativas = 40;
    
    const intervalo = setInterval(() => {
        tentativas++;
        
        const formularioLogin = document.querySelector('input[name="identificacao"]');
        const paginaPrincipal = document.querySelector('#principal, .menu-principal, #menu');
        
        if (!formularioLogin || paginaPrincipal) {
            clearInterval(intervalo);
            console.log('🎉 Login completado (modo original)');
            
            if (window.opener && linkRecibo) {
                try {
                    window.opener.postMessage({
                        type: 'SEFAZ_LOGIN_COMPLETO',
                        linkRecibo: linkRecibo
                    }, '*');
                    console.log('✅ Gatilho enviado (modo original)');
                } catch (error) {
                    console.error('❌ Erro ao enviar gatilho:', error);
                }
            }
        }
        
        if (tentativas >= maxTentativas) {
            clearInterval(intervalo);
            console.error('❌ Timeout login (modo original)');
        }
    }, 500);
}

// Função auxiliar
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

console.log('✅ Extensão SEFAZ pronta (modo visual + original)');
