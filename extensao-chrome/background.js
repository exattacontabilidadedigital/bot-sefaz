// Background Script - Service Worker
console.log('🚀 SEFAZ Auto Login - Background script iniciado');
console.log('🆔 Extension ID:', chrome.runtime.id);
console.log('📋 Manifest:', chrome.runtime.getManifest());

// Verificar se externally_connectable está configurado
const manifest = chrome.runtime.getManifest();
if (manifest.externally_connectable) {
    console.log('🔗 Externally connectable configurado:', manifest.externally_connectable.matches);
} else {
    console.warn('⚠️ Externally connectable NÃO configurado!');
}

// Variáveis globais
let activeConsultaTab = null;
let consultaInProgress = false;

// Log quando a extensão é carregada
chrome.runtime.onStartup.addListener(() => {
    console.log('🔄 Extensão iniciada (startup)');
});

chrome.runtime.onInstalled.addListener((details) => {
    console.log('📦 Extensão instalada/atualizada:', details.reason);
    console.log('🆔 ID da extensão:', chrome.runtime.id);
});

// Listener para mensagens da extensão
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('📨 Mensagem interna recebida:', request);
    
    if (request.type === 'CHECK_EXTENSION') {
        sendResponse({ installed: true, version: '1.1.0', id: chrome.runtime.id });
        return true;
    }
    
    return true;
});

// Listener para mensagens externas (do frontend web)
chrome.runtime.onMessageExternal.addListener((request, sender, sendResponse) => {
    console.log('🌐 === MENSAGEM EXTERNA RECEBIDA ===');
    console.log('📍 Origem:', sender.origin);
    console.log('🔗 URL completa:', sender.url);
    console.log('📦 Dados:', JSON.stringify(request, null, 2));
    console.log('⏰ Timestamp:', new Date().toISOString());
    
    // Verificar origem permitida
    const allowedOrigins = [
        'http://localhost:8000',
        'https://localhost:8000', 
        'http://127.0.0.1:8000',
        'https://127.0.0.1:8000'
    ];
    
    if (!allowedOrigins.includes(sender.origin)) {
        console.warn('⚠️ Origem não permitida:', sender.origin);
        sendResponse({ success: false, error: 'Origem não permitida: ' + sender.origin });
        return false;
    }
    
    switch (request.action) {
        case 'ping':
            console.log('📍 === PING RECEBIDO ===');
            const response = { 
                pong: true, 
                status: 'active', 
                timestamp: Date.now(),
                extensionId: chrome.runtime.id,
                version: '1.1.0'
            };
            console.log('📤 Enviando resposta PING:', response);
            sendResponse(response);
            console.log('✅ Resposta PING enviada com sucesso');
            return false; // Resposta síncrona
            
        case 'executeConsulta':
            console.log('🎯 === EXECUTE CONSULTA RECEBIDO ===');
            console.log('📋 Dados da consulta:', request.data);
            handleExecuteConsulta(request.data)
                .then(result => {
                    console.log('✅ Consulta concluída com sucesso:', result);
                    sendResponse({ success: true, data: result });
                })
                .catch(error => {
                    console.error('❌ Erro na consulta:', error);
                    sendResponse({ success: false, error: error.message });
                });
            return true; // Resposta assíncrona
            
        default:
            console.warn('❓ Ação não reconhecida:', request.action);
            sendResponse({ success: false, error: 'Ação não reconhecida: ' + request.action });
            return false;
    }
});

// Executar consulta no modo visual
async function handleExecuteConsulta(dados) {
    if (consultaInProgress) {
        throw new Error('Já existe uma consulta em execução');
    }
    
    try {
        consultaInProgress = true;
        console.log('🔄 Iniciando consulta visual:', dados);
        
        // Criar nova aba para execução
        const tab = await chrome.tabs.create({
            url: 'https://sefaz.ma.gov.br/portal/cidadao/consultas/pj',
            active: true
        });
        
        activeConsultaTab = tab.id;
        console.log('📂 Nova aba criada:', tab.id);
        
        // Aguardar aba carregar
        await waitForTabToLoad(tab.id);
        console.log('✅ Aba carregada, executando automação...');
        
        // Executar script de automação
        const result = await executeAutomationScript(tab.id, dados);
        console.log('🎯 Automação concluída:', result);
        
        // Fechar aba após execução (opcional)
        // await chrome.tabs.remove(tab.id);
        
        return {
            result: result,
            tabId: tab.id,
            message: 'Consulta executada com sucesso no modo visual'
        };
        
    } catch (error) {
        console.error('❌ Erro na consulta visual:', error);
        
        // Fechar aba em caso de erro
        if (activeConsultaTab) {
            try {
                await chrome.tabs.remove(activeConsultaTab);
                console.log('🗑️ Aba fechada após erro');
            } catch (e) {
                console.warn('Não foi possível fechar aba:', e);
            }
        }
        
        throw error;
        
    } finally {
        consultaInProgress = false;
        activeConsultaTab = null;
        console.log('🔄 Consulta finalizada, status resetado');
    }
}

// Aguardar aba carregar
function waitForTabToLoad(tabId) {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('Timeout ao aguardar carregamento da aba'));
        }, 30000); // 30 segundos timeout
        
        const listener = (updatedTabId, changeInfo) => {
            if (updatedTabId === tabId && changeInfo.status === 'complete') {
                clearTimeout(timeout);
                chrome.tabs.onUpdated.removeListener(listener);
                resolve();
            }
        };
        
        chrome.tabs.onUpdated.addListener(listener);
        
        // Verificar se já está carregada
        chrome.tabs.get(tabId, (tab) => {
            if (tab.status === 'complete') {
                clearTimeout(timeout);
                chrome.tabs.onUpdated.removeListener(listener);
                resolve();
            }
        });
    });
}

// Executar script de automação na aba
async function executeAutomationScript(tabId, dados) {
    return new Promise((resolve, reject) => {
        console.log('📤 Enviando mensagem para content script:', dados);
        
        // Timeout para a operação
        const timeout = setTimeout(() => {
            reject(new Error('Timeout na execução da automação (60 segundos)'));
        }, 60000);
        
        chrome.tabs.sendMessage(tabId, {
            action: 'executarConsulta',
            dados: dados
        }, (response) => {
            clearTimeout(timeout);
            
            if (chrome.runtime.lastError) {
                console.error('❌ Erro no sendMessage:', chrome.runtime.lastError);
                reject(new Error(`Content script não respondeu: ${chrome.runtime.lastError.message}`));
            } else if (response) {
                if (response.success) {
                    console.log('✅ Content script respondeu com sucesso:', response);
                    resolve(response.data);
                } else {
                    console.error('❌ Content script retornou erro:', response.error);
                    reject(new Error(response.error || 'Erro na automação'));
                }
            } else {
                console.error('❌ Content script não retornou resposta');
                reject(new Error('Content script não retornou resposta. Verifique se a página SEFAZ foi carregada.'));
            }
        });
        });
    });
}

// Listener para quando abas são fechadas
chrome.tabs.onRemoved.addListener((tabId) => {
    if (tabId === activeConsultaTab) {
        activeConsultaTab = null;
        if (consultaInProgress) {
            console.log('⚠️ Aba da consulta foi fechada durante execução');
            consultaInProgress = false;
        }
    }
});

console.log('✅ Background script pronto com modo visual');
