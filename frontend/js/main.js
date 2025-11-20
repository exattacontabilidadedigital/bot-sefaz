// Arquivo principal - Inicializa a aplicação e conecta todos os módulos
import * as consultasUI from './modules/consultas.js';
import * as empresasUI from './modules/empresas.js';
import * as filaUI from './modules/fila.js';
import * as tabsUI from './modules/tabs.js';
import { mensagensUI } from './modules/mensagens.js';
import * as agendamentoUI from './modules/agendamento.js';
import { initLucideIcons } from './modules/utils.js';

// Expor módulos globalmente para uso em onclick handlers do HTML
window.consultasUI = consultasUI;
window.empresasUI = empresasUI;
window.filaUI = filaUI;
window.tabsUI = tabsUI;
window.mensagensUI = mensagensUI;
window.agendamentoUI = agendamentoUI;

// Inicializar aplicação quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', async () => {
    // Inicializar ícones Lucide
    initLucideIcons();
    
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

// Configurar toggle do modo headless
function setupHeadlessToggle() {
    const toggle = document.getElementById('headless-toggle');
    const statusText = document.getElementById('headless-status');
    
    if (!toggle || !statusText) return;
    
    // Carregar configuração salva do localStorage
    const savedHeadless = localStorage.getItem('headless_mode');
    if (savedHeadless !== null) {
        toggle.checked = savedHeadless === 'true';
    }
    
    // Atualizar texto inicial
    updateHeadlessStatus(toggle.checked);
    
    // Listener para mudanças
    toggle.addEventListener('change', async (e) => {
        const isHeadless = e.target.checked;
        
        // Salvar no localStorage
        localStorage.setItem('headless_mode', isHeadless);
        
        // Atualizar status visual
        updateHeadlessStatus(isHeadless);
        
        // Mostrar notificação
        showHeadlessNotification(isHeadless);
        
        console.log(`Modo headless ${isHeadless ? 'ativado' : 'desativado'}`);
    });
    
    function updateHeadlessStatus(isHeadless) {
        statusText.textContent = isHeadless ? 'Ativado' : 'Desativado';
        statusText.className = isHeadless 
            ? 'text-xs text-blue-600 ml-2 font-medium' 
            : 'text-xs text-gray-500 ml-2';
    }
    
    function showHeadlessNotification(isHeadless) {
        const message = isHeadless 
            ? 'Modo headless ativado - Browser será invisível nas próximas consultas'
            : 'Modo headless desativado - Browser será visível nas próximas consultas';
        
        // Criar notificação toast
        const toast = document.createElement('div');
        toast.className = 'fixed top-20 right-4 bg-white rounded-lg shadow-lg p-4 border-l-4 border-blue-500 z-50 animate-slide-in-right';
        toast.innerHTML = `
            <div class="flex items-center">
                <i data-lucide="${isHeadless ? 'eye-off' : 'eye'}" class="h-5 w-5 text-blue-600 mr-3"></i>
                <div>
                    <p class="text-sm font-medium text-gray-900">${isHeadless ? 'Modo Invisível' : 'Modo Visível'}</p>
                    <p class="text-xs text-gray-600 mt-1">${message}</p>
                </div>
            </div>
        `;
        
        document.body.appendChild(toast);
        lucide.createIcons();
        
        // Remover após 4 segundos
        setTimeout(() => {
            toast.classList.add('animate-fade-out');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
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
