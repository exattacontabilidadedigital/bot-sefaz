// Módulo de Utilitários
export function formatCNPJ(cnpj) {
    if (!cnpj) return '';
    const numbers = cnpj.replace(/\D/g, '');
    if (numbers.length === 14) {
        return numbers.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    }
    return cnpj;
}

export function formatCPF(cpf) {
    if (!cpf) return '';
    const numbers = cpf.replace(/\D/g, '');
    if (numbers.length === 11) {
        return numbers.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
    return cpf;
}

export function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { 
        style: 'currency', 
        currency: 'BRL' 
    }).format(value || 0);
}

export function formatDate(dateString) {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString('pt-BR');
}

export function formatDateTime(dateString) {
    if (!dateString) return '-';
    try {
        const date = new Date(dateString);
        return date.toLocaleString('pt-BR');
    } catch (error) {
        return dateString;
    }
}

export function getStatusBadge(status) {
    if (!status) return '<span class="badge-info">N/A</span>';
    
    if (status === 'ATIVO') {
        return '<span class="badge-success">Ativo</span>';
    } else if (status === 'INATIVO') {
        return '<span class="badge-danger">Inativo</span>';
    } else {
        return `<span class="badge-warning">${status}</span>`;
    }
}

export function getTVIBadge(tem_tvi) {
    if (!tem_tvi) return '<span class="badge-info">N/A</span>';
    
    if (tem_tvi === 'SIM') {
        return '<span class="badge-warning">Sim</span>';
    } else if (tem_tvi === 'NÃO') {
        return '<span class="badge-success">Não</span>';
    } else {
        return `<span class="badge-info">${tem_tvi}</span>`;
    }
}

export function getDividasBadge(tem_divida) {
    if (!tem_divida) return '<span class="badge-info">N/A</span>';
    
    if (tem_divida === 'SIM') {
        return '<span class="badge-danger">Sim</span>';
    } else if (tem_divida === 'NÃO') {
        return '<span class="badge-success">Não</span>';
    } else {
        return `<span class="badge-info">${tem_divida}</span>`;
    }
}

export function getJobStatusBadge(status) {
    switch (status) {
        case 'pending':
            return '<span class="badge-warning">Pendente</span>';
        case 'running':
            return '<span class="badge-info">Executando</span>';
        case 'completed':
            return '<span class="badge-success">Concluído</span>';
        case 'failed':
            return '<span class="badge-danger">Falhou</span>';
        default:
            return `<span class="badge-info">${status}</span>`;
    }
}

export function formatRecorrencia(recorrencia) {
    switch (recorrencia) {
        case 'unica':
            return 'Única';
        case 'diaria':
            return 'Diária';
        case 'semanal':
            return 'Semanal';
        case 'mensal':
            return 'Mensal';
        default:
            return recorrencia || '-';
    }
}

export function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${
        type === 'success' ? 'notification-success' :
        type === 'error' ? 'notification-error' :
        'notification-info'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

export function initLucideIcons() {
    try {
        // Aguardar um momento para garantir que o DOM esteja completamente carregado
        setTimeout(() => {
            if (typeof lucide !== 'undefined' && lucide.createIcons) {
                // Verificar se existem elementos com data-lucide antes de inicializar
                const lucideElements = document.querySelectorAll('[data-lucide]');
                if (lucideElements.length > 0) {
                    // Interceptar erros de MutationObserver para prevenir crashes
                    const originalObserve = MutationObserver.prototype.observe;
                    MutationObserver.prototype.observe = function(target, options) {
                        try {
                            if (target && target.nodeType === Node.ELEMENT_NODE) {
                                return originalObserve.call(this, target, options);
                            } else {
                                console.warn('⚠️ Tentativa de observar elemento inválido ignorada:', target);
                            }
                        } catch (error) {
                            console.warn('⚠️ Erro no MutationObserver ignorado:', error);
                        }
                    };
                    
                    lucide.createIcons();
                    console.log('✅ Ícones Lucide inicializados com sucesso');
                    
                    // Restaurar função original após um tempo
                    setTimeout(() => {
                        MutationObserver.prototype.observe = originalObserve;
                    }, 2000);
                } else {
                    console.log('⚠️ Nenhum elemento Lucide encontrado');
                }
            } else {
                console.warn('⚠️ Biblioteca Lucide não encontrada');
            }
        }, 200); // Aumentar delay para dar mais tempo ao DOM
    } catch (error) {
        console.warn('❌ Erro ao inicializar ícones Lucide:', error);
    }
}
