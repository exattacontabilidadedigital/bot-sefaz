"""
Módulo especializado para processamento de ciência de mensagens SEFAZ.

Este módulo fornece funcionalidades robustas para:
- Filtrar mensagens aguardando ciência
- Extrair dados completos das mensagens
- Salvar no banco de dados
- Dar ciência automaticamente
- Tratamento de erros específico
"""

import logging
from typing import Optional, Dict, Any, List
from playwright.async_api import Page

from src.bot.utils.selectors import SEFAZSelectors
from src.bot.utils.human_behavior import HumanBehavior
from src.bot.exceptions import (
    ExtractionException,
    ElementNotFoundException,
    TimeoutException,
    DatabaseException,
    create_user_friendly_error_message,
    log_exception_details
)
import sqlite3
from datetime import datetime

logger = logging.getLogger(__name__)


class SEFAZMessageProcessor:
    """Processador especializado para mensagens SEFAZ aguardando ciência"""
    
    def __init__(self, db_path: str = 'sefaz_consulta.db'):
        self.selectors = SEFAZSelectors()
        self.db_path = db_path
        self._ensure_database_schema()
    
    def _ensure_database_schema(self) -> None:
        """Garante que a tabela de mensagens existe com todas as colunas necessárias"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Criar tabela se não existir
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mensagens_sefaz (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inscricao_estadual TEXT,
                    cpf_socio TEXT,
                    enviada_por TEXT,
                    data_envio TEXT,
                    assunto TEXT,
                    classificacao TEXT,
                    tributo TEXT,
                    tipo_mensagem TEXT,
                    numero_documento TEXT,
                    vencimento TEXT,
                    conteudo_mensagem TEXT,
                    competencia_dief TEXT,
                    status_dief TEXT,
                    chave_dief TEXT,
                    protocolo_dief TEXT,
                    conteudo_html TEXT,
                    nome_empresa TEXT,
                    data_leitura TEXT,
                    data_ciencia TEXT,
                    link_recibo TEXT,
                    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Adicionar colunas que podem não existir em bancos antigos
            new_columns = {
                'competencia_dief': 'TEXT',
                'status_dief': 'TEXT', 
                'chave_dief': 'TEXT',
                'protocolo_dief': 'TEXT',
                'conteudo_html': 'TEXT',
                'nome_empresa': 'TEXT',
                'data_leitura': 'TEXT',
                'data_ciencia': 'TEXT',
                'link_recibo': 'TEXT',
                'data_criacao': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }
            
            for col_name, col_type in new_columns.items():
                try:
                    cursor.execute(f"ALTER TABLE mensagens_sefaz ADD COLUMN {col_name} {col_type}")
                    logger.info(f"✅ Coluna {col_name} adicionada à tabela")
                except sqlite3.OperationalError:
                    pass  # Coluna já existe
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar schema do banco: {e}")
            raise DatabaseException(f"Falha na configuração do banco: {e}") from e
    
    async def processar_mensagens_aguardando_ciencia(
        self, 
        page: Page, 
        cpf_socio: Optional[str] = None,
        inscricao_estadual_contexto: Optional[str] = None
    ) -> int:
        """
        Processa todas as mensagens aguardando ciência com fluxo completo
        
        Args:
            page: Página do Playwright
            cpf_socio: CPF do sócio (para contexto)
            inscricao_estadual_contexto: IE da empresa (para contexto)
            
        Returns:
            int: Número de mensagens processadas com sucesso
            
        Raises:
            ElementNotFoundException: Se elementos necessários não forem encontrados
            TimeoutException: Se operações excederem timeout
        """
        try:
            logger.info("="*80)
            logger.info("📬 INICIANDO PROCESSAMENTO DE CIÊNCIA DE MENSAGENS")
            logger.info("="*80)
            
            # Filtrar mensagens aguardando ciência
            if not await self._filter_messages_awaiting_acknowledgment(page):
                logger.info("ℹ️ Não há caixa de mensagens ou não foi possível filtrar")
                return 0
            
            # Buscar mensagens aguardando ciência
            message_links = await self._get_pending_message_links(page)
            
            if not message_links:
                logger.info("✅ Não há mensagens aguardando ciência")
                return 0
            
            logger.info(f"📨 Encontradas {len(message_links)} mensagem(ns) aguardando ciência")
            
            # Processar cada mensagem
            processed_count = await self._process_each_message(
                page, message_links, cpf_socio, inscricao_estadual_contexto
            )
            
            logger.info("="*80)
            logger.info(f"✅ PROCESSAMENTO CONCLUÍDO: {processed_count}/{len(message_links)} mensagens")
            logger.info("="*80)
            
            return processed_count
            
        except Exception as e:
            logger.error(f"❌ Erro geral no processamento de ciência: {e}")
            if isinstance(e, (ElementNotFoundException, TimeoutException, DatabaseException)):
                raise
            else:
                raise ExtractionException(f"Falha no processamento de mensagens: {e}") from e
    
    async def _filter_messages_awaiting_acknowledgment(self, page: Page) -> bool:
        """Filtra mensagens para mostrar apenas as aguardando ciência"""
        try:
            message_selectors = self.selectors.get_message_selectors()
            
            logger.info(f"🔍 Procurando filtro com seletor: {message_selectors['filtro_mensagens']}")
            
            # Verificar se há filtro de mensagens
            filtro = await page.query_selector(message_selectors['filtro_mensagens'])
            if not filtro:
                logger.warning("⚠️ Filtro de mensagens não encontrado")
                # Tentar encontrar qualquer select na página
                all_selects = await page.query_selector_all("select")
                logger.info(f"   ℹ️ Encontrados {len(all_selects)} elementos select na página")
                return False
            
            logger.info("✅ Filtro de mensagens encontrado!")
            
            # Verificar valor atual
            current_value = await filtro.evaluate("el => el.value")
            logger.info(f"   📊 Valor atual do filtro: {current_value}")
            
            # Se já está no filtro correto, não precisa mudar
            if current_value == "4":
                logger.info("   ✓ Filtro já está em 'Aguardando Ciência' (valor 4)")
                return True
            
            logger.info("🔍 Selecionando opção 'Aguardando Ciência' (valor 4)...")
            
            # Mudar o select vai disparar onchange="atualizarCaixaEntrada()" que submete o form
            # Precisamos esperar a navegação
            try:
                # Esperar navegação e load
                async with page.expect_navigation(timeout=30000, wait_until="load"):
                    await filtro.select_option(value="4")
                    logger.info("   ⏳ Aguardando navegação após mudança do filtro...")
                
                logger.info("   ✅ Navegação concluída!")
                
            except Exception as nav_error:
                logger.warning(f"   ⚠️ Timeout na navegação, tentando continuar: {nav_error}")
                # Mesmo com timeout, a página pode ter carregado
            
            # Aguardar estabilidade da página
            await page.wait_for_timeout(1000)
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Verificar se mudou
            filtro_atualizado = await page.query_selector(message_selectors['filtro_mensagens'])
            if filtro_atualizado:
                new_value = await filtro_atualizado.evaluate("el => el.value")
                logger.info(f"   ✓ Valor do filtro após reload: {new_value}")
                
                if new_value == "4":
                    logger.info("✅ Filtro aplicado com sucesso!")
                    return True
                else:
                    logger.warning(f"⚠️ Filtro não mudou conforme esperado. Valor: {new_value}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao filtrar mensagens: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def _get_pending_message_links(self, page: Page) -> List:
        """Busca todos os links de mensagens aguardando ciência com comportamento humano"""
        try:
            # Comportamento humano: aguardar e "ler" a página
            logger.info("⏳ Aguardando lista de mensagens atualizar...")
            await page.wait_for_timeout(2000)
            
            # Aguardar estabilidade da página
            await page.wait_for_load_state("networkidle", timeout=10000)
            
            # Simular leitura humana da página
            await page.wait_for_timeout(1000)
            
            # Debug: verificar conteúdo da página
            page_content = await page.content()
            has_messages = "abrirMensagem" in page_content
            logger.info(f"   🔍 Página contém links de mensagem: {has_messages}")
            
            # Verificar se está no filtro correto
            filtro_atual = await page.query_selector('select[name="visualizarMensagens"]')
            if filtro_atual:
                valor_filtro = await filtro_atual.evaluate("el => el.value")
                logger.info(f"   🎠 Filtro atual: {valor_filtro} (4=Aguardando Ciência)")
            
            # Lista de seletores para mensagens aguardando ciência, em ordem de preferência
            message_selectors = [
                # Seletores mais específicos primeiro
                "a[href*='abrirMensagem'] img[src*='ic_msg_lida.png']",  # Mensagens lidas aguardando ciência
                "a[href*='abrirMensagem'] img[src*='ic_msg_nova.png']",  # Mensagens novas
                "a[href*='abrirMensagem'] img[src*='aguardando']",      # Ícones com "aguardando"
                "a[href*='abrirMensagem'] img[title*='abrir']",         # Ícones com title
                "a[href*='abrirMensagem']",                             # Qualquer link de mensagem
            ]
            
            message_elements = []
            
            # Tentar cada seletor
            for i, selector in enumerate(message_selectors):
                try:
                    logger.info(f"   🔎 Tentativa {i+1}: {selector}")
                    elements = await page.query_selector_all(selector)
                    
                    if elements:
                        logger.info(f"   ✅ Encontrados {len(elements)} elementos com seletor {i+1}")
                        
                        # Se são imagens, pegar os links pais
                        if "img" in selector:
                            links = []
                            for img in elements:
                                parent_link = await img.query_selector("xpath=..")
                                if parent_link:
                                    # Verificar se é realmente um link de mensagem
                                    href = await parent_link.get_attribute("href")
                                    if href and "abrirMensagem" in href:
                                        links.append(parent_link)
                            message_elements = links
                        else:
                            message_elements = elements
                        
                        if message_elements:
                            break
                            
                except Exception as e:
                    logger.debug(f"   Seletor {selector} falhou: {e}")
                    continue
            
            if message_elements:
                logger.info(f"📧 Encontradas {len(message_elements)} mensagem(ns) aguardando ciência")
                
                # Debug: mostrar detalhes das mensagens encontradas
                for i, element in enumerate(message_elements[:3]):  # Mostrar apenas as primeiras 3
                    try:
                        href = await element.get_attribute("href")
                        title = await element.get_attribute("title") or "sem title"
                        logger.info(f"   Mensagem {i+1}: {href[:50]}... (title: {title[:30]}...)")
                    except:
                        pass
                        
                return message_elements
            else:
                logger.info("ℹ️ Nenhuma mensagem aguardando ciência encontrada")
                
                # Debug adicional: listar todos os links na página
                all_links = await page.query_selector_all("a")
                message_links = []
                for link in all_links[:10]:  # Apenas primeiros 10
                    try:
                        href = await link.get_attribute("href")
                        if href and "abrirMensagem" in href:
                            message_links.append(href)
                    except:
                        pass
                
                if message_links:
                    logger.info(f"   🔍 Debug: Encontrados {len(message_links)} links gerais de mensagem")
                    for i, href in enumerate(message_links[:3]):
                        logger.info(f"     Link {i+1}: {href[:60]}...")
                
                return []
            if esperando_icons:
                logger.info(f"   ℹ️ Encontrados {len(esperando_icons)} ícones de 'esperando_ciencia.png'")
            
            # Último fallback: buscar todos os links de mensagem
            message_links = await page.query_selector_all("a[href*='abrirMensagem']")
            if message_links:
                logger.info(f"📧 Encontrados {len(message_links)} links de mensagem (fallback)")
                return message_links
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Erro ao buscar links de mensagens: {e}")
            return []
    
    async def _process_each_message(
        self, 
        page: Page, 
        message_links: List, 
        cpf_socio: Optional[str],
        inscricao_estadual_contexto: Optional[str]
    ) -> int:
        """Processa cada mensagem individualmente"""
        processed_count = 0
        
        for idx in range(len(message_links)):
            try:
                logger.info(f"")
                logger.info(f"{'='*60}")
                logger.info(f"📖 PROCESSANDO MENSAGEM {idx + 1}/{len(message_links)}")
                logger.info(f"{'='*60}")
                
                # Re-buscar links a cada iteração (página muda após processar)
                # Tentar primeiro ic_msg_lida.png (aguardando ciência)
                current_links = await page.query_selector_all("a[href*='abrirMensagem'] img[src*='ic_msg_lida.png']")
                if not current_links:
                    # Fallback: ic_msg_nova.png
                    current_links = await page.query_selector_all("a[href*='abrirMensagem'] img[src*='ic_msg_nova.png']")
                
                if idx >= len(current_links):
                    logger.info("✅ Todas as mensagens foram processadas")
                    break
                
                # Obter elemento da imagem e extrair a URL do JavaScript
                img_element = current_links[idx]
                
                logger.info(f"🔍 Extraindo URL da mensagem {idx + 1}...")
                
                # Extrair a URL real de dentro do javascript:abrirMensagem('URL')
                link_href = await img_element.evaluate(r"""
                    el => {
                        const link = el.closest('a');
                        if (!link) {
                            console.log('Link pai não encontrado');
                            return null;
                        }
                        const href = link.getAttribute('href');
                        if (!href) {
                            console.log('Href não encontrado');
                            return null;
                        }
                        
                        console.log('Href original:', href);
                        
                        // Extrair URL de dentro de javascript:abrirMensagem('URL')
                        const match = href.match(/abrirMensagem\('([^']+)'\)/);
                        if (match) {
                            console.log('URL extraída:', match[1]);
                            return match[1];
                        }
                        
                        console.log('Padrão não encontrado, retornando href original');
                        return href;
                    }
                """)
                
                if not link_href:
                    logger.warning(f"⚠️ URL da mensagem {idx + 1} não encontrada")
                    continue
                
                logger.info(f"✅ URL extraída: {link_href}")
                
                # Processar mensagem completa (passando a URL extraída)
                success = await self._process_single_message(
                    page, link_href, cpf_socio, inscricao_estadual_contexto
                )
                
                if success:
                    processed_count += 1
                    logger.info(f"✅ Mensagem {idx + 1} processada com sucesso!")
                else:
                    logger.warning(f"⚠️ Mensagem {idx + 1} não foi processada")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar mensagem {idx + 1}: {e}")
                # Tentar voltar para lista em caso de erro
                await self._safe_return_to_list(page)
                continue
        
        return processed_count
    
    async def _process_single_message(
        self, 
        page: Page, 
        link_url: str, 
        cpf_socio: Optional[str],
        inscricao_estadual_contexto: Optional[str]
    ) -> bool:
        """Processa uma única mensagem: abrir -> extrair -> salvar -> dar ciência -> voltar"""
        try:
            # 1. Abrir mensagem navegando para a URL extraída
            logger.info("1️⃣ Abrindo mensagem...")
            logger.info(f"   🔗 Navegando para: {link_url}")
            
            # Construir URL completa se necessário
            if link_url.startswith('/'):
                # URL relativa - pegar o domínio da página atual
                current_url = page.url
                base_url = '/'.join(current_url.split('/')[:3])  # https://dominio.com
                full_url = base_url + link_url
            else:
                full_url = link_url
            
            logger.info(f"   🌐 URL completa: {full_url}")
            
            # Navegar para a página da mensagem
            await page.goto(full_url, wait_until="networkidle", timeout=30000)
            await HumanBehavior.wait_for_page_stability(page, timeout=15000)
            await page.wait_for_timeout(HumanBehavior.random_delay(1500, 2500))
            logger.info("✅ Mensagem aberta")
            
            # 2. Extrair dados completos da mensagem (método próprio agora)
            logger.info("2️⃣ Extraindo dados da mensagem...")
            message_data = await self._extract_complete_message_data(page, inscricao_estadual_contexto)
            
            if message_data:
                if cpf_socio:
                    message_data['cpf_socio'] = cpf_socio
                
                logger.info("✅ Dados extraídos:")
                logger.info(f"   - Assunto: {message_data.get('assunto', 'N/A')}")
                logger.info(f"   - IE: {message_data.get('inscricao_estadual', 'N/A')}")
                logger.info(f"   - Empresa: {message_data.get('nome_empresa', 'N/A')}")
                logger.info(f"   - Competência DIEF: {message_data.get('competencia_dief', 'N/A')}")
                logger.info(f"   - Status DIEF: {message_data.get('status_dief', 'N/A')}")
                
                # 3. Salvar no banco
                logger.info("3️⃣ Salvando no banco de dados...")
                message_id = self._save_message_to_database(message_data)
                if message_id:
                    logger.info(f"✅ Mensagem salva com ID: {message_id}")
                else:
                    logger.error("❌ Falha ao salvar mensagem!")
            else:
                logger.warning("⚠️ Nenhum dado extraído da mensagem")
            
            # 4. Dar ciência
            logger.info("4️⃣ Dando ciência na mensagem...")
            ciencia_success = await self._give_acknowledgment(page)
            
            # 5. Voltar para lista
            logger.info("5️⃣ Voltando para lista de mensagens...")
            await self._safe_return_to_list(page)
            
            return ciencia_success
            
        except Exception as e:
            logger.error(f"❌ Erro no processamento da mensagem: {e}")
            await self._safe_return_to_list(page)
            return False
    
    async def _extract_complete_message_data(
        self, 
        page: Page, 
        inscricao_estadual_contexto: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extrai todos os dados de uma mensagem SEFAZ aberta, incluindo:
        - Dados gerais (enviada por, data, assunto, etc)
        - Competência DIEF (extraída do conteúdo da mensagem)
        - Status DIEF (extraída do conteúdo: "DIEF PROCESSADA", etc)
        - Chave DIEF (extraída do conteúdo: "Chave de segurança: XXXX-XXXX...")
        - Protocolo DIEF
        - Conteúdo HTML completo da mensagem
        
        Args:
            page: Página do navegador
            inscricao_estadual_contexto: IE da empresa sendo consultada (usada como fallback)
        
        Returns:
            dict: Dicionário com todos os dados extraídos ou None em caso de erro
        """
        try:
            dados = {}
            
            # Se temos contexto da empresa, usar como padrão (pode ser sobrescrito pela mensagem)
            if inscricao_estadual_contexto:
                dados['inscricao_estadual'] = inscricao_estadual_contexto
                logger.info(f"   📌 Usando IE do contexto: {inscricao_estadual_contexto}")
            
            # Extrair dados da tabela de informações
            logger.info("   📋 Extraindo dados da tabela...")
            
            # Enviada por
            try:
                el = await page.query_selector("th:has-text('Enviada por:') + td")
                if el:
                    dados['enviada_por'] = (await el.text_content()).strip()
            except: pass
            
            # Data do Envio
            try:
                el = await page.query_selector("th:has-text('Data do Envio:') + td")
                if el:
                    dados['data_envio'] = (await el.text_content()).strip()
            except: pass
            
            # Assunto
            try:
                el = await page.query_selector("th:has-text('Assunto:') + td")
                if el:
                    dados['assunto'] = (await el.text_content()).strip()
            except: pass
            
            # Classificação
            try:
                el = await page.query_selector("th:has-text('Classificação:') + td")
                if el:
                    dados['classificacao'] = (await el.text_content()).strip()
            except: pass
            
            # Tributo
            try:
                el = await page.query_selector("th:has-text('Tributo:') + td")
                if el:
                    dados['tributo'] = (await el.text_content()).strip()
            except: pass
            
            # Tipo da Mensagem
            try:
                el = await page.query_selector("th:has-text('Tipo da Mensagem:') + td")
                if el:
                    dados['tipo_mensagem'] = (await el.text_content()).strip()
            except: pass
            
            # Inscrição Estadual
            try:
                el = await page.query_selector("th:has-text('Inscrição Estadual:') + td")
                if el:
                    ie_texto = (await el.text_content()).strip()
                    # Formato: "125383983 - A&D SOLUTIONS LTDA"
                    if " - " in ie_texto:
                        dados['inscricao_estadual'] = ie_texto.split(" - ")[0].strip()
                        dados['nome_empresa'] = ie_texto.split(" - ")[1].strip()
                    else:
                        dados['inscricao_estadual'] = ie_texto
            except: pass
            
            # Número do Documento
            try:
                el = await page.query_selector("th:has-text('Número do Documento:') + td")
                if el:
                    dados['numero_documento'] = (await el.text_content()).strip()
            except: pass
            
            # Vencimento
            try:
                el = await page.query_selector("th:has-text('Vencimento:') + td")
                if el:
                    dados['vencimento'] = (await el.text_content()).strip()
            except: pass
            
            # Data da Leitura
            try:
                el = await page.query_selector("th:has-text('Data da Leitura:') + td")
                if el:
                    dados['data_leitura'] = (await el.text_content()).strip()
            except: pass
            
            # EXTRAIR CONTEÚDO HTML COMPLETO DA MENSAGEM
            logger.info("   📄 Extraindo conteúdo HTML da mensagem...")
            try:
                # Primeiro, fazer screenshot da página para debug
                screenshot_path = f"debug_mensagem_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=screenshot_path)
                logger.info(f"      📸 Screenshot salvo: {screenshot_path}")
                
                # Seletor correto baseado na estrutura HTML real da página
                # O conteúdo está dentro de: <td width="100%"> que contém o recibo completo
                # Esse td vem depois da linha <th>Mensagem:</th>
                
                conteudo_selectors = [
                    # MAIS ESPECÍFICO: td width=100% que contém "RECIBO" ou "DIEF" ou "Protocolo"
                    "td[width='100%']:has-text('RECIBO')",
                    "td[width='100%']:has-text('Protocolo DIEF')",
                    "td[width='100%']:has-text('ESTADO DO MARANHÃO')",
                    # td que contém div com "DADOS DO PROCESSAMENTO"
                    "td[width='100%']:has-text('DADOS DO PROCESSAMENTO')",
                    # Último td[width='100%'] da página (geralmente é o conteúdo)
                    "td[width='100%']:last-of-type",
                    # Qualquer td[width='100%'] com bastante conteúdo
                    "td[width='100%']",
                    # Fallback: body inteiro
                    "body",
                ]
                
                conteudo_element = None
                conteudo_html = None
                conteudo_texto = None
                
                for selector in conteudo_selectors:
                    try:
                        logger.info(f"      🔍 Tentando seletor: {selector}")
                        el = await page.query_selector(selector)
                        if el:
                            texto = await el.text_content()
                            html = await el.inner_html()
                            
                            # Log para debug
                            logger.info(f"      📏 Elemento encontrado - Texto: {len(texto.strip())} chars, HTML: {len(html)} chars")
                            
                            # Aceitar se tiver conteúdo substancial OU se for a tabela com "Mensagem:"
                            if (texto and len(texto.strip()) > 50) or "Mensagem:" in html:
                                conteudo_element = el
                                conteudo_html = html
                                conteudo_texto = texto
                                logger.info(f"      ✅ Conteúdo aceito! Tamanho: {len(texto.strip())} caracteres")
                                logger.info(f"      📝 Preview HTML: {html[:200]}...")
                                break
                            else:
                                logger.info(f"      ⚠️ Elemento encontrado mas conteúdo insuficiente")
                    except Exception as e:
                        logger.debug(f"      ⚠️ Erro com seletor {selector}: {e}")
                        continue
                
                # Se não encontrou, pegar todo o body como fallback
                if not conteudo_element:
                    logger.info("      ⚠️ Nenhum seletor específico funcionou, tentando abordagem alternativa...")
                    
                    # ABORDAGEM 1: Tentar pegar via JavaScript toda a área de conteúdo
                    try:
                        conteudo_completo = await page.evaluate("""
                            () => {
                                // Procurar todas as tabelas
                                const tables = document.querySelectorAll('table');
                                let conteudoHTML = '';
                                let conteudoTexto = '';
                                
                                // Pegar todas as tabelas que tenham conteúdo relevante
                                for (const table of tables) {
                                    const tableText = table.innerText || '';
                                    // Se a tabela tem conteúdo substancial, adicionar
                                    if (tableText.length > 100) {
                                        conteudoHTML += table.outerHTML;
                                        conteudoTexto += tableText + '\\n\\n';
                                    }
                                }
                                
                                return {
                                    html: conteudoHTML,
                                    texto: conteudoTexto
                                };
                            }
                        """)
                        
                        if conteudo_completo and conteudo_completo.get('texto'):
                            conteudo_html = conteudo_completo['html']
                            conteudo_texto = conteudo_completo['texto']
                            logger.info(f"      ✅ Conteúdo extraído via JavaScript: {len(conteudo_texto)} caracteres")
                    except Exception as js_error:
                        logger.warning(f"      ⚠️ Erro na extração via JavaScript: {js_error}")
                    
                    # ABORDAGEM 2: Fallback para body completo
                    if not conteudo_html or not conteudo_texto:
                        logger.info("      ⚠️ Usando body completo como último recurso")
                        body = await page.query_selector("body")
                        if body:
                            conteudo_html = await body.inner_html()
                            conteudo_texto = await body.text_content()
                
                if conteudo_html and conteudo_texto:
                    dados['conteudo_html'] = conteudo_html
                    dados['conteudo_mensagem'] = conteudo_texto.strip()
                    logger.info(f"      ✅ HTML extraído: {len(conteudo_html)} caracteres")
                    logger.info(f"      ✅ Texto extraído: {len(conteudo_texto)} caracteres")
                    logger.info(f"      📝 Preview: {conteudo_texto.strip()[:200]}...")
                    
                    # EXTRAIR DADOS ESPECÍFICOS DA DIEF DO CONTEÚDO
                    logger.info("   🔍 Extraindo dados da DIEF do conteúdo...")
                    
                    import re
                    
                    # Competência DIEF (Período da DIEF: 202510)
                    match_competencia = re.search(r'Período da DIEF:\s*(\d{6})', conteudo_texto)
                    if match_competencia:
                        dados['competencia_dief'] = match_competencia.group(1)
                        logger.info(f"      ✓ Competência: {dados['competencia_dief']}")
                    else:
                        logger.warning(f"      ⚠️ Competência DIEF não encontrada")
                    
                    # Status DIEF (Situação: DIEF PROCESSADA)
                    match_status = re.search(r'Situação:\s*([^\n]+)', conteudo_texto)
                    if match_status:
                        dados['status_dief'] = match_status.group(1).strip()
                        logger.info(f"      ✓ Status: {dados['status_dief']}")
                    else:
                        logger.warning(f"      ⚠️ Status DIEF não encontrado")
                    
                    # Chave de segurança DIEF
                    match_chave = re.search(r'Chave de segurança:\s*([\d-]+)', conteudo_texto)
                    if match_chave:
                        dados['chave_dief'] = match_chave.group(1).strip()
                        logger.info(f"      ✓ Chave: {dados['chave_dief']}")
                    else:
                        logger.warning(f"      ⚠️ Chave DIEF não encontrada")
                    
                    # Protocolo DIEF
                    match_protocolo = re.search(r'Protocolo DIEF:\s*(\d+)', conteudo_texto)
                    if match_protocolo:
                        dados['protocolo_dief'] = match_protocolo.group(1).strip()
                        logger.info(f"      ✓ Protocolo: {dados['protocolo_dief']}")
                    else:
                        logger.warning(f"      ⚠️ Protocolo DIEF não encontrado")
                else:
                    logger.warning("      ❌ Não foi possível extrair conteúdo")
                    
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao extrair conteúdo HTML: {e}")
            
            # Log resumo de dados extraídos
            logger.info("   📊 RESUMO DOS DADOS EXTRAÍDOS:")
            logger.info(f"      - IE: {dados.get('inscricao_estadual', 'N/A')}")
            logger.info(f"      - Empresa: {dados.get('nome_empresa', 'N/A')}")
            logger.info(f"      - Assunto: {dados.get('assunto', 'N/A')}")
            logger.info(f"      - Data Envio: {dados.get('data_envio', 'N/A')}")
            logger.info(f"      - Competência DIEF: {dados.get('competencia_dief', 'N/A')}")
            logger.info(f"      - Status DIEF: {dados.get('status_dief', 'N/A')}")
            logger.info(f"      - Chave DIEF: {dados.get('chave_dief', 'N/A')}")
            logger.info(f"      - Protocolo: {dados.get('protocolo_dief', 'N/A')}")
            logger.info(f"      - HTML: {len(dados.get('conteudo_html', '')) if dados.get('conteudo_html') else 0} chars")
            logger.info(f"      - Texto: {len(dados.get('conteudo_mensagem', '')) if dados.get('conteudo_mensagem') else 0} chars")
            
            # PREVIEW DO CONTEÚDO REAL QUE SERÁ GRAVADO
            conteudo_real = dados.get('conteudo_mensagem', '')
            if conteudo_real:
                preview = conteudo_real[:500].replace('\n', ' ').replace('\r', '')
                logger.info(f"      📄 PREVIEW CONTEÚDO: {preview}...")
            else:
                logger.warning(f"      ⚠️ CONTEÚDO VAZIO! Será gravado vazio no banco!")
            
            return dados
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados da mensagem: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def _give_acknowledgment(self, page: Page) -> bool:
        """Dá ciência na mensagem atual"""
        try:
            logger.info("   🔘 Procurando botão 'Informar Ciência'...")
            
            # Aguardar página carregar completamente antes de procurar botão
            await page.wait_for_load_state("load")
            await page.wait_for_timeout(HumanBehavior.random_delay(1000, 2000))
            
            # Procurar botão "Informar Ciência" ou "Dar Ciência"
            ciencia_selectors = [
                # MAIS ESPECÍFICO - Estrutura exata do HTML: button.btn.btn-success com onclick e ícone
                "button.btn.btn-success[onclick*='registrarCiencia']",
                "button.btn-success[onclick*='registrarCiencia']",
                "button[onclick*='registrarCiencia']",
                # Por texto no botão
                "button.btn.btn-success:has-text('Informar Ciência')",
                "button.btn-success:has-text('Informar Ciência')",
                "button:has-text('Informar Ciência')",
                # Fallbacks
                "button:has-text('Dar Ciência')",
                "button:has-text('Ciência')",
                "input[type='button'][value*='Ciência']"
            ]
            
            botao_encontrado = False
            
            for selector in ciencia_selectors:
                try:
                    logger.info(f"      🔍 Tentando seletor: {selector}")
                    
                    # Aguardar até 5 segundos pelo botão aparecer
                    try:
                        await page.wait_for_selector(selector, timeout=5000, state="visible")
                        logger.info(f"      ✅ Botão encontrado e visível!")
                    except Exception:
                        logger.debug(f"      ⚠️ Timeout esperando botão com: {selector}")
                        continue
                    
                    btn_ciencia = await page.query_selector(selector)
                    if btn_ciencia:
                        is_visible = await btn_ciencia.is_visible()
                        is_enabled = await btn_ciencia.is_enabled()
                        logger.info(f"      ✅ Botão - Visível: {is_visible}, Habilitado: {is_enabled}")
                        
                        if is_visible and is_enabled:
                            botao_encontrado = True
                            logger.info(f"      🖱️ Clicando no botão...")
                            
                            # Tentar clicar até 3 vezes se necessário
                            max_tentativas = 3
                            for tentativa in range(1, max_tentativas + 1):
                                try:
                                    logger.info(f"      🎯 Tentativa {tentativa} de {max_tentativas}...")
                                    
                                    # Scroll até o botão se necessário
                                    await btn_ciencia.scroll_into_view_if_needed()
                                    await page.wait_for_timeout(500)
                                    
                                    # Clicar
                                    await HumanBehavior.human_click(page, btn_ciencia)
                                    await page.wait_for_timeout(HumanBehavior.random_delay(1500, 2500))
                                    
                                    logger.info(f"      ✅ Ciência registrada com sucesso via: {selector}")
                                    
                                    # Aguardar e clicar em OK se aparecer
                                    await self._handle_confirmation_dialog(page)
                                    return True
                                    
                                except Exception as click_error:
                                    logger.warning(f"      ⚠️ Erro na tentativa {tentativa}: {click_error}")
                                    if tentativa == max_tentativas:
                                        raise
                                    await page.wait_for_timeout(1000)
                    else:
                        logger.debug(f"      ⚠️ Botão não encontrado com seletor: {selector}")
                except Exception as e:
                    logger.debug(f"      ⚠️ Erro com seletor {selector}: {e}")
                    continue
            
            if not botao_encontrado:
                logger.error("   ❌ ERRO: Botão de ciência não encontrado com nenhum seletor!")
                # Salvar screenshot e HTML para debug
                await page.screenshot(path=f"debug_botao_ciencia_nao_encontrado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                html_content = await page.content()
                with open(f"debug_botao_ciencia_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.error("   📸 Screenshot e HTML salvos para debug")
            
            return False
            
        except Exception as e:
            logger.error(f"   ❌ Erro ao dar ciência: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def _handle_confirmation_dialog(self, page: Page) -> None:
        """Trata diálogo de confirmação após dar ciência"""
        try:
            logger.info("   ⏳ Aguardando diálogo de confirmação...")
            await page.wait_for_timeout(HumanBehavior.random_delay(500, 1000))
            
            # Procurar botão OK de confirmação
            ok_selectors = [
                "button.btn-primary:has-text('OK')",
                "input[type='button'][value='OK'].btn-primary",
                "button:has-text('OK')",
                "input[value='OK']",
                "button[onclick*='confirmar']"
            ]
            
            for selector in ok_selectors:
                try:
                    logger.info(f"      🔍 Procurando OK com: {selector}")
                    btn_ok = await page.query_selector(selector)
                    if btn_ok:
                        is_visible = await btn_ok.is_visible()
                        logger.info(f"      {'✅' if is_visible else '⚠️'} Botão OK encontrado - Visível: {is_visible}")
                        
                        if is_visible:
                            logger.info(f"      🖱️ Clicando em 'OK'...")
                            await HumanBehavior.human_click(page, btn_ok)
                            await page.wait_for_timeout(HumanBehavior.random_delay(1000, 1500))
                            logger.info(f"      ✅ Confirmação OK clicada via: {selector}")
                            return
                    else:
                        logger.debug(f"      ⚠️ Botão OK não encontrado com: {selector}")
                except Exception as e:
                    logger.debug(f"      ⚠️ Erro com seletor {selector}: {e}")
                    continue
            
            logger.info("   ℹ️ Nenhum diálogo de confirmação detectado")
                    
        except Exception as e:
            logger.debug(f"   ℹ️ Sem diálogo de confirmação ou erro: {e}")
    
    async def _safe_return_to_list(self, page: Page) -> None:
        """Retorna com segurança para a lista de mensagens"""
        try:
            logger.info("   🔙 Procurando botão 'Voltar'...")
            
            # Procurar botão Voltar
            voltar_selectors = self.selectors.get_voltar_button_selectors()
            
            for selector in voltar_selectors:
                try:
                    logger.info(f"      🔍 Tentando seletor: {selector}")
                    btn_voltar = await page.query_selector(selector)
                    if btn_voltar:
                        is_visible = await btn_voltar.is_visible()
                        logger.info(f"      {'✅' if is_visible else '⚠️'} Botão encontrado - Visível: {is_visible}")
                        
                        if is_visible:
                            logger.info(f"      🖱️ Clicando em 'Voltar'...")
                            await HumanBehavior.human_click(page, btn_voltar)
                            logger.info(f"      ⏳ Aguardando navegação de volta...")
                            await HumanBehavior.wait_for_page_stability(page, timeout=15000)
                            await page.wait_for_timeout(HumanBehavior.random_delay(1500, 2500))
                            logger.info(f"      ✅ Voltou para lista de mensagens via: {selector}")
                            return
                    else:
                        logger.debug(f"      ⚠️ Botão não encontrado com seletor: {selector}")
                except Exception:
                    continue
            
            # Fallback: usar navegação do browser
            await page.go_back()
            await HumanBehavior.wait_for_page_stability(page)
            logger.info("✅ Voltou via navegação do browser")
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao voltar para lista: {e}")
    
    def _save_message_to_database(self, message_data: Dict[str, Any]) -> Optional[int]:
        """Salva mensagem no banco de dados"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extrair link do recibo se presente no HTML
            link_recibo = self._extract_receipt_link(message_data.get('conteudo_html', ''))
            
            # Data de ciência atual
            data_ciencia = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO mensagens_sefaz 
                (inscricao_estadual, cpf_socio, enviada_por, data_envio, assunto, 
                 classificacao, tributo, tipo_mensagem, numero_documento, vencimento, 
                 conteudo_mensagem, competencia_dief, status_dief, chave_dief, 
                 protocolo_dief, conteudo_html, nome_empresa, data_leitura, 
                 data_ciencia, link_recibo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_data.get('inscricao_estadual'),
                message_data.get('cpf_socio'),
                message_data.get('enviada_por'),
                message_data.get('data_envio'),
                message_data.get('assunto'),
                message_data.get('classificacao'),
                message_data.get('tributo'),
                message_data.get('tipo_mensagem'),
                message_data.get('numero_documento'),
                message_data.get('vencimento'),
                message_data.get('conteudo_mensagem'),
                message_data.get('competencia_dief'),
                message_data.get('status_dief'),
                message_data.get('chave_dief'),
                message_data.get('protocolo_dief'),
                message_data.get('conteudo_html'),
                message_data.get('nome_empresa'),
                message_data.get('data_leitura'),
                data_ciencia,
                link_recibo
            ))
            
            message_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return message_id
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mensagem: {e}")
            return None
    
    def _extract_receipt_link(self, html_content: str) -> Optional[str]:
        """Extrai link do recibo do conteúdo HTML"""
        if not html_content or 'listIReciboDief' not in html_content:
            return None
        
        try:
            import re
            match = re.search(r'href=["\']([^"\']*listIReciboDief\.do[^"\']*)["\']', html_content, re.IGNORECASE)
            if match:
                link = match.group(1).replace('&amp;', '&')
                logger.info(f"🔗 Link do recibo extraído: {link}")
                return link
        except Exception as e:
            logger.debug(f"Erro ao extrair link do recibo: {e}")
        
        return None


    async def processar_mensagem_individual(
        self, 
        page: Page, 
        cpf_socio: str, 
        inscricao_estadual: str
    ) -> bool:
        """Processa uma única mensagem individual (compatibilidade com message_bot)"""
        try:
            logger.info("📝 Processando mensagem individual...")
            
            # Extrair dados da mensagem atual
            logger.info("   🔍 Extraindo dados da mensagem...")
            message_data = await self._extract_complete_message_data(page, inscricao_estadual)
            
            if message_data:
                message_data['cpf_socio'] = cpf_socio
                
                logger.info(f"   ✅ Dados extraídos - Assunto: {message_data.get('assunto', 'N/A')}")
                
                # Salvar no banco
                logger.info("   💾 Salvando no banco...")
                message_id = self._save_message_to_database(message_data)
                
                if message_id:
                    logger.info(f"   ✅ Mensagem salva com ID: {message_id}")
                    
                    # Dar ciência
                    logger.info("   📋 Dando ciência...")
                    if await self._give_acknowledgment(page):
                        await self._handle_confirmation_dialog(page)
                        logger.info("   ✅ Ciência registrada com sucesso")
                        return True
                    else:
                        logger.warning("   ⚠️ Falha ao dar ciência")
                        return False
                else:
                    logger.error("   ❌ Falha ao salvar no banco")
                    return False
            else:
                logger.warning("   ⚠️ Não foi possível extrair dados da mensagem")
                return False
        
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem individual: {e}")
            return False


# Classe compatível com o código antigo
class SEFAZBotCiencia(SEFAZMessageProcessor):
    """Classe de compatibilidade com a interface antiga"""
    
    def __init__(self, db_path: str = 'sefaz_consulta.db'):
        super().__init__(db_path)
        self.logger = logger  # Manter compatibilidade
    
    async def processar_ciencia(self, page: Page) -> int:
        """Método de compatibilidade com a interface antiga"""
        return await self.processar_mensagens_aguardando_ciencia(page)

    async def processar_mensagem_individual(
        self, 
        page: Page, 
        cpf_socio: str, 
        inscricao_estadual: str
    ) -> bool:
        """Processa uma única mensagem individual (compatibilidade com message_bot)"""
        try:
            logger.info("📝 Processando mensagem individual...")
            
            # Extrair dados da mensagem atual
            logger.info("   🔍 Extraindo dados da mensagem...")
            message_data = await self._extract_complete_message_data(page, inscricao_estadual)
            
            if message_data:
                message_data['cpf_socio'] = cpf_socio
                
                logger.info(f"   ✅ Dados extraídos - Assunto: {message_data.get('assunto', 'N/A')}")
                
                # Salvar no banco
                logger.info("   💾 Salvando no banco...")
                message_id = self._save_message_to_database(message_data)
                
                if message_id:
                    logger.info(f"   ✅ Mensagem salva com ID: {message_id}")
                    
                    # Dar ciência
                    logger.info("   📋 Dando ciência...")
                    if await self._give_acknowledgment(page):
                        await self._handle_confirmation_dialog(page)
                        logger.info("   ✅ Ciência registrada com sucesso")
                        return True
                    else:
                        logger.warning("   ⚠️ Falha ao dar ciência")
                        return False
                else:
                    logger.error("   ❌ Falha ao salvar no banco")
                    return False
            else:
                logger.warning("   ⚠️ Não foi possível extrair dados da mensagem")
                return False
        
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagem individual: {e}")
            return False
