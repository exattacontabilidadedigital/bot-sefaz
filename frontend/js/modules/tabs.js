// Módulo de UI - Gerenciamento de Abas
import { appState } from './state.js';

export function switchTab(tabName) {
    console.log('🔄 Trocando para aba:', tabName);
    appState.currentTab = tabName;
    
    // Atualizar botões das abas
    document.querySelectorAll('[data-tab]').forEach(btn => {
        const isActive = btn.dataset.tab === tabName;
        btn.classList.toggle('border-blue-500', isActive);
        btn.classList.toggle('text-blue-600', isActive);
        btn.classList.toggle('border-transparent', !isActive);
        btn.classList.toggle('text-gray-500', !isActive);
        btn.classList.toggle('hover:text-gray-700', !isActive);
        btn.classList.toggle('hover:border-gray-300', !isActive);
    });
    
    // Atualizar painéis de conteúdo
    document.querySelectorAll('[data-tab-content]').forEach(panel => {
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
