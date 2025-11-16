// Background Script - Service Worker
console.log('🚀 SEFAZ Auto Login - Background script iniciado');

// Listener para mensagens da extensão
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('📨 Mensagem recebida:', request);
    
    if (request.type === 'CHECK_EXTENSION') {
        sendResponse({ installed: true, version: '1.0.0' });
    }
    
    return true;
});

console.log('✅ Background script pronto');
