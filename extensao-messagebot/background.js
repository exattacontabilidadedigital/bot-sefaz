// Background Service Worker - SEFAZ MessageBot
console.log('SEFAZ MessageBot - Background carregado');

// Listener para mensagens externas (do frontend)
chrome.runtime.onMessageExternal.addListener((request, sender, sendResponse) => {
    console.log('Mensagem externa recebida:', request);
    
    if (request.action === 'processarMensagens') {
        console.log('Iniciando processamento de mensagens...');
        
        // Abrir nova aba do SEFAZ
        chrome.tabs.create({
            url: 'https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin',
            active: true
        }, (tab) => {
            console.log('Aba criada:', tab.id);
            
            // Aguardar tab carregar e enviar dados
            const tabId = tab.id;
            
            chrome.tabs.onUpdated.addListener(function listener(updatedTabId, info) {
                if (updatedTabId === tabId && info.status === 'complete') {
                    chrome.tabs.onUpdated.removeListener(listener);
                    
                    console.log('Página carregada, aguardando 2s antes de enviar dados...');
                    
                    // Aguardar um pouco para garantir que o content script está pronto
                    setTimeout(() => {
                        console.log('Enviando dados para content script...');
                        
                        // Enviar dados para content script
                        chrome.tabs.sendMessage(tabId, {
                            action: 'processarMensagensFluxo',
                            dados: request.dados
                        }, (response) => {
                            console.log('Resposta do content script:', response);
                            
                            if (response && response.success) {
                                sendResponse({
                                    success: true,
                                    data: response.data
                                });
                            } else {
                                sendResponse({
                                    success: false,
                                    error: response?.error || 'Erro desconhecido'
                                });
                            }
                        });
                    }, 2000);
                }
            });
        });
        
        return true; // Manter canal aberto para resposta assincrona
    }
    
    if (request.action === 'ping') {
        console.log('Ping recebido');
        sendResponse({ success: true, message: 'MessageBot ativo' });
        return true;
    }
    
    return false;
});

console.log('MessageBot background pronto');
