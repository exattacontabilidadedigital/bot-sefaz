// Módulo de UI - Gerenciamento de Abas
import { appState } from './state.js';

export function switchTab(tabName) {
    console.log('🔄 Trocando para aba:', tabName);
    
    if (!tabName) {
        console.error('Nome da aba não fornecido');
        return;
    }
    
    appState.currentTab = tabName;
    
    // Atualizar botões das abas
    const tabButtons = document.querySelectorAll('[data-tab]');
    if (tabButtons.length === 0) {
        console.warn('Nenhum botão de aba encontrado');
        return;
    }
    
    tabButtons.forEach(btn => {
        if (!btn || !btn.dataset) return;
        const isActive = btn.dataset.tab === tabName;
        btn.classList.toggle('border-blue-500', isActive);
        btn.classList.toggle('text-blue-600', isActive);
        btn.classList.toggle('border-transparent', !isActive);
        btn.classList.toggle('text-gray-500', !isActive);
        btn.classList.toggle('hover:text-gray-700', !isActive);
        btn.classList.toggle('hover:border-gray-300', !isActive);
    });
    
    // Atualizar painéis de conteúdo
    const tabPanels = document.querySelectorAll('[data-tab-content]');
    if (tabPanels.length === 0) {
        console.warn('Nenhum painel de aba encontrado');
        return;
    }
    
    tabPanels.forEach(panel => {
        if (!panel || !panel.dataset) return;
        const isActive = panel.dataset.tabContent === tabName;
        console.log(`   ${panel.dataset.tabContent}: ${isActive ? 'VISIBLE' : 'HIDDEN'}`);
        panel.classList.toggle('hidden', !isActive);
    });
    
    // Carregar dados da aba ativa
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch (tabName) {
        case 'consultas':
            if (window.consultasUI && window.consultasUI.loadConsultas) {
                window.consultasUI.loadConsultas();
                window.consultasUI.loadEstatisticas();
            }
            break;
            
        case 'empresas':
            if (window.empresasUI && window.empresasUI.loadEmpresas) {
                window.empresasUI.loadEmpresas();
            }
            break;

        case 'mensagens':
            if (window.mensagensUI && window.mensagensUI.init) {
                window.mensagensUI.init();
            }
            break;
            
        case 'fila':
            if (window.filaUI && window.filaUI.loadFila) {
                window.filaUI.loadFila();
                window.filaUI.checkProcessingStatus();
            }
            break;
    }
}

export function setupTabListeners() {
    document.querySelectorAll('[data-tab]').forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });
}

export function initializeTabs() {
    // Carregar aba inicial (consultas)
    switchTab('consultas');
}
