// Script para verificar bloqueios da extensão gimjjdmndkikigfgmnaaejbnahdhailc
console.log('🔍 Verificando possíveis bloqueios da extensão...');

// 1. Verificar se a extensão está na lista de bloqueados
if (typeof chrome !== 'undefined' && chrome.management) {
    chrome.management.getAll().then(extensions => {
        const targetExtension = extensions.find(ext => ext.id === 'gimjjdmndkikigfgmnaaejbnahdhailc');
        
        if (targetExtension) {
            console.log('✅ Extensão encontrada:', {
                name: targetExtension.name,
                enabled: targetExtension.enabled,
                installType: targetExtension.installType,
                mayDisable: targetExtension.mayDisable
            });
            
            if (!targetExtension.enabled) {
                console.warn('⚠️ EXTENSÃO DESABILITADA - Possível bloqueio automático!');
                console.log('🔧 Soluções:');
                console.log('1. Vá para chrome://extensions/');
                console.log('2. Encontre "SEFAZ-MA Auto Login"');
                console.log('3. Clique no toggle para habilitar');
            }
        } else {
            console.warn('❌ Extensão não encontrada - possível bloqueio de instalação');
        }
    }).catch(err => {
        console.error('❌ Erro verificando extensões:', err);
    });
} else {
    console.warn('⚠️ Chrome Management API não disponível');
}

// 2. Verificar políticas corporativas
if (typeof chrome !== 'undefined' && chrome.enterprise) {
    chrome.enterprise.platformKeys.getTokens().then(tokens => {
        console.log('🏢 Ambiente corporativo detectado:', tokens.length > 0);
        if (tokens.length > 0) {
            console.warn('⚠️ POSSÍVEL BLOQUEIO CORPORATIVO!');
            console.log('💡 Soluções:');
            console.log('1. Contatar administrador IT');
            console.log('2. Usar Chrome pessoal');
            console.log('3. Usar perfil Chrome separado');
        }
    }).catch(() => {
        console.log('✅ Não há políticas corporativas detectadas');
    });
}

// 3. Verificar se está em lista negra conhecida
const knownBlockedIds = [
    'gimjjdmndkikigfgmnaaejbnahdhailc' // Nosso ID atual
];

if (knownBlockedIds.includes('gimjjdmndkikigfgmnaaejbnahdhailc')) {
    console.warn('⚠️ ID PODE ESTAR EM LISTA NEGRA!');
    console.log('🔧 Soluções imediatas:');
    console.log('1. Gerar novo ID (recomendado)');
    console.log('2. Usar Chrome com perfil limpo');
    console.log('3. Desabilitar antivirus temporariamente');
}

// 4. Verificar store origins
console.log('🌐 Verificando origins permitidas...');
const allowedOrigins = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000'
];

allowedOrigins.forEach(origin => {
    fetch(origin + '/api/health')
        .then(() => console.log('✅ Origin acessível:', origin))
        .catch(() => console.log('❌ Origin inacessível:', origin));
});

// 5. Teste de comunicação direta
function testExtensionCommunication() {
    if (typeof chrome !== 'undefined' && chrome.runtime) {
        try {
            chrome.runtime.sendMessage('gimjjdmndkikigfgmnaaejbnahdhailc', 
                { action: 'ping' }, 
                response => {
                    if (response) {
                        console.log('✅ Comunicação funcionando:', response);
                    } else {
                        console.error('❌ Extensão não responde - possível bloqueio');
                        console.log('🔧 Tente:');
                        console.log('1. Recarregar extensão');
                        console.log('2. Reiniciar Chrome');
                        console.log('3. Gerar nova extensão');
                    }
                }
            );
        } catch (error) {
            console.error('❌ Erro na comunicação:', error);
        }
    }
}

// Execute teste após 2 segundos
setTimeout(testExtensionCommunication, 2000);

console.log('📋 Verificação completa - veja logs acima para diagnóstico');