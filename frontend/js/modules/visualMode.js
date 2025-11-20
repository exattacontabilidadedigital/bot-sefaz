// Módulo de Modo Visual
import * as api from './api.js';
import { loadConsultas } from './consultas.js';
import { updateDashboard } from './dashboard.js';
import * as utils from './utils.js';

// Configuração da extensão Chrome
let EXTENSION_ID = localStorage.getItem('chrome_extension_id') || 'your-extension-id-here';

// Variáveis globais do modo visual
let extensionAvailable = false;
let visualModeEnabled = false;

// Função para configurar o ID da extensão
export function setExtensionId(id) {
    console.log('🔧 Configurando novo ID da extensão:', id);
    EXTENSION_ID = id;
    localStorage.setItem('chrome_extension_id', id);
    
    // Forçar verificação imediata
    setTimeout(async () => {
        console.log('🔍 Verificando extensão após configuração...');
        extensionAvailable = await checkChromeExtension();
        updateExtensionStatus();
        
        if (extensionAvailable) {
            console.log('🎉 Extensão configurada e funcionando!');
        } else {
            console.log('⚠️ Extensão configurada mas não está respondendo');
        }
    }, 1000);
}

// Função para obter o ID atual da extensão
export function getExtensionId() {
    return EXTENSION_ID;
}

// Função para verificar se a extensão Chrome está disponível
export async function checkChromeExtension() {
    return new Promise((resolve) => {
        try {
            // Verificar se Chrome runtime API está disponível
            if (typeof chrome === 'undefined' || !chrome.runtime) {
                console.log('🔍 Chrome runtime API não disponível');
                resolve(false);
                return;
            }
            
            // Se ID ainda não foi configurado
            if (EXTENSION_ID === 'your-extension-id-here') {
                console.log('🔍 ID da extensão ainda não configurado');
                resolve(false);
                return;
            }
            
            // Log do ID atual para debug
            console.log('🔌 Testando comunicação com extensão ID:', EXTENSION_ID);
            
            // Primeiro, verificar se a extensão está instalada usando chrome.management
            if (chrome.management) {
                chrome.management.get(EXTENSION_ID, (extensionInfo) => {
                    if (chrome.runtime.lastError) {
                        console.log('❌ Extensão não encontrada no sistema:', chrome.runtime.lastError.message);
                        resolve(false);
                        return;
                    }
                    
                    if (!extensionInfo.enabled) {
                        console.log('⚠️ Extensão encontrada mas está DESABILITADA');
                        resolve(false);
                        return;
                    }
                    
                    console.log('✅ Extensão encontrada e ativa:', extensionInfo.name);
                    
                    // Agora testar comunicação
                    testExtensionCommunication(resolve);
                });
            } else {
                // Fallback se management API não disponível
                console.log('⚠️ Chrome Management API não disponível, testando comunicação direta');
                testExtensionCommunication(resolve);
            }
            
        } catch (error) {
            console.error('💥 Erro crítico ao verificar extensão:', error);
            resolve(false);
        }
    });
    
    function testExtensionCommunication(resolve) {
        // Tentar comunicação com timeout mais longo
        const timeout = setTimeout(() => {
            console.log('⏰ Timeout na comunicação com extensão (10s)');
            resolve(false);
        }, 10000);
        
        chrome.runtime.sendMessage(EXTENSION_ID, { action: 'ping', timestamp: Date.now() }, (response) => {
            clearTimeout(timeout);
            
            if (chrome.runtime.lastError) {
                console.log('❌ Erro na comunicação:', chrome.runtime.lastError.message);
                // Se erro específico de ID inválido, limpar localStorage
                if (chrome.runtime.lastError.message.includes('Extension') || 
                    chrome.runtime.lastError.message.includes('Invalid') ||
                    chrome.runtime.lastError.message.includes('does not exist')) {
                    console.log('🗑️ Removendo ID inválido do localStorage');
                    localStorage.removeItem('chrome_extension_id');
                    EXTENSION_ID = 'your-extension-id-here';
                }
                resolve(false);
            } else if (response && response.pong === true) {
                console.log('✅ Extensão respondeu:', response);
                resolve(true);
            } else {
                console.log('📭 Resposta inválida da extensão:', response);
                resolve(false);
            }
        });
    }
}

// Função para verificar extensão com retry logic
export async function checkChromeExtensionWithRetry(maxRetries = 3, delayMs = 1000) {
    console.log(`🔄 Verificando extensão com retry (máximo ${maxRetries} tentativas)`);
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        console.log(`🎯 Tentativa ${attempt}/${maxRetries}...`);
        
        const result = await checkChromeExtension();
        if (result) {
            console.log(`✅ Extensão respondeu na tentativa ${attempt}`);
            return true;
        }
        
        // Se não é a última tentativa, aguarda antes da próxima
        if (attempt < maxRetries) {
            console.log(`⏳ Aguardando ${delayMs}ms antes da próxima tentativa...`);
            await new Promise(resolve => setTimeout(resolve, delayMs));
        }
    }
    
    console.log(`❌ Extensão não respondeu após ${maxRetries} tentativas`);
    return false;
}

// Função para oferecer diálogo de retry
function offerRetryDialog(message, onRetry) {
    const confirmed = confirm(`${message}\n\n✅ Sim - Tentar novamente\n❌ Não - Desativar modo visual`);
    
    if (confirmed) {
        onRetry();
    } else {
        // Usuário escolheu desativar
        const visualModeCheckbox = document.getElementById('visualModeConsulta');
        const visualModeToggle = document.getElementById('visual-mode-toggle');
        
        if (visualModeCheckbox) visualModeCheckbox.checked = false;
        if (visualModeToggle) visualModeToggle.checked = false;
        
        visualModeEnabled = false;
        console.log('👤 Usuário optou por desativar modo visual');
    }
}

// Auto-detecção de ID da extensão
export async function autoDetectExtensionId() {
    console.log('🔍 Iniciando auto-detecção do ID da extensão...');
    
    // Lista de IDs conhecidos para testar
    const knownIds = [
        localStorage.getItem('chrome_extension_id'),
        'gimjjdmndkikigfgmnaaejbnahdhailc', // ID conhecido atual
        'your-extension-id-here', // Placeholder (vai falhar, mas está na lista)
    ].filter(Boolean).filter(id => id !== 'your-extension-id-here');
    
    if (knownIds.length === 0) {
        console.log('❌ Nenhum ID conhecido para testar');
        return false;
    }
    
    console.log('🧪 Testando IDs:', knownIds);
    
    for (const testId of knownIds) {
        console.log(`🎯 Testando ID: ${testId}`);
        
        // Temporariamente definir o ID para teste
        const originalId = EXTENSION_ID;
        EXTENSION_ID = testId;
        
        try {
            const result = await checkChromeExtension();
            if (result) {
                console.log(`✅ ID válido encontrado: ${testId}`);
                // Salvar ID válido
                localStorage.setItem('chrome_extension_id', testId);
                return testId;
            } else {
                console.log(`❌ ID inválido: ${testId}`);
            }
        } catch (error) {
            console.log(`💥 Erro testando ID ${testId}:`, error.message);
        } finally {
            // Restaurar ID original se teste falhou
            if (EXTENSION_ID !== testId || !result) {
                EXTENSION_ID = originalId;
            }
        }
    }
    
    console.log('❌ Nenhum ID válido encontrado na auto-detecção');
    return false;
}

// Função para verificar status detalhado da extensão
export async function checkExtensionStatus() {
    console.log('🔍 === VERIFICAÇÃO DETALHADA DE STATUS ===');
    
    if (typeof chrome === 'undefined' || !chrome.runtime) {
        console.log('❌ Chrome API não disponível');
        return { installed: false, enabled: false, error: 'Chrome API não disponível' };
    }
    
    if (EXTENSION_ID === 'your-extension-id-here') {
        console.log('❌ ID da extensão não configurado');
        return { installed: false, enabled: false, error: 'ID não configurado' };
    }
    
    // Verificar se extensão está instalada usando management API
    if (chrome.management) {
        try {
            const extensionInfo = await new Promise((resolve, reject) => {
                chrome.management.get(EXTENSION_ID, (info) => {
                    if (chrome.runtime.lastError) {
                        reject(chrome.runtime.lastError);
                    } else {
                        resolve(info);
                    }
                });
            });
            
            console.log('📦 Extensão encontrada:', {
                name: extensionInfo.name,
                version: extensionInfo.version,
                enabled: extensionInfo.enabled,
                installType: extensionInfo.installType
            });
            
            if (!extensionInfo.enabled) {
                return { 
                    installed: true, 
                    enabled: false, 
                    error: 'Extensão instalada mas DESABILITADA',
                    info: extensionInfo 
                };
            }
            
            // Testar comunicação
            const communicating = await checkChromeExtension();
            
            return {
                installed: true,
                enabled: true,
                communicating,
                info: extensionInfo
            };
            
        } catch (error) {
            console.log('❌ Extensão NÃO INSTALADA:', error.message);
            return { 
                installed: false, 
                enabled: false, 
                error: 'Extensão não instalada: ' + error.message 
            };
        }
    } else {
        console.log('⚠️ Management API não disponível, testando comunicação direta');
        const communicating = await checkChromeExtension();
        return {
            installed: communicating, // Assume instalada se comunica
            enabled: communicating,
            communicating,
            error: communicating ? null : 'Não consegue comunicar'
        };
    }
}

// Atualizar status da extensão na interface
export function updateExtensionStatus() {
    const statusElement = document.getElementById('extensionStatus');
    const visualModeCheckbox = document.getElementById('visualModeConsulta');
    const visualModeToggle = document.getElementById('visual-mode-toggle');
    const visualModeStatusText = document.getElementById('visual-mode-status');
    
    if (extensionAvailable) {
        if (statusElement) {
            statusElement.textContent = 'Extensão Ativa';
            statusElement.className = 'text-xs px-2 py-1 rounded-full bg-green-100 text-green-800';
        }
        
        if (visualModeCheckbox) visualModeCheckbox.disabled = false;
        if (visualModeToggle) visualModeToggle.disabled = false;
        
        if (visualModeStatusText) {
            visualModeStatusText.textContent = 'Disponível';
            visualModeStatusText.className = 'text-xs text-green-600 ml-2';
        }
    } else {
        if (statusElement) {
            statusElement.textContent = 'Extensão Não Detectada';
            statusElement.className = 'text-xs px-2 py-1 rounded-full bg-red-100 text-red-800';
        }
        
        if (visualModeCheckbox) {
            visualModeCheckbox.disabled = true;
            visualModeCheckbox.checked = false;
        }
        
        if (visualModeToggle) {
            visualModeToggle.disabled = true;
            visualModeToggle.checked = false;
        }
        
        if (visualModeStatusText) {
            visualModeStatusText.textContent = 'Extensão necessária';
            visualModeStatusText.className = 'text-xs text-red-600 ml-2';
        }
        
        visualModeEnabled = false;
    }
}

// Função para guiar resolução de problemas
export async function troubleshootExtension() {
    console.log('🛠️ === DIAGNÓSTICO E RESOLUÇÃO ===');
    
    const status = await checkExtensionStatus();
    
    if (!status.installed) {
        console.log('📋 AÇÃO NECESSÁRIA: Instalar extensão');
        console.log('1. Vá em chrome://extensions/');
        console.log('2. Ative "Modo do desenvolvedor"');
        console.log('3. Clique "Carregar sem compactação"');
        console.log('4. Selecione a pasta: extensao-chrome/');
        console.log('5. Anote o ID gerado');
        console.log('6. Execute: visualModeUI.setExtensionId("ID_COPIADO")');
        
        return {
            action: 'install',
            message: 'Extensão precisa ser instalada',
            steps: [
                'Ir em chrome://extensions/',
                'Ativar "Modo do desenvolvedor"', 
                'Carregar extensão da pasta extensao-chrome/',
                'Configurar ID na aplicação'
            ]
        };
    }
    
    if (!status.enabled) {
        console.log('📋 AÇÃO NECESSÁRIA: Ativar extensão');
        console.log('1. Vá em chrome://extensions/');
        console.log('2. Encontre "SEFAZ-MA Auto Login"');
        console.log('3. Ative o toggle (deve ficar azul)');
        console.log('4. Recarregue esta página');
        
        return {
            action: 'enable',
            message: 'Extensão instalada mas desabilitada',
            steps: [
                'Ir em chrome://extensions/',
                'Ativar extensão "SEFAZ-MA Auto Login"',
                'Recarregar aplicação'
            ]
        };
    }
    
    if (!status.communicating) {
        console.log('📋 AÇÃO NECESSÁRIA: Recarregar extensão');
        console.log('1. Vá em chrome://extensions/');
        console.log('2. Encontre "SEFAZ-MA Auto Login"');
        console.log('3. Clique no ícone 🔄 (recarregar)');
        console.log('4. Aguarde alguns segundos');
        console.log('5. Teste novamente: visualModeUI.checkExtension()');
        
        return {
            action: 'reload',
            message: 'Extensão ativa mas não responde (service worker inativo)',
            steps: [
                'Ir em chrome://extensions/',
                'Recarregar extensão "SEFAZ-MA Auto Login"',
                'Aguardar e testar novamente'
            ]
        };
    }
    
    console.log('✅ Extensão funcionando corretamente!');
    return {
        action: 'working',
        message: 'Extensão funcionando perfeitamente',
        status
    };
}

// Configurar eventos do modo visual
export function setupVisualModeEvents() {
    const visualModeToggle = document.getElementById('visual-mode-toggle');
    const visualModeCheckbox = document.getElementById('visualModeConsulta');
    const consultaForm = document.getElementById('consultaForm');
    
    // Evento do toggle global no header
    if (visualModeToggle) {
        visualModeToggle.addEventListener('change', (e) => {
            visualModeEnabled = e.target.checked && extensionAvailable;
            if (visualModeCheckbox) {
                visualModeCheckbox.checked = visualModeEnabled;
            }
            
            // Se tentou ativar mas extensão não está disponível
            if (e.target.checked && !extensionAvailable) {
                // Manter marcado mas oferecer retry
                e.target.checked = true;
                offerRetryDialog('Extensão Chrome não detectada. Deseja tentar detectar novamente?', async () => {
                    console.log('🔄 Usuário solicitou retry da detecção...');
                    const detected = await checkChromeExtensionWithRetry();
                    if (detected) {
                        extensionAvailable = true;
                        updateExtensionStatus();
                        visualModeEnabled = true;
                        utils.showNotification('✅ Extensão detectada! Modo visual ativado.', 'success');
                    } else {
                        e.target.checked = false;
                        visualModeEnabled = false;
                        utils.showNotification('❌ Extensão ainda não detectada. Verifique se está instalada e ativa.', 'error');
                    }
                });
            }
        });
    }
    
    // Evento do checkbox individual na consulta
    if (visualModeCheckbox) {
        visualModeCheckbox.addEventListener('change', (e) => {
            visualModeEnabled = e.target.checked && extensionAvailable;
            if (visualModeToggle) {
                visualModeToggle.checked = visualModeEnabled;
            }
            
            // Se tentou ativar mas extensão não está disponível
            if (e.target.checked && !extensionAvailable) {
                // Manter marcado mas oferecer retry
                e.target.checked = true;
                offerRetryDialog('Extensão Chrome não detectada. Deseja tentar detectar novamente?', async () => {
                    console.log('🔄 Usuário solicitou retry da detecção...');
                    const detected = await checkChromeExtensionWithRetry();
                    if (detected) {
                        extensionAvailable = true;
                        updateExtensionStatus();
                        visualModeEnabled = true;
                        utils.showNotification('✅ Extensão detectada! Modo visual ativado.', 'success');
                    } else {
                        e.target.checked = false;
                        visualModeEnabled = false;
                        utils.showNotification('❌ Extensão ainda não detectada. Verifique se está instalada e ativa.', 'error');
                    }
                });
            }
        });
    }
    
    // Evento de submissão do formulário
    if (consultaForm) {
        consultaForm.addEventListener('submit', handleConsultaSubmit);
    }
}

// Manipular submissão do formulário de consulta
async function handleConsultaSubmit(e) {
    e.preventDefault();
    
    const cpf = document.getElementById('consultaCpf').value.trim();
    const senha = document.getElementById('consultaSenha').value.trim();
    const ie = document.getElementById('consultaIe').value.trim();
    
    // Validação básica
    if (!cpf || !senha) {
        utils.showNotification('CPF e Senha são obrigatórios', 'error');
        return;
    }
    
    // Validar formato CPF
    const cpfLimpo = cpf.replace(/\D/g, '');
    if (cpfLimpo.length !== 11) {
        utils.showNotification('CPF deve conter 11 dígitos', 'error');
        return;
    }
    
    // Verificar se modo visual está realmente disponível
    if (visualModeEnabled && !extensionAvailable) {
        utils.showNotification('Modo visual não está disponível. Execute em modo headless?', 'warning');
        visualModeEnabled = false;
        document.getElementById('visualModeConsulta').checked = false;
        document.getElementById('visual-mode-toggle').checked = false;
    }
    
    const consultaData = {
        cpf_socio: cpfLimpo,
        senha,
        inscricao_estadual: ie || null,
        modo_visual: visualModeEnabled && extensionAvailable
    };
    
    try {
        await executarConsulta(consultaData);
        utils.showNotification('Consulta executada com sucesso!', 'success');
    } catch (error) {
        console.error('Erro ao executar consulta:', error);
        
        // Se falhou no modo visual, oferecer fallback para headless
        if (consultaData.modo_visual && error.message.includes('extensão')) {
            const tentarHeadless = confirm(
                `Erro no modo visual: ${error.message}\n\n` +
                'Deseja tentar executar a consulta em modo headless (tradicional)?'
            );
            
            if (tentarHeadless) {
                try {
                    consultaData.modo_visual = false;
                    await executarConsulta(consultaData);
                    utils.showNotification('Consulta executada com sucesso em modo headless!', 'success');
                } catch (fallbackError) {
                    utils.showNotification('Erro também no modo headless: ' + fallbackError.message, 'error');
                }
            }
        } else {
            utils.showNotification('Erro ao executar consulta: ' + error.message, 'error');
        }
    }
}

// Executar consulta (visual ou headless)
async function executarConsulta(dados) {
    const progressDiv = document.getElementById('consultaProgress');
    const progressText = document.getElementById('consultaProgressText');
    const submitBtn = document.getElementById('executarConsultaBtn');
    
    // Mostrar progresso
    if (progressDiv) progressDiv.classList.remove('hidden');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>Executando...';
    }
    
    try {
        let response;
        
        if (dados.modo_visual && extensionAvailable) {
            // Modo visual - comunicar com extensão
            if (progressText) progressText.textContent = 'Iniciando modo visual...';
            response = await executarConsultaVisual(dados);
        } else {
            // Modo headless tradicional
            if (progressText) progressText.textContent = 'Executando consulta...';
            response = await api.executeConsulta(dados);
        }
        
        // Sucesso
        if (progressText) progressText.textContent = 'Consulta concluída!';
        
        // Limpar formulário
        document.getElementById('consultaForm').reset();
        
        // Recarregar dados
        setTimeout(() => {
            loadConsultas();
            updateDashboard();
        }, 1000);
        
        return response;
        
    } catch (error) {
        if (progressText) progressText.textContent = 'Erro na consulta';
        throw error;
    } finally {
        // Ocultar progresso
        setTimeout(() => {
            if (progressDiv) progressDiv.classList.add('hidden');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i data-lucide="play" class="h-4 w-4 mr-2"></i>Executar';
                // Reinicializar ícones Lucide
                if (window.lucide) window.lucide.createIcons();
            }
        }, 2000);
    }
}

// Executar consulta no modo visual (via extensão Chrome)
async function executarConsultaVisual(dados) {
    return new Promise(async (resolve, reject) => {
        try {
            // Verificar se extensão ainda está disponível
            const isAvailable = await checkChromeExtension();
            if (!isAvailable) {
                throw new Error('Extensão Chrome não está respondendo. Verifique se está instalada e ativa.');
            }
            
            console.log('📡 Enviando dados para extensão:', dados);
            
            // Configurar timeout para a operação
            const timeout = setTimeout(() => {
                reject(new Error('Timeout na execução da consulta (60 segundos). A extensão pode estar ocupada.'));
            }, 60000);
            
            // Enviar dados para extensão Chrome
            chrome.runtime.sendMessage(EXTENSION_ID, {
                action: 'executeConsulta',
                data: dados
            }, (response) => {
                clearTimeout(timeout);
                
                if (chrome.runtime.lastError) {
                    console.error('❌ Erro na comunicação:', chrome.runtime.lastError);
                    reject(new Error(`Erro de comunicação com extensão: ${chrome.runtime.lastError.message}`));
                } else if (response) {
                    if (response.success) {
                        console.log('✅ Consulta visual concluída:', response);
                        resolve(response);
                    } else {
                        console.error('❌ Erro na execução visual:', response.error);
                        reject(new Error(response.error || 'Erro desconhecido na execução visual'));
                    }
                } else {
                    console.error('❌ Resposta vazia da extensão');
                    reject(new Error('Extensão não retornou resposta. Verifique se está funcionando corretamente.'));
                }
            });
            
        } catch (error) {
            console.error('💥 Erro crítico na execução visual:', error);
            reject(error);
        }
    });
}

// Inicializar módulo de modo visual
export async function initVisualMode() {
    console.log('Inicializando modo visual...');
    
    // Criar interface de configuração se necessário
    createExtensionConfigInterface();
    
    // Adicionar listener para evento de configuração
    document.addEventListener('show-extension-config', showExtensionConfigModal);
    
    // Tentar auto-detectar ID se não estiver configurado
    if (EXTENSION_ID === 'your-extension-id-here') {
        console.log('🔍 ID não configurado, tentando auto-detecção...');
        const detectedId = await autoDetectExtensionId();
        if (detectedId) {
            EXTENSION_ID = detectedId;
            console.log('✅ ID auto-detectado:', EXTENSION_ID);
        }
    }
    
    // Verificar extensão Chrome com retry logic
    console.log('🚀 Verificando extensão com retry logic...');
    extensionAvailable = await checkChromeExtensionWithRetry();
    updateExtensionStatus();
    setupVisualModeEvents();
    
    // Verificar extensão periodicamente (reduzido para 30s para evitar sobrecarga)
    setInterval(async () => {
        const wasAvailable = extensionAvailable;
        // Usar verificação simples para polling periódico
        extensionAvailable = await checkChromeExtension();
        
        if (wasAvailable !== extensionAvailable) {
            updateExtensionStatus();
            console.log('Status da extensão alterado:', extensionAvailable ? 'Disponível' : 'Indisponível');
        }
    }, 30000); // 30s em vez de 5s
    
    console.log('Modo visual inicializado. Extensão:', extensionAvailable ? 'Disponível' : 'Não detectada');
}

// Getters para estado atual
export function isExtensionAvailable() {
    return extensionAvailable;
}

export function isVisualModeEnabled() {
    return visualModeEnabled;
}

// Função de diagnóstico da extensão
export function diagnoseExtension() {
    console.log('🔍 === DIAGNÓSTICO DA EXTENSÃO ===');
    console.log('Chrome API disponível:', typeof chrome !== 'undefined' && !!chrome.runtime);
    console.log('ID configurado:', EXTENSION_ID);
    console.log('ID no localStorage:', localStorage.getItem('chrome_extension_id'));
    console.log('Extensão disponível:', extensionAvailable);
    console.log('Modo visual habilitado:', visualModeEnabled);
    
    if (typeof chrome !== 'undefined' && chrome.runtime) {
        console.log('🔌 Tentando ping na extensão...');
        chrome.runtime.sendMessage(EXTENSION_ID, { action: 'ping' }, (response) => {
            if (chrome.runtime.lastError) {
                console.log('❌ Erro no ping:', chrome.runtime.lastError.message);
            } else {
                console.log('✅ Resposta do ping:', response);
            }
        });
    }
    console.log('🔍 === FIM DO DIAGNÓSTICO ===');
}

// Função para listar extensões instaladas (se possível)
export async function listInstalledExtensions() {
    if (typeof chrome !== 'undefined' && chrome.management) {
        try {
            const extensions = await chrome.management.getAll();
            console.log('📋 Extensões instaladas:', extensions.filter(ext => ext.type === 'extension').map(ext => ({
                id: ext.id,
                name: ext.name,
                enabled: ext.enabled
            })));
        } catch (error) {
            console.log('❌ Não foi possível listar extensões:', error.message);
            console.log('💡 Para listar extensões, use: chrome://extensions/');
        }
    } else {
        console.log('❌ API chrome.management não disponível');
        console.log('💡 Para ver extensões, vá em: chrome://extensions/');
    }
}

// Função para recarregar extensão (se tiver permissões)
export async function reloadExtension() {
    if (typeof chrome !== 'undefined' && chrome.management) {
        try {
            console.log('🔄 Tentando recarregar extensão...');
            await chrome.management.setEnabled(EXTENSION_ID, false);
            await new Promise(resolve => setTimeout(resolve, 1000));
            await chrome.management.setEnabled(EXTENSION_ID, true);
            console.log('✅ Extensão recarregada com sucesso!');
            
            // Aguardar um pouco e verificar novamente
            setTimeout(async () => {
                extensionAvailable = await checkChromeExtension();
                updateExtensionStatus();
            }, 2000);
        } catch (error) {
            console.log('❌ Não foi possível recarregar automaticamente:', error.message);
            console.log('💡 Recarregue manualmente em: chrome://extensions/');
        }
    } else {
        console.log('❌ Para recarregar, vá em chrome://extensions/ e clique no ícone de recarregar');
    }
}

// Função de teste específica para comunicação
export async function testCommunication() {
    console.log('🧪 === TESTE ESPECÍFICO DE COMUNICAÇÃO ===');
    
    if (typeof chrome === 'undefined' || !chrome.runtime) {
        console.log('❌ Chrome runtime API não disponível');
        return false;
    }
    
    if (EXTENSION_ID === 'your-extension-id-here') {
        console.log('❌ ID da extensão não configurado');
        return false;
    }
    
    console.log('🎯 Testando com ID:', EXTENSION_ID);
    console.log('🌐 Origem:', window.location.origin);
    console.log('🔗 URL:', window.location.href);
    
    return new Promise((resolve) => {
        const startTime = Date.now();
        
        // Ping específico com dados detalhados
        const message = {
            action: 'ping',
            timestamp: startTime,
            origin: window.location.origin,
            url: window.location.href,
            userAgent: navigator.userAgent
        };
        
        console.log('📤 Enviando mensagem:', message);
        
        try {
            chrome.runtime.sendMessage(EXTENSION_ID, message, (response) => {
                const endTime = Date.now();
                const duration = endTime - startTime;
                
                console.log('⏱️ Duração do teste:', duration + 'ms');
                
                if (chrome.runtime.lastError) {
                    console.log('❌ Erro na comunicação:', chrome.runtime.lastError);
                    console.log('💡 Possíveis causas:');
                    console.log('   1. Extensão não carregada');
                    console.log('   2. ID incorreto');
                    console.log('   3. Origem não permitida');
                    console.log('   4. Service worker inativo');
                    resolve(false);
                } else if (response) {
                    console.log('✅ Resposta recebida:', response);
                    console.log('🎉 Comunicação funcionando!');
                    resolve(true);
                } else {
                    console.log('📭 Resposta vazia');
                    resolve(false);
                }
            });
        } catch (error) {
            console.error('💥 Erro crítico:', error);
            resolve(false);
        }
    });
}

// Criar interface de configuração da extensão
function createExtensionConfigInterface() {
    // Verificar se já existe ID configurado
    if (EXTENSION_ID !== 'your-extension-id-here') {
        return; // Já configurado
    }
    
    // Criar botão de configuração no toggle do modo visual
    const visualModeContainer = document.querySelector('[data-container="visual-mode"]') || 
                               document.getElementById('visual-mode-toggle')?.parentElement;
    
    if (visualModeContainer) {
        // Adicionar botão de configuração
        const configButton = document.createElement('button');
        configButton.innerHTML = '⚙️';
        configButton.title = 'Configurar Extensão Chrome';
        configButton.className = 'ml-2 text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200';
        configButton.onclick = showExtensionConfigModal;
        
        visualModeContainer.appendChild(configButton);
    }
}

// Mostrar modal de configuração da extensão
function showExtensionConfigModal() {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-gray-900 bg-opacity-50 z-50 flex items-center justify-center';
    modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 w-[500px] max-w-full mx-4">
            <h3 class="text-lg font-semibold mb-4 flex items-center">
                <i data-lucide="settings" class="h-5 w-5 mr-2"></i>
                Configurar Extensão Chrome
            </h3>
            
            <div class="mb-4 p-4 bg-blue-50 rounded-lg">
                <h4 class="font-medium text-blue-900 mb-2">📋 Como obter o ID:</h4>
                <ol class="text-sm text-blue-800 space-y-1">
                    <li>1. Abra uma nova aba e digite: <code class="bg-blue-200 px-1 rounded">chrome://extensions/</code></li>
                    <li>2. Ative o <strong>Modo do desenvolvedor</strong> (canto superior direito)</li>
                    <li>3. Localize a extensão <strong>"SEFAZ-MA Auto Login"</strong></li>
                    <li>4. Copie o <strong>ID</strong> (string longa abaixo do nome)</li>
                </ol>
            </div>
            
            <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    ID da Extensão:
                </label>
                <input 
                    id="extension-id-input" 
                    type="text" 
                    class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
                    placeholder="Ex: abcdefghijklmnopqrstuvwxyz123456"
                    value="${EXTENSION_ID !== 'your-extension-id-here' ? EXTENSION_ID : ''}"
                >
                <p class="text-xs text-gray-500 mt-1">
                    O ID tem cerca de 32 caracteres alfanuméricos
                </p>
            </div>
            
            <div class="mb-4">
                <button 
                    id="auto-detect-btn"
                    class="w-full px-3 py-2 bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors text-sm"
                >
                    🔍 Tentar detectar automaticamente
                </button>
            </div>
            
            <div class="flex justify-end space-x-2">
                <button 
                    id="cancel-config" 
                    class="px-4 py-2 text-gray-600 bg-gray-100 rounded hover:bg-gray-200"
                >
                    Cancelar
                </button>
                <button 
                    id="save-config" 
                    class="px-4 py-2 text-white bg-blue-600 rounded hover:bg-blue-700"
                >
                    Salvar e Testar
                </button>
            </div>
        </div>
    `;
    
    // Adicionar eventos
    const input = modal.querySelector('#extension-id-input');
    const cancelBtn = modal.querySelector('#cancel-config');
    const saveBtn = modal.querySelector('#save-config');
    const autoDetectBtn = modal.querySelector('#auto-detect-btn');
    
    cancelBtn.onclick = () => document.body.removeChild(modal);
    
    // Auto-detectar extensão
    autoDetectBtn.onclick = async () => {
        autoDetectBtn.innerHTML = '🔄 Detectando...';
        autoDetectBtn.disabled = true;
        
        try {
            // Verificar se Chrome APIs estão disponíveis
            if (typeof chrome === 'undefined' || !chrome.management) {
                utils.showNotification('APIs do Chrome não disponíveis. Use configuração manual.', 'warning');
                return;
            }
            
            // Tentar listar extensões instaladas
            chrome.management.getAll((extensions) => {
                if (chrome.runtime.lastError) {
                    console.log('Não foi possível listar extensões:', chrome.runtime.lastError);
                    utils.showNotification('Não foi possível acessar lista de extensões. Use configuração manual.', 'warning');
                    return;
                }
                
                // Procurar por extensão SEFAZ
                const sefazExtension = extensions.find(ext => 
                    ext.name.toLowerCase().includes('sefaz') ||
                    ext.name.toLowerCase().includes('auto login') ||
                    ext.description?.toLowerCase().includes('sefaz')
                );
                
                if (sefazExtension) {
                    input.value = sefazExtension.id;
                    utils.showNotification(`Extensão encontrada: ${sefazExtension.name}`, 'success');
                } else {
                    utils.showNotification('Extensão SEFAZ não encontrada. Configure manualmente.', 'warning');
                }
            });
            
        } catch (error) {
            console.error('Erro na detecção automática:', error);
            utils.showNotification('Erro na detecção automática. Use configuração manual.', 'error');
        } finally {
            autoDetectBtn.innerHTML = '🔍 Tentar detectar automaticamente';
            autoDetectBtn.disabled = false;
        }
    };
    
    saveBtn.onclick = () => {
        const newId = input.value.trim();
        if (newId && newId !== 'your-extension-id-here' && newId.length >= 20) {
            setExtensionId(newId);
            utils.showNotification('ID configurado! Verificando conexão...', 'success');
            
            // Testar conexão após configurar
            setTimeout(async () => {
                const testResult = await checkChromeExtension();
                if (testResult) {
                    utils.showNotification('✅ Extensão detectada e conectada!', 'success');
                } else {
                    utils.showNotification('⚠️ ID salvo, mas extensão não responde. Verifique se está instalada e ativa.', 'warning');
                }
            }, 1000);
        } else {
            utils.showNotification('Por favor, insira um ID válido (mínimo 20 caracteres)', 'error');
            return;
        }
        document.body.removeChild(modal);
    };
    
    // Fechar ao clicar fora
    modal.onclick = (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    };
    
    // Fechar com ESC
    const handleEsc = (e) => {
        if (e.key === 'Escape') {
            document.body.removeChild(modal);
            document.removeEventListener('keydown', handleEsc);
        }
    };
    document.addEventListener('keydown', handleEsc);
    
    document.body.appendChild(modal);
    input.focus();
    
    // Inicializar ícones Lucide no modal
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

// Setter para ID da extensão (para configuração dinâmica) - mantido para compatibilidade
export function setExtensionId_legacy(id) {
    // Função mantida para compatibilidade - use setExtensionId() no lugar
    console.warn('setExtensionId_legacy() está depreciado. Use setExtensionId() no lugar.');
    setExtensionId(id);
}