// Background Script - Service Worker Enhanced v1.2.0
console.log('🚀 SEFAZ Auto Login v1.2.0 - Service Worker iniciado');
console.log('⏰ Timestamp:', new Date().toISOString());
console.log('🆔 Extension ID:', chrome.runtime.id);

// Estado global persistente
let state = {
    activeConsultaTab: null,
    consultaInProgress: false,
    lastPing: null,
    connectionCount: 0,
    serviceWorkerActive: true,
    startTime: Date.now()
};

// Heartbeat para manter service worker ativo
const HEARTBEAT_INTERVAL = 25000; // 25 segundos
let heartbeatTimer = null;

function startHeartbeat() {
    if (heartbeatTimer) clearInterval(heartbeatTimer);
    
    heartbeatTimer = setInterval(() => {
        state.serviceWorkerActive = true;
        console.log('💓 Service Worker heartbeat:', new Date().toISOString());
        
        // Limpar dados antigos se necessário
        if (Date.now() - state.startTime > 3600000) { // 1 hora
            console.log('🧹 Limpando estado antigo...');
            state.connectionCount = 0;
            state.startTime = Date.now();
        }
    }, HEARTBEAT_INTERVAL);
}

// Inicialização robusta
function initializeExtension() {
    const manifest = chrome.runtime.getManifest();
    console.log('📋 Manifest v' + manifest.version);
    
    if (manifest.externally_connectable) {
        console.log('🔗 Externally connectable:', manifest.externally_connectable.matches.length + ' patterns');
    } else {
        console.error('❌ CRÍTICO: Externally connectable NÃO configurado!');
    }
    
    startHeartbeat();
    console.log('✅ Extensão inicializada com sucesso');
}

// Event listeners otimizados
chrome.runtime.onStartup.addListener(() => {
    console.log('🔄 Chrome startup detectado');
    initializeExtension();
});

chrome.runtime.onInstalled.addListener((details) => {
    console.log('📦 Extensão ' + details.reason + ':', details);
    initializeExtension();
});

// Inicialização imediata
initializeExtension();

// Listener para mensagens internas robustas
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('📨 Mensagem interna:', request.type || request.action || 'unknown');
    
    try {
        const response = handleInternalMessage(request, sender);
        if (response) {
            sendResponse(response);
        }
    } catch (error) {
        console.error('❌ Erro em mensagem interna:', error);
        sendResponse({ success: false, error: error.message });
    }
    
    return true;
});

function handleInternalMessage(request, sender) {
    switch (request.type || request.action) {
        case 'CHECK_EXTENSION':
        case 'ping':
            state.lastPing = Date.now();
            return {
                success: true,
                installed: true,
                version: '1.2.0',
                id: chrome.runtime.id,
                active: state.serviceWorkerActive,
                uptime: Date.now() - state.startTime,
                connections: state.connectionCount
            };
            
        case 'GET_STATE':
            return { success: true, state: { ...state } };
            
        case 'RESET_STATE':
            state.consultaInProgress = false;
            state.activeConsultaTab = null;
            return { success: true, message: 'Estado resetado' };
            
        default:
            console.warn('❓ Tipo de mensagem interna desconhecida:', request.type);
            return { success: false, error: 'Tipo não reconhecido' };
    }
}

// Listener para mensagens externas com validação robusta
chrome.runtime.onMessageExternal.addListener((request, sender, sendResponse) => {
    const timestamp = new Date().toISOString();
    const connectionId = ++state.connectionCount;
    
    console.log(`🌐 [${connectionId}] MENSAGEM EXTERNA [${timestamp}]`);
    console.log(`📍 [${connectionId}] Origem:`, sender.origin);
    console.log(`📦 [${connectionId}] Ação:`, request.action);
    
    // Validação de origem robusta
    if (!isOriginAllowed(sender.origin)) {
        const error = 'Origem não permitida: ' + sender.origin;
        console.error(`❌ [${connectionId}] ${error}`);
        sendResponse({ success: false, error, timestamp, connectionId });
        return false;
    }
    
    // Processamento da mensagem com timeout
    const timeoutMs = 30000; // 30 segundos
    const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error(`Timeout de ${timeoutMs}ms atingido`)), timeoutMs);
    });
    
    try {
        const result = handleExternalMessage(request, sender, connectionId);
        
        if (result && typeof result.then === 'function') {
            // Resposta assíncrona com timeout
            Promise.race([result, timeoutPromise])
                .then(data => {
                    console.log(`✅ [${connectionId}] Sucesso:`, data);
                    sendResponse({ success: true, data, timestamp, connectionId });
                })
                .catch(error => {
                    console.error(`❌ [${connectionId}] Erro:`, error.message);
                    sendResponse({ success: false, error: error.message, timestamp, connectionId });
                });
            return true;
        } else {
            // Resposta síncrona
            console.log(`✅ [${connectionId}] Resposta síncrona:`, result);
            sendResponse({ success: true, data: result, timestamp, connectionId });
            return false;
        }
    } catch (error) {
        console.error(`❌ [${connectionId}] Erro no processamento:`, error);
        sendResponse({ success: false, error: error.message, timestamp, connectionId });
        return false;
    }
});

// Validação de origem
function isOriginAllowed(origin) {
    if (!origin) return false;
    
    const allowedPatterns = [
        /^http:\/\/localhost:\d+$/,
        /^https:\/\/localhost:\d+$/,
        /^http:\/\/127\.0\.0\.1:\d+$/,
        /^https:\/\/127\.0\.0\.1:\d+$/,
        /^http:\/\/192\.168\.\d+\.\d+:\d+$/,
        /^http:\/\/10\.\d+\.\d+\.\d+:\d+$/,
        /^file:\/\/\//
    ];
    
    return allowedPatterns.some(pattern => pattern.test(origin));
}

// Processamento de mensagens externas
function handleExternalMessage(request, sender, connectionId) {
    state.lastPing = Date.now();
    
    switch (request.action) {
        case 'ping':
            console.log(`📍 [${connectionId}] PING processado`);
            return {
                pong: true,
                status: 'active',
                timestamp: Date.now(),
                extensionId: chrome.runtime.id,
                version: '1.2.0',
                uptime: Date.now() - state.startTime,
                serviceWorker: state.serviceWorkerActive,
                connections: state.connectionCount
            };
            
        case 'executeConsulta':
            console.log(`🎯 [${connectionId}] EXECUTE CONSULTA iniciado`);
            return handleExecuteConsulta(request.data, connectionId);
            
        case 'getStatus':
            return {
                extension: {
                    id: chrome.runtime.id,
                    version: '1.2.0',
                    active: true
                },
                state: { ...state },
                performance: {
                    uptime: Date.now() - state.startTime,
                    lastPing: state.lastPing,
                    connections: state.connectionCount
                }
            };
            
        default:
            throw new Error('Ação não reconhecida: ' + request.action);
    }
}

// Executar consulta robusta
async function handleExecuteConsulta(dados, connectionId) {
    if (state.consultaInProgress) {
        throw new Error('Já existe uma consulta em execução');
    }
    
    try {
        state.consultaInProgress = true;
        console.log(`🔄 [${connectionId}] Iniciando consulta visual:`, dados);
        
        // Criar nova aba com configurações robustas
        const tab = await chrome.tabs.create({
            url: 'https://sefaz.ma.gov.br/portal/cidadao/consultas/pj',
            active: true,
            pinned: false
        });
        
        state.activeConsultaTab = tab.id;
        console.log(`📂 [${connectionId}] Nova aba criada:`, tab.id);
        
        // Aguardar aba carregar com timeout
        await waitForTabToLoad(tab.id);
        console.log(`✅ [${connectionId}] Aba carregada, executando automação...`);
        
        // Injetar e executar script
        const result = await executeAutomationScript(tab.id, dados, connectionId);
        console.log(`🎯 [${connectionId}] Automação concluída:`, result);
        
        // Opcional: manter aba aberta para visualização
        // await chrome.tabs.remove(tab.id);
        
        return {
            result: result,
            tabId: tab.id,
            message: 'Consulta executada com sucesso no modo visual',
            connectionId
        };
        
    } catch (error) {
        console.error(`❌ [${connectionId}] Erro na consulta visual:`, error);
        
        // Fechar aba em caso de erro
        if (state.activeConsultaTab) {
            try {
                await chrome.tabs.remove(state.activeConsultaTab);
                console.log(`🗑️ [${connectionId}] Aba fechada após erro`);
            } catch (e) {
                console.warn('Não foi possível fechar aba:', e);
            }
        }
        
        throw error;
        
    } finally {
        state.consultaInProgress = false;
        state.activeConsultaTab = null;
        console.log(`🔄 [${connectionId}] Consulta finalizada, status resetado`);
    }
}

// Aguardar aba carregar com timeout robusto
function waitForTabToLoad(tabId) {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('Timeout ao aguardar carregamento da aba (45s)'));
        }, 45000);
        
        const listener = (updatedTabId, changeInfo) => {
            if (updatedTabId === tabId) {
                if (changeInfo.status === 'complete') {
                    clearTimeout(timeout);
                    chrome.tabs.onUpdated.removeListener(listener);
                    // Aguardar mais um pouco para garantir
                    setTimeout(resolve, 2000);
                } else if (changeInfo.status === 'loading') {
                    console.log('📂 Aba carregando...');
                }
            }
        };
        
        chrome.tabs.onUpdated.addListener(listener);
        
        // Verificar se já está carregada
        chrome.tabs.get(tabId, (tab) => {
            if (chrome.runtime.lastError) {
                clearTimeout(timeout);
                chrome.tabs.onUpdated.removeListener(listener);
                reject(new Error('Erro ao verificar status da aba'));
                return;
            }
            
            if (tab.status === 'complete') {
                clearTimeout(timeout);
                chrome.tabs.onUpdated.removeListener(listener);
                setTimeout(resolve, 2000);
            }
        });
    });
}

// Executar script com robustez
async function executeAutomationScript(tabId, dados, connectionId) {
    console.log(`📤 [${connectionId}] Enviando mensagem para content script:`, dados);
    
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('Timeout na execução da automação (90 segundos)'));
        }, 90000);
        
        chrome.tabs.sendMessage(tabId, {
            action: 'executarConsulta',
            dados: dados,
            connectionId: connectionId,
            timestamp: Date.now()
        }, (response) => {
            clearTimeout(timeout);
            
            if (chrome.runtime.lastError) {
                console.error(`❌ [${connectionId}] Erro no sendMessage:`, chrome.runtime.lastError);
                reject(new Error(`Content script erro: ${chrome.runtime.lastError.message}`));
            } else if (response) {
                if (response.success) {
                    console.log(`✅ [${connectionId}] Content script sucesso:`, response);
                    resolve(response.data);
                } else {
                    console.error(`❌ [${connectionId}] Content script erro:`, response.error);
                    reject(new Error(response.error || 'Erro na automação'));
                }
            } else {
                console.error(`❌ [${connectionId}] Content script sem resposta`);
                reject(new Error('Content script não respondeu. Verifique se a página SEFAZ carregou corretamente.'));
            }
        });
    });
}

// Listener para abas fechadas
chrome.tabs.onRemoved.addListener((tabId) => {
    if (tabId === state.activeConsultaTab) {
        state.activeConsultaTab = null;
        if (state.consultaInProgress) {
            console.log('⚠️ Aba da consulta foi fechada durante execução');
            state.consultaInProgress = false;
        }
    }
});

// Listener para mudanças de estado das abas
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (tabId === state.activeConsultaTab && changeInfo.status) {
        console.log(`📂 Aba consulta ${tabId} status:`, changeInfo.status);
    }
});

console.log('✅ Background script v1.2.0 pronto com comunicação robusta e modo visual otimizado');
