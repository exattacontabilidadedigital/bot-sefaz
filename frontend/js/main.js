// Arquivo principal - Inicializa a aplicação e conecta todos os módulos
import * as consultasUI from './modules/consultas.js';
import * as empresasUI from './modules/empresas.js';
import * as filaUI from './modules/fila.js';
import * as tabsUI from './modules/tabs.js';
import { mensagensUI } from './modules/mensagens.js';
import * as agendamentoUI from './modules/agendamento.js';
import { initLucideIcons } from './modules/utils.js';
import { initVisualMode } from './modules/visualMode.js';
import { initDashboard } from './modules/dashboard.js';
import * as visualModeModule from './modules/visualMode.js';

// Expor módulos globalmente para uso em onclick handlers do HTML
window.consultasUI = consultasUI;
window.empresasUI = empresasUI;
window.filaUI = filaUI;
window.tabsUI = tabsUI;
window.mensagensUI = mensagensUI;
window.agendamentoUI = agendamentoUI;

// Expor funcionalidades do modo visual
window.visualModeUI = {
    showConfig: () => {
        // Chamar função interna do módulo
        const event = new CustomEvent('show-extension-config');
        document.dispatchEvent(event);
    },
    setExtensionId: visualModeModule.setExtensionId,
    getExtensionId: visualModeModule.getExtensionId,
    diagnose: visualModeModule.diagnoseExtension,
    checkExtension: visualModeModule.checkChromeExtension,
    listExtensions: visualModeModule.listInstalledExtensions,
    reloadExtension: visualModeModule.reloadExtension
};

// Inicializar aplicação quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Proteção global contra erros de MutationObserver
        setupMutationObserverProtection();
        
        // Aguardar DOM completamente carregado e ícones renderizados
        await waitForDOMComplete();
        
        // Inicializar ícones Lucide
        initLucideIcons();
        
        // Aguardar um pouco mais para ícones carregarem
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // Configurar listeners das abas
        tabsUI.setupTabListeners();
        
        // Inicializar abas (carrega aba de consultas por padrão)
        tabsUI.initializeTabs();
        
        // Configurar polling da fila
        filaUI.setupFilaPolling();
        
        // Inicializar módulo de agendamento
        agendamentoUI.initAgendamento();
        
        // Setup de event listeners para consultas
        setupConsultasListeners();
        
        // Setup de event listeners para empresas
        setupEmpresasListeners();
        
        // Setup de event listeners para fila
        setupFilaListeners();
        
        // Setup do toggle de modo headless
        setupHeadlessToggle();
        
        // Inicializar modo visual
        await initVisualMode();
        
        // Inicializar dashboard
        initDashboard();
        
    } catch (error) {
        console.error('Erro durante inicialização da aplicação:', error);
    }
});

function setupConsultasListeners() {
    // Filtros
    const searchFilter = document.getElementById('searchFilter');
    const statusFilter = document.getElementById('statusFilter');
    const tviFilter = document.getElementById('tviFilter');
    const dividaFilter = document.getElementById('dividaFilter');
    const clearFiltersBtn = document.getElementById('clearFiltersBtn');
    
    if (searchFilter) {
        searchFilter.addEventListener('input', debounce(() => {
            consultasUI.applyFilters();
        }, 500));
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', () => consultasUI.applyFilters());
    }
    
    if (tviFilter) {
        tviFilter.addEventListener('change', () => consultasUI.applyFilters());
    }
    
    if (dividaFilter) {
        dividaFilter.addEventListener('change', () => consultasUI.applyFilters());
    }
    
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => consultasUI.clearFilters());
    }
    
    // Paginação
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    
    if (prevPageBtn) {
        prevPageBtn.addEventListener('click', () => consultasUI.prevPage());
    }
    
    if (nextPageBtn) {
        nextPageBtn.addEventListener('click', () => consultasUI.nextPage());
    }
    
    // Modal
    const closeModalBtn = document.getElementById('closeModalBtn');
    const detailsModal = document.getElementById('detailsModal');
    
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', () => consultasUI.closeModal());
    }
    
    if (detailsModal) {
        detailsModal.addEventListener('click', (e) => {
            if (e.target === detailsModal) {
                consultasUI.closeModal();
            }
        });
    }
}

function setupEmpresasListeners() {
    // Filtros
    const empresasSearchFilter = document.getElementById('empresasSearchFilter');
    const clearEmpresasFiltersBtn = document.getElementById('clearEmpresasFiltersBtn');
    
    if (empresasSearchFilter) {
        empresasSearchFilter.addEventListener('input', debounce(() => {
            empresasUI.applyEmpresasFilters();
        }, 500));
    }
    
    if (clearEmpresasFiltersBtn) {
        clearEmpresasFiltersBtn.addEventListener('click', () => empresasUI.clearEmpresasFilters());
    }
    
    // Paginação
    const empresasPrevPageBtn = document.getElementById('empresasPrevPageBtn');
    const empresasNextPageBtn = document.getElementById('empresasNextPageBtn');
    
    if (empresasPrevPageBtn) {
        empresasPrevPageBtn.addEventListener('click', () => empresasUI.prevPage());
    }
    
    if (empresasNextPageBtn) {
        empresasNextPageBtn.addEventListener('click', () => empresasUI.nextPage());
    }
    
    // Seleção
    const selectAllEmpresas = document.getElementById('selectAllEmpresas');
    const addToQueueBtn = document.getElementById('addToQueueBtn');
    
    if (selectAllEmpresas) {
        selectAllEmpresas.addEventListener('change', function() {
            empresasUI.selectAllEmpresas(this);
        });
    }
    
    if (addToQueueBtn) {
        addToQueueBtn.addEventListener('click', () => empresasUI.addSelectedToQueue());
    }
    
    // Modal de empresa
    const addEmpresaBtn = document.getElementById('addEmpresaBtn');
    const closeEmpresaModalBtn = document.getElementById('closeEmpresaModalBtn');
    const empresaModal = document.getElementById('empresaModal');
    const empresaForm = document.getElementById('empresaForm');
    
    if (addEmpresaBtn) {
        addEmpresaBtn.addEventListener('click', () => empresasUI.showAddEmpresaModal());
    }
    
    if (closeEmpresaModalBtn) {
        closeEmpresaModalBtn.addEventListener('click', () => empresasUI.closeEmpresaModal());
    }
    
    if (empresaModal) {
        empresaModal.addEventListener('click', (e) => {
            if (e.target === empresaModal) {
                empresasUI.closeEmpresaModal();
            }
        });
    }
    
    if (empresaForm) {
        empresaForm.addEventListener('submit', (e) => empresasUI.saveEmpresa(e));
    }
    
    // Máscaras de input
    setupInputMasks();
}

function setupFilaListeners() {
    // Botões de controle
    const startProcessingBtn = document.getElementById('startProcessingBtn');
    const stopProcessingBtn = document.getElementById('stopProcessingBtn');
    const clearCompletedBtn = document.getElementById('clearCompletedBtn');
    
    if (startProcessingBtn) {
        startProcessingBtn.addEventListener('click', () => filaUI.startProcessing());
    }
    
    if (stopProcessingBtn) {
        stopProcessingBtn.addEventListener('click', () => filaUI.stopProcessing());
    }
    
    if (clearCompletedBtn) {
        clearCompletedBtn.addEventListener('click', () => filaUI.clearCompletedJobs());
    }
}

function setupInputMasks() {
    const cnpjInput = document.getElementById('empresaCnpj');
    const cpfInput = document.getElementById('empresaCpf');
    
    if (cnpjInput) {
        cnpjInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 14) {
                value = value.replace(/^(\d{2})(\d)/, '$1.$2');
                value = value.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
                value = value.replace(/\.(\d{3})(\d)/, '.$1/$2');
                value = value.replace(/(\d{4})(\d)/, '$1-$2');
            }
            e.target.value = value;
        });
    }
    
    if (cpfInput) {
        cpfInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) {
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
            }
            e.target.value = value;
        });
    }
}

// Configurar toggle do modo headless (mantido para compatibilidade)
function setupHeadlessToggle() {
    // Esta função foi substituída pelo modo visual
    // Manter por compatibilidade se necessário
    console.log('Toggle headless substituído pelo modo visual');
}

// Função auxiliar de debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Proteção global contra erros de MutationObserver
function setupMutationObserverProtection() {
    // Interceptar e corrigir erros de bibliotecas externas com MutationObserver
    const originalConsoleError = console.error;
    console.error = function(...args) {
        const message = args.join(' ');
        // Filtrar erros específicos de MutationObserver de bibliotecas externas
        if (message.includes("Failed to execute 'observe' on 'MutationObserver'") && 
            message.includes("parameter 1 is not of type 'Node'")) {
            console.warn('⚠️ Erro de MutationObserver de biblioteca externa interceptado e ignorado');
            return;
        }
        // Permitir outros erros normais
        originalConsoleError.apply(console, args);
    };
    
    // Interceptar erros não tratados que podem ser do MutationObserver
    window.addEventListener('error', (event) => {
        if (event.message && event.message.includes('MutationObserver') && 
            event.message.includes('not of type')) {
            console.warn('⚠️ Erro global de MutationObserver interceptado:', event.message);
            event.preventDefault();
            return false;
        }
    });
    
    console.log('🛡️ Proteção contra erros de MutationObserver ativada');
}

// Aguardar DOM completamente carregado
async function waitForDOMComplete() {
    // Aguardar alguns frames para garantir renderização completa
    for (let i = 0; i < 3; i++) {
        await new Promise(resolve => requestAnimationFrame(resolve));
    }
    
    // Aguardar carregamento de scripts externos (Lucide, etc)
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Verificar se bibliotecas externas estão carregadas
    let attempts = 0;
    while (typeof lucide === 'undefined' && attempts < 10) {
        await new Promise(resolve => setTimeout(resolve, 50));
        attempts++;
    }
    
    console.log('✅ DOM completamente carregado e pronto para inicialização');
}
