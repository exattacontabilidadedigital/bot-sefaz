// Módulo de Dashboard - Atualização de estatísticas e métricas
import * as api from './api.js';

// Cache para evitar requisições desnecessárias
let dashboardCache = {
    data: null,
    lastUpdate: 0,
    cacheTimeout: 30000 // 30 segundos
};

// Elementos do dashboard
const dashboardElements = {
    totalConsultas: document.getElementById('totalConsultas'),
    consultasAtivas: document.getElementById('consultasAtivas'),
    consultasSuspensas: document.getElementById('consultasSuspensas'),
    consultasComDivida: document.getElementById('consultasComDivida'),
    ultimaAtualizacao: document.getElementById('ultimaAtualizacao')
};

// Função principal para atualizar dashboard
export async function updateDashboard() {
    try {
        console.log('📊 Atualizando dashboard...');
        
        // Verificar cache
        const now = Date.now();
        if (dashboardCache.data && (now - dashboardCache.lastUpdate) < dashboardCache.cacheTimeout) {
            console.log('📊 Usando dados do cache');
            renderDashboard(dashboardCache.data);
            return dashboardCache.data;
        }
        
        // Buscar dados das estatísticas
        const stats = await api.fetchEstatatisticas();
        console.log('📊 Dados recebidos:', stats);
        
        if (stats) {
            // Atualizar cache
            dashboardCache.data = stats;
            dashboardCache.lastUpdate = now;
            
            // Renderizar dashboard
            renderDashboard(stats);
            
            console.log('✅ Dashboard atualizado com sucesso');
            return stats;
        }
        
    } catch (error) {
        console.error('❌ Erro ao atualizar dashboard:', error);
        showDashboardError();
    }
}

// Renderizar dados no dashboard
function renderDashboard(stats) {
    try {
        // Total de consultas
        if (dashboardElements.totalConsultas) {
            dashboardElements.totalConsultas.textContent = formatNumber(stats.total_consultas || 0);
        }
        
        // Consultas ativas
        if (dashboardElements.consultasAtivas) {
            dashboardElements.consultasAtivas.textContent = formatNumber(stats.consultas_ativas || 0);
        }
        
        // Consultas suspensas
        if (dashboardElements.consultasSuspensas) {
            dashboardElements.consultasSuspensas.textContent = formatNumber(stats.consultas_suspensas || 0);
        }
        
        // Consultas com dívida
        if (dashboardElements.consultasComDivida) {
            dashboardElements.consultasComDivida.textContent = formatNumber(stats.consultas_com_divida || 0);
        }
        
        // Última atualização
        if (dashboardElements.ultimaAtualizacao) {
            dashboardElements.ultimaAtualizacao.textContent = formatDateTime(new Date());
        }
        
        // Atualizar indicadores visuais
        updateVisualIndicators(stats);
        
    } catch (error) {
        console.error('❌ Erro ao renderizar dashboard:', error);
    }
}

// Atualizar indicadores visuais (cores, ícones, etc.)
function updateVisualIndicators(stats) {
    try {
        // Calcular percentuais
        const total = stats.total_consultas || 0;
        const ativas = stats.consultas_ativas || 0;
        const suspensas = stats.consultas_suspensas || 0;
        const comDivida = stats.consultas_com_divida || 0;
        
        const percentAtivas = total > 0 ? (ativas / total) * 100 : 0;
        const percentSuspensas = total > 0 ? (suspensas / total) * 100 : 0;
        const percentComDivida = total > 0 ? (comDivida / total) * 100 : 0;
        
        // Atualizar classes CSS baseadas nos percentuais
        updateCardStatus('totalConsultas', total > 0 ? 'success' : 'neutral');
        updateCardStatus('consultasAtivas', percentAtivas > 70 ? 'success' : percentAtivas > 30 ? 'warning' : 'danger');
        updateCardStatus('consultasSuspensas', percentSuspensas < 30 ? 'success' : percentSuspensas < 60 ? 'warning' : 'danger');
        updateCardStatus('consultasComDivida', percentComDivida < 20 ? 'success' : percentComDivida < 50 ? 'warning' : 'danger');
        
    } catch (error) {
        console.error('❌ Erro ao atualizar indicadores visuais:', error);
    }
}

// Atualizar status visual de um card
function updateCardStatus(cardId, status) {
    const card = document.getElementById(`${cardId}Card`) || document.querySelector(`[data-card="${cardId}"]`);
    if (!card) return;
    
    // Remover classes anteriores
    card.classList.remove('border-green-200', 'border-yellow-200', 'border-red-200', 'border-gray-200');
    card.classList.remove('bg-green-50', 'bg-yellow-50', 'bg-red-50', 'bg-gray-50');
    
    // Adicionar novas classes baseadas no status
    switch (status) {
        case 'success':
            card.classList.add('border-green-200', 'bg-green-50');
            break;
        case 'warning':
            card.classList.add('border-yellow-200', 'bg-yellow-50');
            break;
        case 'danger':
            card.classList.add('border-red-200', 'bg-red-50');
            break;
        default:
            card.classList.add('border-gray-200', 'bg-gray-50');
    }
}

// Mostrar erro no dashboard
function showDashboardError() {
    const errorMessage = 'Erro ao carregar dados';
    
    Object.values(dashboardElements).forEach(element => {
        if (element && element.textContent !== null) {
            element.textContent = '--';
            element.classList.add('text-red-500');
        }
    });
    
    if (dashboardElements.ultimaAtualizacao) {
        dashboardElements.ultimaAtualizacao.textContent = errorMessage;
        dashboardElements.ultimaAtualizacao.classList.add('text-red-500');
    }
}

// Formatação de números
function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '0';
    
    // Para números grandes, usar formatação com separadores
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    
    return num.toLocaleString('pt-BR');
}

// Formatação de data/hora
function formatDateTime(date) {
    if (!date || !(date instanceof Date)) return '';
    
    return new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// Limpar cache do dashboard
export function clearDashboardCache() {
    dashboardCache.data = null;
    dashboardCache.lastUpdate = 0;
    console.log('🗑️ Cache do dashboard limpo');
}

// Inicializar dashboard
export function initDashboard() {
    console.log('📊 Inicializando dashboard...');
    
    // Atualização inicial
    updateDashboard();
    
    // Atualização periódica a cada 60 segundos
    setInterval(updateDashboard, 60000);
    
    console.log('✅ Dashboard inicializado');
}

// Auto-atualização quando dados mudam
export function triggerDashboardUpdate() {
    clearDashboardCache();
    updateDashboard();
}

// Configurar intervalo de atualização
export function setUpdateInterval(seconds) {
    dashboardCache.cacheTimeout = seconds * 1000;
    console.log(`📊 Intervalo de atualização definido para ${seconds} segundos`);
}

// Obter dados atuais do cache
export function getDashboardData() {
    return dashboardCache.data;
}

// Verificar se dashboard está carregado
export function isDashboardLoaded() {
    return dashboardCache.data !== null;
}