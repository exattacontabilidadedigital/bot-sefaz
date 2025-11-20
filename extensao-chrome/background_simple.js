// Background Script - Service Worker
console.log('SEFAZ Auto Login - Background script iniciado');

// Variaveis globais
let activeConsultaTab = null;
let consultaInProgress = false;

// Listener para mensagens da extensao
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Mensagem recebida:', request);
    
    if (request.type === 'CHECK_EXTENSION') {
        sendResponse({ installed: true, version: '1.1.0' });
        return true;
    }
    
    return true;
});

// Listener para mensagens externas (do frontend web)
chrome.runtime.onMessageExternal.addListener((request, sender, sendResponse) => {
    console.log('Mensagem externa recebida:', request);
    
    switch (request.action) {
        case 'ping':
            console.log('Ping recebido, respondendo...');
            sendResponse({ pong: true, status: 'active' });
            return false; // Resposta sincrona
            
        case 'executeConsulta':
            console.log('Executando consulta:', request.data);
            handleExecuteConsulta(request.data, sendResponse);
            return true; // Resposta assincrona
            
        default:
            console.log('Acao nao reconhecida:', request.action);
            sendResponse({ error: 'Acao nao reconhecida' });
            return false;
    }
});

// Funcao para executar consulta
async function handleExecuteConsulta(data, sendResponse) {
    try {
        console.log('Dados da consulta:', data);
        
        // Criar nova aba para consulta
        const tab = await chrome.tabs.create({
            url: 'https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin',
            active: data.modo_visual === true
        });
        
        activeConsultaTab = tab.id;
        consultaInProgress = true;
        
        // Aguardar pagina carregar
        await waitTabLoad(tab.id);
        
        // Enviar dados para content script
        const result = await sendToContentScript(tab.id, {
            action: 'executarConsulta',
            dados: data
        });
        
        sendResponse({
            success: true,
            data: result,
            tabId: tab.id
        });
        
    } catch (error) {
        console.error('Erro na consulta:', error);
        sendResponse({
            success: false,
            error: error.message
        });
    } finally {
        consultaInProgress = false;
    }
}

// Aguardar aba carregar
function waitTabLoad(tabId) {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('Timeout aguardando carregamento da aba'));
        }, 30000);
        
        chrome.tabs.onUpdated.addListener(function listener(updatedTabId, info) {
            if (updatedTabId === tabId && info.status === 'complete') {
                chrome.tabs.onUpdated.removeListener(listener);
                clearTimeout(timeout);
                setTimeout(resolve, 2000); // Aguardar JS carregar
            }
        });
    });
}

// Enviar mensagem para content script
function sendToContentScript(tabId, message) {
    return new Promise((resolve, reject) => {
        chrome.tabs.sendMessage(tabId, message, (response) => {
            if (chrome.runtime.lastError) {
                reject(new Error(chrome.runtime.lastError.message));
            } else {
                resolve(response);
            }
        });
    });
}

console.log('Background script carregado com sucesso');