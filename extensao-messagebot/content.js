// Content Script - SEFAZ MessageBot
console.log('🤖 SEFAZ MessageBot - Content script carregado');
console.log('📍 URL:', window.location.href);

// Proteção contra erros da página do SEFAZ (silenciar completamente)
window.addEventListener('error', function(e) {
    // Ignorar TODOS os erros do domínio SEFAZ (adrum.js, inicializaForm, etc)
    const ignoredErrors = [
        'adrum.js',
        'inicializaForm',
        'login.do',
        'SyntaxError',
        'Failed to load resource'
    ];
    
    const shouldIgnore = ignoredErrors.some(err => 
        e.message?.includes(err) || 
        e.filename?.includes(err) ||
        e.error?.stack?.includes(err)
    );
    
    if (shouldIgnore) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        return true;
    }
}, true);

// Proteção contra erros de MutationObserver
const originalConsoleError = console.error;
console.error = function(...args) {
    const message = args.join(' ');
    if (message.includes('MutationObserver') || 
        message.includes('observe') ||
        message.includes('not of type')) {
        return; // Silenciar
    }
    originalConsoleError.apply(console, args);
};

// Funcao auxiliar
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Simular digitação humana
async function digitarComoHumano(campo, texto) {
    campo.value = '';
    campo.focus();
    
    for (let i = 0; i < texto.length; i++) {
        campo.value += texto[i];
        campo.dispatchEvent(new Event('input', { bubbles: true }));
        // Delay aleatório entre 80-150ms por caractere
        await sleep(80 + Math.random() * 70);
    }
    
    campo.dispatchEvent(new Event('change', { bubbles: true }));
    campo.blur();
}

// ============================================
// SISTEMA DE DEBUG E DESCOBERTA
// ============================================

// Função principal de debug que analisa toda a página
function debugPage() {
    console.log('🔬 === DEBUG DA PÁGINA ===');
    console.log('📍 URL:', window.location.href);
    console.log('📄 Title:', document.title);
    
    // Selects
    const selects = document.querySelectorAll('select');
    console.log(`\n📊 SELECTS (${selects.length}):`);
    selects.forEach((sel, i) => {
        const options = Array.from(sel.options).map(o => `${o.value}:"${o.text}"`);
        console.log(`  ${i}. name="${sel.name}" id="${sel.id}"`);
        console.log(`     options: [${options.join(', ')}]`);
    });
    
    // Links
    const links = document.querySelectorAll('a');
    console.log(`\n🔗 LINKS (${links.length} total, mostrando relevantes):`);
    links.forEach((link, i) => {
        const href = link.href;
        const onclick = link.getAttribute('onclick');
        const texto = link.textContent.trim();
        if (href?.includes('mensagem') || onclick?.includes('mensagem') || texto.toLowerCase().includes('mensag')) {
            console.log(`  ${i}. "${texto}" href="${href}" onclick="${onclick}"`);
        }
    });
    
    // Botões
    const botoes = document.querySelectorAll('button, input[type="button"], input[type="submit"]');
    console.log(`\n🔘 BOTÕES (${botoes.length}):`);
    botoes.forEach((btn, i) => {
        const texto = btn.textContent || btn.value || '';
        const onclick = btn.getAttribute('onclick');
        console.log(`  ${i}. "${texto}" onclick="${onclick}"`);
    });
    
    // Tabelas
    const tabelas = document.querySelectorAll('table');
    console.log(`\n📋 TABELAS (${tabelas.length}):`);
    tabelas.forEach((tab, i) => {
        const classe = tab.className;
        const rows = tab.querySelectorAll('tr').length;
        console.log(`  ${i}. class="${classe}" rows=${rows}`);
    });
    
    // Avisos vermelhos
    console.log('\n⚠️ PROCURANDO AVISOS:');
    const fontVermelho = document.querySelectorAll('font[color="red"], font[color="#FF0000"]');
    console.log(`  font vermelho: ${fontVermelho.length}`);
    fontVermelho.forEach((f, i) => console.log(`    ${i}. "${f.textContent.trim()}"`));
    
    const estiloVermelho = document.querySelectorAll('[style*="color: red"], [style*="color:#ff0000"]');
    console.log(`  estilo vermelho: ${estiloVermelho.length}`);
    
    // Busca por texto "aguardando ciência"
    const textoCompleto = document.body.textContent;
    const temAviso = /aguardando\s+ci[êe]ncia/i.test(textoCompleto);
    console.log(`  texto "aguardando ciência": ${temAviso}`);
    
    console.log('🔬 === FIM DEBUG ===\n');
}

// Analisa especificamente a página de mensagens
function analisarPaginaMensagens() {
    console.log('📨 === ANÁLISE PÁGINA DE MENSAGENS ===');
    
    // Descobrir select de filtro
    const selects = document.querySelectorAll('select');
    console.log(`\n🔽 Analisando ${selects.length} selects:`);
    
    let selectFiltro = null;
    selects.forEach((sel, i) => {
        const options = Array.from(sel.options).map(o => ({
            value: o.value,
            text: o.text
        }));
        console.log(`  Select ${i}: name="${sel.name}" id="${sel.id}"`);
        options.forEach(opt => {
            console.log(`    - ${opt.value}: "${opt.text}"`);
        });
        
        // Identificar select do SEFAZ-MA pelo name
        if (sel.name === 'visualizarMensagens') {
            console.log(`    ✅ Este é o select de filtro do SEFAZ-MA (name="visualizarMensagens")!`);
            selectFiltro = sel;
        }
        
        // Fallback: verificar se tem opções de filtro de mensagem
        const temNaoLidas = options.some(o => o.text.includes('Não Lidas') || o.text.includes('Nao Lidas'));
        const temAguardando = options.some(o => o.text.includes('Aguardando'));
        
        if ((temNaoLidas || temAguardando) && !selectFiltro) {
            console.log(`    ✅ Este parece ser o select de filtro (fallback)!`);
            selectFiltro = sel;
        }
    });
    
    // Descobrir links de mensagens
    console.log('\n📧 Procurando links de mensagens:');
    const todosLinks = document.querySelectorAll('a');
    const linksMensagem = [];
    
    todosLinks.forEach((link, i) => {
        const href = link.href || '';
        const onclick = link.getAttribute('onclick') || '';
        const texto = link.textContent.trim();
        
        // Tentar vários padrões
        if (href.includes('abrirMensagem') || 
            href.includes('mensagem.do') ||
            href.includes('detalhe') ||
            onclick.includes('abrir') ||
            onclick.includes('mensagem')) {
            linksMensagem.push({
                index: i,
                href: href,
                onclick: onclick,
                texto: texto
            });
        }
    });
    
    console.log(`  Encontrados ${linksMensagem.length} links de mensagem:`);
    linksMensagem.forEach((link, i) => {
        console.log(`    ${i}. "${link.texto}"`);
        console.log(`       href: ${link.href}`);
        console.log(`       onclick: ${link.onclick}`);
    });
    
    // Estrutura da tabela de mensagens
    console.log('\n📋 Estrutura de tabelas:');
    const tabelas = document.querySelectorAll('table');
    tabelas.forEach((tab, i) => {
        const rows = tab.querySelectorAll('tr').length;
        const cells = tab.querySelectorAll('td').length;
        const classe = tab.className;
        console.log(`  Tabela ${i}: class="${classe}" rows=${rows} cells=${cells}`);
        
        // Se tiver muitas linhas, provavelmente é a tabela de mensagens
        if (rows > 2) {
            console.log(`    ✅ Esta pode ser a tabela de mensagens`);
            const primeiraLinha = tab.querySelector('tr:nth-child(2)'); // pular header
            if (primeiraLinha) {
                console.log(`    Primeira linha: ${primeiraLinha.textContent.trim().substring(0, 100)}`);
            }
        }
    });
    
    console.log('📨 === FIM ANÁLISE ===\n');
    
    return {
        selectFiltro: selectFiltro,
        linksMensagem: linksMensagem,
        totalSelects: selects.length,
        totalLinks: todosLinks.length
    };
}

// Descobre o select de filtro real
function descobrirSelectFiltro() {
    console.log('🔍 Descobrindo select de filtro...');
    
    const selects = document.querySelectorAll('select');
    
    for (const select of selects) {
        // Verificar pelo name específico do SEFAZ-MA
        if (select.name === 'visualizarMensagens') {
            console.log('✅ Select de filtro encontrado pelo name "visualizarMensagens"');
            const options = Array.from(select.options);
            console.log('   Opções:', options.map(o => `${o.value}:"${o.text}"`));
            return select;
        }
        
        // Fallback: verificar por opções
        const options = Array.from(select.options);
        const textos = options.map(o => o.text.toLowerCase());
        
        // Verificar se tem opções relacionadas a mensagens
        const temNaoLidas = textos.some(t => t.includes('não lidas') || t.includes('nao lidas'));
        const temAguardando = textos.some(t => t.includes('aguardando'));
        const temTodas = textos.some(t => t.includes('todas'));
        
        if (temNaoLidas || temAguardando || temTodas) {
            console.log('✅ Select de filtro encontrado por opções:', {
                name: select.name,
                id: select.id,
                options: options.map(o => `${o.value}:"${o.text}"`)
            });
            return select;
        }
    }
    
    console.log('❌ Select de filtro não encontrado');
    return null;
}

// Descobre links de mensagens
function descobrirLinksMensagem() {
    console.log('🔍 Descobrindo links de mensagens...');
    
    const todosLinks = document.querySelectorAll('a');
    const linksMensagem = [];
    
    for (const link of todosLinks) {
        const href = link.href || '';
        const onclick = link.getAttribute('onclick') || '';
        
        // Múltiplos padrões
        const padroes = [
            'abrirMensagem',
            'mensagem.do?',
            'detalhe',
            'visualizar'
        ];
        
        const match = padroes.some(p => href.includes(p) || onclick.includes(p));
        
        if (match) {
            linksMensagem.push(link);
        }
    }
    
    console.log(`✅ Encontrados ${linksMensagem.length} links de mensagem`);
    return linksMensagem;
}

// Descobre botão de ciência
function descobrirBotaoCiencia() {
    console.log('🔍 Descobrindo botão de ciência...');
    
    const elementos = document.querySelectorAll('button, input[type="button"], input[type="submit"], a');
    
    console.log(`  Analisando ${elementos.length} elementos...`);
    
    for (const el of elementos) {
        const texto = (el.textContent || el.value || '').toLowerCase();
        const onclick = (el.getAttribute('onclick') || '').toLowerCase();
        
        if (texto.includes('cienc') || texto.includes('ciente') || 
            onclick.includes('cienc') || onclick.includes('ciente')) {
            console.log('✅ Botão de ciência encontrado:', {
                tag: el.tagName,
                texto: el.textContent || el.value,
                onclick: el.getAttribute('onclick')
            });
            return el;
        }
    }
    
    console.log('❌ Botão de ciência não encontrado');
    return null;
}

// Modo descoberta completo
async function modoDescoberta() {
    console.log('🔬 === MODO DESCOBERTA ATIVADO ===');
    
    debugPage();
    
    await sleep(1000);
    
    const analise = analisarPaginaMensagens();
    
    console.log('\n📊 RESUMO DA DESCOBERTA:');
    console.log('  Select filtro:', analise.selectFiltro ? 'ENCONTRADO ✅' : 'NÃO ENCONTRADO ❌');
    console.log('  Links mensagem:', analise.linksMensagem.length, analise.linksMensagem.length > 0 ? '✅' : '❌');
    
    console.log('🔬 === FIM MODO DESCOBERTA ===\n');
    
    return analise;
}

// Listener para mensagens do frontend (postMessage)
window.addEventListener('message', async (event) => {
    // Ignorar mensagens de outras extensões (WXT, etc)
    if (event.data.type && (
        event.data.type.includes('wxt:content-script') ||
        event.data.type.includes('content-script-started') ||
        event.data.contentScriptName
    )) {
        return;
    }
    
    console.log('📨 postMessage recebido:', event.data);
    
    if (event.data.type === 'SEFAZ_PROCESSAR_MENSAGENS') {
        console.log('✅ Processar mensagens solicitado');
        
        const { cpf, cpfSocio, senha, inscricao_estadual, inscricaoEstadual } = event.data;
        
        await sleep(1000);
        
        // Fazer login primeiro
        const campoUsuario = document.querySelector('input[name="identificacao"]');
        if (campoUsuario) {
            campoUsuario.value = cpf;
            campoUsuario.dispatchEvent(new Event('input', { bubbles: true }));
            console.log('✅ CPF preenchido:', cpf);
        }
        
        const campoSenha = document.querySelector('input[name="senha"]');
        if (campoSenha) {
            campoSenha.value = senha;
            campoSenha.dispatchEvent(new Event('input', { bubbles: true }));
            console.log('✅ Senha preenchida');
        }
        
        await sleep(500);
        
        const botaoEntrar = document.querySelector('button[type="submit"]');
        if (botaoEntrar) {
            botaoEntrar.click();
            console.log('✅ Login iniciado');
            
            // Aguardar login e processar mensagens
            await aguardarLoginEProcessarMensagens(
                cpfSocio || cpf,
                inscricaoEstadual || inscricao_estadual
            );
        }
    }
});

// Listener para mensagens da extensao (chrome.runtime)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('🔔 Mensagem da extensao recebida:', request);
    console.log('🔔 Action:', request?.action);
    console.log('🔔 Dados:', request?.dados);
    
    if (request.action === 'processarMensagensFluxo') {
        console.log('✅ Acao processarMensagensFluxo detectada - INICIANDO FLUXO');
        
        // Executar fluxo do MessageBot
        handleMessageBotFluxo(request.dados)
            .then(result => {
                console.log('✅ MessageBot concluido:', result);
                sendResponse({
                    success: true,
                    data: result
                });
            })
            .catch(error => {
                console.error('❌ MessageBot falhou:', error);
                sendResponse({
                    success: false,
                    error: error.message || 'Erro no processamento de mensagens'
                });
            });
        
        return true; // Indicar resposta assincrona
    }
    
    console.log('⚠️ Action não reconhecida:', request?.action);
    return false;
});

// Aguardar login e processar mensagens
async function aguardarLoginEProcessarMensagens(cpfSocio, inscricaoEstadual) {
    console.log('Aguardando login para processar mensagens...');
    
    let tentativas = 0;
    const maxTentativas = 40;
    
    const intervalo = setInterval(async () => {
        tentativas++;
        
        const formularioLogin = document.querySelector('input[name="identificacao"]');
        const paginaPrincipal = document.querySelector('#principal, .menu-principal, #menu');
        
        if (!formularioLogin || paginaPrincipal) {
            clearInterval(intervalo);
            console.log('Login completado! Iniciando MessageBot...');
            
            try {
                const resultado = await handleMessageBotFluxo({
                    cpfSocio: cpfSocio,
                    cpf_socio: cpfSocio,
                    inscricaoEstadual: inscricaoEstadual,
                    inscricao_estadual: inscricaoEstadual
                });
                
                // Notificar conclusao
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'SEFAZ_MENSAGENS_PROCESSADAS',
                        resultado: resultado
                    }, '*');
                }
            } catch (error) {
                console.error('Erro ao processar mensagens:', error);
                if (window.opener) {
                    window.opener.postMessage({
                        type: 'SEFAZ_MENSAGENS_ERRO',
                        error: error.message
                    }, '*');
                }
            }
        }
        
        if (tentativas >= maxTentativas) {
            clearInterval(intervalo);
            console.error('Timeout login MessageBot');
            if (window.opener) {
                window.opener.postMessage({
                    type: 'SEFAZ_MENSAGENS_ERRO',
                    error: 'Timeout no login'
                }, '*');
            }
        }
    }, 500);
}

// ============================================
// MESSAGEBOT - Processamento de Mensagens SEFAZ
// ============================================

async function handleMessageBotFluxo(dados) {
    console.log('🚀 === INICIANDO MESSAGEBOT ===');
    console.log('📋 Dados:', dados);
    
    try {
        // 1. Verificar se está na página de login
        console.log('⏳ 1. Aguardando carregamento completo...');
        await sleep(2000);
        
        const urlAtual = window.location.href;
        console.log('📍 URL atual:', urlAtual);
        
        // 2. Se estiver na página de login, fazer login primeiro
        if (urlAtual.includes('login.do')) {
            console.log('🔐 2. Realizando login...');
            
            const cpf = dados.cpf || dados.cpfSocio || dados.cpf_socio;
            const senha = dados.senha;
            
            if (!cpf || !senha) {
                throw new Error('CPF ou senha não fornecida');
            }
            
            const loginOk = await realizarLogin(cpf, senha);
            if (!loginOk) {
                throw new Error('Falha ao realizar login');
            }
            console.log('✅ 2. Login realizado com sucesso');
            
            // Aguardar redirecionamento após login
            await sleep(3000);
        } else {
            console.log('✅ 2. Já está logado, pulando etapa de login');
        }
        
        // Debug inicial
        debugPage();
        
        // 3. Navegar para mensagens
        console.log('🔍 3. Navegando para mensagens...');
        const navegouOk = await navegarParaMensagens();
        if (!navegouOk) {
            throw new Error('Falha ao navegar para mensagens');
        }
        console.log('✅ 3. Navegação para mensagens OK');
        await sleep(5000); // Aguardar carregamento
        
        // Debug página de mensagens
        console.log('🔬 Analisando página de mensagens...');
        await modoDescoberta();
        
        // 4. Verificar se tem aviso de ciencia
        console.log('🔍 4. Verificando aviso de ciência...');
        const temAvisoCiencia = await verificarAvisoCiencia();
        console.log(temAvisoCiencia ? '⚠️ TEM aviso de ciência' : '✅ SEM aviso de ciência');
        
        // 5. Processar todas as mensagens disponiveis com filtros
        console.log('📨 5. Processando mensagens com filtros...');
        const mensagensProcessadas = await processarTodasMensagensDisponiveis(
            dados.cpfSocio || dados.cpf_socio,
            dados.inscricaoEstadual || dados.inscricao_estadual,
            temAvisoCiencia
        );
        
        console.log(`🎯 Total processadas: ${mensagensProcessadas.length}`);
        
        return {
            total: mensagensProcessadas.length,
            processadas: mensagensProcessadas.length,
            erros: 0,
            mensagens: mensagensProcessadas
        };
        
    } catch (error) {
        console.error('❌ Erro no fluxo do MessageBot:', error);
        throw error;
    }
}

// Verifica se ha aviso de ciencia pendente
async function verificarAvisoCiencia() {
    try {
        console.log('🔍 Procurando aviso de ciência...');
        
        // Método 1: Font vermelho
        const fontVermelho = document.querySelector('font[color="red"], font[color="#FF0000"]');
        if (fontVermelho && fontVermelho.textContent.toLowerCase().includes('aguardando')) {
            const texto = fontVermelho.textContent;
            const match = texto.match(/(\d+)\s+mensage[mn]s?\s+aguardando\s+ci[êe]ncia/i);
            if (match) {
                const quantidade = parseInt(match[1]);
                console.log('✅ Método 1 (font vermelho): Detectado', quantidade, 'mensagens');
                return quantidade > 0;
            }
        }
        
        // Método 2: Estilo inline
        const estiloVermelho = document.querySelector('[style*="color: red"], [style*="color:#ff0000"]');
        if (estiloVermelho && estiloVermelho.textContent.toLowerCase().includes('aguardando')) {
            console.log('✅ Método 2 (estilo inline): Detectado aviso');
            return true;
        }
        
        // Método 3: Classe CSS
        const porClasse = document.querySelector('.alerta, .aviso, .warning, .alert');
        if (porClasse && porClasse.textContent.toLowerCase().includes('aguardando')) {
            console.log('✅ Método 3 (classe CSS): Detectado aviso');
            return true;
        }
        
        // Método 4: Busca em todo body
        const textoCompleto = document.body.textContent;
        const matchTexto = textoCompleto.match(/(\d+)\s+mensage[mn]s?\s+aguardando\s+ci[êe]ncia/i);
        if (matchTexto) {
            const quantidade = parseInt(matchTexto[1]);
            console.log('✅ Método 4 (body.textContent): Detectado', quantidade, 'mensagens');
            return quantidade > 0;
        }
        
        // Método 5: Busca em todos os elementos
        const todosElementos = Array.from(document.querySelectorAll('*'));
        const elementoAviso = todosElementos.find(el => {
            const texto = el.textContent;
            return texto.length < 200 && // não pegar elementos muito grandes
                   /aguardando.*ci[êe]ncia/i.test(texto) &&
                   el.children.length === 0; // elemento folha
        });
        
        if (elementoAviso) {
            console.log('✅ Método 5 (busca em elementos): Detectado aviso');
            console.log('   Elemento:', elementoAviso.tagName, elementoAviso.textContent);
            return true;
        }
        
        console.log('ℹ️ Nenhum aviso de ciência detectado');
        return false;
    } catch (erro) {
        console.error('❌ Erro ao verificar aviso:', erro);
        return false;
    }
}

// Processa todas as mensagens disponiveis usando filtros
async function processarTodasMensagensDisponiveis(cpfSocio, inscricaoEstadual, temAvisoCiencia) {
    const todasMensagens = [];
    const filtros = [];
    
    // Se tem aviso de ciencia, processar primeiro "Aguardando Ciencia" (valor 4)
    if (temAvisoCiencia) {
        filtros.push({ nome: 'Aguardando Ciência', valor: '4' });
    }
    
    // Sempre processar "Nao Lidas" (valor 3)
    filtros.push({ nome: 'Não Lidas', valor: '3' });
    
    for (const filtro of filtros) {
        console.log('Processando filtro:', filtro.nome);
        try {
            const mensagensFiltro = await processarMensagensFiltro(
                cpfSocio,
                inscricaoEstadual,
                filtro,
                100 // max mensagens por filtro
            );
            todasMensagens.push(...mensagensFiltro);
            console.log('Filtro', filtro.nome, ':', mensagensFiltro.length, 'mensagens processadas');
        } catch (erro) {
            console.error('Erro ao processar filtro', filtro.nome, ':', erro);
        }
    }
    
    return todasMensagens;
}

// Aplica um filtro de mensagens
async function aplicarFiltroMensagens(valorFiltro) {
    try {
        console.log(`🔽 Aplicando filtro ${valorFiltro}...`);
        
        // Descobrir select real (name="visualizarMensagens")
        let selectFiltro = document.querySelector('select[name="visualizarMensagens"]');
        
        if (!selectFiltro) {
            console.log('⚠️ Select "visualizarMensagens" não encontrado, tentando descoberta...');
            selectFiltro = descobrirSelectFiltro();
        }
        
        if (!selectFiltro) {
            console.error('❌ Select de filtro não encontrado');
            console.log('📋 Listando todos os selects:');
            const selects = document.querySelectorAll('select');
            selects.forEach((sel, i) => {
                console.log(`  ${i}: name="${sel.name}" id="${sel.id}"`);
            });
            return false;
        }
        
        // Verificar se o valor existe
        const opcoes = Array.from(selectFiltro.options).map(opt => ({
            value: opt.value,
            text: opt.text
        }));
        console.log('📋 Opções disponíveis:', opcoes);
        
        const opcaoExiste = opcoes.some(opt => opt.value === valorFiltro);
        if (!opcaoExiste) {
            console.error(`❌ Valor ${valorFiltro} não existe no select`);
            return false;
        }
        
        // Aplicar filtro
        const valorAnterior = selectFiltro.value;
        selectFiltro.value = valorFiltro;
        console.log(`✅ Valor alterado de "${valorAnterior}" para "${valorFiltro}"`);
        
        // Disparar evento change (select tem onchange="javascript:atualizarCaixaEntrada();")
        const evento = new Event('change', { bubbles: true });
        selectFiltro.dispatchEvent(evento);
        console.log('✅ Evento change disparado (atualizarCaixaEntrada será chamado)');
        
        // Aguardar função JavaScript atualizarCaixaEntrada() executar
        await sleep(4000);
        
        console.log('✅ Filtro aplicado com sucesso');
        return true;
    } catch (erro) {
        console.error('❌ Erro ao aplicar filtro:', erro);
        return false;
    }
}

// Conta mensagens na tabela atual
function contarMensagensNaTabela() {
    try {
        console.log('📊 Contando mensagens...');
        
        // Tentar vários seletores
        const seletores = [
            'a[href*="abrirMensagem"]',
            'a[onclick*="abrirMensagem"]',
            'a[href*="mensagem"][href*="id"]',
            'a[onclick*="abrir"]'
        ];
        
        for (const seletor of seletores) {
            const links = document.querySelectorAll(seletor);
            if (links.length > 0) {
                console.log(`✅ Encontradas ${links.length} mensagens (${seletor})`);
                return links.length;
            }
        }
        
        // Método alternativo: contar linhas da tabela
        const linhasTabela = document.querySelectorAll('table tr');
        if (linhasTabela.length > 2) { // Mais que header
            const quantidade = linhasTabela.length - 1; // Remove header
            console.log(`✅ Encontradas ${quantidade} mensagens (linhas da tabela)`);
            return quantidade;
        }
        
        console.log('ℹ️ Nenhuma mensagem encontrada');
        return 0;
    } catch (erro) {
        console.error('❌ Erro ao contar mensagens:', erro);
        return 0;
    }
}

// Processa mensagens de um filtro especifico
async function processarMensagensFiltro(cpfSocio, inscricaoEstadual, filtro, maxMensagens) {
    const mensagensProcessadas = [];
    let tentativasConsecutivasSemMensagens = 0;
    const maxTentativasSemMensagens = 3;
    
    while (mensagensProcessadas.length < maxMensagens && tentativasConsecutivasSemMensagens < maxTentativasSemMensagens) {
        // Reaplicar filtro antes de processar cada mensagem (retry logic)
        const filtroAplicado = await aplicarFiltroMensagens(filtro.valor);
        if (!filtroAplicado) {
            console.error('Falha ao reaplicar filtro');
            break;
        }
        
        // Contar mensagens disponiveis
        const quantidadeMensagens = contarMensagensNaTabela();
        console.log('Mensagens disponiveis no filtro:', quantidadeMensagens);
        
        if (quantidadeMensagens === 0) {
            tentativasConsecutivasSemMensagens++;
            console.log('Nenhuma mensagem encontrada. Tentativa', tentativasConsecutivasSemMensagens, 'de', maxTentativasSemMensagens);
            
            if (tentativasConsecutivasSemMensagens >= maxTentativasSemMensagens) {
                console.log('Finalizando processamento do filtro - sem mensagens');
                break;
            }
            
            await sleep(2000);
            continue;
        }
        
        // Reset contador quando encontrar mensagens
        tentativasConsecutivasSemMensagens = 0;
        
        // Pegar primeira mensagem disponivel
        console.log('🔍 Procurando primeira mensagem...');
        
        const seletoresLink = [
            'a[href*="abrirMensagem"]',
            'a[onclick*="abrirMensagem"]',
            'a[href*="mensagem"][href*="id"]'
        ];
        
        let primeiraLinkMensagem = null;
        for (const seletor of seletoresLink) {
            primeiraLinkMensagem = document.querySelector(seletor);
            if (primeiraLinkMensagem) {
                console.log('✅ Link encontrado:', seletor);
                break;
            }
        }
        
        if (!primeiraLinkMensagem) {
            console.log('⚠️ Nenhum link de mensagem encontrado');
            break;
        }
        
        try {
            // Clicar na mensagem
            console.log('👆 Abrindo mensagem...');
            console.log('   Texto:', primeiraLinkMensagem.textContent.trim());
            console.log('   Href:', primeiraLinkMensagem.href);
            
            primeiraLinkMensagem.click();
            await sleep(4000); // Aguardar carregamento
            
            // Processar mensagem individual
            console.log('📧 Processando mensagem...');
            const dadosMensagem = await processarMensagemAtual(cpfSocio, inscricaoEstadual);
            if (dadosMensagem) {
                mensagensProcessadas.push(dadosMensagem);
                console.log('✅ Mensagem processada com sucesso');
            } else {
                console.warn('⚠️ Falha ao processar mensagem');
            }
            
            // Voltar para lista (aguardar redirecionamento apos ciencia)
            await sleep(3000);
            
        } catch (erro) {
            console.error('Erro ao processar mensagem individual:', erro);
            
            // Tentar voltar para lista de mensagens
            try {
                const voltarLink = document.querySelector('a[href*="listarMensagens"]');
                if (voltarLink) {
                    voltarLink.click();
                    await sleep(2000);
                }
            } catch (erroVoltar) {
                console.error('Erro ao voltar para lista:', erroVoltar);
            }
        }
        
        // Pequena pausa entre mensagens
        await sleep(1000);
    }
    
    return mensagensProcessadas;
}

// Processa a mensagem atualmente aberta
async function processarMensagemAtual(cpfSocio, inscricaoEstadual) {
    try {
        console.log('\n📧 === PROCESSANDO MENSAGEM ===');
        
        // Aguardar carregamento completo
        await sleep(2000);
        
        // Debug da estrutura
        console.log('🔍 Analisando estrutura da mensagem...');
        const tabelas = document.querySelectorAll('table').length;
        const ths = document.querySelectorAll('th').length;
        const tds = document.querySelectorAll('td').length;
        console.log(`  Tabelas: ${tabelas}, TH: ${ths}, TD: ${tds}`);
        
        // Extrair dados completos da mensagem
        console.log('📊 Extraindo dados...');
        const dadosMensagem = await extrairDadosMensagemCompleta(cpfSocio, inscricaoEstadual);
        
        if (!dadosMensagem) {
            console.error('❌ Falha ao extrair dados da mensagem');
            return null;
        }
        
        console.log('✅ Dados extraídos:', {
            assunto: dadosMensagem.assunto,
            tipo: dadosMensagem.tipo_mensagem,
            temDIEF: !!dadosMensagem.competencia_dief
        });
        
        // Salvar no backend
        console.log('💾 Salvando no backend...');
        const salvamentoOk = await salvarMensagemNoBackend(dadosMensagem);
        if (!salvamentoOk) {
            console.warn('⚠️ Falha ao salvar mensagem no backend');
        } else {
            console.log('✅ Mensagem salva no backend');
        }
        
        // Dar ciência
        console.log('✓ Dando ciência...');
        const cienciaOk = await darCiencia();
        if (!cienciaOk) {
            console.warn('⚠️ Falha ao dar ciência');
        } else {
            console.log('✅ Ciência dada');
        }
        
        // Tratar possível diálogo de confirmação
        await tratarDialogoConfirmacao();
        
        console.log('📧 === FIM PROCESSAMENTO ===\n');
        
        return dadosMensagem;
        
    } catch (erro) {
        console.error('❌ Erro ao processar mensagem atual:', erro);
        return null;
    }
}

async function navegarParaMensagens() {
    console.log('🔍 Procurando link de mensagens...');
    
    const urlAtual = window.location.href;
    console.log('📍 URL atual:', urlAtual);
    
    // Se já está na página de mensagens, não fazer nada
    if (urlAtual.includes('listarMensagens') || 
        urlAtual.includes('mensagem.do') || 
        urlAtual.includes('caixaEntradaDomicilio')) {
        console.log('✅ Já está na página de mensagens');
        return true;
    }
    
    // Após login, ir direto para a URL de mensagens
    console.log('🚀 Navegando diretamente para página de mensagens...');
    window.location.href = 'https://sefaznet.sefaz.ma.gov.br/sefaznet/caixaEntradaDomicilio.do?method=mostrarPaginaInicial';
    await sleep(5000); // Aguardar carregamento da página
    console.log('✅ Navegação para mensagens concluída');
    return true;
    
    // DEBUG: Listar TODOS os links da página
    const todosLinks = document.querySelectorAll('a');
    console.log(`📊 Total de links na página: ${todosLinks.length}`);
    console.log('🔗 Primeiros 20 links:');
    Array.from(todosLinks).slice(0, 20).forEach((link, i) => {
        console.log(`  ${i}. "${link.textContent.trim()}" href="${link.href}" onclick="${link.getAttribute('onclick')}"`);
    });
    
    // Método 1: Link com href específico
    const seletoresHref = [
        'a[href*="listarMensagens"]',
        'a[href*="mensagens.do"]',
        'a[href*="mensagem.do"]',
        'a[href*="caixaEntrada"]',
        'a[href*="caixa"]'
    ];
    
    for (const seletor of seletoresHref) {
        const link = document.querySelector(seletor);
        if (link) {
            console.log('✅ Método 1: Link encontrado por href:', seletor);
            console.log('   Texto:', link.textContent.trim());
            console.log('   Href:', link.href);
            link.click();
            await sleep(3000);
            return true;
        }
    }
    
    // Método 2: Link por onclick
    console.log('🔍 Método 2: Procurando por onclick...');
    const linksOnclick = document.querySelectorAll('a[onclick]');
    console.log(`   Encontrados ${linksOnclick.length} links com onclick`);
    for (const link of linksOnclick) {
        const onclick = link.getAttribute('onclick') || '';
        const texto = link.textContent.trim().toLowerCase();
        console.log(`   Analisando: "${texto}" onclick="${onclick}"`);
        if (onclick.toLowerCase().includes('mensagem') || texto.includes('mensagem')) {
            console.log('✅ Método 2: Link encontrado por onclick');
            link.click();
            await sleep(3000);
            return true;
        }
    }
    
    // Método 3: Link por texto exato
    console.log('🔍 Método 3: Procurando por texto...');
    const textosExatos = ['mensagens', 'caixa de entrada', 'mensagem', 'caixa'];
    for (const link of todosLinks) {
        const texto = link.textContent.toLowerCase().trim();
        if (textosExatos.includes(texto)) {
            console.log('✅ Método 3: Link encontrado por texto:', texto);
            link.click();
            await sleep(3000);
            return true;
        }
    }
    
    // Método 4: Busca mais ampla por texto
    console.log('🔍 Método 4: Busca ampla...');
    for (const link of todosLinks) {
        const texto = link.textContent.toLowerCase().trim();
        if (texto.includes('mensage') && texto.length < 30) {
            console.log('✅ Método 4: Link encontrado por texto parcial:', texto);
            link.click();
            await sleep(3000);
            return true;
        }
    }
    
    // Método 5: Procurar em menus/iframes
    console.log('🔍 Método 5: Procurando em iframes/frames...');
    const frames = document.querySelectorAll('iframe, frame');
    console.log(`   Encontrados ${frames.length} frames`);
    for (const frame of frames) {
        try {
            const frameDoc = frame.contentDocument || frame.contentWindow.document;
            const frameLinks = frameDoc.querySelectorAll('a');
            console.log(`   Frame com ${frameLinks.length} links`);
            for (const link of frameLinks) {
                const texto = link.textContent.toLowerCase().trim();
                if (texto.includes('mensage')) {
                    console.log('✅ Método 5: Link encontrado em frame:', texto);
                    link.click();
                    await sleep(3000);
                    return true;
                }
            }
        } catch (e) {
            console.log('   ⚠️ Não foi possível acessar frame (cross-origin)');
        }
    }
    
    // Se nenhum método funcionou, tentar URL direta da caixa de entrada
    console.log('⚠️ Nenhum link encontrado, tentando URL direta da caixa de entrada...');
    window.location.href = 'https://sefaznet.sefaz.ma.gov.br/sefaznet/caixaEntradaDomicilio.do?method=mostrarPaginaInicial';
    await sleep(3000);
    return true;
}

async function extrairDadosMensagemCompleta(cpfSocio, inscricaoEstadual) {
    const dados = {
        inscricao_estadual: inscricaoEstadual,
        cpf_socio: cpfSocio,
        timestamp: new Date().toISOString()
    };
    
    // Extrair dados da tabela de informacoes
    const campos = {
        'Enviada por:': 'enviada_por',
        'Data do Envio:': 'data_envio',
        'Assunto:': 'assunto',
        'Classificacao:': 'classificacao',
        'Tributo:': 'tributo',
        'Tipo da Mensagem:': 'tipo_mensagem',
        'Numero do Documento:': 'numero_documento',
        'Vencimento:': 'vencimento',
        'Data da Leitura:': 'data_leitura'
    };
    
    for (const [label, campo] of Object.entries(campos)) {
        try {
            const th = Array.from(document.querySelectorAll('th')).find(el => 
                el.textContent.includes(label)
            );
            
            if (th) {
                const td = th.nextElementSibling;
                if (td) {
                    dados[campo] = td.textContent.trim();
                }
            }
        } catch (e) {
            console.warn(`Erro ao extrair ${campo}:`, e);
        }
    }
    
    // Extrair nome da empresa
    try {
        const nomeEmpresaEl = document.querySelector('td[colspan] b');
        if (nomeEmpresaEl) {
            dados.nome_empresa = nomeEmpresaEl.textContent.trim();
        }
    } catch (e) {
        console.warn('Erro ao extrair nome empresa:', e);
    }
    
    // Extrair conteudo da mensagem com priority selectors
    try {
        const conteudoSelectors = [
            'td[width="100%"]',
            'table.table-tripped tbody tr td:last-child',
            '.mensagem-conteudo',
            '#mensagem-corpo'
        ];
        
        let conteudoHtml = null;
        let conteudoTexto = null;
        
        for (const selector of conteudoSelectors) {
            const elementos = document.querySelectorAll(selector);
            for (const elemento of elementos) {
                const html = elemento.innerHTML;
                const texto = elemento.textContent.trim();
                
                // Verificar tamanho minimo (50 caracteres)
                if (texto.length >= 50) {
                    conteudoHtml = html;
                    conteudoTexto = texto;
                    break;
                }
            }
            if (conteudoHtml) break;
        }
        
        if (conteudoHtml) {
            dados.conteudo_html = conteudoHtml;
            dados.conteudo_mensagem = conteudoTexto;
            
            // Extrair dados especificos da DIEF usando regex
            extrairDadosDIEF(conteudoTexto, dados);
        }
    } catch (e) {
        console.warn('Erro ao extrair conteudo:', e);
    }
    
    return dados.assunto ? dados : null;
}

// Extrai dados especificos da DIEF usando regex
function extrairDadosDIEF(texto, dados) {
    try {
        // Competencia da DIEF (formato: MMAAAA ou MM/AAAA)
        const matchCompetencia = texto.match(/Período da DIEF:\s*(\d{6})/i) || 
                                 texto.match(/Competência:\s*(\d{2})\/(\d{4})/i);
        if (matchCompetencia) {
            if (matchCompetencia[1].length === 6) {
                dados.competencia_dief = matchCompetencia[1];
            } else if (matchCompetencia[2]) {
                dados.competencia_dief = matchCompetencia[1] + matchCompetencia[2];
            }
        }
        
        // Status da DIEF (PROCESSADA, NAO PROCESSADA, REJEITADA)
        const matchStatus = texto.match(/DIEF\s+(PROCESSADA|NÃO\s+PROCESSADA|NAO\s+PROCESSADA|REJEITADA)/i);
        if (matchStatus) {
            dados.status_dief = matchStatus[1].replace(/\s+/g, ' ').toUpperCase();
        }
        
        // Chave de seguranca
        const matchChave = texto.match(/Chave de segurança:\s*([\d-]+)/i);
        if (matchChave) {
            dados.chave_dief = matchChave[1];
        }
        
        // Protocolo
        const matchProtocolo = texto.match(/Protocolo:\s*(\d+)/i);
        if (matchProtocolo) {
            dados.protocolo_dief = matchProtocolo[1];
        }
        
        // Link do recibo
        try {
            const linkRecibo = document.querySelector('a[href*="listIReciboDief.do"]');
            if (linkRecibo) {
                dados.link_recibo = linkRecibo.href;
            }
        } catch (e) {
            console.warn('Erro ao extrair link recibo:', e);
        }
        
    } catch (erro) {
        console.error('Erro ao extrair dados DIEF:', erro);
    }
}

// Trata dialogos de confirmacao
async function tratarDialogoConfirmacao() {
    try {
        await sleep(1000);
        
        // Procurar botao OK, Confirmar, etc
        const botoes = document.querySelectorAll('button, input[type="button"], input[type="submit"]');
        
        for (const botao of botoes) {
            const texto = (botao.textContent || botao.value || '').toLowerCase();
            if (texto.includes('ok') || texto.includes('confirmar') || texto.includes('fechar')) {
                console.log('Tratando dialogo de confirmacao:', texto);
                botao.click();
                await sleep(1000);
                return true;
            }
        }
        
        return false;
    } catch (erro) {
        console.error('Erro ao tratar dialogo:', erro);
        return false;
    }
}

// Salva mensagem no backend
async function salvarMensagemNoBackend(dados) {
    try {
        const response = await fetch('http://localhost:8000/api/mensagens', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dados)
        });
        
        if (!response.ok) {
            throw new Error(`Erro na API: ${response.status}`);
        }
        
        const resultado = await response.json();
        console.log('Mensagem salva no backend:', resultado);
        return true;
    } catch (error) {
        console.error('Erro ao salvar no backend:', error);
        return false;
    }
}

async function extrairDadosMensagem(inscricaoEstadual) {
    const dados = {
        inscricao_estadual: inscricaoEstadual,
        timestamp: new Date().toISOString()
    };
    
    // Extrair dados da tabela de informacoes
    const campos = {
        'Enviada por:': 'enviada_por',
        'Data do Envio:': 'data_envio',
        'Assunto:': 'assunto',
        'Classificacao:': 'classificacao',
        'Tributo:': 'tributo',
        'Tipo da Mensagem:': 'tipo_mensagem',
        'Numero do Documento:': 'numero_documento',
        'Vencimento:': 'vencimento'
    };
    
    for (const [label, campo] of Object.entries(campos)) {
        try {
            const th = Array.from(document.querySelectorAll('th')).find(el => 
                el.textContent.includes(label)
            );
            
            if (th) {
                const td = th.nextElementSibling;
                if (td) {
                    dados[campo] = td.textContent.trim();
                }
            }
        } catch (e) {
            console.warn(`Erro ao extrair ${campo}:`, e);
        }
    }
    
    // Extrair conteudo da mensagem
    try {
        const conteudoSelectors = [
            'table.table-tripped tbody tr td',
            '.mensagem-conteudo',
            '#mensagem-corpo'
        ];
        
        for (const selector of conteudoSelectors) {
            const elemento = document.querySelector(selector);
            if (elemento) {
                dados.conteudo_html = elemento.innerHTML;
                dados.conteudo_mensagem = elemento.textContent.trim();
                break;
            }
        }
    } catch (e) {
        console.warn('Erro ao extrair conteudo:', e);
    }
    
    return dados.assunto ? dados : null;
}

async function darCiencia() {
    try {
        console.log('🔍 Procurando botão de ciência...');
        
        // Descobrir botão
        const botaoCiencia = descobrirBotaoCiencia();
        
        if (botaoCiencia) {
            console.log('✅ Botão encontrado, clicando...');
            botaoCiencia.click();
            await sleep(2000);
            return true;
        }
        
        // Método alternativo: procurar manualmente
        const botoes = document.querySelectorAll('button, input[type="button"], input[type="submit"], a');
        
        console.log(`📋 Analisando ${botoes.length} botões...`);
        
        for (const botao of botoes) {
            const texto = (botao.textContent || botao.value || '').toLowerCase();
            if (texto.includes('cienc') || texto.includes('ciente')) {
                console.log('✅ Botão encontrado:', texto);
                botao.click();
                await sleep(2000);
                return true;
            }
        }
        
        console.warn('⚠️ Botão de ciência não encontrado');
        console.log('📋 Botões disponíveis:');
        botoes.forEach((b, i) => {
            console.log(`  ${i}: "${b.textContent || b.value}"`);
        });
        
        return false;
    } catch (error) {
        console.error('❌ Erro ao dar ciência:', error);
        return false;
    }
}

// Funcao de login (pode ser chamada pelo fluxo)
async function realizarLogin(cpf, senha) {
    try {
        console.log('🔐 Iniciando login (simulando comportamento humano)...');
        
        // Delay inicial - usuário observando a página
        await sleep(800 + Math.random() * 400);
        
        const campoUsuario = document.querySelector('input[name="identificacao"]');
        if (campoUsuario) {
            console.log('⌨️ Digitando CPF...');
            await digitarComoHumano(campoUsuario, cpf);
            
            // Pausa após preencher usuário - comportamento humano
            await sleep(500 + Math.random() * 300);
        }
        
        const campoSenha = document.querySelector('input[name="senha"]');
        if (campoSenha) {
            console.log('🔑 Digitando senha...');
            await digitarComoHumano(campoSenha, senha);
            
            // Pausa antes de clicar no botão - usuário conferindo dados
            await sleep(700 + Math.random() * 400);
        }
        
        const botaoEntrar = document.querySelector('button[type="submit"]');
        if (botaoEntrar) {
            console.log('👆 Clicando em Entrar...');
            botaoEntrar.click();
            console.log('✅ Login submetido');
            
            // Aguardar login completar - mais tempo para processamento
            await sleep(5000);
            return true;
        }
        
        return false;
    } catch (error) {
        console.error('❌ Erro no login:', error);
        return false;
    }
}

console.log('✅ MessageBot content script pronto - Versão com debug completo');

// Expor funções de debug globalmente para teste manual
window.debugMessageBot = {
    debugPage: debugPage,
    modoDescoberta: modoDescoberta,
    descobrirSelectFiltro: descobrirSelectFiltro,
    descobrirLinksMensagem: descobrirLinksMensagem,
    descobrirBotaoCiencia: descobrirBotaoCiencia
};

console.log('💡 Dica: Execute window.debugMessageBot.modoDescoberta() para analisar a página');
