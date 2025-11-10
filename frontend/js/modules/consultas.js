// Módulo de UI - Consultas
import { appState } from './state.js';
import * as api from './api.js';
import * as utils from './utils.js';

export async function loadConsultas() {
    try {
        const consultas = await api.fetchConsultas(
            appState.itemsPerPage,
            (appState.currentPage - 1) * appState.itemsPerPage,
            appState.currentFilters
        );
        
        const countData = await api.fetchConsultasCount(appState.currentFilters);
        appState.totalItems = countData.total;
        appState.consultasData = consultas;
        
        updateConsultasTable(consultas);
        updateConsultasPagination();
        
    } catch (error) {
        console.error('Erro ao buscar consultas:', error);
        utils.showNotification('Erro ao carregar consultas', 'error');
    }
}

function updateConsultasTable(consultas) {
    const tbody = document.getElementById('resultTable');
    const emptyState = document.getElementById('emptyState');
    const totalResults = document.getElementById('totalResults');
    
    if (totalResults) {
        totalResults.textContent = `${appState.totalItems} resultado${appState.totalItems !== 1 ? 's' : ''}`;
    }
    
    if (consultas.length === 0) {
        if (tbody) tbody.innerHTML = '';
        if (emptyState) emptyState.classList.remove('hidden');
        return;
    }
    
    if (emptyState) emptyState.classList.add('hidden');
    
    if (tbody) {
        // Filtrar consultas que não têm dados válidos (erro na consulta)
        const consultasValidas = consultas.filter(c => c.nome_empresa && c.inscricao_estadual);
        
        tbody.innerHTML = consultasValidas.map(consulta => `
            <tr>
                <td class="px-3 py-3">
                    <div class="text-sm font-medium text-gray-900 truncate">${consulta.nome_empresa}</div>
                </td>
                <td class="px-3 py-3 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${consulta.inscricao_estadual}</div>
                </td>
                <td class="px-3 py-3 whitespace-nowrap">
                    ${utils.getStatusBadge(consulta.status_ie)}
                </td>
                <td class="px-3 py-3 whitespace-nowrap">
                    ${utils.getTVIBadge(consulta.tem_tvi)}
                </td>
                <td class="px-3 py-3 whitespace-nowrap">
                    ${utils.getDividasBadge(consulta.tem_divida_pendente)}
                </td>
                <td class="px-3 py-3 whitespace-nowrap">
                    <div class="text-sm text-gray-900">
                        ${utils.formatCurrency(consulta.valor_debitos)}
                    </div>
                </td>
                <td class="px-3 py-3 whitespace-nowrap">
                    <div class="text-sm text-gray-500">
                        ${utils.formatDate(consulta.data_consulta)}
                    </div>
                </td>
                <td class="px-3 py-3 whitespace-nowrap text-right text-sm font-medium">
                    <div class="flex space-x-2 justify-end">
                        <button onclick="window.consultasUI.showDetails(${consulta.id})" class="text-blue-600 hover:text-blue-900">
                            <i data-lucide="eye" class="h-4 w-4"></i>
                        </button>
                        <button onclick="window.consultasUI.deleteConsulta(${consulta.id})" class="text-red-600 hover:text-red-900">
                            <i data-lucide="trash-2" class="h-4 w-4"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        
        utils.initLucideIcons();
    }
}

function updateConsultasPagination() {
    const totalPages = Math.ceil(appState.totalItems / appState.itemsPerPage);
    const currentPage = appState.currentPage;
    
    // Atualizar informações de paginação
    const pageInfo = document.getElementById('consultasPageInfo');
    if (pageInfo) {
        const startItem = appState.totalItems === 0 ? 0 : (currentPage - 1) * appState.itemsPerPage + 1;
        const endItem = Math.min(currentPage * appState.itemsPerPage, appState.totalItems);
        pageInfo.textContent = `Mostrando ${startItem} a ${endItem} de ${appState.totalItems} resultados`;
    }
    
    // Atualizar botões de paginação
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    
    if (prevBtn) {
        prevBtn.disabled = currentPage === 1;
        prevBtn.classList.toggle('opacity-50', currentPage === 1);
        prevBtn.classList.toggle('cursor-not-allowed', currentPage === 1);
    }
    
    if (nextBtn) {
        nextBtn.disabled = currentPage >= totalPages;
        nextBtn.classList.toggle('opacity-50', currentPage >= totalPages);
        nextBtn.classList.toggle('cursor-not-allowed', currentPage >= totalPages);
    }
    
    // Atualizar número da página
    const pageNumber = document.getElementById('consultasPageNumber');
    if (pageNumber) {
        pageNumber.textContent = `Página ${currentPage} de ${totalPages || 1}`;
    }
}

export function applyFilters() {
    const elements = {
        search: document.getElementById('searchFilter'),
        status: document.getElementById('statusFilter'),
        tvi: document.getElementById('tviFilter'),
        divida: document.getElementById('dividaFilter'),
        clearBtn: document.getElementById('clearFiltersBtn')
    };
    
    appState.currentFilters = {
        search: elements.search ? elements.search.value.trim() : '',
        status: elements.status ? elements.status.value : '',
        tem_tvi: elements.tvi ? elements.tvi.value : '',
        tem_divida: elements.divida ? elements.divida.value : ''
    };
    
    appState.currentPage = 1;
    loadConsultas();
    
    const hasFilters = Object.values(appState.currentFilters).some(value => value !== '');
    if (elements.clearBtn) {
        elements.clearBtn.classList.toggle('hidden', !hasFilters);
    }
}

export function clearFilters() {
    const elements = {
        search: document.getElementById('searchFilter'),
        status: document.getElementById('statusFilter'),
        tvi: document.getElementById('tviFilter'),
        divida: document.getElementById('dividaFilter'),
        clearBtn: document.getElementById('clearFiltersBtn')
    };
    
    if (elements.search) elements.search.value = '';
    if (elements.status) elements.status.value = '';
    if (elements.tvi) elements.tvi.value = '';
    if (elements.divida) elements.divida.value = '';
    
    appState.currentFilters = { search: '', status: '', tem_tvi: '', tem_divida: '' };
    appState.currentPage = 1;
    
    loadConsultas();
    if (elements.clearBtn) {
        elements.clearBtn.classList.add('hidden');
    }
}

export async function deleteConsulta(consultaId) {
    if (!confirm('Tem certeza que deseja excluir esta consulta?')) {
        return;
    }
    
    try {
        await api.deleteConsulta(consultaId);
        await loadConsultas();
        await loadEstatisticas();
        utils.showNotification('Consulta excluída com sucesso!', 'success');
    } catch (error) {
        console.error('Erro ao excluir consulta:', error);
        utils.showNotification('Erro ao excluir consulta', 'error');
    }
}

export function showDetails(consultaId) {
    const consulta = appState.consultasData.find(c => c.id === consultaId);
    if (!consulta) return;

    const modalContent = document.getElementById('modalContent');
    modalContent.innerHTML = `
        <div class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700">Nome da Empresa</label>
                <p class="mt-1 text-sm text-gray-900">${consulta.nome_empresa || 'N/A'}</p>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">Inscrição Estadual</label>
                    <p class="mt-1 text-sm text-gray-900">${consulta.inscricao_estadual || 'N/A'}</p>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">CNPJ</label>
                    <p class="mt-1 text-sm text-gray-900">${consulta.cnpj || 'N/A'}</p>
                </div>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700">Status Cadastral</label>
                <div class="mt-1">${utils.getStatusBadge(consulta.status_ie)}</div>
            </div>
            
            <div class="grid grid-cols-3 gap-4">
                <div>
                    <label class="block text-sm font-medium text-gray-700">TVIs</label>
                    <div class="mt-1">${utils.getTVIBadge(consulta.tem_tvi)}</div>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Dívida Pendente</label>
                    <div class="mt-1">${utils.getDividasBadge(consulta.tem_divida_pendente)}</div>
                </div>
                <div>
                    <label class="block text-sm font-medium text-gray-700">Omisso Declaração</label>
                    <div class="mt-1">${utils.getDividasBadge(consulta.omisso_declaracao)}</div>
                </div>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700">Valor das Dívidas</label>
                <p class="mt-1 text-lg font-semibold text-gray-900">
                    ${utils.formatCurrency(consulta.valor_debitos)}
                </p>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700">Inscrito em Cadastro Restritivo</label>
                <div class="mt-1">${utils.getDividasBadge(consulta.inscrito_restritivo)}</div>
            </div>
            
            <div>
                <label class="block text-sm font-medium text-gray-700">Data da Consulta</label>
                <p class="mt-1 text-sm text-gray-900">
                    ${utils.formatDateTime(consulta.data_consulta)}
                </p>
            </div>
        </div>
    `;

    document.getElementById('detailsModal').classList.remove('hidden');
    utils.initLucideIcons();
}

export function closeModal() {
    document.getElementById('detailsModal').classList.add('hidden');
}

export async function loadEstatisticas() {
    try {
        const data = await api.fetchEstatatisticas();
        
        const elements = {
            totalConsultas: document.getElementById('totalConsultas'),
            empresasAtivas: document.getElementById('empresasAtivas'),
            empresasComDividas: document.getElementById('empresasComDividas'),
            empresasNaoAtivas: document.getElementById('empresasNaoAtivas')
        };
        
        if (elements.totalConsultas) elements.totalConsultas.textContent = data.total_consultas;
        if (elements.empresasAtivas) elements.empresasAtivas.textContent = data.empresas_ativas;
        if (elements.empresasComDividas) elements.empresasComDividas.textContent = data.empresas_com_dividas;
        
        // Calcular empresas não ativas (total - ativas)
        const empresasNaoAtivas = data.total_consultas - data.empresas_ativas;
        if (elements.empresasNaoAtivas) elements.empresasNaoAtivas.textContent = empresasNaoAtivas;
        
    } catch (error) {
        console.error('Erro ao buscar estatísticas:', error);
    }
}

export function nextPage() {
    const totalPages = Math.ceil(appState.totalItems / appState.itemsPerPage);
    if (appState.currentPage < totalPages) {
        appState.currentPage++;
        loadConsultas();
    }
}

export function prevPage() {
    if (appState.currentPage > 1) {
        appState.currentPage--;
        loadConsultas();
    }
}

export function changeItemsPerPage(itemsPerPage) {
    appState.itemsPerPage = parseInt(itemsPerPage);
    appState.currentPage = 1;
    loadConsultas();
}

export function filterByAll() {
    // Limpar todos os filtros
    clearFilters();
}

export function filterByAtivas() {
    // Limpar outros filtros
    const searchFilter = document.getElementById('searchFilter');
    const statusFilter = document.getElementById('statusFilter');
    const tviFilter = document.getElementById('tviFilter');
    const dividaFilter = document.getElementById('dividaFilter');
    
    if (searchFilter) searchFilter.value = '';
    if (tviFilter) tviFilter.value = '';
    if (dividaFilter) dividaFilter.value = '';
    
    // Verificar se já está filtrando por ativas
    const statusAtual = statusFilter ? statusFilter.value : '';
    
    if (statusAtual === 'ATIVO') {
        // Se já está filtrando por ativas, limpar filtro
        clearFilters();
    } else {
        // Aplicar filtro de ativas
        if (statusFilter) statusFilter.value = 'ATIVO';
        
        appState.currentFilters = {
            search: '',
            status: 'ATIVO',
            tem_tvi: '',
            tem_divida: ''
        };
        appState.currentPage = 1;
        
        // Mostrar botão limpar filtros
        const clearBtn = document.getElementById('clearFiltersBtn');
        if (clearBtn) clearBtn.classList.remove('hidden');
        
        loadConsultas();
    }
}

export function filterByComDividas() {
    // Limpar outros filtros
    const searchFilter = document.getElementById('searchFilter');
    const statusFilter = document.getElementById('statusFilter');
    const tviFilter = document.getElementById('tviFilter');
    const dividaFilter = document.getElementById('dividaFilter');
    
    if (searchFilter) searchFilter.value = '';
    if (statusFilter) statusFilter.value = '';
    if (tviFilter) tviFilter.value = '';
    
    // Verificar se já está filtrando por dívidas
    const dividaAtual = dividaFilter ? dividaFilter.value : '';
    
    if (dividaAtual === 'SIM') {
        // Se já está filtrando por dívidas, limpar filtro
        clearFilters();
    } else {
        // Aplicar filtro de com dívidas
        if (dividaFilter) dividaFilter.value = 'SIM';
        
        appState.currentFilters = {
            search: '',
            status: '',
            tem_tvi: '',
            tem_divida: 'SIM'
        };
        appState.currentPage = 1;
        
        // Mostrar botão limpar filtros
        const clearBtn = document.getElementById('clearFiltersBtn');
        if (clearBtn) clearBtn.classList.remove('hidden');
        
        loadConsultas();
    }
}

export function filterByInativas() {
    // Limpar outros filtros
    const searchFilter = document.getElementById('searchFilter');
    const statusFilter = document.getElementById('statusFilter');
    const tviFilter = document.getElementById('tviFilter');
    const dividaFilter = document.getElementById('dividaFilter');
    
    if (searchFilter) searchFilter.value = '';
    if (tviFilter) tviFilter.value = '';
    if (dividaFilter) dividaFilter.value = '';
    
    // Verificar se já está filtrando por não ativas
    const statusAtual = statusFilter ? statusFilter.value : '';
    
    if (statusAtual && statusAtual !== 'ATIVO') {
        // Se já está filtrando por não ativas, limpar todos os filtros
        if (statusFilter) statusFilter.value = '';
        clearFilters();
    } else {
        // Aplicar filtro de não ativas
        // Como o backend não tem um filtro específico para "não ativas",
        // vamos usar "SUSPENSO DE OFICIO" como exemplo
        // Idealmente, o backend deveria suportar filtro "!ATIVO"
        if (statusFilter) {
            // Selecionar "Suspenso de Ofício" como representante dos não ativos
            statusFilter.value = 'SUSPENSO DE OFICIO';
        }
        
        appState.currentFilters = {
            search: '',
            status: 'SUSPENSO DE OFICIO',
            tem_tvi: '',
            tem_divida: ''
        };
        appState.currentPage = 1;
        
        // Mostrar botão limpar filtros
        const clearBtn = document.getElementById('clearFiltersBtn');
        if (clearBtn) clearBtn.classList.remove('hidden');
        
        loadConsultas();
    }
}
