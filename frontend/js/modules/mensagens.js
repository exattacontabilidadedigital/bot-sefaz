import * as api from './api.js';
import { showNotification } from './utils.js';

class MensagensUI {
    constructor() {
        this.currentPage = 0;
        this.pageSize = 20;
        this.filters = {
            empresa: '',
            assunto: '',
            data_inicial: '',
            data_final: ''
        };
        this.totalMensagens = 0;
        this.empresas = [];
    }

    /**
     * Inicializa a aba de mensagens
     */
    async init() {
        await this.loadEmpresas();
        await this.loadMensagens();
        await this.updateCounters();
        this.setupEventListeners();
    }

    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Enter nos campos de filtro aplica os filtros
        ['filter-assunto'].forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') {
                        this.applyFilters();
                    }
                });
            }
        });
        
        // Change nos selects e dates aplica os filtros automaticamente
        ['filter-empresa', 'filter-data-inicial', 'filter-data-final'].forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => {
                    this.applyFilters();
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

            if (this.filters.empresa) {
                params.append('inscricao_estadual', this.filters.empresa);
                console.log('🔍 Filtro empresa aplicado:', this.filters.empresa);
            }
            if (this.filters.assunto) {
                params.append('assunto', this.filters.assunto);
                console.log('🔍 Filtro assunto aplicado:', this.filters.assunto);
            }
            
            console.log('📡 URL da requisição:', `/api/mensagens?${params.toString()}`);

            let mensagens = await api.get(`/api/mensagens?${params.toString()}`);
            
            // Aplicar filtros de data no frontend
            if (mensagens && (this.filters.data_inicial || this.filters.data_final)) {
                mensagens = mensagens.filter(msg => {
                    if (!msg.data_envio) return true;
                    
                    const dataEnvio = new Date(msg.data_envio);
                    
                    if (this.filters.data_inicial) {
                        const dataInicial = new Date(this.filters.data_inicial);
                        if (dataEnvio < dataInicial) return false;
                    }
                    
                    if (this.filters.data_final) {
                        const dataFinal = new Date(this.filters.data_final);
                        dataFinal.setHours(23, 59, 59, 999); // Incluir todo o dia
                        if (dataEnvio > dataFinal) return false;
                    }
                    
                    return true;
                });
            }
            
            console.log('📨 Mensagens recebidas:', mensagens);
            console.log('📊 Quantidade:', mensagens ? mensagens.length : 0);
            
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

            console.log('🔧 Criando linhas da tabela...');
            const rows = mensagens.map((msg, index) => {
                console.log(`   Mensagem ${index + 1}:`, msg);
                return this.createMensagemRow(msg);
            });
            console.log('✅ Linhas criadas:', rows.length);
            
            tbody.innerHTML = rows.join('');
            console.log('✅ HTML inserido no tbody');
            console.log('📏 Tamanho do HTML:', tbody.innerHTML.length);
            console.log('🔍 Primeiras 500 caracteres:', tbody.innerHTML.substring(0, 500));
            console.log('👀 Elemento tbody visível?', tbody.offsetHeight > 0);
            console.log('📐 Altura do tbody:', tbody.offsetHeight);
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
        const statusProcTag = this.getStatusProcessamento(msg);
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
                <td class="px-6 py-4 whitespace-nowrap">
                    ${statusProcTag}
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
     * Retorna o status de processamento da mensagem
     */
    getStatusProcessamento(mensagem) {
        const texto = (mensagem.conteudo_mensagem || mensagem.conteudo_html || '').toLowerCase();
        if (texto.includes('processada com sucesso')) {
            return '<span style="display:inline-block;background:#22c55e;color:#fff;font-weight:600;padding:2px 10px;border-radius:6px;font-size:0.95rem;margin-bottom:6px;">Processada</span>';
        }
        if (texto.includes('não foi processada') || texto.includes('nao foi processada')) {
            return '<span style="display:inline-block;background:#ef4444;color:#fff;font-weight:600;padding:2px 10px;border-radius:6px;font-size:0.95rem;margin-bottom:6px;">Não Processada</span>';
        }
        return '';
    }

    /**
     * Carrega lista de empresas para o dropdown
     */
    async loadEmpresas() {
        try {
            const empresas = await api.get('/api/empresas?limit=1000');
            this.empresas = empresas || [];
            
            const select = document.getElementById('filter-empresa');
            if (select) {
                // Limpar opções existentes (exceto "Todas")
                select.innerHTML = '<option value="">Todas as empresas</option>';
                
                // Adicionar empresas ao select, ordenadas por nome
                this.empresas
                    .sort((a, b) => a.nome_empresa.localeCompare(b.nome_empresa))
                    .forEach(empresa => {
                        const option = document.createElement('option');
                        option.value = empresa.inscricao_estadual || '';
                        option.textContent = `${empresa.nome_empresa} - IE: ${empresa.inscricao_estadual}`;
                        select.appendChild(option);
                    });
                
                console.log(`✅ Carregadas ${this.empresas.length} empresas da tabela 'empresas'`);
            }
        } catch (error) {
            console.error('Erro ao carregar empresas:', error);
            showNotification('Erro ao carregar lista de empresas', 'error');
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
            if (this.filters.empresa) {
                params.append('inscricao_estadual', this.filters.empresa);
            }
            if (this.filters.assunto) {
                params.append('assunto', this.filters.assunto);
            }

            const countResponse = await api.get(`/api/mensagens/count?${params.toString()}`);
            let total = countResponse.total || 0;
            
            // Se há filtros de data, precisamos considerar a filtragem no frontend
            if (this.filters.data_inicial || this.filters.data_final) {
                total = currentCount; // Usar count atual já filtrado
            }
            
            this.totalMensagens = total;

            const start = this.currentPage * this.pageSize + 1;
            const end = Math.min(start + currentCount - 1, this.totalMensagens);
            
            const totalPages = Math.ceil(this.totalMensagens / this.pageSize);
            const currentPageDisplay = this.totalMensagens > 0 ? this.currentPage + 1 : 0;

            // Atualizar info de exibição
            const pageInfo = document.getElementById('mensagensPageInfo');
            if (pageInfo) {
                pageInfo.textContent = `Mostrando ${this.totalMensagens > 0 ? start : 0} a ${end} de ${this.totalMensagens} resultados`;
            }
            
            // Atualizar número da página
            const pageNumber = document.getElementById('mensagensPageNumber');
            if (pageNumber) {
                pageNumber.textContent = `Página ${currentPageDisplay} de ${totalPages}`;
            }

            // Habilitar/desabilitar botões
            const prevBtn = document.getElementById('msg-prev-btn');
            const nextBtn = document.getElementById('msg-next-btn');

            if (prevBtn) {
                prevBtn.disabled = this.currentPage === 0;
                if (prevBtn.disabled) {
                    prevBtn.classList.add('opacity-50', 'cursor-not-allowed');
                } else {
                    prevBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                }
            }
            
            if (nextBtn) {
                nextBtn.disabled = end >= this.totalMensagens;
                if (nextBtn.disabled) {
                    nextBtn.classList.add('opacity-50', 'cursor-not-allowed');
                } else {
                    nextBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                }
            }

        } catch (error) {
            console.error('Erro ao atualizar paginação:', error);
        }
    }

    /**
     * Próxima página
     */
    async nextPage() {
        const maxPage = Math.ceil(this.totalMensagens / this.pageSize) - 1;
        if (this.currentPage < maxPage) {
            this.currentPage++;
            await this.loadMensagens();
        }
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
     * Altera quantidade de itens por página
     */
    async changeItemsPerPage(newSize) {
        this.pageSize = parseInt(newSize);
        this.currentPage = 0;
        await this.loadMensagens();
    }

    /**
     * Aplica os filtros
     */
    async applyFilters() {
        this.filters.empresa = document.getElementById('filter-empresa')?.value || '';
        this.filters.assunto = document.getElementById('filter-assunto')?.value || '';
        this.filters.data_inicial = document.getElementById('filter-data-inicial')?.value || '';
        this.filters.data_final = document.getElementById('filter-data-final')?.value || '';

        this.currentPage = 0; // Resetar para primeira página
        await this.loadMensagens();
        showNotification('Filtros aplicados', 'success');
    }

    /**
     * Limpa os filtros
     */
    async clearFilters() {
        document.getElementById('filter-empresa').value = '';
        document.getElementById('filter-assunto').value = '';
        document.getElementById('filter-data-inicial').value = '';
        document.getElementById('filter-data-final').value = '';

        this.filters = {
            empresa: '',
            assunto: '',
            data_inicial: '',
            data_final: ''
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
            this.currentMensagem = mensagem;
            const statusTag = this.getStatusProcessamento(mensagem);
            const detalhesDiv = document.getElementById('mensagem-detalhes');
            detalhesDiv.innerHTML = `
                <div>${statusTag}</div>
                <div class="space-y-3">
                    <!-- INFORMAÇÕES PRINCIPAIS -->
                    <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                        <div class="grid grid-cols-2 gap-3 text-sm">
                            <div>
                                <span class="font-medium text-gray-700">Enviada por:</span>
                                <span class="text-gray-900 ml-2">${this.escapeHtml(mensagem.enviada_por || '-')}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">Data Envio:</span>
                                <span class="text-gray-900 ml-2">${this.formatDate(mensagem.data_envio)}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">Assunto:</span>
                                <span class="text-gray-900 ml-2">${this.escapeHtml(mensagem.assunto || '-')}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">Classificação:</span>
                                <span class="text-gray-900 ml-2">${this.escapeHtml(mensagem.classificacao || '-')}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">Tributo:</span>
                                <span class="text-gray-900 ml-2">${this.escapeHtml(mensagem.tributo || '-')}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">Tipo:</span>
                                <span class="text-gray-900 ml-2">${this.escapeHtml(mensagem.tipo_mensagem || '-')}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">IE:</span>
                                <span class="text-gray-900 ml-2">${this.escapeHtml(mensagem.inscricao_estadual || '-')}</span>
                            </div>
                            <div>
                                <span class="font-medium text-gray-700">Nº Doc:</span>
                                <span class="text-gray-900 ml-2">${this.escapeHtml(mensagem.numero_documento || '-')}</span>
                            </div>
                            ${mensagem.data_leitura ? `
                            <div>
                                <span class="font-medium text-gray-700">Data Leitura:</span>
                                <span class="text-gray-900 ml-2">${this.formatDate(mensagem.data_leitura)}</span>
                            </div>
                            ` : ''}
                            ${mensagem.vencimento ? `
                            <div>
                                <span class="font-medium text-gray-700">Vencimento:</span>
                                <span class="text-gray-900 ml-2">${this.formatDate(mensagem.vencimento)}</span>
                            </div>
                            ` : ''}
                            ${mensagem.data_ciencia ? `
                            <div>
                                <span class="font-medium text-gray-700">Data Ciência:</span>
                                <span class="text-gray-900 ml-2">${this.formatDate(mensagem.data_ciencia)}</span>
                            </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- SEÇÃO ESPECÍFICA DA DIEF -->
                    ${mensagem.competencia_dief || mensagem.status_dief || mensagem.chave_dief ? `
                    <div class="bg-blue-50 p-4 rounded-lg border-2 border-blue-200">
                        <h3 class="text-base font-semibold text-blue-900 mb-3 flex items-center">
                            <i data-lucide="file-text" class="h-5 w-5 mr-2"></i>
                            Dados do Processamento DIEF
                        </h3>
                        <div class="grid grid-cols-2 gap-3 text-sm">
                            ${mensagem.protocolo_dief ? `
                            <div>
                                <span class="font-medium text-blue-700">Protocolo:</span>
                                <span class="text-gray-900 ml-2">${this.escapeHtml(mensagem.protocolo_dief)}</span>
                            </div>
                            ` : ''}
                            ${mensagem.competencia_dief ? `
                            <div>
                                <span class="font-medium text-blue-700">Período:</span>
                                <span class="text-gray-900 ml-2 font-semibold">${this.formatCompetencia(mensagem.competencia_dief)}</span>
                            </div>
                            ` : ''}
                            ${mensagem.status_dief ? `
                            <div class="col-span-2">
                                <span class="font-medium text-blue-700">Situação:</span>
                                <span class="text-gray-900 ml-2 font-semibold">${this.escapeHtml(mensagem.status_dief)}</span>
                            </div>
                            ` : ''}
                            ${mensagem.chave_dief ? `
                            <div class="col-span-2">
                                <span class="font-medium text-blue-700">Chave de Segurança:</span>
                                <p class="text-xs text-gray-900 font-mono mt-1">${this.escapeHtml(mensagem.chave_dief)}</p>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    ` : ''}

                    <!-- CONTEÚDO DA MENSAGEM -->
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 mb-2">Mensagem Completa</label>
                        <div class="p-4 bg-white rounded-md border border-gray-300 max-h-96 overflow-y-auto">
                            ${mensagem.conteudo_html ? 
                                mensagem.conteudo_html :
                                `<pre class="text-sm text-gray-900 whitespace-pre-wrap">${this.escapeHtml(mensagem.conteudo_mensagem || 'Sem conteúdo')}</pre>`
                            }
                        </div>
                    </div>

                    ${mensagem.link_recibo ? `
                    <div class="flex justify-center">
                        <a href="${this.escapeHtml(mensagem.link_recibo)}" target="_blank" 
                           class="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors shadow-md">
                            <i data-lucide="external-link" class="h-5 w-5 mr-2"></i>
                            Abrir Recibo DIEF
                        </a>
                    </div>
                    ` : ''}
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
     * Abre SEFAZ com Auto-Login (usando extensão)
     */
    async abrirSEFAZComAutoLogin() {
        try {
            if (!this.currentMensagem || !this.currentMensagem.inscricao_estadual) {
                showNotification('Mensagem não carregada', 'error');
                return;
            }

            // Buscar credenciais da empresa
            const empresa = await api.get(`/api/empresas/credenciais-por-ie/${this.currentMensagem.inscricao_estadual}`);
            
            const cpf = empresa.cpf_socio;
            const senha = empresa.senha;

            if (!senha) {
                showNotification('Senha não disponível para esta empresa', 'error');
                return;
            }

            // Extrair link do recibo - primeiro tentar do banco, depois do conteúdo
            let linkRecibo = this.currentMensagem.link_recibo; // Link já extraído e salvo no banco
            
            if (!linkRecibo) {
                console.log('⚠️ Link não encontrado no banco, tentando extrair do conteúdo...');
                console.log('🔍 Verificando conteúdo da mensagem...');
                console.log('📄 Conteúdo existe?', !!this.currentMensagem.conteudo_mensagem);
                
                if (this.currentMensagem.conteudo_mensagem) {
                    console.log('📏 Tamanho total do conteúdo:', this.currentMensagem.conteudo_mensagem.length);
                    
                    // Tentar várias regex para pegar o link
                    const regex1 = /href="([^"]*listIReciboDief\.do[^"]*)"/i;
                    const regex2 = /href='([^']*listIReciboDief\.do[^']*)'/i;
                    const regex3 = /(https?:\/\/[^"'\s]*listIReciboDief\.do[^"'\s]*)/i;
                    
                    let match = this.currentMensagem.conteudo_mensagem.match(regex1);
                    if (!match) match = this.currentMensagem.conteudo_mensagem.match(regex2);
                    if (!match) match = this.currentMensagem.conteudo_mensagem.match(regex3);
                    
                    if (match) {
                        linkRecibo = match[1].replace(/&amp;/g, '&');
                        console.log('✅ Link do recibo extraído do conteúdo:', linkRecibo);
                    } else {
                        console.error('❌ Link do recibo NÃO encontrado');
                    }
                }
            } else {
                console.log('✅ Link do recibo obtido do banco:', linkRecibo);
            }

            // Abrir SEFAZ em nova aba
            const sefazWindow = window.open('https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin', '_blank');
            
            if (!sefazWindow) {
                showNotification('Popup bloqueado! Permita popups para este site.', 'error');
                return;
            }

            // Configurar listener para quando a extensão avisar que login completou
            console.log('👂 Configurando listener para aguardar login completo...');
            
            const loginListener = (event) => {
                console.log('📨 Mensagem recebida:', event.data);
                
                if (event.data && event.data.type === 'SEFAZ_LOGIN_COMPLETO') {
                    console.log('✅ Recebido aviso de login completo!', event.data);
                    const link = event.data.linkRecibo;
                    
                    if (link) {
                        console.log('📄 Abrindo recibo:', link);
                        const novaAba = window.open(link, '_blank');
                        
                        if (novaAba) {
                            console.log('✅ Recibo aberto com sucesso!');
                            showNotification('Recibo DIEF aberto! 📄', 'success');
                        } else {
                            console.error('❌ Falha ao abrir recibo - popup bloqueado?');
                            showNotification('Popup bloqueado! Permita popups e tente novamente.', 'error');
                        }
                    } else {
                        console.warn('⚠️ Link do recibo não encontrado no evento');
                    }
                    
                    window.removeEventListener('message', loginListener);
                    console.log('✅ Listener removido');
                }
            };
            
            window.addEventListener('message', loginListener);
            console.log('✅ Listener configurado e aguardando mensagem...');
            
            // Aguardar página carregar e enviar credenciais
            setTimeout(() => {
                console.log('📤 Enviando credenciais para extensão...');
                console.log('🪟 sefazWindow existe?', !!sefazWindow);
                console.log('📦 Dados a enviar:', { type: 'SEFAZ_AUTO_LOGIN', cpf, linkRecibo });
                
                sefazWindow.postMessage({
                    type: 'SEFAZ_AUTO_LOGIN',
                    cpf: cpf,
                    senha: senha,
                    linkRecibo: linkRecibo
                }, 'https://sefaznet.sefaz.ma.gov.br');
                
                console.log('✅ postMessage executado');
                showNotification('Fazendo login automaticamente! 🚀', 'success');
            }, 3000);

        } catch (error) {
            console.error('Erro ao abrir SEFAZ:', error);
            showNotification('Erro ao buscar credenciais da empresa', 'error');
        }
    }

    /**
     * Fecha o modal de mensagem
     */
    closeMensagemModal() {
        document.getElementById('mensagemModal').classList.add('hidden');
    }

    /**
     * Imprime o recibo da DIEF
     */
    async imprimirReciboDIEF() {
        try {
            if (!this.currentMensagem || !this.currentMensagem.inscricao_estadual) {
                showNotification('Mensagem não carregada', 'error');
                return;
            }

            // Buscar credenciais da empresa pela IE
            const empresa = await api.get(`/api/empresas/credenciais-por-ie/${this.currentMensagem.inscricao_estadual}`);
            
            console.log('👤 Dados da empresa:', empresa);
            
            const cpf = empresa.cpf_socio;
            const senha = empresa.senha || '[SENHA NÃO DISPONÍVEL]';

            // Guardar credenciais para copiar depois
            this.credenciais = { cpf, senha };

            // Criar modal personalizado com botões de cópia
            const modalHtml = `
                <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                            background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); 
                            z-index: 10000; max-width: 500px; width: 90%;">
                    <h3 style="margin: 0 0 20px 0; color: #1e40af; font-size: 20px;">🔐 Credenciais SEFAZ-MA</h3>
                    
                    <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <p style="margin: 5px 0; font-size: 14px;"><strong>Empresa:</strong> ${empresa.nome_empresa}</p>
                        <p style="margin: 5px 0; font-size: 14px;"><strong>IE:</strong> ${this.currentMensagem.inscricao_estadual}</p>
                    </div>
                    
                    <div style="background: #eff6ff; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #374151;"><strong>👤 CPF:</strong></p>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <input type="text" value="${cpf}" readonly 
                                   style="flex: 1; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 16px;">
                            <button onclick="copiarCPF()" 
                                    style="padding: 8px 16px; background: #3b82f6; color: white; border: none; 
                                           border-radius: 4px; cursor: pointer; font-size: 14px;">
                                📋 Copiar
                            </button>
                        </div>
                    </div>
                    
                    <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #374151;"><strong>🔑 Senha:</strong></p>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <input type="text" value="${senha}" readonly 
                                   style="flex: 1; padding: 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 16px;">
                            <button onclick="copiarSenha()" 
                                    style="padding: 8px 16px; background: #f59e0b; color: white; border: none; 
                                           border-radius: 4px; cursor: pointer; font-size: 14px;">
                                📋 Copiar
                            </button>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button onclick="fecharModalCredenciais()" 
                                style="padding: 10px 20px; background: #6b7280; color: white; border: none; 
                                       border-radius: 4px; cursor: pointer; font-size: 14px;">
                            Fechar
                        </button>
                        <button onclick="abrirSEFAZ()" 
                                style="padding: 10px 20px; background: #10b981; color: white; border: none; 
                                       border-radius: 4px; cursor: pointer; font-size: 14px; font-weight: bold;">
                            🌐 Abrir SEFAZ
                        </button>
                    </div>
                </div>
                <div onclick="fecharModalCredenciais()" 
                     style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; 
                            background: rgba(0,0,0,0.5); z-index: 9999;"></div>
            `;

            // Adicionar modal ao body
            const modalDiv = document.createElement('div');
            modalDiv.id = 'credenciaisModal';
            modalDiv.innerHTML = modalHtml;
            document.body.appendChild(modalDiv);

            // Funções globais para os botões
            window.copiarCPF = async () => {
                await navigator.clipboard.writeText(cpf);
                showNotification('CPF copiado!', 'success');
            };

            window.copiarSenha = async () => {
                await navigator.clipboard.writeText(senha);
                showNotification('Senha copiada!', 'success');
            };

            window.abrirSEFAZ = () => {
                window.open('https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin', '_blank');
                showNotification('Página SEFAZ aberta! Use os botões para copiar CPF e Senha.', 'info');
            };

            window.fecharModalCredenciais = () => {
                const modal = document.getElementById('credenciaisModal');
                if (modal) modal.remove();
            };

        } catch (error) {
            console.error('Erro ao buscar credenciais:', error);
            showNotification('Erro ao buscar credenciais da empresa', 'error');
        }
    }

    /**
     * Imprime o conteúdo do modal com design igual ao print desejado
     */
    imprimirModal() {
        const m = this.currentMensagem;
        const dataHora = new Date().toLocaleString('pt-BR');
        const statusTag = this.getStatusProcessamento(m);
        // Bloco Resumo
        const resumo = `
            <div class="print-box">
                <div class="print-box-title">Resumo da Mensagem</div>
                <div class="print-grid">
                    <div><span class="print-label">Enviada por:</span> <span class="print-value">${m.enviada_por || '-'}</span></div>
                    <div><span class="print-label">Assunto:</span> <span class="print-value">${m.assunto || '-'}</span></div>
                    <div><span class="print-label">Classificação:</span> <span class="print-value">${m.classificacao || '-'}</span></div>
                    <div><span class="print-label">Tributo:</span> <span class="print-value">${m.tributo || '-'}</span></div>
                    <div><span class="print-label">Tipo:</span> <span class="print-value">${m.tipo_mensagem || '-'}</span></div>
                    <div><span class="print-label">IE:</span> <span class="print-value">${m.inscricao_estadual || '-'}</span></div>
                    <div><span class="print-label">Nº Doc:</span> <span class="print-value">${m.numero_documento || '-'}</span></div>
                    <div><span class="print-label">Data Envio:</span> <span class="print-value">${m.data_envio || '-'}</span></div>
                    <div><span class="print-label">Vencimento:</span> <span class="print-value">${m.vencimento || '-'}</span></div>
                    <div><span class="print-label">Data Leitura:</span> <span class="print-value">${m.data_leitura || '-'}</span></div>
                    <div><span class="print-label">Data Ciência:</span> <span class="print-value">${m.data_ciencia || '-'}</span></div>
                </div>
            </div>
        `;
        // Bloco Mensagem Completa
        const conteudo = m.conteudo_html ? m.conteudo_html : `<pre class="print-content">${m.conteudo_mensagem || 'Sem conteúdo'}</pre>`;
        const mensagemCompleta = `
            <div class="print-box">
                <div class="print-box-title">Mensagem Completa</div>
                ${conteudo}
            </div>
        `;
        // Chave destacada
        let chaveHtml = '';
        if (m.chave_dief) {
            chaveHtml = `<div class="print-key">Chave de segurança: ${m.chave_dief}</div>`;
        }
        // Link recibo
        let linkHtml = '';
        if (m.link_recibo) {
            linkHtml = `<a href="${m.link_recibo}" target="_blank" class="print-link">Abrir Recibo DIEF</a>`;
        }
        const janelaImpressao = window.open('', '_blank', 'width=900,height=700');
        janelaImpressao.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset='UTF-8'>
                <title>Detalhes da Mensagem - SEFAZ</title>
                <style>
                    @page { size: A4 portrait; margin: 18mm 12mm 18mm 12mm; }
                    body { background: #fff; margin: 0; padding: 0; font-family: Arial, sans-serif; }
                    .print-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-top: 24px;
                        margin-bottom: 8px;
                    }
                    .print-title {
                        font-size: 1.6rem;
                        font-weight: bold;
                        color: #222;
                        margin-left: 8px;
                    }
                    .print-date {
                        font-size: 0.95rem;
                        color: #888;
                        margin-right: 8px;
                    }
                    .print-box {
                        background: #f9fafb;
                        border-radius: 10px;
                        border: 1px solid #e5e7eb;
                        padding: 18px 24px;
                        margin-bottom: 18px;
                        font-size: 1rem;
                        color: #222;
                    }
                    .print-box-title {
                        font-size: 1.1rem;
                        font-weight: bold;
                        color: #222;
                        margin-bottom: 12px;
                    }
                    .print-grid {
                        display: grid;
                        grid-template-columns: repeat(3, 1fr);
                        gap: 8px 24px;
                        margin-bottom: 8px;
                    }
                    .print-label {
                        font-weight: 500;
                        color: #444;
                        font-size: 0.98rem;
                    }
                    .print-value {
                        color: #222;
                        font-size: 1rem;
                        font-weight: 400;
                    }
                    .print-content {
                        font-family: 'Courier New', Courier, monospace;
                        font-size: 1rem;
                        margin-bottom: 18px;
                        color: #222;
                        white-space: pre-wrap;
                    }
                    .print-key {
                        font-weight: bold;
                        color: #374151;
                        background: #f3f4f6;
                        border-radius: 6px;
                        padding: 6px 10px;
                        margin-top: 10px;
                        margin-bottom: 6px;
                        font-size: 1rem;
                        display: inline-block;
                    }
                    .print-link {
                        display: inline-block;
                        background: #2563eb;
                        color: #fff !important;
                        font-weight: bold;
                        padding: 8px 18px;
                        border-radius: 6px;
                        text-decoration: none;
                        margin-top: 12px;
                        font-size: 1rem;
                    }
                    @media print {
                        html, body { width: 100%; height: 100%; background: #fff; }
                        .print-header, .print-title { margin-top: 0; }
                        .print-box { margin-bottom: 12px; }
                    }
                </style>
            </head>
            <body>
                <div class="print-header">
                    <div class="print-title">Detalhes da Mensagem - SEFAZ</div>
                    <div class="print-date">Recebido em ${dataHora}</div>
                </div>
                ${statusTag}
                ${resumo}
                ${mensagemCompleta}
                ${chaveHtml}
                ${linkHtml}
                <script>window.onload = function() { window.print(); }</script>
            </body>
            </html>
        `);
        janelaImpressao.document.close();
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
     * Formata competência DIEF (formato 202510 -> 10/2025)
     */
    formatCompetencia(competencia) {
        if (!competencia || competencia.length !== 6) return competencia;
        
        const ano = competencia.substring(0, 4);
        const mes = competencia.substring(4, 6);
        
        return `${mes}/${ano}`;
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
