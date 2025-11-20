// Módulo de API - Requisições HTTP
const API_BASE_URL = '/api';

export async function fetchEstatatisticas() {
    const response = await fetch(`${API_BASE_URL}/estatisticas`);
    return await response.json();
}

export async function fetchConsultas(limit, offset, filters = {}) {
    const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString()
    });
    
    if (filters.search) params.append('search', filters.search);
    if (filters.status) params.append('status', filters.status);
    if (filters.tem_tvi) params.append('tem_tvi', filters.tem_tvi);
    if (filters.tem_divida) params.append('tem_divida', filters.tem_divida);
    
    const response = await fetch(`${API_BASE_URL}/consultas?${params}`);
    return await response.json();
}

export async function fetchConsultasCount(filters = {}) {
    const params = new URLSearchParams();
    if (filters.search) params.append('search', filters.search);
    if (filters.status) params.append('status', filters.status);
    if (filters.tem_tvi) params.append('tem_tvi', filters.tem_tvi);
    if (filters.tem_divida) params.append('tem_divida', filters.tem_divida);
    
    const response = await fetch(`${API_BASE_URL}/consultas/count?${params}`);
    return await response.json();
}

export async function deleteConsulta(consultaId) {
    const response = await fetch(`${API_BASE_URL}/consultas/${consultaId}`, {
        method: 'DELETE'
    });
    return response.ok;
}

export async function fetchEmpresas(limit, offset, filters = {}) {
    const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString()
    });
    
    if (filters.search) params.append('search', filters.search);
    
    const response = await fetch(`${API_BASE_URL}/empresas?${params}`);
    return await response.json();
}

export async function fetchEmpresasCount(filters = {}) {
    const params = new URLSearchParams();
    if (filters.search) params.append('search', filters.search);
    
    const response = await fetch(`${API_BASE_URL}/empresas/count?${params}`);
    return await response.json();
}

export async function createEmpresa(empresaData) {
    const response = await fetch(`${API_BASE_URL}/empresas`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(empresaData)
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao criar empresa');
    }
    
    return await response.json();
}

export async function updateEmpresa(empresaId, empresaData) {
    const response = await fetch(`${API_BASE_URL}/empresas/${empresaId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(empresaData)
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao atualizar empresa');
    }
    
    return await response.json();
}

export async function deleteEmpresa(empresaId) {
    const response = await fetch(`${API_BASE_URL}/empresas/${empresaId}`, {
        method: 'DELETE'
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao excluir empresa');
    }
    
    return response.ok;
}

export async function importarEmpresasCSV(empresas) {
    const response = await fetch(`${API_BASE_URL}/empresas/importar-csv`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ empresas })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao importar empresas');
    }
    
    return await response.json();
}

export async function adicionarEmpresasNaFila(empresaIds, prioridade = 0) {
    const response = await fetch(`${API_BASE_URL}/fila/adicionar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            empresa_ids: empresaIds,
            prioridade: prioridade
        })
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao adicionar à fila');
    }
    
    return await response.json();
}

export async function fetchFilaJobs(limit = 50, offset = 0) {
    const response = await fetch(`${API_BASE_URL}/fila?limit=${limit}&offset=${offset}`);
    return await response.json();
}

export async function fetchFilaStats() {
    const response = await fetch(`${API_BASE_URL}/fila/stats`);
    return await response.json();
}

export async function fetchStatus() {
    const response = await fetch(`${API_BASE_URL}/status`);
    return await response.json();
}

export async function executarConsulta(data) {
    // Adicionar configuração de headless do localStorage
    const headlessMode = localStorage.getItem('headless_mode');
    const payload = {
        ...data,
        headless: headlessMode === 'true' || headlessMode === null // true por padrão
    };
    
    const response = await fetch(`${API_BASE_URL}/consulta`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao executar consulta');
    }
    
    return await response.json();
}

// Função genérica para requisições GET
export async function get(url) {
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Função genérica para requisições POST
export async function post(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

// Controle de processamento da fila
export async function iniciarProcessamento() {
    const response = await fetch(`${API_BASE_URL}/fila/iniciar`, {
        method: 'POST'
    });
    return await response.json();
}

export async function pararProcessamento() {
    const response = await fetch(`${API_BASE_URL}/fila/parar`, {
        method: 'POST'
    });
    return await response.json();
}

export async function fetchStatusProcessamento() {
    const response = await fetch(`${API_BASE_URL}/fila/status`);
    return await response.json();
}

export async function deletarJob(jobId) {
    const response = await fetch(`${API_BASE_URL}/fila/${jobId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao deletar job');
    }
    return await response.json();
}

export async function cancelarJob(jobId) {
    const response = await fetch(`${API_BASE_URL}/fila/cancelar/${jobId}`, {
        method: 'POST'
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao cancelar job');
    }
    return await response.json();
}

// Funções de Agendamento
export async function criarAgendamento(data) {
    const response = await fetch(`${API_BASE_URL}/agendamentos`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao criar agendamento');
    }
    return await response.json();
}

export async function fetchAgendamentos(limit = 50, offset = 0, ativoApenas = true, futuroApenas = true) {
    const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
        ativo_apenas: ativoApenas.toString(),
        futuro_apenas: futuroApenas.toString()
    });
    
    const response = await fetch(`${API_BASE_URL}/agendamentos?${params}`);
    if (!response.ok) {
        throw new Error('Erro ao buscar agendamentos');
    }
    return await response.json();
}

export async function atualizarAgendamento(jobId, data) {
    const response = await fetch(`${API_BASE_URL}/agendamentos/${jobId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao atualizar agendamento');
    }
    return await response.json();
}

export async function cancelarAgendamento(jobId) {
    const response = await fetch(`${API_BASE_URL}/agendamentos/${jobId}`, {
        method: 'DELETE'
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Erro ao cancelar agendamento');
    }
    return await response.json();
}

export async function fetchCredenciaisEmpresa(empresaId) {
    const response = await fetch(`${API_BASE_URL}/empresas/${empresaId}/credenciais`);
    if (!response.ok) {
        throw new Error('Erro ao buscar credenciais da empresa');
    }
    return await response.json();
}
