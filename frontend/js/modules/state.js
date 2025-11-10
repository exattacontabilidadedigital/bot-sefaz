// Módulo de Estado Global da Aplicação
export const appState = {
    // Polling
    isPolling: false,
    pollInterval: null,
    
    // Consultas
    consultasData: [],
    currentPage: 1,
    itemsPerPage: 10,
    totalItems: 0,
    currentFilters: {
        search: '',
        status: '',
        tem_tvi: '',
        tem_divida: ''
    },
    
    // Empresas
    empresasData: [],
    empresasCurrentPage: 1,
    empresasItemsPerPage: 10,
    empresasTotalItems: 0,
    empresasFilters: {
        search: ''
    },
    selectedEmpresas: new Set(),
    
    // Fila
    filaData: [],
    filaCurrentPage: 1,
    filaItemsPerPage: 10,
    filaTotalItems: 0,
    
    // Abas
    currentTab: 'consultas'
};

// Resetar filtros de consultas
export function resetConsultasFilters() {
    appState.currentFilters = {
        search: '',
        status: '',
        tem_tvi: '',
        tem_divida: ''
    };
    appState.currentPage = 1;
}

// Resetar filtros de empresas
export function resetEmpresasFilters() {
    appState.empresasFilters = {
        search: ''
    };
    appState.empresasCurrentPage = 1;
}

// Limpar seleção de empresas
export function clearSelectedEmpresas() {
    appState.selectedEmpresas.clear();
}
