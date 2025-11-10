// Módulo de UI - Fila de Processamento
import { appState } from './state.js';
import * as api from './api.js';
import * as utils from './utils.js';

// Funções de filtro por status
let filaStatusFilter = null;

export async function loadFila() {
    try {
        // Usar applyFilaFilters para respeitar o filtro ativo
        await applyFilaFilters();
    } catch (error) {
        console.error('Erro ao buscar fila:', error);
        utils.showNotification('Erro ao carregar fila', 'error');
    }
}

function updateFilaTable() {
    const tbody = document.getElementById('filaTable');
    const emptyState = document.getElementById('filaEmptyState');
    
    if (appState.filaData.length === 0) {
        if (tbody) tbody.innerHTML = '';
        if (emptyState) emptyState.classList.remove('hidden');
        return;
    }
    
    if (emptyState) emptyState.classList.add('hidden');
    
    if (tbody) {
        // Calcular índices de paginação
        const startIndex = (appState.filaCurrentPage - 1) * appState.filaItemsPerPage;
        const endIndex = startIndex + appState.filaItemsPerPage;
        const jobsPaginados = appState.filaData.slice(startIndex, endIndex);
        
        tbody.innerHTML = jobsPaginados.map(job => `
            <tr>
                <td class="px-6 py-4">
                    <div class="text-sm font-medium text-gray-900">${job.nome_empresa || 'N/A'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${utils.formatCNPJ(job.cnpj)}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${job.inscricao_estadual || 'N/A'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${utils.getJobStatusBadge(job.status)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-500">${utils.formatDateTime(job.data_adicao)}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-500">
                        ${job.data_processamento ? utils.formatDateTime(job.data_processamento) : '-'}
                    </div>
                </td>
                <td class="px-6 py-4">
                    <div class="text-sm text-gray-500">${job.erro || '-'}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    ${job.status === 'pending' ? `
                        <button onclick="window.filaUI.removeFromQueue(${job.id})" 
                                class="text-red-600 hover:text-red-900 mr-2"
                                title="Deletar">
                            <i data-lucide="trash-2" class="h-4 w-4"></i>
                        </button>
                    ` : ''}
                    ${job.status === 'running' ? `
                        <button onclick="window.filaUI.cancelJob(${job.id})" 
                                class="text-orange-600 hover:text-orange-900"
                                title="Cancelar">
                            <i data-lucide="x-circle" class="h-4 w-4"></i>
                        </button>
                    ` : ''}
                </td>
            </tr>
        `).join('');
        
        utils.initLucideIcons();
    }
}

export async function loadFilaStats() {
    try {
        const stats = await api.fetchFilaStats();
        
        const elements = {
            totalFila: document.getElementById('totalFila'),
            pendentes: document.getElementById('filaPendentes'),
            processando: document.getElementById('filaProcessando'),
            concluidos: document.getElementById('filaConcluidos'),
            falhas: document.getElementById('filaFalhas')
        };
        
        if (elements.totalFila) elements.totalFila.textContent = stats.total;
        if (elements.pendentes) elements.pendentes.textContent = stats.pendente || 0;
        if (elements.processando) elements.processando.textContent = stats.processando || 0;
        if (elements.concluidos) elements.concluidos.textContent = stats.concluido || 0;
        if (elements.falhas) elements.falhas.textContent = stats.erro || 0;
        
    } catch (error) {
        console.error('Erro ao buscar estatísticas da fila:', error);
    }
}

export async function removeFromQueue(jobId) {
    if (!confirm('Tem certeza que deseja remover este item da fila?')) {
        return;
    }
    
    try {
        await api.deletarJob(jobId);
        await loadFila();
        utils.showNotification('Item removido da fila', 'success');
    } catch (error) {
        console.error('Erro ao remover da fila:', error);
        utils.showNotification(error.message || 'Erro ao remover da fila', 'error');
    }
}

export async function cancelJob(jobId) {
    if (!confirm('Tem certeza que deseja cancelar este job em execução?')) {
        return;
    }
    
    try {
        await api.cancelarJob(jobId);
        await loadFila();
        utils.showNotification('Job cancelado com sucesso', 'success');
    } catch (error) {
        console.error('Erro ao cancelar job:', error);
        utils.showNotification(error.message || 'Erro ao cancelar job', 'error');
    }
}

export async function clearCompletedJobs() {
    if (!confirm('Tem certeza que deseja limpar todos os jobs concluídos?')) {
        return;
    }
    
    try {
        const completedJobs = appState.filaData.filter(job => job.status === 'concluido');
        
        for (const job of completedJobs) {
            await api.deleteFilaJob(job.id);
        }
        
        await loadFila();
        utils.showNotification('Jobs concluídos removidos', 'success');
    } catch (error) {
        console.error('Erro ao limpar jobs concluídos:', error);
        utils.showNotification('Erro ao limpar jobs concluídos', 'error');
    }
}

export async function startProcessing() {
    const startBtn = document.getElementById('startProcessingBtn');
    const stopBtn = document.getElementById('stopProcessingBtn');
    
    if (startBtn) startBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = false;
    
    try {
        await api.iniciarProcessamento();
        utils.showNotification('Processamento iniciado!', 'success');
        
        // Aguardar um pouco e recarregar a fila
        setTimeout(() => loadFila(), 1000);
        
    } catch (error) {
        console.error('Erro ao iniciar processamento:', error);
        utils.showNotification('Erro ao iniciar processamento', 'error');
        
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
    }
}

export async function stopProcessing() {
    const startBtn = document.getElementById('startProcessingBtn');
    const stopBtn = document.getElementById('stopProcessingBtn');
    
    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
    
    try {
        await api.pararProcessamento();
        utils.showNotification('Processamento pausado', 'info');
        
        // Recarregar a fila
        await loadFila();
        
    } catch (error) {
        console.error('Erro ao parar processamento:', error);
        utils.showNotification('Erro ao parar processamento', 'error');
        
        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
    }
}

export async function checkProcessingStatus() {
    try {
        const status = await api.fetchStatusProcessamento();
        
        const startBtn = document.getElementById('startProcessingBtn');
        const stopBtn = document.getElementById('stopProcessingBtn');
        const statusIndicator = document.getElementById('processingStatusIndicator');
        const statusText = document.getElementById('processingStatusText');
        
        if (status.processando) {
            if (startBtn) startBtn.disabled = true;
            if (stopBtn) stopBtn.disabled = false;
            if (statusIndicator) {
                statusIndicator.className = 'h-3 w-3 bg-green-500 rounded-full animate-pulse';
            }
            if (statusText) {
                statusText.textContent = 'Processando';
                statusText.className = 'text-sm font-medium text-green-600';
            }
        } else {
            if (startBtn) startBtn.disabled = false;
            if (stopBtn) stopBtn.disabled = true;
            if (statusIndicator) {
                statusIndicator.className = 'h-3 w-3 bg-gray-400 rounded-full';
            }
            if (statusText) {
                statusText.textContent = 'Pausado';
                statusText.className = 'text-sm font-medium text-gray-600';
            }
        }
        
        return status.processando;
        
    } catch (error) {
        console.error('Erro ao verificar status do processamento:', error);
        return false;
    }
}

export function setupFilaPolling() {
    // Carregar fila imediatamente ao iniciar (sem await para não bloquear)
    loadFila().catch(err => console.error('Erro ao carregar fila inicial:', err));
    
    // Atualizar fila a cada 3 segundos (sempre, não apenas quando na aba fila)
    setInterval(async () => {
        try {
            await loadFila();
            // Só atualiza status se estiver na aba fila (para não fazer requisições desnecessárias)
            if (appState.currentTab === 'fila') {
                await checkProcessingStatus();
            }
        } catch (err) {
            console.error('Erro no polling da fila:', err);
        }
    }, 3000);
}

// Funções de Paginação
function updateFilaPagination() {
    const totalPages = Math.ceil(appState.filaTotalItems / appState.filaItemsPerPage);
    const currentPage = appState.filaCurrentPage;
    
    // Atualizar informações de paginação
    const pageInfo = document.getElementById('filaPageInfo');
    if (pageInfo) {
        const startItem = appState.filaTotalItems === 0 ? 0 : (currentPage - 1) * appState.filaItemsPerPage + 1;
        const endItem = Math.min(currentPage * appState.filaItemsPerPage, appState.filaTotalItems);
        pageInfo.textContent = `Mostrando ${startItem} a ${endItem} de ${appState.filaTotalItems} resultados`;
    }
    
    // Atualizar botões de paginação
    const prevBtn = document.getElementById('filaPrevBtn');
    const nextBtn = document.getElementById('filaNextBtn');
    
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
    const pageNumber = document.getElementById('filaPageNumber');
    if (pageNumber) {
        pageNumber.textContent = `Página ${currentPage} de ${totalPages || 1}`;
    }
}

export function nextFilaPage() {
    const totalPages = Math.ceil(appState.filaTotalItems / appState.filaItemsPerPage);
    if (appState.filaCurrentPage < totalPages) {
        appState.filaCurrentPage++;
        updateFilaTable();
        updateFilaPagination();
    }
}

export function prevFilaPage() {
    if (appState.filaCurrentPage > 1) {
        appState.filaCurrentPage--;
        updateFilaTable();
        updateFilaPagination();
    }
}

export function changeFilaItemsPerPage(itemsPerPage) {
    appState.filaItemsPerPage = parseInt(itemsPerPage);
    appState.filaCurrentPage = 1;
    updateFilaTable();
    updateFilaPagination();
}

// Funções de filtro por status
// (variável já declarada no topo do arquivo)

export function filterByAllStatus() {
    // Toggle: se já está mostrando todos, não faz nada
    if (filaStatusFilter === null) {
        return;
    }
    
    filaStatusFilter = null;
    applyFilaFilters();
    updateFilterIndicators();
    utils.showNotification('Mostrando todos os status', 'info');
}

export async function filterByStatus(status) {
    // Mapear status em português para inglês (como está no banco)
    const statusMap = {
        'pendente': 'pending',
        'processando': 'running',
        'concluido': 'completed',
        'falha': 'failed'
    };
    
    const statusDB = statusMap[status] || status;
    
    // Toggle: se clicar no mesmo status, limpa o filtro
    if (filaStatusFilter === statusDB) {
        filaStatusFilter = null;
        await applyFilaFilters();
        updateFilterIndicators();
        utils.showNotification('Filtro removido', 'info');
        return;
    }
    
    filaStatusFilter = statusDB;
    await applyFilaFilters();
    updateFilterIndicators();
    
    const statusNames = {
        'pending': 'Pendentes',
        'running': 'Processando',
        'completed': 'Concluídos',
        'failed': 'Falhas'
    };
    
    utils.showNotification(`Filtrando por: ${statusNames[statusDB]}`, 'info');
}

function updateFilterIndicators() {
    // Remover classe de filtro ativo de todos os cards
    const allCards = document.querySelectorAll('[onclick^="window.filaUI.filter"]');
    allCards.forEach(card => {
        card.classList.remove('ring-2', 'ring-blue-500');
    });
    
    // Adicionar classe ao card do filtro ativo
    if (filaStatusFilter) {
        const statusMap = {
            'pending': 'pendente',
            'running': 'processando',
            'completed': 'concluido',
            'failed': 'falha'
        };
        const statusPT = statusMap[filaStatusFilter];
        const activeCard = document.querySelector(`[onclick="window.filaUI.filterByStatus('${statusPT}')"]`);
        if (activeCard) {
            activeCard.classList.add('ring-2', 'ring-blue-500');
        }
    }
}

async function applyFilaFilters() {
    try {
        const jobs = await api.fetchFilaJobs();
        
        // Ordenar por data_adicao decrescente (mais recentes primeiro)
        let jobsOrdenados = [...jobs].sort((a, b) => {
            const dateA = new Date(a.data_adicao);
            const dateB = new Date(b.data_adicao);
            return dateB - dateA;
        });
        
        // Aplicar filtro de status se houver
        if (filaStatusFilter) {
            jobsOrdenados = jobsOrdenados.filter(job => job.status === filaStatusFilter);
        }
        
        appState.filaData = jobsOrdenados;
        appState.filaTotalItems = jobsOrdenados.length;
        appState.filaCurrentPage = 1; // Voltar para primeira página
        
        updateFilaTable();
        updateFilaPagination();
        await loadFilaStats(); // Adicionar carregamento das estatísticas
    } catch (error) {
        console.error('Erro ao aplicar filtros:', error);
        utils.showNotification('Erro ao filtrar fila', 'error');
    }
}
