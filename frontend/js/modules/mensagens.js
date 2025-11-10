import * as api from './api.js';
import { showNotification } from './utils.js';

class MensagensUI {
    constructor() {
        this.currentPage = 0;
        this.pageSize = 20;
        this.filters = {
            inscricao_estadual: '',
            cpf_socio: '',
            assunto: ''
        };
        this.totalMensagens = 0;
    }

    /**
     * Inicializa a aba de mensagens
     */
    async init() {
        await this.loadMensagens();
        await this.updateCounters();
        this.setupEventListeners();
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Enter nos campos de filtro aplica os filtros
        ['filter-ie', 'filter-cpf', 'filter-assunto'].forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.applyFilters();
                    }
                });
            }
        });
    }

    /**
     * Carrega as mensagens da API
     */
    async loadMensagens() {
        try {
            const tbody = document.getElementById('mensagens-tbody');
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="px-6 py-4 text-center text-gray-500">
                        <i data-lucide="loader" class="h-6 w-6 animate-spin inline mr-2"></i>
                        Carregando mensagens...
                    </td>
                </tr>
            `;
            lucide.createIcons();

            // Construir query params
            const params = new URLSearchParams({
                limit: this.pageSize,
                offset: this.currentPage * this.pageSize
            });

            if (this.filters.inscricao_estadual) {
                params.append('inscricao_estadual', this.filters.inscricao_estadual);
            }
            if (this.filters.cpf_socio) {
                params.append('cpf_socio', this.filters.cpf_socio);
            }
            if (this.filters.assunto) {
                params.append('assunto', this.filters.assunto);
            }

            const mensagens = await api.get(`/api/mensagens?${params.toString()}`);
            
            if (!mensagens || mensagens.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" class="px-6 py-4 text-center text-gray-500">
                            <i data-lucide="inbox" class="h-8 w-8 mx-auto mb-2"></i>
                            <p>Nenhuma mensagem encontrada</p>
                        </td>
                    </tr>
                `;
                lucide.createIcons();
                this.updatePagination(0);
                return;
            }

            tbody.innerHTML = mensagens.map(msg => this.createMensagemRow(msg)).join('');
            lucide.createIcons();

            // Atualizar paginação
            await this.updatePagination(mensagens.length);
            
        } catch (error) {
            console.error('Erro ao carregar mensagens:', error);
            const tbody = document.getElementById('mensagens-tbody');
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="px-6 py-4 text-center text-red-500">
                        <i data-lucide="alert-circle" class="h-6 w-6 inline mr-2"></i>
                        Erro ao carregar mensagens: ${error.message}
                    </td>
                </tr>
            `;
            lucide.createIcons();
            showNotification('Erro ao carregar mensagens', 'error');
        }
    }

    /**
     * Cria uma linha da tabela para uma mensagem
     */
    createMensagemRow(msg) {
        const statusBadge = this.getStatusBadge(msg);
        const dataEnvio = this.formatDate(msg.data_envio);
        const vencimento = msg.vencimento ? this.formatDate(msg.vencimento) : '-';

        return `
            <tr class="hover:bg-gray-50 cursor-pointer" onclick="window.mensagensUI.showMensagemModal(${msg.id})">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-medium text-gray-900">${this.escapeHtml(msg.assunto || 'Sem assunto')}</div>
                    <div class="text-xs text-gray-500">IE: ${this.escapeHtml(msg.inscricao_estadual || '-')}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-900">${this.escapeHtml(msg.enviada_por || '-')}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${dataEnvio}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                        ${this.escapeHtml(msg.tipo_mensagem || 'Geral')}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${vencimento}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${statusBadge}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button onclick="event.stopPropagation(); window.mensagensUI.showMensagemModal(${msg.id})" class="text-indigo-600 hover:text-indigo-900">
                        <i data-lucide="eye" class="h-4 w-4 inline"></i> Ver
                    </button>
                </td>
            </tr>
        `;
    }

    /**
     * Retorna o badge de status da mensagem
     */
    getStatusBadge(msg) {
        if (msg.data_ciencia && msg.data_ciencia !== 'N/A') {
            return `<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                        <i data-lucide="check-circle" class="h-3 w-3 mr-1"></i> Lida
                    </span>`;
        } else {
            return `<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                        <i data-lucide="clock" class="h-3 w-3 mr-1"></i> Pendente
                    </span>`;
        }
    }

    /**
     * Atualiza os contadores no topo da página
     */
    async updateCounters() {
        try {
            // Total geral
            const countResponse = await api.get('/api/mensagens/count');
            const total = countResponse.total || 0;
            document.getElementById('total-mensagens').textContent = total;

            // Para calcular pendentes e lidas, buscar todas as mensagens
            const allMensagens = await api.get(`/api/mensagens?limit=${total}`);
            
            const pendentes = allMensagens.filter(m => !m.data_ciencia || m.data_ciencia === 'N/A').length;
            const lidas = allMensagens.filter(m => m.data_ciencia && m.data_ciencia !== 'N/A').length;

            document.getElementById('mensagens-pendentes').textContent = pendentes;
            document.getElementById('mensagens-lidas').textContent = lidas;

        } catch (error) {
            console.error('Erro ao atualizar contadores:', error);
        }
    }

    /**
     * Atualiza a paginação
     */
    async updatePagination(currentCount) {
        try {
            // Obter total com filtros aplicados
            const params = new URLSearchParams();
            if (this.filters.inscricao_estadual) {
                params.append('inscricao_estadual', this.filters.inscricao_estadual);
            }
            if (this.filters.cpf_socio) {
                params.append('cpf_socio', this.filters.cpf_socio);
            }

            const countResponse = await api.get(`/api/mensagens/count?${params.toString()}`);
            this.totalMensagens = countResponse.total || 0;

            const start = this.currentPage * this.pageSize + 1;
            const end = Math.min(start + currentCount - 1, this.totalMensagens);

            document.getElementById('msg-showing-start').textContent = this.totalMensagens > 0 ? start : 0;
            document.getElementById('msg-showing-end').textContent = end;
            document.getElementById('msg-total').textContent = this.totalMensagens;

            // Habilitar/desabilitar botões
            const prevBtn = document.getElementById('msg-prev-btn');
            const nextBtn = document.getElementById('msg-next-btn');

            prevBtn.disabled = this.currentPage === 0;
            nextBtn.disabled = end >= this.totalMensagens;

        } catch (error) {
            console.error('Erro ao atualizar paginação:', error);
        }
    }

    /**
     * Próxima página
     */
    async nextPage() {
        this.currentPage++;
        await this.loadMensagens();
    }

    /**
     * Página anterior
     */
    async previousPage() {
        if (this.currentPage > 0) {
            this.currentPage--;
            await this.loadMensagens();
        }
    }

    /**
     * Aplica os filtros
     */
    async applyFilters() {
        this.filters.inscricao_estadual = document.getElementById('filter-ie')?.value || '';
        this.filters.cpf_socio = document.getElementById('filter-cpf')?.value || '';
        this.filters.assunto = document.getElementById('filter-assunto')?.value || '';

        this.currentPage = 0; // Resetar para primeira página
        await this.loadMensagens();
        showNotification('Filtros aplicados', 'success');
    }

    /**
     * Limpa os filtros
     */
    async clearFilters() {
        document.getElementById('filter-ie').value = '';
        document.getElementById('filter-cpf').value = '';
        document.getElementById('filter-assunto').value = '';

        this.filters = {
            inscricao_estadual: '',
            cpf_socio: '',
            assunto: ''
        };

        this.currentPage = 0;
        await this.loadMensagens();
        showNotification('Filtros limpos', 'success');
    }

    /**
     * Mostra modal com detalhes da mensagem
     */
    async showMensagemModal(mensagemId) {
        try {
            const mensagem = await api.get(`/api/mensagens/${mensagemId}`);
            
            const detalhesDiv = document.getElementById('mensagem-detalhes');
            detalhesDiv.innerHTML = `
                <div class="space-y-3">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Inscrição Estadual</label>
                            <p class="mt-1 text-sm text-gray-900">${this.escapeHtml(mensagem.inscricao_estadual || '-')}</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">CPF Sócio</label>
                            <p class="mt-1 text-sm text-gray-900">${this.escapeHtml(mensagem.cpf_socio || '-')}</p>
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700">Assunto</label>
                        <p class="mt-1 text-sm text-gray-900 font-medium">${this.escapeHtml(mensagem.assunto || '-')}</p>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Enviada Por</label>
                            <p class="mt-1 text-sm text-gray-900">${this.escapeHtml(mensagem.enviada_por || '-')}</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Data de Envio</label>
                            <p class="mt-1 text-sm text-gray-900">${this.formatDate(mensagem.data_envio)}</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Classificação</label>
                            <p class="mt-1 text-sm text-gray-900">${this.escapeHtml(mensagem.classificacao || '-')}</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Tributo</label>
                            <p class="mt-1 text-sm text-gray-900">${this.escapeHtml(mensagem.tributo || '-')}</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Tipo de Mensagem</label>
                            <p class="mt-1 text-sm text-gray-900">${this.escapeHtml(mensagem.tipo_mensagem || '-')}</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Número do Documento</label>
                            <p class="mt-1 text-sm text-gray-900">${this.escapeHtml(mensagem.numero_documento || '-')}</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Vencimento</label>
                            <p class="mt-1 text-sm text-gray-900">${mensagem.vencimento ? this.formatDate(mensagem.vencimento) : '-'}</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Tipo de Ciência</label>
                            <p class="mt-1 text-sm text-gray-900">${this.escapeHtml(mensagem.tipo_ciencia || '-')}</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Data de Ciência</label>
                            <p class="mt-1 text-sm text-gray-900">${mensagem.data_ciencia && mensagem.data_ciencia !== 'N/A' ? this.formatDate(mensagem.data_ciencia) : 'Não dada ciência'}</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700">Data de Leitura</label>
                            <p class="mt-1 text-sm text-gray-900">${this.formatDate(mensagem.data_leitura)}</p>
                        </div>
                    </div>

                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Conteúdo da Mensagem</label>
                        <div class="mt-1 p-4 bg-gray-50 rounded-md border border-gray-200 max-h-96 overflow-y-auto">
                            <pre class="text-sm text-gray-900 whitespace-pre-wrap">${this.escapeHtml(mensagem.conteudo_mensagem || 'Sem conteúdo')}</pre>
                        </div>
                    </div>
                </div>
            `;

            document.getElementById('mensagemModal').classList.remove('hidden');
            lucide.createIcons();

        } catch (error) {
            console.error('Erro ao carregar detalhes da mensagem:', error);
            showNotification('Erro ao carregar detalhes da mensagem', 'error');
        }
    }

    /**
     * Fecha o modal de mensagem
     */
    closeMensagemModal() {
        document.getElementById('mensagemModal').classList.add('hidden');
    }

    /**
     * Formata data para exibição
     */
    formatDate(dateString) {
        if (!dateString || dateString === 'N/A') return 'N/A';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) return dateString;
            
            return new Intl.DateTimeFormat('pt-BR', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            }).format(date);
        } catch (error) {
            return dateString;
        }
    }

    /**
     * Escapa HTML para prevenir XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Criar instância global
const mensagensUI = new MensagensUI();
window.mensagensUI = mensagensUI;

export { mensagensUI };
