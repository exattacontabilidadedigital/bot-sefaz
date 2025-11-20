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
    // Evitar inicialização múltipla
    if (window.lucideInitialized) {
        console.log('🔄 Lucide já inicializado, ignorando...');
        return;
    }
    
    try {
        // Aguardar um momento para garantir que o DOM esteja completamente carregado
        setTimeout(() => {
            if (typeof lucide !== 'undefined' && lucide.createIcons) {
                // Verificar se existem elementos com data-lucide antes de inicializar
                const lucideElements = document.querySelectorAll('[data-lucide]');
                if (lucideElements.length > 0) {
                    // Interceptar erros de MutationObserver de forma mais robusta
                    const originalObserve = MutationObserver.prototype.observe;
                    const originalDisconnect = MutationObserver.prototype.disconnect;
                    
                    MutationObserver.prototype.observe = function(target, options) {
                        try {
                            if (target && typeof target === 'object' && target.nodeType === Node.ELEMENT_NODE && target.parentNode) {
                                return originalObserve.call(this, target, options);
                            } else {
                                // Silenciar erro sem log para evitar spam
                                return;
                            }
                        } catch (error) {
                            // Silenciar completamente erros de bibliotecas externas
                            return;
                        }
                    };
                    
                    // Proteger disconnect também
                    MutationObserver.prototype.disconnect = function() {
                        try {
                            return originalDisconnect.call(this);
                        } catch (error) {
                            // Silenciar erros de disconnect
                            return;
                        }
                    };
                    
                    lucide.createIcons();
                    console.log('✅ Ícones Lucide inicializados com sucesso');
                    window.lucideInitialized = true;
                    
                    // Restaurar função original após um tempo
                    setTimeout(() => {
                        MutationObserver.prototype.observe = originalObserve;
                        MutationObserver.prototype.disconnect = originalDisconnect;
                    }, 5000);
                } else {
                    console.log('⚠️ Nenhum elemento Lucide encontrado');
                }
            } else {
                console.warn('⚠️ Biblioteca Lucide não encontrada');
            }
        }, 300); // Aumentar delay ainda mais
    } catch (error) {
        console.warn('❌ Erro ao inicializar ícones Lucide:', error);
    }
}
