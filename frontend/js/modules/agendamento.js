// Módulo de UI - Agendamentos
import { appState } from './state.js';
import * as api from './api.js';
import * as utils from './utils.js';

export function initAgendamento() {
    // Configurar data mínima (5 minutos a partir de agora)
    const now = new Date();
    const minDate = new Date(now.getTime() + 5 * 60 * 1000); // 5 minutos a partir de agora
    document.getElementById('dataAgendada').min = minDate.toISOString().slice(0, 16);
    
    // Event listeners
    setupEventListeners();
    
    // Carregar empresas para seleção
    loadEmpresasParaAgendamento();
    
    // Carregar agendamentos existentes
    loadAgendamentos();
}

function setupEventListeners() {
    // Toggle do formulário de agendamento
    document.getElementById('toggleAgendamentoBtn').addEventListener('click', toggleAgendamentoForm);
    
    // Cancelar formulário
    document.getElementById('cancelAgendamentoBtn').addEventListener('click', hideAgendamentoForm);
    
    // Submit do formulário
    document.getElementById('scheduleForm').addEventListener('submit', handleCreateAgendamento);
    
    // Seleção de empresas
    document.getElementById('selectAllEmpresasBtn').addEventListener('click', selectAllEmpresas);
    document.getElementById('clearSelectionBtn').addEventListener('click', clearEmpresaSelection);
    
    // Refresh de agendamentos
    document.getElementById('refreshAgendamentosBtn').addEventListener('click', loadAgendamentos);
    
    // Visualização de calendário
    document.getElementById('viewCalendarBtn').addEventListener('click', showCalendarView);
    document.getElementById('backToListBtn').addEventListener('click', showListView);
    
    // Navegação do calendário
    document.getElementById('calendarioPrevBtn').addEventListener('click', () => navigateCalendar(-1));
    document.getElementById('calendarioNextBtn').addEventListener('click', () => navigateCalendar(1));
    document.getElementById('calendarioHojeBtn').addEventListener('click', goToToday);
}

function toggleAgendamentoForm() {
    const form = document.getElementById('agendamentoForm');
    const btn = document.getElementById('toggleAgendamentoBtn');
    const icon = btn.querySelector('i[data-lucide]');
    
    if (form.classList.contains('hidden')) {
        form.classList.remove('hidden');
        btn.innerHTML = '<i data-lucide="minus" class="h-4 w-4 mr-2"></i>Fechar';
        utils.initLucideIcons();
        loadEmpresasParaAgendamento(); // Carregar empresas quando abrir
    } else {
        hideAgendamentoForm();
    }
}

function hideAgendamentoForm() {
    document.getElementById('agendamentoForm').classList.add('hidden');
    const btn = document.getElementById('toggleAgendamentoBtn');
    btn.innerHTML = '<i data-lucide="plus" class="h-4 w-4 mr-2"></i>Criar Agendamento';
    utils.initLucideIcons();
    
    // Limpar formulário
    document.getElementById('scheduleForm').reset();
    clearEmpresaSelection();
}

async function loadEmpresasParaAgendamento() {
    try {
        const empresas = await api.fetchEmpresas(1000, 0); // Buscar muitas empresas
        renderEmpresasList(empresas);
    } catch (error) {
        console.error('Erro ao carregar empresas:', error);
        utils.showNotification('Erro ao carregar empresas', 'error');
    }
}

function renderEmpresasList(empresas) {
    const container = document.getElementById('empresasListAgendamento');
    
    if (!empresas || empresas.length === 0) {
        container.innerHTML = '<p class="p-4 text-gray-500">Nenhuma empresa encontrada</p>';
        return;
    }
    
    container.innerHTML = empresas.map(empresa => `
        <div class="flex items-center p-3 border-b border-gray-200 hover:bg-gray-50">
            <input type="checkbox" 
                   id="empresa_${empresa.id}" 
                   value="${empresa.id}"
                   class="empresa-checkbox h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500">
            <label for="empresa_${empresa.id}" class="ml-3 flex-1 cursor-pointer">
                <div class="text-sm font-medium text-gray-900">${empresa.nome_empresa}</div>
                <div class="text-xs text-gray-500">
                    CNPJ: ${utils.formatCNPJ(empresa.cnpj)} | IE: ${empresa.inscricao_estadual}
                </div>
            </label>
        </div>
    `).join('');
    
    // Adicionar event listeners para contagem
    const checkboxes = container.querySelectorAll('.empresa-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedCount);
    });
    
    updateSelectedCount();
}

function selectAllEmpresas() {
    const checkboxes = document.querySelectorAll('.empresa-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    updateSelectedCount();
}

function clearEmpresaSelection() {
    const checkboxes = document.querySelectorAll('.empresa-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    updateSelectedCount();
}

function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('.empresa-checkbox:checked');
    const count = checkboxes.length;
    document.getElementById('selectedCountAgendamento').textContent = 
        `${count} empresa${count !== 1 ? 's' : ''} selecionada${count !== 1 ? 's' : ''}`;
}

async function handleCreateAgendamento(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const selectedEmpresas = Array.from(document.querySelectorAll('.empresa-checkbox:checked'))
        .map(checkbox => parseInt(checkbox.value));
    
    if (selectedEmpresas.length === 0) {
        utils.showNotification('Selecione pelo menos uma empresa', 'error');
        return;
    }
    
    // Validar data/hora mínima (5 minutos no futuro)
    const dataAgendada = new Date(formData.get('dataAgendada'));
    const agora = new Date();
    const cincoMinutosNoFuturo = new Date(agora.getTime() + 5 * 60 * 1000);
    
    if (dataAgendada < cincoMinutosNoFuturo) {
        utils.showNotification('O agendamento deve ser pelo menos 5 minutos no futuro', 'error');
        return;
    }
    
    const data = {
        empresa_ids: selectedEmpresas,
        data_agendada: formData.get('dataAgendada'),
        recorrencia: formData.get('recorrencia'),
        prioridade: parseInt(formData.get('prioridade')),
        ativo: true
    };
    
    try {
        const btn = document.getElementById('createAgendamentoBtn');
        btn.disabled = true;
        btn.innerHTML = '<i data-lucide="loader-2" class="h-4 w-4 mr-2 animate-spin"></i>Criando...';
        utils.initLucideIcons();
        
        const result = await api.criarAgendamento(data);
        
        utils.showNotification(result.message, 'success');
        hideAgendamentoForm();
        loadAgendamentos();
        
        // Recarregar fila para mostrar novos jobs
        if (window.filaUI && window.filaUI.loadFila) {
            window.filaUI.loadFila();
        }
        
    } catch (error) {
        console.error('Erro ao criar agendamento:', error);
        utils.showNotification(error.message, 'error');
    } finally {
        const btn = document.getElementById('createAgendamentoBtn');
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="calendar-plus" class="h-4 w-4 mr-2"></i>Criar Agendamento';
        utils.initLucideIcons();
    }
}

async function loadAgendamentos() {
    try {
        const agendamentos = await api.fetchAgendamentos(20, 0, true, true);
        renderAgendamentosList(agendamentos);
    } catch (error) {
        console.error('Erro ao carregar agendamentos:', error);
        utils.showNotification('Erro ao carregar agendamentos', 'error');
    }
}

function renderAgendamentosList(agendamentos) {
    const container = document.getElementById('agendamentosList');
    
    if (!agendamentos || agendamentos.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i data-lucide="calendar-x" class="h-12 w-12 mx-auto mb-3 text-gray-400"></i>
                <p>Nenhum agendamento encontrado</p>
            </div>
        `;
        utils.initLucideIcons();
        return;
    }
    
    container.innerHTML = agendamentos.map(agendamento => `
        <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg bg-white hover:shadow-sm transition-shadow">
            <div class="flex-1">
                <div class="flex items-center space-x-3">
                    <div class="flex-shrink-0">
                        <i data-lucide="calendar-clock" class="h-5 w-5 text-purple-600"></i>
                    </div>
                    <div>
                        <div class="text-sm font-medium text-gray-900">
                            ${agendamento.nome_empresa || 'Empresa não encontrada'}
                        </div>
                        <div class="text-xs text-gray-500">
                            IE: ${agendamento.inscricao_estadual} | ${utils.formatRecorrencia(agendamento.recorrencia)}
                        </div>
                    </div>
                </div>
                <div class="mt-2 text-sm text-gray-600">
                    <i data-lucide="clock" class="h-4 w-4 inline mr-1"></i>
                    ${utils.formatDateTime(agendamento.data_agendada)}
                </div>
            </div>
            <div class="flex items-center space-x-2">
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                    ${agendamento.status === 'pending' ? 'Agendado' : agendamento.status}
                </span>
                ${agendamento.status === 'pending' ? `
                    <button onclick="editarAgendamento(${agendamento.id})" 
                            class="text-blue-600 hover:text-blue-800 p-1"
                            title="Editar">
                        <i data-lucide="edit-3" class="h-4 w-4"></i>
                    </button>
                    <button onclick="cancelarAgendamentoConfirm(${agendamento.id})" 
                            class="text-red-600 hover:text-red-800 p-1"
                            title="Cancelar">
                        <i data-lucide="x-circle" class="h-4 w-4"></i>
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
    
    utils.initLucideIcons();
}

async function editarAgendamento(jobId) {
    // TODO: Implementar modal de edição
    utils.showNotification('Funcionalidade de edição em desenvolvimento', 'info');
}

async function cancelarAgendamentoConfirm(jobId) {
    if (!confirm('Tem certeza que deseja cancelar este agendamento?')) {
        return;
    }
    
    try {
        await api.cancelarAgendamento(jobId);
        utils.showNotification('Agendamento cancelado com sucesso', 'success');
        loadAgendamentos();
        
        // Recarregar fila
        if (window.filaUI && window.filaUI.loadFila) {
            window.filaUI.loadFila();
        }
    } catch (error) {
        console.error('Erro ao cancelar agendamento:', error);
        utils.showNotification(error.message, 'error');
    }
}

// Exportar funções globais
window.editarAgendamento = editarAgendamento;
window.cancelarAgendamentoConfirm = cancelarAgendamentoConfirm;

// Estado do calendário
let currentCalendarDate = new Date();
let calendarAgendamentos = [];

function showCalendarView() {
    document.getElementById('agendamentosList').classList.add('hidden');
    document.getElementById('calendarioView').classList.remove('hidden');
    loadCalendarAgendamentos();
}

function showListView() {
    document.getElementById('calendarioView').classList.add('hidden');
    document.getElementById('agendamentosList').classList.remove('hidden');
}

function navigateCalendar(direction) {
    currentCalendarDate.setMonth(currentCalendarDate.getMonth() + direction);
    renderCalendar();
}

function goToToday() {
    currentCalendarDate = new Date();
    renderCalendar();
}

async function loadCalendarAgendamentos() {
    try {
        // Buscar agendamentos de 3 meses (atual + próximos 2)
        const agendamentos = await api.fetchAgendamentos(1000, 0, true, false);
        calendarAgendamentos = agendamentos;
        renderCalendar();
    } catch (error) {
        console.error('Erro ao carregar agendamentos do calendário:', error);
        utils.showNotification('Erro ao carregar calendário', 'error');
    }
}

function renderCalendar() {
    const year = currentCalendarDate.getFullYear();
    const month = currentCalendarDate.getMonth();
    
    // Atualizar título
    const monthNames = [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];
    document.getElementById('calendarioMesAno').textContent = `${monthNames[month]} ${year}`;
    
    // Gerar grid do calendário
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const firstDayWeek = firstDay.getDay();
    const daysInMonth = lastDay.getDate();
    
    const grid = document.getElementById('calendarioGrid');
    
    // Cabeçalhos dos dias
    const dayHeaders = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
    let gridHTML = '';
    
    // Adicionar cabeçalhos
    dayHeaders.forEach(day => {
        gridHTML += `<div class="text-center text-xs font-medium text-gray-500 p-2 bg-gray-100">${day}</div>`;
    });
    
    // Adicionar dias vazios do início
    for (let i = 0; i < firstDayWeek; i++) {
        gridHTML += '<div class="p-2"></div>';
    }
    
    // Adicionar dias do mês
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dateStr = date.toISOString().split('T')[0];
        const agendamentosNoDia = getAgendamentosNoDia(dateStr);
        const isToday = isDateToday(date);
        
        let dayClass = 'p-2 border border-gray-200 min-h-[80px] hover:bg-gray-50 cursor-pointer';
        if (isToday) {
            dayClass += ' bg-blue-50 border-blue-300';
        }
        
        gridHTML += `
            <div class="${dayClass}" title="${agendamentosNoDia.length} agendamento(s)">
                <div class="text-sm font-medium ${isToday ? 'text-blue-800' : 'text-gray-900'}">${day}</div>
                <div class="space-y-1 mt-1">
                    ${agendamentosNoDia.slice(0, 3).map(agendamento => `
                        <div class="text-xs bg-purple-100 text-purple-800 px-1 py-0.5 rounded truncate" 
                             title="${agendamento.nome_empresa} - ${utils.formatDateTime(agendamento.data_agendada)}">
                            ${(agendamento.nome_empresa || 'Empresa').substring(0, 12)}${(agendamento.nome_empresa || 'Empresa').length > 12 ? '...' : ''}
                        </div>
                    `).join('')}
                    ${agendamentosNoDia.length > 3 ? `
                        <div class="text-xs text-gray-600">+${agendamentosNoDia.length - 3} mais</div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    grid.innerHTML = gridHTML;
    utils.initLucideIcons();
}

function getAgendamentosNoDia(dateStr) {
    return calendarAgendamentos.filter(agendamento => {
        if (!agendamento.data_agendada) return false;
        const agendamentoDate = new Date(agendamento.data_agendada).toISOString().split('T')[0];
        return agendamentoDate === dateStr;
    });
}

function isDateToday(date) {
    const today = new Date();
    return date.toDateString() === today.toDateString();
}

export { editarAgendamento, cancelarAgendamentoConfirm };