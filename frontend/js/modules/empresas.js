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
                        <button onclick="window.empresasUI.copyCredentials(${empresa.id})" 
                                class="text-purple-600 hover:text-purple-900"
                                title="Copiar dados de acesso (CPF e senha)">
                            <i data-lucide="copy" class="h-4 w-4"></i>
                        </button>
                        <button onclick="window.empresasUI.autoLoginEmpresa('${empresa.inscricao_estadual}')" 
                                class="text-green-600 hover:text-green-900"
                                title="Auto Login SEFAZ">
                            <i data-lucide="log-in" class="h-4 w-4"></i>
                        </button>
                        <button onclick="window.empresasUI.editEmpresa(${empresa.id})" 
                                class="text-blue-600 hover:text-blue-900"
                                title="Editar empresa">
                            <i data-lucide="edit" class="h-4 w-4"></i>
                        </button>
                        <button onclick="window.empresasUI.deleteEmpresa(${empresa.id})" 
                                class="text-red-600 hover:text-red-900"
                                title="Excluir empresa">
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
    const messageBotBtn = document.getElementById('messagebot-process-btn');
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
    
    if (messageBotBtn) {
        messageBotBtn.disabled = appState.selectedEmpresas.size === 0;
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
    
    // Resetar tab para Manual
    switchImportTab('manual');
    
    // Resetar estado da importação CSV
    resetCSVImport();
    
    // Garantir que os listeners estão configurados
    initializeCSVImport();
    
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
    
    // Resetar estado CSV ao fechar modal
    resetCSVImport();
    switchImportTab('manual');
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

// ================================
// IMPORTAÇÃO CSV
// ================================

let csvData = null;
let csvListenersInitialized = false;

function resetCSVImport() {
    csvData = null;
    
    const csvFileName = document.getElementById('csvFileName');
    const csvPreview = document.getElementById('csvPreview');
    const importResult = document.getElementById('importResult');
    const csvFileInput = document.getElementById('csvFileInput');
    const importBtn = document.getElementById('importarCsvBtn');
    
    if (csvFileName) {
        csvFileName.classList.add('hidden');
        csvFileName.textContent = '';
    }
    if (csvPreview) csvPreview.classList.add('hidden');
    if (importResult) {
        importResult.classList.add('hidden');
        importResult.innerHTML = '';
    }
    if (csvFileInput) csvFileInput.value = '';
    if (importBtn) importBtn.disabled = true;
}

export function initializeCSVImport() {
    // Evitar adicionar listeners múltiplas vezes
    if (csvListenersInitialized) {
        return;
    }
    
    const tabManual = document.getElementById('tabManual');
    const tabImportar = document.getElementById('tabImportar');
    const csvFileInput = document.getElementById('csvFileInput');
    
    if (tabManual) {
        tabManual.addEventListener('click', () => {
            switchImportTab('manual');
        });
    }
    
    if (tabImportar) {
        tabImportar.addEventListener('click', () => {
            switchImportTab('importar');
        });
    }
    
    if (csvFileInput) {
        csvFileInput.addEventListener('change', handleCSVFileSelect);
    }
    
    csvListenersInitialized = true;
}

function switchImportTab(tab) {
    const tabManual = document.getElementById('tabManual');
    const tabImportar = document.getElementById('tabImportar');
    const empresaForm = document.getElementById('empresaForm');
    const importarCsvForm = document.getElementById('importarCsvForm');
    
    if (!tabManual || !tabImportar || !empresaForm || !importarCsvForm) {
        return;
    }
    
    if (tab === 'manual') {
        tabManual.classList.add('border-blue-500', 'text-blue-600');
        tabManual.classList.remove('border-transparent', 'text-gray-500');
        tabImportar.classList.remove('border-blue-500', 'text-blue-600');
        tabImportar.classList.add('border-transparent', 'text-gray-500');
        empresaForm.classList.remove('hidden');
        importarCsvForm.classList.add('hidden');
    } else {
        tabImportar.classList.add('border-blue-500', 'text-blue-600');
        tabImportar.classList.remove('border-transparent', 'text-gray-500');
        tabManual.classList.remove('border-blue-500', 'text-blue-600');
        tabManual.classList.add('border-transparent', 'text-gray-500');
        empresaForm.classList.add('hidden');
        importarCsvForm.classList.remove('hidden');
    }
}

function handleCSVFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const fileName = document.getElementById('csvFileName');
    if (fileName) {
        fileName.textContent = `Arquivo selecionado: ${file.name}`;
        fileName.classList.remove('hidden');
    }
    
    // Função para detectar e limpar caracteres corrompidos
    const fixEncoding = (text) => {
        // Se encontrar caracteres corrompidos típicos de Windows-1252 lido como UTF-8
        if (text.includes('Ã§') || text.includes('Ã£') || text.includes('Ã©') || text.includes('Ã­')) {
            console.log('Detectado encoding incorreto, tentando corrigir...');
            // Tentar reconverter de UTF-8 mal interpretado para Windows-1252
            try {
                const encoder = new TextEncoder();
                const decoder = new TextDecoder('windows-1252');
                const bytes = encoder.encode(text);
                text = decoder.decode(bytes);
            } catch (e) {
                console.warn('Não foi possível corrigir encoding automaticamente');
            }
        }
        return text;
    };
    
    const processFile = (text) => {
        // Corrigir encoding se necessário
        text = fixEncoding(text);
        
        // CORREÇÃO: Remover o pré-processamento global de notação científica
        // A conversão será feita campo por campo durante o parse para proteger senhas
        
        console.log('Texto original (primeiras 500 caracteres):', text.substring(0, 500));
        
        parseCSV(text);
    };
    
    const reader = new FileReader();
    reader.onload = (e) => {
        processFile(e.target.result);
    };
    
    reader.onerror = () => {
        console.error('Erro ao ler arquivo');
        utils.showNotification('Erro ao ler arquivo CSV', 'error');
    };
    
    // Ler como UTF-8 (o navegador tentará detectar automaticamente)
    reader.readAsText(file);
}

function parseCSV(text) {
    const lines = text.split('\n').filter(line => line.trim());
    if (lines.length < 2) {
        utils.showNotification('Arquivo CSV vazio ou inválido', 'error');
        return;
    }
    
    // Detectar o delimitador automaticamente
    const firstLine = lines[0];
    // Contar occorrências de cada delimitador
    const tabCount = (firstLine.match(/\t/g) || []).length;
    const commaCount = (firstLine.match(/,/g) || []).length;
    const semicolonCount = (firstLine.match(/;/g) || []).length;
    
    // Usar o delimitador que aparece mais vezes
    let delimiter = ',';
    let maxCount = commaCount;
    
    if (tabCount > maxCount) {
        delimiter = '\t';
        maxCount = tabCount;
    }
    
    if (semicolonCount > maxCount) {
        delimiter = ';';
        maxCount = semicolonCount;
    }
    
    console.log('Delimitador detectado:', delimiter === '\t' ? 'TAB' : delimiter === ';' ? 'PONTO E VÍRGULA' : 'VÍRGULA');
    console.log(`Contagem: TABs=${tabCount}, VÍRGULAs=${commaCount}, PONTO E VÍRGULA=${semicolonCount}`);
    
    // Parser CSV que lida com valores entre aspas
    const parseCSVLine = (line) => {
        const values = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            const nextChar = line[i + 1];
            
            if (char === '"') {
                if (inQuotes && nextChar === '"') {
                    // Aspas duplas escapadas
                    current += '"';
                    i++; // Pular próximo caractere
                } else {
                    // Toggle estado de aspas
                    inQuotes = !inQuotes;
                }
            } else if (char === delimiter && !inQuotes) {
                // Fim do campo
                values.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        
        // Adicionar último campo
        values.push(current.trim());
        
        return values;
    };
    
    // CORREÇÃO: Função específica para converter notação científica apenas para campos numéricos
    const convertScientificNotationForNumericFields = (value, fieldName) => {
        if (!value || value === '') return '';
        
        // Remover aspas se houver
        value = value.replace(/^["']|["']$/g, '').trim();
        
        // IMPORTANTE: Só converter notação científica para campos que são realmente números
        // SENHA NÃO DEVE SER CONVERTIDA
        const numericFields = ['cnpj', 'inscricao_estadual', 'cpf_socio'];
        
        if (!numericFields.includes(fieldName)) {
            // Para campos não numéricos (como senha), retornar o valor original
            return value;
        }
        
        // Verificar se tem notação científica
        if (!/[eE][+-]?\d+/.test(value)) {
            return value;
        }
        
        // Converter apenas para campos numéricos
        const normalizedValue = value.replace(',', '.');
        
        try {
            const number = parseFloat(normalizedValue);
            if (!isNaN(number)) {
                return number.toFixed(0);
            }
        } catch (e) {
            console.error('Erro ao converter notação científica:', value, e);
        }
        
        return value;
    };
    
    const headers = parseCSVLine(lines[0]).map(h => h.trim().toLowerCase().replace(/\s+/g, '_').replace(/^["']|["']$/g, ''));
    const expectedHeaders = ['nome_empresa', 'cnpj', 'inscricao_estadual', 'cpf_socio', 'senha', 'observacoes'];
    
    console.log('Headers encontrados:', headers);
    console.log('Headers esperados:', expectedHeaders);
    
    // Verificar se todos os headers esperados estão presentes
    const missingHeaders = expectedHeaders.filter(h => !headers.includes(h));
    if (missingHeaders.length > 0) {
        utils.showNotification(`Arquivo CSV com colunas faltando: ${missingHeaders.join(', ')}. Headers encontrados: ${headers.join(', ')}`, 'error');
        return;
    }
    
    csvData = [];
    for (let i = 1; i < lines.length; i++) {
        const values = parseCSVLine(lines[i]);
        
        // Pular linhas vazias ou com número incorreto de colunas
        if (values.length === 0 || values.every(v => !v)) {
            console.warn(`Linha ${i+1} vazia, ignorando`);
            continue;
        }
        
        if (values.length !== headers.length) {
            console.warn(`Linha ${i+1} ignorada: número incorreto de colunas (${values.length} vs ${headers.length})`);
            console.warn(`Valores:`, values);
            continue;
        }
        
        const row = {};
        headers.forEach((header, index) => {
            let value = values[index];
            
            // CORREÇÃO: Aplicar conversão de notação científica apenas para campos específicos
            value = convertScientificNotationForNumericFields(value, header);
            
            // Log específico para senha para debug
            if (header === 'senha') {
                console.log(`Linha ${i+1} - Senha processada: "${values[index]}" -> "${value}"`);
            }
            
            row[header] = value;
        });
        
        csvData.push(row);
    }
    
    // Verificar duplicados dentro do próprio CSV
    const cnpjMap = new Map();
    const duplicadosNoCSV = [];
    
    csvData.forEach((row, index) => {
        const cnpj = row.cnpj;
        if (cnpjMap.has(cnpj)) {
            duplicadosNoCSV.push({
                linha: index + 2, // +2 porque index é 0-based e primeira linha é header
                nome: row.nome_empresa,
                cnpj: cnpj,
                primeiraOcorrencia: cnpjMap.get(cnpj)
            });
        } else {
            cnpjMap.set(cnpj, index + 2);
        }
    });
    
    // Avisar sobre duplicados no CSV
    if (duplicadosNoCSV.length > 0) {
        const mensagem = duplicadosNoCSV.map(d => 
            `Linha ${d.linha}: "${d.nome}" (CNPJ: ${d.cnpj}) duplicado da linha ${d.primeiraOcorrencia}`
        ).join('\n');
        
        utils.showNotification(`⚠️ Encontrados ${duplicadosNoCSV.length} CNPJs duplicados no arquivo CSV:\n${mensagem}`, 'error');
        console.warn('Duplicados no CSV:', duplicadosNoCSV);
    }
    
    showCSVPreview(csvData, headers);
    
    console.log('CSV parseado com sucesso:', csvData.length, 'linhas');
    console.log('Primeira linha:', csvData[0]);
    
    const importBtn = document.getElementById('importarCsvBtn');
    if (importBtn) {
        importBtn.disabled = false;
    }
}

function showCSVPreview(data, headers) {
    const preview = document.getElementById('csvPreview');
    const previewHeader = document.getElementById('csvPreviewHeader');
    const previewBody = document.getElementById('csvPreviewBody');
    const totalRows = document.getElementById('csvTotalRows');
    
    if (!preview || !previewHeader || !previewBody) return;
    
    // Mostrar cabeçalho
    previewHeader.innerHTML = `
        <tr>
            ${headers.map(h => `<th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">${h}</th>`).join('')}
        </tr>
    `;
    
    // Mostrar primeiras 5 linhas
    const previewData = data.slice(0, 5);
    previewBody.innerHTML = previewData.map(row => `
        <tr>
            ${headers.map(h => `<td class="px-4 py-2 text-sm text-gray-900">${row[h] || ''}</td>`).join('')}
        </tr>
    `).join('');
    
    if (totalRows) {
        totalRows.textContent = `Total de ${data.length} empresa${data.length !== 1 ? 's' : ''} para importar`;
    }
    
    preview.classList.remove('hidden');
}

export async function importarCSV() {
    if (!csvData || csvData.length === 0) {
        utils.showNotification('Nenhum dado para importar', 'error');
        return;
    }
    
    console.log('Iniciando importação de', csvData.length, 'empresas');
    console.log('Dados a enviar:', csvData);
    
    const importBtn = document.getElementById('importarCsvBtn');
    const resultDiv = document.getElementById('importResult');
    
    if (importBtn) {
        importBtn.disabled = true;
        importBtn.innerHTML = '<i data-lucide="loader" class="h-4 w-4 mr-2 animate-spin"></i> Importando...';
    }
    
    try {
        const result = await api.importarEmpresasCSV(csvData);
        
        if (resultDiv) {
            // Determinar a cor e ícone baseado no resultado
            const hasSuccess = result.sucesso > 0;
            const hasErrors = result.erros > 0;
            const allFailed = result.sucesso === 0 && result.erros > 0;
            
            const bgColor = allFailed ? 'bg-red-50' : hasSuccess ? 'bg-green-50' : 'bg-yellow-50';
            const borderColor = allFailed ? 'border-red-200' : hasSuccess ? 'border-green-200' : 'border-yellow-200';
            const iconColor = allFailed ? 'text-red-600' : hasSuccess ? 'text-green-600' : 'text-yellow-600';
            const iconName = allFailed ? 'x-circle' : hasSuccess ? 'check-circle' : 'alert-circle';
            const titleColor = allFailed ? 'text-red-900' : hasSuccess ? 'text-green-900' : 'text-yellow-900';
            const titleText = allFailed ? 'Nenhuma empresa importada!' : hasSuccess && !hasErrors ? 'Importação concluída!' : 'Importação concluída com avisos';
            
            resultDiv.innerHTML = `
                <div class="${bgColor} border ${borderColor} rounded-lg p-4">
                    <div class="flex items-start">
                        <i data-lucide="${iconName}" class="h-5 w-5 ${iconColor} mr-3 mt-0.5"></i>
                        <div class="flex-1">
                            <h4 class="text-sm font-medium ${titleColor}">${titleText}</h4>
                            <div class="mt-2 text-sm">
                                ${result.sucesso > 0 ? `<p class="text-green-700">✓ ${result.sucesso} empresa${result.sucesso !== 1 ? 's' : ''} importada${result.sucesso !== 1 ? 's' : ''} com sucesso</p>` : ''}
                                ${result.erros > 0 ? `<p class="text-red-700">✗ ${result.erros} ${allFailed ? 'empresa' : 'erro'}${result.erros !== 1 ? 's' : ''} ${allFailed ? 'não foi importada (já existe no sistema)' : ''}</p>` : ''}
                            </div>
                            ${result.detalhes && result.detalhes.length > 0 ? `
                                <details class="mt-3" ${allFailed ? 'open' : ''}>
                                    <summary class="text-sm font-medium cursor-pointer ${allFailed ? 'text-red-800' : 'text-green-800'} hover:underline">
                                        ${allFailed ? 'Ver empresas não importadas' : 'Ver detalhes da importação'}
                                    </summary>
                                    <ul class="mt-2 text-xs space-y-1 max-h-60 overflow-y-auto">
                                        ${result.detalhes.map(d => `<li class="${d.includes('✓') ? 'text-green-700' : 'text-red-700'}">${d}</li>`).join('')}
                                    </ul>
                                </details>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
            resultDiv.classList.remove('hidden');
            lucide.createIcons();
        }
        
        // Notificação baseada no resultado
        if (result.sucesso === 0 && result.erros > 0) {
            utils.showNotification(
                `❌ Nenhuma empresa foi importada. ${result.erros} empresa${result.erros !== 1 ? 's' : ''} já existe${result.erros === 1 ? '' : 'm'} no sistema.`,
                'error'
            );
        } else if (result.sucesso > 0 && result.erros === 0) {
            utils.showNotification(
                `✅ ${result.sucesso} empresa${result.sucesso !== 1 ? 's' : ''} importada${result.sucesso !== 1 ? 's' : ''} com sucesso!`,
                'success'
            );
        } else if (result.sucesso > 0 && result.erros > 0) {
            utils.showNotification(
                `⚠️ Importação parcial: ${result.sucesso} importada${result.sucesso !== 1 ? 's' : ''}, ${result.erros} já existente${result.erros !== 1 ? 's' : ''}`,
                'error'
            );
        }
        
        // Fechar modal e recarregar lista após sucesso parcial ou total
        if (result.sucesso > 0) {
            setTimeout(() => {
                closeEmpresaModal();
                loadEmpresas();
            }, 3000);
        }
        
    } catch (error) {
        console.error('Erro ao importar CSV:', error);
        console.error('Stack:', error.stack);
        
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div class="flex items-start">
                        <i data-lucide="x-circle" class="h-5 w-5 text-red-600 mr-3 mt-0.5"></i>
                        <div>
                            <h4 class="text-sm font-medium text-red-900">Erro na importação</h4>
                            <p class="mt-1 text-sm text-red-700">${error.message || 'Erro desconhecido'}</p>
                        </div>
                    </div>
                </div>
            `;
            resultDiv.classList.remove('hidden');
            lucide.createIcons();
        }
        
        utils.showNotification('Erro ao importar empresas', 'error');
    } finally {
        if (importBtn) {
            importBtn.disabled = false;
            importBtn.innerHTML = '<i data-lucide="upload" class="h-4 w-4 mr-2"></i> Importar Empresas';
            lucide.createIcons();
        }
    }
}

// Função de auto-login SEFAZ (idêntica à das mensagens)
export async function autoLoginEmpresa(inscricaoEstadual) {
    try {
        if (!inscricaoEstadual) {
            utils.showNotification('Inscrição estadual não informada', 'error');
            return;
        }

        // Buscar credenciais da empresa
        const empresa = await api.get(`/api/empresas/credenciais-por-ie/${inscricaoEstadual}`);
        
        const cpf = empresa.cpf_socio;
        const senha = empresa.senha;

        if (!senha) {
            utils.showNotification('Senha não disponível para esta empresa', 'error');
            return;
        }

        // Extrair link do recibo - primeiro tentar do banco, depois do conteúdo
        let linkRecibo = empresa.link_recibo;
        
        if (!linkRecibo && empresa.conteudo_mensagem) {
            console.log('⚠️ Link não encontrado no banco, tentando extrair do conteúdo...');
            
            // Tentar várias regex para pegar o link
            const regex1 = /href="([^"]*listIReciboDief\.do[^"]*)">/i;
            const regex2 = /href='([^']*listIReciboDief\.do[^']*)'>/i;
            const regex3 = /(https?:\/\/[^"'\s]*listIReciboDief\.do[^"'\s]*)/i;
            
            let match = empresa.conteudo_mensagem.match(regex1);
            if (!match) match = empresa.conteudo_mensagem.match(regex2);
            if (!match) match = empresa.conteudo_mensagem.match(regex3);
            
            if (match) {
                linkRecibo = match[1].replace(/&amp;/g, '&');
                console.log('✅ Link do recibo extraído do conteúdo:', linkRecibo);
            }
        }

        // Abrir SEFAZ em nova aba
        const sefazWindow = window.open('https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin', '_blank');
        
        if (!sefazWindow) {
            utils.showNotification('Popup bloqueado! Permita popups para este site.', 'error');
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
                        utils.showNotification('Recibo DIEF aberto! 📄', 'success');
                    } else {
                        console.error('❌ Falha ao abrir recibo - popup bloqueado?');
                        utils.showNotification('Popup bloqueado! Permita popups e tente novamente.', 'error');
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
            utils.showNotification('Fazendo login automaticamente! 🚀', 'success');
        }, 3000);

    } catch (error) {
        console.error('Erro ao abrir SEFAZ:', error);
        utils.showNotification('Erro ao buscar credenciais da empresa', 'error');
    }
}

export async function copyCredentials(empresaId) {
    try {
        // Buscar credenciais da empresa
        const credenciais = await api.fetchCredenciaisEmpresa(empresaId);
        
        // Formatar os dados para cópia - CPF sem pontos
        const cpfLimpo = credenciais.cpf_socio.replace(/\D/g, '');
        const dadosAcesso = `CPF: ${cpfLimpo}\nSenha: ${credenciais.senha}`;
        
        // Copiar para clipboard
        try {
            await navigator.clipboard.writeText(dadosAcesso);
            utils.showNotification(`Dados de acesso copiados para a área de transferência!\n${credenciais.nome_empresa}`, 'success');
        } catch (clipboardError) {
            // Fallback para navegadores que não suportam clipboard API
            const textArea = document.createElement('textarea');
            textArea.value = dadosAcesso;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                document.execCommand('copy');
                utils.showNotification(`Dados de acesso copiados!\n${credenciais.nome_empresa}`, 'success');
            } catch (execError) {
                console.error('Erro ao copiar:', execError);
                // Mostrar modal com os dados para cópia manual
                showCredentialsModal(credenciais);
            }
            
            document.body.removeChild(textArea);
        }
        
    } catch (error) {
        console.error('Erro ao buscar credenciais:', error);
        utils.showNotification('Erro ao buscar dados de acesso da empresa', 'error');
    }
}

function showCredentialsModal(credenciais) {
    const cpfLimpo = credenciais.cpf_socio.replace(/\D/g, '');
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50';
    modal.innerHTML = `
        <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div class="mt-3">
                <h3 class="text-lg font-medium text-gray-900 mb-4">Dados de Acesso</h3>
                <div class="bg-gray-50 p-4 rounded-md mb-4">
                    <p class="text-sm font-medium text-gray-700 mb-2">Empresa: ${credenciais.nome_empresa}</p>
                    <p class="text-sm text-gray-600 mb-2">CPF: <span class="font-mono">${cpfLimpo}</span></p>
                    <p class="text-sm text-gray-600">Senha: <span class="font-mono">${credenciais.senha}</span></p>
                </div>
                <p class="text-xs text-gray-500 mb-4">Copie manualmente os dados acima</p>
                <div class="flex justify-end">
                    <button onclick="this.closest('.fixed').remove()" 
                            class="btn-secondary">
                        Fechar
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Fechar modal ao clicar fora
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    utils.initLucideIcons();
}

// ================================
// MESSAGEBOT FUNCTIONS
// ================================

/**
 * Processa mensagens para empresas selecionadas usando o MessageBot
 */
export async function processarMensagensEmpresas() {
    const selectedEmpresas = Array.from(appState.selectedEmpresas);
    
    if (selectedEmpresas.length === 0) {
        utils.showNotification('Selecione pelo menos uma empresa', 'error');
        return;
    }
    
    if (!confirm(`Processar mensagens para ${selectedEmpresas.length} empresa(s) selecionada(s)?`)) {
        return;
    }
    
    try {
        showMessageBotProgress(true, `Iniciando processamento de ${selectedEmpresas.length} empresa(s)...`);
        
        let sucessos = 0;
        let erros = 0;
        
        for (let i = 0; i < selectedEmpresas.length; i++) {
            const empresaId = selectedEmpresas[i];
            const empresa = appState.empresasData.find(e => e.id === empresaId);
            
            if (!empresa) continue;
            
            try {
                const progress = Math.round(((i + 1) / selectedEmpresas.length) * 100);
                showMessageBotProgress(true, `Processando ${empresa.nome_empresa} (${i + 1}/${selectedEmpresas.length})...`, progress);
                
                // Buscar credenciais da empresa
                const credenciais = await api.fetchCredenciaisEmpresa(empresaId);
                
                if (!credenciais.senha) {
                    throw new Error('Senha não configurada para esta empresa');
                }
                
                // Processar mensagens
                const result = await api.processarMensagensEmpresa({
                    cpf: credenciais.cpf_socio,
                    senha: credenciais.senha,
                    inscricao_estadual: credenciais.inscricao_estadual,
                    headless: true
                });
                
                if (result.sucesso) {
                    sucessos++;
                    console.log(`✅ ${empresa.nome_empresa}: ${result.mensagens_processadas} mensagens processadas`);
                } else {
                    erros++;
                    console.error(`❌ ${empresa.nome_empresa}: ${result.mensagem}`);
                }
                
            } catch (error) {
                erros++;
                console.error(`❌ ${empresa.nome_empresa}: ${error.message}`);
            }
        }
        
        showMessageBotProgress(false);
        
        // Resultado final
        if (sucessos > 0 || erros > 0) {
            const resultMessage = `Processamento concluído: ${sucessos} sucesso(s), ${erros} erro(s)`;
            utils.showNotification(resultMessage, sucessos > 0 ? 'success' : 'warning');
        }
        
        // Limpar seleções
        appState.selectedEmpresas.clear();
        updateSelectionInfo();
        updateEmpresasTable(appState.empresasData);
        
    } catch (error) {
        showMessageBotProgress(false);
        console.error('Erro no processamento de mensagens:', error);
        utils.showNotification(`Erro no processamento: ${error.message}`, 'error');
    }
}

/**
 * Mostra/esconde o indicador de progresso do MessageBot
 */
function showMessageBotProgress(show, message = 'Processando...', progress = 0) {
    const progressDiv = document.getElementById('messagebot-progress');
    const messageSpan = document.getElementById('messagebot-status');
    const progressBar = document.getElementById('messagebot-progress-bar');
    const processBtn = document.getElementById('messagebot-process-btn');
    
    if (show) {
        if (progressDiv) progressDiv.classList.remove('hidden');
        if (messageSpan) messageSpan.textContent = message;
        if (progressBar) progressBar.style.width = `${progress}%`;
        if (processBtn) {
            processBtn.disabled = true;
            processBtn.classList.add('opacity-50');
        }
    } else {
        if (progressDiv) progressDiv.classList.add('hidden');
        if (processBtn) {
            processBtn.disabled = false;
            processBtn.classList.remove('opacity-50');
        }
    }
}

/**
 * Mostra estatísticas de mensagens para empresa selecionada
 */
export async function showMensagensStats(empresaId) {
    try {
        const empresa = appState.empresasData.find(e => e.id === empresaId);
        if (!empresa) return;
        
        const stats = await api.fetchMensagensEstatisticas(empresa.inscricao_estadual);
        
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50';
        modal.innerHTML = `
            <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
                <div class="mt-3">
                    <h3 class="text-lg font-medium text-gray-900 mb-4">Estatísticas de Mensagens</h3>
                    <div class="bg-gray-50 p-4 rounded-md mb-4">
                        <p class="text-sm font-medium text-gray-700 mb-2">Empresa: ${empresa.nome_empresa}</p>
                        <p class="text-sm text-gray-600 mb-2">IE: ${empresa.inscricao_estadual}</p>
                        <hr class="my-3">
                        <div class="grid grid-cols-3 gap-4 text-center">
                            <div>
                                <p class="text-lg font-bold text-blue-600">${stats.total}</p>
                                <p class="text-xs text-gray-500">Total</p>
                            </div>
                            <div>
                                <p class="text-lg font-bold text-green-600">${stats.hoje}</p>
                                <p class="text-xs text-gray-500">Hoje</p>
                            </div>
                            <div>
                                <p class="text-lg font-bold text-purple-600">${stats.semana}</p>
                                <p class="text-xs text-gray-500">7 dias</p>
                            </div>
                        </div>
                    </div>
                    <div class="flex justify-end">
                        <button onclick="this.closest('.fixed').remove()" class="btn-secondary">Fechar</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
    } catch (error) {
        console.error('Erro ao buscar estatísticas de mensagens:', error);
        utils.showNotification('Erro ao buscar estatísticas de mensagens', 'error');
    }
}

// Create empresasUI object and expose globally
const empresasUI = {
    loadEmpresas,
    applyEmpresasFilters,
    clearEmpresasFilters,
    showAddEmpresaModal,
    editEmpresa,
    closeEmpresaModal,
    saveEmpresa,
    deleteEmpresa,
    addSelectedToQueue,
    nextEmpresasPage,
    prevEmpresasPage,
    changeEmpresasItemsPerPage,
    initializeCSVImport,
    importarCSV,
    autoLoginEmpresa,
    copyCredentials,
    processarMensagensEmpresas,
    showMensagensStats
};

window.empresasUI = empresasUI;
