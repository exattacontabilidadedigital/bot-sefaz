// Módulo de UI - Empresas
import { appState, resetEmpresasFilters, clearSelectedEmpresas } from './state.js';
import * as api from './api.js';
import * as utils from './utils.js';

export async function loadEmpresas() {
    try {
        const empresas = await api.fetchEmpresas(
            appState.empresasItemsPerPage,
            (appState.empresasCurrentPage - 1) * appState.empresasItemsPerPage,
            appState.empresasFilters
        );
        
        const countData = await api.fetchEmpresasCount(appState.empresasFilters);
        appState.empresasTotalItems = countData.total;
        appState.empresasData = empresas;
        
        updateEmpresasTable(empresas);
        updateEmpresasPagination();
        updateSelectionInfo();
        
    } catch (error) {
        console.error('Erro ao buscar empresas:', error);
        utils.showNotification('Erro ao carregar empresas', 'error');
    }
}

function updateEmpresasTable(empresas) {
    const tbody = document.getElementById('empresasTable');
    const emptyState = document.getElementById('empresasEmptyState');
    const totalResults = document.getElementById('empresasTotalResults');
    
    if (totalResults) {
        totalResults.textContent = `${appState.empresasTotalItems} empresa${appState.empresasTotalItems !== 1 ? 's' : ''}`;
    }
    
    if (empresas.length === 0) {
        if (tbody) tbody.innerHTML = '';
        if (emptyState) emptyState.classList.remove('hidden');
        return;
    }
    
    if (emptyState) emptyState.classList.add('hidden');
    
    if (tbody) {
        tbody.innerHTML = empresas.map(empresa => `
            <tr class="${appState.selectedEmpresas.has(empresa.id) ? 'bg-blue-50' : ''}">
                <td class="px-6 py-4 whitespace-nowrap">
                    <input type="checkbox" 
                           class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded empresa-checkbox"
                           data-empresa-id="${empresa.id}"
                           ${appState.selectedEmpresas.has(empresa.id) ? 'checked' : ''}>
                </td>
                <td class="px-6 py-4">
                    <div class="text-sm font-medium text-gray-900">${empresa.nome_empresa || 'N/A'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${utils.formatCNPJ(empresa.cnpj)}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${empresa.inscricao_estadual || 'N/A'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-500">${utils.formatDateTime(empresa.data_criacao)}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div class="flex space-x-2 justify-end">
                        <button onclick="window.empresasUI.editEmpresa(${empresa.id})" 
                                class="text-blue-600 hover:text-blue-900">
                            <i data-lucide="edit" class="h-4 w-4"></i>
                        </button>
                        <button onclick="window.empresasUI.deleteEmpresa(${empresa.id})" 
                                class="text-red-600 hover:text-red-900">
                            <i data-lucide="trash-2" class="h-4 w-4"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
        
        utils.initLucideIcons();
        setupCheckboxListeners();
    }
}

function setupCheckboxListeners() {
    document.querySelectorAll('.empresa-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const empresaId = parseInt(this.dataset.empresaId);
            if (this.checked) {
                appState.selectedEmpresas.add(empresaId);
            } else {
                appState.selectedEmpresas.delete(empresaId);
            }
            updateSelectionInfo();
            const row = this.closest('tr');
            row.classList.toggle('bg-blue-50', this.checked);
        });
    });
}

function updateSelectionInfo() {
    const selectionInfo = document.getElementById('selectionInfo');
    const addToQueueBtn = document.getElementById('addToQueueBtn');
    const selectAllBtn = document.getElementById('selectAllEmpresas');
    
    if (selectionInfo) {
        if (appState.selectedEmpresas.size > 0) {
            selectionInfo.textContent = `${appState.selectedEmpresas.size} empresa${appState.selectedEmpresas.size > 1 ? 's' : ''} selecionada${appState.selectedEmpresas.size > 1 ? 's' : ''}`;
            selectionInfo.classList.remove('hidden');
        } else {
            selectionInfo.classList.add('hidden');
        }
    }
    
    if (addToQueueBtn) {
        addToQueueBtn.disabled = appState.selectedEmpresas.size === 0;
    }
    
    if (selectAllBtn) {
        const visibleEmpresas = appState.empresasData.map(e => e.id);
        const allSelected = visibleEmpresas.length > 0 && 
                           visibleEmpresas.every(id => appState.selectedEmpresas.has(id));
        selectAllBtn.checked = allSelected;
    }
}

function updateEmpresasPagination() {
    const totalPages = Math.ceil(appState.empresasTotalItems / appState.empresasItemsPerPage);
    const currentPage = appState.empresasCurrentPage;
    
    // Atualizar informações de paginação
    const pageInfo = document.getElementById('empresasPageInfo');
    if (pageInfo) {
        const startItem = appState.empresasTotalItems === 0 ? 0 : (currentPage - 1) * appState.empresasItemsPerPage + 1;
        const endItem = Math.min(currentPage * appState.empresasItemsPerPage, appState.empresasTotalItems);
        pageInfo.textContent = `Mostrando ${startItem} a ${endItem} de ${appState.empresasTotalItems} empresas`;
    }
    
    // Atualizar botões de paginação
    const prevBtn = document.getElementById('empresasPrevPageBtn');
    const nextBtn = document.getElementById('empresasNextPageBtn');
    
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
    const pageNumber = document.getElementById('empresasPageNumber');
    if (pageNumber) {
        pageNumber.textContent = `Página ${currentPage} de ${totalPages || 1}`;
    }
}

export function applyEmpresasFilters() {
    const searchInput = document.getElementById('empresasSearchFilter');
    const clearBtn = document.getElementById('clearEmpresasFiltersBtn');
    
    appState.empresasFilters = {
        search: searchInput ? searchInput.value.trim() : ''
    };
    
    appState.empresasCurrentPage = 1;
    loadEmpresas();
    
    if (clearBtn) {
        clearBtn.classList.toggle('hidden', !appState.empresasFilters.search);
    }
}

export function clearEmpresasFilters() {
    const searchInput = document.getElementById('empresasSearchFilter');
    const clearBtn = document.getElementById('clearEmpresasFiltersBtn');
    
    if (searchInput) searchInput.value = '';
    resetEmpresasFilters();
    appState.empresasCurrentPage = 1;
    
    loadEmpresas();
    if (clearBtn) clearBtn.classList.add('hidden');
}

export function selectAllEmpresas(checkbox) {
    const visibleEmpresas = appState.empresasData.map(e => e.id);
    
    if (checkbox.checked) {
        visibleEmpresas.forEach(id => appState.selectedEmpresas.add(id));
    } else {
        visibleEmpresas.forEach(id => appState.selectedEmpresas.delete(id));
    }
    
    updateEmpresasTable(appState.empresasData);
    updateSelectionInfo();
}

export function showAddEmpresaModal() {
    document.getElementById('empresaModalTitle').textContent = 'Nova Empresa';
    document.getElementById('empresaForm').reset();
    document.getElementById('empresaId').value = '';
    document.getElementById('empresaModal').classList.remove('hidden');
}

export function editEmpresa(empresaId) {
    const empresa = appState.empresasData.find(e => e.id === empresaId);
    if (!empresa) return;
    
    document.getElementById('empresaModalTitle').textContent = 'Editar Empresa';
    document.getElementById('empresaId').value = empresa.id;
    document.getElementById('empresaNome').value = empresa.nome_empresa || '';
    document.getElementById('empresaCnpj').value = empresa.cnpj || '';
    document.getElementById('empresaIe').value = empresa.inscricao_estadual || '';
    document.getElementById('empresaCpf').value = empresa.cpf_socio || '';
    document.getElementById('empresaSenha').value = empresa.senha_sefaz || '';
    
    document.getElementById('empresaModal').classList.remove('hidden');
}

export function closeEmpresaModal() {
    document.getElementById('empresaModal').classList.add('hidden');
    document.getElementById('empresaForm').reset();
}

export async function saveEmpresa(event) {
    event.preventDefault();
    
    const empresaId = document.getElementById('empresaId').value;
    const empresaData = {
        nome_empresa: document.getElementById('empresaNome').value.trim(),
        cnpj: document.getElementById('empresaCnpj').value.replace(/\D/g, ''),
        inscricao_estadual: document.getElementById('empresaIe').value.trim(),
        cpf_socio: document.getElementById('empresaCpf').value.replace(/\D/g, ''),
        senha: document.getElementById('empresaSenha').value
    };
    
    try {
        if (empresaId) {
            await api.updateEmpresa(empresaId, empresaData);
            utils.showNotification('Empresa atualizada com sucesso!', 'success');
        } else {
            await api.createEmpresa(empresaData);
            utils.showNotification('Empresa cadastrada com sucesso!', 'success');
        }
        
        closeEmpresaModal();
        await loadEmpresas();
        
    } catch (error) {
        console.error('Erro ao salvar empresa:', error);
        utils.showNotification(error.message || 'Erro ao salvar empresa', 'error');
    }
}

export async function deleteEmpresa(empresaId) {
    if (!confirm('Tem certeza que deseja excluir esta empresa?')) {
        return;
    }
    
    try {
        await api.deleteEmpresa(empresaId);
        await loadEmpresas();
        utils.showNotification('Empresa excluída com sucesso!', 'success');
    } catch (error) {
        console.error('Erro ao excluir empresa:', error);
        utils.showNotification('Erro ao excluir empresa', 'error');
    }
}

export async function addSelectedToQueue() {
    if (appState.selectedEmpresas.size === 0) {
        utils.showNotification('Selecione pelo menos uma empresa', 'warning');
        return;
    }
    
    try {
        const empresaIds = Array.from(appState.selectedEmpresas);
        await api.adicionarEmpresasNaFila(empresaIds);
        
        clearSelectedEmpresas();
        updateSelectionInfo();
        updateEmpresasTable(appState.empresasData);
        
        utils.showNotification(
            `${empresaIds.length} empresa${empresaIds.length > 1 ? 's' : ''} adicionada${empresaIds.length > 1 ? 's' : ''} à fila!`,
            'success'
        );
        
        // Trocar para aba da fila
        if (window.tabsUI && window.tabsUI.switchTab) {
            window.tabsUI.switchTab('fila');
        }
        
    } catch (error) {
        console.error('Erro ao adicionar empresas na fila:', error);
        utils.showNotification('Erro ao adicionar empresas na fila', 'error');
    }
}

export function nextEmpresasPage() {
    const totalPages = Math.ceil(appState.empresasTotalItems / appState.empresasItemsPerPage);
    if (appState.empresasCurrentPage < totalPages) {
        appState.empresasCurrentPage++;
        loadEmpresas();
    }
}

export function prevEmpresasPage() {
    if (appState.empresasCurrentPage > 1) {
        appState.empresasCurrentPage--;
        loadEmpresas();
    }
}

export function changeEmpresasItemsPerPage(itemsPerPage) {
    appState.empresasItemsPerPage = parseInt(itemsPerPage);
    appState.empresasCurrentPage = 1;
    loadEmpresas();
}
