"""
MessageBot - Bot especializado exclusivamente em processamento de mensagens SEFAZ.

Este bot é completamente independente e pode ser executado separadamente do bot principal.
Ele implementa todo o fluxo necessário: login → navegação → processamento → logout.
"""

import logging
import os
import sqlite3
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

from src.bot.core.authenticator import SEFAZAuthenticator
from src.bot.core.navigator import SEFAZNavigator  
from src.bot.core.message_processor import SEFAZMessageProcessor
from src.bot.utils.constants import URL_SEFAZ_LOGIN
from src.bot.exceptions import (
    BrowserLaunchException,
    LoginFailedException,
    NavigationException,
    ExtractionException,
    ElementNotFoundException,
    TimeoutException,
    DatabaseException,
    create_user_friendly_error_message,
    log_exception_details
)

logger = logging.getLogger(__name__)


class BrowserManager:
    """Context manager para gestão segura do navegador do MessageBot"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def __aenter__(self):
        """Inicializa o navegador ao entrar no contexto"""
        try:
            logger.info("🌐 MessageBot: Iniciando navegador...")
            self.playwright = await async_playwright().start()
            
            # Configurar opções do navegador com comportamento mais humano
            launch_options = {
                'headless': self.headless,
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]
            }
            
            self.browser = await self.playwright.chromium.launch(**launch_options)
            
            # Configurar contexto com comportamento humano
            self.context = await self.browser.new_context(
                viewport={'width': 1366, 'height': 768},  # Resolução mais comum
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                permissions=['geolocation'],
                extra_http_headers={
                    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
                }
            )
            
            self.page = await self.context.new_page()
            
            logger.info("✅ MessageBot: Navegador iniciado com sucesso")
            return self.page
            
        except Exception as e:
            logger.error(f"❌ MessageBot: Erro ao iniciar navegador: {e}")
            await self._cleanup()
            raise BrowserLaunchException(f"Erro ao iniciar navegador: {e}") from e
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Garante que o navegador seja fechado ao sair do contexto"""
        await self._cleanup()
        
        if exc_type:
            logger.error(f"❌ MessageBot: Exceção capturada: {exc_type.__name__}: {exc_val}")
    
    async def _cleanup(self):
        """Limpa recursos do navegador"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"⚠️ MessageBot: Erro durante limpeza: {e}")


class MessageBot:
    """
    Bot especializado EXCLUSIVAMENTE em processamento de mensagens SEFAZ.
    
    Executa fluxo completo e independente:
    1. Fazer login
    2. Navegar para mensagens  
    3. Processar mensagens
    4. Fazer logout
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa o MessageBot.
        
        Args:
            db_path: Caminho para o banco de dados. Se None, usa detecção automática.
        """
        # Detecção automática do caminho do banco
        if db_path is None:
            if os.getenv('ENVIRONMENT') == 'production':
                os.makedirs('/data', exist_ok=True)
                db_path = '/data/sefaz_consulta.db'
            else:
                db_path = os.getenv('DB_PATH', 'sefaz_consulta.db')
        
        self.db_path = db_path
        self.authenticator = SEFAZAuthenticator()
        self.navigator = SEFAZNavigator()
        self.message_processor = SEFAZMessageProcessor(db_path)
        
        logger.info(f"📂 MessageBot: Usando banco: {db_path}")
    
    async def processar_mensagens_empresa(
        self, 
        cpf: str, 
        senha: str, 
        inscricao_estadual: str,
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Executa o fluxo completo de processamento de mensagens para uma empresa.
        
        Args:
            cpf: CPF do usuário (com ou sem formatação)
            senha: Senha de acesso
            inscricao_estadual: Inscrição estadual da empresa
            headless: Se True, executa sem interface gráfica
            
        Returns:
            Dict com resultados do processamento:
            {
                'sucesso': bool,
                'mensagens_processadas': int,
                'mensagem': str,
                'detalhes': dict
            }
            
        Raises:
            LoginFailedException: Se login falhar
            NavigationException: Se navegação falhar
            ExtractionException: Se processamento falhar
        """
        resultado = {
            'sucesso': False,
            'mensagens_processadas': 0,
            'mensagem': '',
            'detalhes': {}
        }
        
        try:
            logger.info("=" * 80)
            logger.info("📬 MessageBot - INICIANDO PROCESSAMENTO DE MENSAGENS")
            logger.info("=" * 80)
            logger.info(f"   - CPF: {cpf}")
            logger.info(f"   - IE: {inscricao_estadual}")
            logger.info(f"   - Headless: {headless}")
            logger.info("=" * 80)
            
            async with BrowserManager(headless=headless) as page:
                # Etapa 1: Login
                logger.info("🔐 Etapa 1/4: Fazendo login...")
                login_success = await self.authenticator.perform_login(
                    page, cpf, senha, URL_SEFAZ_LOGIN
                )
                
                if not login_success:
                    raise LoginFailedException("Falha na autenticação")
                
                logger.info("✅ Login realizado com sucesso")
                
                # Etapa 2: Verificar se há mensagens aguardando ciência
                logger.info("🧭 Etapa 2/4: Verificando mensagens pendentes...")
                
                has_pending_messages = await self.navigator.check_pending_messages(page)
                
                if has_pending_messages:
                    logger.info("📨 Mensagens aguardando ciência detectadas - indo diretamente para processamento")
                    
                    # Clicar no link da mensagem
                    message_clicked = await self.navigator.click_message_link(page)
                    if not message_clicked:
                        raise NavigationException("Não foi possível acessar mensagens aguardando ciência")
                        
                else:
                    logger.info("🧭 Navegando para área de mensagens via menu...")
                    
                    # Abrir menu sistemas
                    menu_opened = await self.navigator.open_sistemas_menu(page)
                    if not menu_opened:
                        raise NavigationException("Não foi possível abrir menu Sistemas")
                    
                    # Navegar para todas as áreas de negócio
                    areas_clicked = await self.navigator.click_todas_areas_negocio(page)
                    if not areas_clicked:
                        raise NavigationException("Não foi possível acessar Todas as Áreas de Negócio")
                
                logger.info("✅ Navegação para área de mensagens concluída")
                
                # Etapa 3: Processar mensagens (múltiplos filtros)
                logger.info("📨 Etapa 3/4: Processando TODAS as mensagens disponíveis...")
                
                mensagens_processadas = await self._processar_todas_mensagens_disponiveis(
                    page, cpf, inscricao_estadual
                )
                
                resultado['mensagens_processadas'] = mensagens_processadas
                
                if mensagens_processadas > 0:
                    logger.info(f"✅ {mensagens_processadas} mensagem(ns) processada(s) com sucesso")
                else:
                    logger.info("ℹ️ Nenhuma mensagem nova encontrada")
                
                # Etapa 4: Logout
                logger.info("🚪 Etapa 4/4: Fazendo logout...")
                await self.authenticator.perform_logout(page)
                logger.info("✅ Logout realizado com sucesso")
                
                # Resultado final
                resultado.update({
                    'sucesso': True,
                    'mensagem': f'Processamento avançado concluído: {mensagens_processadas} mensagem(ns) processada(s)',
                    'detalhes': {
                        'empresa': inscricao_estadual,
                        'mensagens': mensagens_processadas,
                        'filtros_processados': ['Aguardando Ciência', 'Não Lidas'],
                        'login_ok': True,
                        'navegacao_ok': True,
                        'processamento_ok': True,
                        'logout_ok': True
                    }
                })
                
                logger.info("=" * 80)
                logger.info("🎉 MessageBot - PROCESSAMENTO AVANÇADO CONCLUÍDO COM SUCESSO")
                logger.info(f"   - Mensagens processadas: {mensagens_processadas}")
                logger.info(f"   - Filtros processados: Aguardando Ciência + Não Lidas")
                logger.info("=" * 80)
                
                return resultado
                
        except LoginFailedException as e:
            logger.error(f"❌ Erro de login: {e}")
            resultado.update({
                'mensagem': f'Erro de login: {e}',
                'detalhes': {'erro_tipo': 'login', 'erro_detalhes': str(e)}
            })
            raise
            
        except NavigationException as e:
            logger.error(f"❌ Erro de navegação: {e}")
            resultado.update({
                'mensagem': f'Erro de navegação: {e}',
                'detalhes': {'erro_tipo': 'navegacao', 'erro_detalhes': str(e)}
            })
            raise
            
        except ExtractionException as e:
            logger.error(f"❌ Erro de processamento: {e}")
            resultado.update({
                'mensagem': f'Erro no processamento de mensagens: {e}',
                'detalhes': {'erro_tipo': 'processamento', 'erro_detalhes': str(e)}
            })
            raise
            
        except Exception as e:
            logger.error(f"❌ Erro inesperado: {e}")
            
            # Criar uma exceção SEFAZ wrapper usando ExtractionException
            if isinstance(e, (ElementNotFoundException, TimeoutException, DatabaseException, ExtractionException)):
                log_exception_details(e, logger)
                error_message = create_user_friendly_error_message(e)
                raise
            else:
                wrapped_exception = ExtractionException(f"MessageBot: {str(e)}")
                log_exception_details(wrapped_exception, logger)
                error_message = create_user_friendly_error_message(wrapped_exception)
            
            resultado.update({
                'mensagem': error_message,
                'detalhes': {'erro_tipo': 'geral', 'erro_detalhes': str(e)}
            })
            
            raise wrapped_exception from e
    
    async def _verificar_aviso_ciencia(self, page) -> bool:
        """
        Verifica se existe o aviso de mensagens aguardando ciência na página.
        
        Args:
            page: Página do navegador
            
        Returns:
            bool: True se há aviso de mensagens aguardando ciência
        """
        try:
            logger.info("🔍 Verificando presença de aviso de mensagens aguardando ciência...")
            
            # Procurar pelo texto específico do aviso
            aviso_element = page.locator('text="ATENÇÃO: VOCÊ POSSUI"')
            
            if await aviso_element.count() > 0:
                # Capturar o texto completo do aviso para log
                texto_aviso = await aviso_element.first.inner_text()
                logger.info(f"⚠️ Aviso detectado: {texto_aviso}")
                return True
            
            # Verificação alternativa usando contains para maior flexibilidade
            aviso_contains = page.locator('text*="AGUARDANDO CIÊNCIA"')
            if await aviso_contains.count() > 0:
                texto_aviso = await aviso_contains.first.inner_text()
                logger.info(f"⚠️ Aviso detectado (alternativo): {texto_aviso}")
                return True
                
            # Verificação final usando xpath mais flexível
            aviso_xpath = page.locator('xpath=//text()[contains(., "MENSAGEM") and contains(., "AGUARDANDO")]')
            if await aviso_xpath.count() > 0:
                texto_aviso = await aviso_xpath.first.inner_text()
                logger.info(f"⚠️ Aviso detectado (xpath): {texto_aviso}")
                return True
                
            logger.info("ℹ️ Nenhum aviso de mensagens aguardando ciência encontrado")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar aviso de ciência: {e}")
            # Em caso de erro, retornar True para tentar processar mesmo assim
            return True
    
    async def _validar_pagina_mensagens(self, page) -> bool:
        """
        Valida se estamos na página correta de mensagens.
        
        Args:
            page: Página do navegador
            
        Returns:
            bool: True se estamos na página de mensagens
        """
        try:
            # Verificar se temos elementos característicos da página de mensagens
            select_element = page.locator('select[name="visualizarMensagens"]')
            if await select_element.count() > 0:
                return True
                
            # Verificação alternativa por título ou outros elementos
            titulo_mensagens = page.locator('text*="Mensagem", text*="Domicílio"')
            if await titulo_mensagens.count() > 0:
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao validar página de mensagens: {e}")
            return False
    
    async def _processar_todas_mensagens_disponiveis(
        self, 
        page, 
        cpf: str, 
        inscricao_estadual: str
    ) -> int:
        """
        Processa todas as mensagens disponíveis usando múltiplos filtros.
        
        Primeiro verifica se há aviso de mensagens aguardando ciência,
        e então processa mensagens em filtros apropriados:
        1. Aguardando Ciência (se há aviso) 
        2. Não Lidas (sempre verifica)
        
        Args:
            page: Página do navegador
            cpf: CPF do usuário
            inscricao_estadual: Inscrição estadual da empresa
            
        Returns:
            int: Total de mensagens processadas
        """
        total_processadas = 0
        
        # Primeiro, verificar se há aviso de mensagens aguardando ciência
        logger.info("🔍 Verificando se há mensagens aguardando ciência...")
        tem_aviso_ciencia = await self._verificar_aviso_ciencia(page)
        
        # Lista de filtros baseada na presença do aviso
        filtros = []
        
        if tem_aviso_ciencia:
            logger.info("📋 Aviso de ciência detectado - incluindo filtro 'Aguardando Ciência'")
            filtros.append({
                'nome': 'Aguardando Ciência',
                'valor': '4',  # Valor do select para "Aguardando Ciência"
                'prioridade': 'alta'
            })
        
        # Sempre incluir "Não Lidas" para verificar outras mensagens
        filtros.append({
            'nome': 'Não Lidas', 
            'valor': '3',  # Valor do select para "Não Lidas"
            'prioridade': 'normal'
        })
        
        logger.info(f"📊 Filtros selecionados para processamento: {[f['nome'] for f in filtros]}")
        
        for filtro in filtros:
            logger.info(f"🔍 Verificando mensagens: {filtro['nome']}...")
            
            try:
                # Aplicar filtro específico
                filtro_aplicado = await self._aplicar_filtro_mensagens(page, filtro['valor'])
                if not filtro_aplicado:
                    logger.warning(f"⚠️ Não foi possível aplicar filtro: {filtro['nome']}")
                    continue
                
                # Aguardar carregamento da página após filtro
                await page.wait_for_timeout(2000)
                
                # Contar quantas mensagens estão disponíveis neste filtro
                count_mensagens = await self._contar_mensagens_na_tabela(page)
                
                if count_mensagens == 0:
                    logger.info(f"ℹ️ Nenhuma mensagem encontrada em: {filtro['nome']}")
                    continue
                    
                logger.info(f"📊 Encontradas {count_mensagens} mensagem(ns) em: {filtro['nome']}")
                
                # Processar todas as mensagens deste filtro
                processadas_filtro = await self._processar_mensagens_do_filtro(
                    page, cpf, inscricao_estadual, filtro, count_mensagens
                )
                
                total_processadas += processadas_filtro
                
                logger.info(f"✅ Processadas {processadas_filtro} mensagem(ns) do filtro: {filtro['nome']}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar filtro {filtro['nome']}: {e}")
                # Continuar com próximo filtro mesmo se houver erro
                continue
        
        logger.info(f"🎯 Total de mensagens processadas: {total_processadas}")
        return total_processadas
    
    async def _aplicar_filtro_mensagens(self, page, valor_filtro: str) -> bool:
        """
        Aplica filtro específico na caixa de entrada.
        
        Args:
            page: Página do navegador
            valor_filtro: Valor do select (3=Não Lidas, 4=Aguardando Ciência)
            
        Returns:
            bool: True se filtro foi aplicado com sucesso
        """
        try:
            logger.info(f"🔧 Aplicando filtro com valor: {valor_filtro}")
            
            # Primeiro, validar se estamos na página correta
            if not await self._validar_pagina_mensagens(page):
                logger.error("❌ Não estamos na página de mensagens correta")
                return False
            
            # Aguardar um momento para garantir que a página esteja carregada
            await page.wait_for_timeout(1500)
            
            # Localizar e configurar o select de visualizar mensagens
            select_filtro = page.locator('select[name="visualizarMensagens"]')
            
            # Verificar se o select existe e está visível
            if not await select_filtro.is_visible():
                logger.warning(f"⚠️ Select de filtro não encontrado ou não visível")
                
                # Tentativa alternativa de localizar o select
                select_alt = page.locator('select').filter(has_text="Todas")
                if await select_alt.count() > 0:
                    logger.info("🔍 Encontrado select alternativo")
                    select_filtro = select_alt.first
                else:
                    logger.error("❌ Nenhum select de filtro encontrado")
                    return False
            
            # Verificar se a opção desejada existe
            opcao_desejada = select_filtro.locator(f'option[value="{valor_filtro}"]')
            if not await opcao_desejada.count() > 0:
                logger.warning(f"⚠️ Opção {valor_filtro} não encontrada no select")
                return False
            
            # Selecionar o filtro desejado
            await select_filtro.select_option(valor_filtro)
            logger.info(f"✅ Filtro {valor_filtro} selecionado")
            
            # Aguardar um pouco para o select ser processado
            await page.wait_for_timeout(1000)
            
            # Clicar no botão "Atualizar" para aplicar o filtro
            btn_atualizar = page.locator('button:has-text("Atualizar"), input[value*="Atualizar"]')
            
            if await btn_atualizar.count() > 0 and await btn_atualizar.first.is_visible():
                await btn_atualizar.first.click()
                logger.info("✅ Botão Atualizar clicado")
                
                # Aguardar carregamento da página
                await page.wait_for_timeout(3000)
                return True
            else:
                logger.warning("⚠️ Botão Atualizar não encontrado")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao aplicar filtro {valor_filtro}: {e}")
            return False
    
    async def _contar_mensagens_na_tabela(self, page) -> int:
        """
        Conta quantas mensagens estão visíveis na tabela.
        
        Args:
            page: Página do navegador
            
        Returns:
            int: Número de mensagens na tabela
        """
        try:
            # Procurar por linhas da tabela que contêm mensagens
            # As mensagens têm links com padrão abrirMensagem
            linhas_mensagem = page.locator('a[href*="abrirMensagem"]')
            
            count = await linhas_mensagem.count()
            
            logger.info(f"📊 Contadas {count} mensagens na tabela atual")
            return count
            
        except Exception as e:
            logger.error(f"❌ Erro ao contar mensagens: {e}")
            return 0
    
    async def _processar_mensagens_do_filtro(
        self, 
        page, 
        cpf: str, 
        inscricao_estadual: str, 
        filtro: Dict[str, str], 
        count_mensagens: int
    ) -> int:
        """
        Processa todas as mensagens de um filtro específico.
        
        Args:
            page: Página do navegador
            cpf: CPF do usuário
            inscricao_estadual: Inscrição estadual
            filtro: Dados do filtro atual
            count_mensagens: Número de mensagens para processar
            
        Returns:
            int: Número de mensagens processadas com sucesso
        """
        processadas = 0
        
        logger.info(f"🔄 Iniciando processamento de {count_mensagens} mensagem(ns) do filtro: {filtro['nome']}")
        
        for i in range(count_mensagens):
            try:
                logger.info(f"📝 Processando mensagem {i + 1}/{count_mensagens} - Filtro: {filtro['nome']}")
                
                # Recarregar página para garantir que estamos na lista atual
                await self._aplicar_filtro_mensagens(page, filtro['valor'])
                
                # Procurar por links de mensagens
                links_mensagem = page.locator('a[href*="abrirMensagem"]')
                
                # Verificar se ainda há mensagens
                count_atual = await links_mensagem.count()
                if count_atual == 0:
                    logger.info(f"ℹ️ Não há mais mensagens no filtro: {filtro['nome']}")
                    break
                
                # Sempre processar a primeira mensagem disponível (após recarregamento)
                primeiro_link = links_mensagem.first
                
                if not await primeiro_link.is_visible():
                    logger.warning(f"⚠️ Link da mensagem não está visível")
                    continue
                
                # Clicar na mensagem
                await primeiro_link.click()
                
                # Aguardar carregamento da página da mensagem
                await page.wait_for_timeout(3000)
                
                # Processar a mensagem usando o processador existente
                resultado_processamento = await self.message_processor.processar_mensagem_individual(
                    page, cpf, inscricao_estadual
                )
                
                if resultado_processamento:
                    processadas += 1
                    logger.info(f"✅ Mensagem {i + 1} processada com sucesso")
                else:
                    logger.warning(f"⚠️ Falha ao processar mensagem {i + 1}")
                
                # Voltar para a lista de mensagens
                await self._voltar_para_lista_mensagens(page)
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar mensagem {i + 1}: {e}")
                # Tentar voltar para lista mesmo em caso de erro
                try:
                    await self._voltar_para_lista_mensagens(page)
                except:
                    pass
                continue
        
        return processadas
    
    async def _voltar_para_lista_mensagens(self, page):
        """
        Volta para a lista principal de mensagens.
        
        Args:
            page: Página do navegador
        """
        try:
            # Procurar por botão "Voltar" ou link de retorno
            botao_voltar = page.locator('button:has-text("Voltar"), a:has-text("Voltar"), input[value*="Voltar"]')
            
            if await botao_voltar.first.is_visible():
                await botao_voltar.first.click()
                await page.wait_for_timeout(2000)
                logger.info("🔙 Voltou para lista de mensagens")
                return True
            
            # Se não encontrar botão voltar, tentar navegar via JavaScript/history
            await page.go_back()
            await page.wait_for_timeout(2000)
            logger.info("🔙 Voltou via navegação do browser")
            
        except Exception as e:
            logger.error(f"❌ Erro ao voltar para lista: {e}")
            # Em caso de erro, recarregar a página principal do domicílio eletrônico
            try:
                await page.goto(page.url.split('?')[0])  # Remove parâmetros e recarrega
                await page.wait_for_timeout(3000)
            except:
                pass

    def verificar_conexao_banco(self) -> bool:
        """
        Verifica se a conexão com o banco de dados está funcionando.
        
        Returns:
            bool: True se conexão está OK
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            return True
        except Exception as e:
            logger.error(f"❌ Erro na conexão com banco: {e}")
            return False
    
    def get_estatisticas_mensagens(self, inscricao_estadual: Optional[str] = None) -> Dict[str, int]:
        """
        Obtém estatísticas de mensagens processadas.
        
        Args:
            inscricao_estadual: Se fornecido, filtra por empresa específica
            
        Returns:
            Dict com estatísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if inscricao_estadual:
                # Estatísticas para empresa específica
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN data_envio >= datetime('now', '-1 day') THEN 1 END) as hoje,
                        COUNT(CASE WHEN data_envio >= datetime('now', '-7 days') THEN 1 END) as semana
                    FROM mensagens_sefaz 
                    WHERE inscricao_estadual = ?
                """, (inscricao_estadual,))
            else:
                # Estatísticas globais
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN data_envio >= datetime('now', '-1 day') THEN 1 END) as hoje,
                        COUNT(CASE WHEN data_envio >= datetime('now', '-7 days') THEN 1 END) as semana
                    FROM mensagens_sefaz
                """)
            
            row = cursor.fetchone()
            conn.close()
            
            return {
                'total': row[0] if row else 0,
                'hoje': row[1] if row else 0,
                'semana': row[2] if row else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {'total': 0, 'hoje': 0, 'semana': 0}


# Função utilitária para uso direto
async def processar_mensagens_direto(
    cpf: str, 
    senha: str, 
    inscricao_estadual: str,
    headless: bool = True,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Função utilitária para processamento direto de mensagens.
    
    Args:
        cpf: CPF do usuário
        senha: Senha de acesso
        inscricao_estadual: Inscrição estadual da empresa  
        headless: Se True, executa sem interface gráfica
        db_path: Caminho para o banco de dados
        
    Returns:
        Dict com resultados do processamento
    """
    bot = MessageBot(db_path)
    return await bot.processar_mensagens_empresa(cpf, senha, inscricao_estadual, headless)


if __name__ == "__main__":
    """
    Exemplo de uso direto do MessageBot para testes.
    
    Execute: python -m src.bot.message_bot
    """
    import asyncio
    
    async def exemplo():
        # Configurar logging para testes
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Dados de exemplo (substituir por dados reais para teste)
        cpf = "12345678900"
        senha = "senha_exemplo"  
        ie = "123456789"
        
        try:
            resultado = await processar_mensagens_direto(
                cpf=cpf,
                senha=senha, 
                inscricao_estadual=ie,
                headless=False  # Para ver o que está acontecendo durante teste
            )
            
            print("\n🎉 Resultado do processamento:")
            print(f"✅ Sucesso: {resultado['sucesso']}")
            print(f"📨 Mensagens processadas: {resultado['mensagens_processadas']}")
            print(f"💬 Mensagem: {resultado['mensagem']}")
            print(f"📊 Detalhes: {resultado['detalhes']}")
            
        except Exception as e:
            print(f"\n❌ Erro durante teste: {e}")
    
    # Executar exemplo apenas se não estivermos importando o módulo
    # asyncio.run(exemplo())
    print("MessageBot criado com sucesso! Descomente a linha acima para testar.")