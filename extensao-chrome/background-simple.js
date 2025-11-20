// Background Script - Portal SEFAZ Automator v2.0.0 - ID RENOVADO
console.log('🚀 Portal SEFAZ Automator v2.0.0 - Background iniciado');
console.log('🆔 NOVO ID (evita bloqueios):', chrome.runtime.id);
console.log('⏰ Timestamp:', new Date().toISOString());

// Estado simples
let extensionState = {
    isActive: true,
    connections: 0
};

// Listener para instalação
chrome.runtime.onInstalled.addListener(() => {
    console.log('📦 Extensão instalada com sucesso');
    extensionState.isActive = true;
});

// Listener para mensagens internas
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('📨 Mensagem interna:', request);
    
    if (request.type === 'CHECK_EXTENSION' || request.action === 'ping') {
        sendResponse({
            success: true,
            installed: true,
            version: '2.0.0',
            id: chrome.runtime.id,
            active: true
        });
    }
    
    return true;
});

// Listener para mensagens externas
chrome.runtime.onMessageExternal.addListener((request, sender, sendResponse) => {
    extensionState.connections++;
    const connId = extensionState.connections;
    
    console.log(`🌐 [${connId}] Mensagem externa de:`, sender.origin);
    console.log(`📦 [${connId}] Ação:`, request.action);
    
    // Validar origem
    const allowedOrigins = [
        'http://localhost:3000',
        'http://localhost:8000',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:8000'
    ];
    
    if (!allowedOrigins.includes(sender.origin)) {
        console.error(`❌ [${connId}] Origem não permitida:`, sender.origin);
        sendResponse({ success: false, error: 'Origem não permitida' });
        return false;
    }
    
    // Processar ação
    switch (request.action) {
        case 'ping':
            console.log(`📍 [${connId}] PING recebido`);
            sendResponse({
                success: true,
                data: {
                    pong: true,
                    status: 'active',
                    timestamp: Date.now(),
                    extensionId: chrome.runtime.id,
                    version: '2.0.0',
                    connections: extensionState.connections
                }
            });
            return false;
            
        case 'executeConsulta':
            console.log(`🎯 [${connId}] Executar consulta iniciado`);
            handleExecuteConsulta(request.data, connId)
                .then(result => {
                    console.log(`✅ [${connId}] Consulta concluída`);
                    sendResponse({ success: true, data: result });
                })
                .catch(error => {
                    console.error(`❌ [${connId}] Erro na consulta:`, error.message);
                    sendResponse({ success: false, error: error.message });
                });
            return true; // Async response
            
        default:
            console.warn(`❓ [${connId}] Ação desconhecida:`, request.action);
            sendResponse({ success: false, error: 'Ação não reconhecida' });
            return false;
    }
});

// Função para executar consulta
async function handleExecuteConsulta(dados, connId) {
    try {
        console.log(`🔄 [${connId}] Criando nova aba...`);
        
        const tab = await chrome.tabs.create({
            url: 'https://sefaz.ma.gov.br/portal/cidadao/consultas/pj',
            active: true
        });
        
        console.log(`📂 [${connId}] Aba criada:`, tab.id);
        
        // Aguardar aba carregar
        await waitTabLoad(tab.id);
        
        // Enviar dados para content script
        const result = await sendToContentScript(tab.id, dados, connId);
        
        return {
            result: result,
            tabId: tab.id,
            message: 'Consulta executada com sucesso'
        };
        
    } catch (error) {
        console.error(`❌ [${connId}] Erro:`, error);
        throw error;
    }
}

// Aguardar aba carregar
function waitTabLoad(tabId) {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('Timeout carregando aba'));
        }, 30000);
        
        const checkTab = () => {
            chrome.tabs.get(tabId, (tab) => {
                if (chrome.runtime.lastError) {
                    clearTimeout(timeout);
                    reject(new Error('Erro verificando aba'));
                    return;
                }
                
                if (tab.status === 'complete') {
                    clearTimeout(timeout);
                    setTimeout(resolve, 2000); // Aguardar mais 2s
                } else {
                    setTimeout(checkTab, 1000);
                }
            });
        };
        
        checkTab();
    });
}

// Enviar para content script
function sendToContentScript(tabId, dados, connId) {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('Timeout comunicando com content script'));
        }, 60000);
        
        chrome.tabs.sendMessage(tabId, {
            action: 'executarConsulta',
            dados: dados,
            connectionId: connId
        }, (response) => {
            clearTimeout(timeout);
            
            if (chrome.runtime.lastError) {
                reject(new Error('Content script não respondeu: ' + chrome.runtime.lastError.message));
                return;
            }
            
            if (response && response.success) {
                resolve(response.data);
            } else {
                reject(new Error(response?.error || 'Erro no content script'));
            }
        });
    });
}

console.log('✅ Background script carregado e pronto');