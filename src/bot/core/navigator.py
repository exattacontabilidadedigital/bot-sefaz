"""
Módulo de navegação para o bot SEFAZ.

Este módulo contém classes especializadas para navegação no sistema SEFAZ,
separando responsabilidades para melhor manutenibilidade.
"""

from typing import Optional
import logging
from playwright.async_api import Page

from src.bot.utils.selectors import SEFAZSelectors
from src.bot.utils.human_behavior import HumanBehavior
from src.bot.exceptions.base import (
    NavigationException,
    ElementNotFoundException,
    TimeoutException
)

logger = logging.getLogger(__name__)


class SEFAZNavigator:
    """Classe responsável pela navegação no sistema SEFAZ"""
    
    def __init__(self):
        self.selectors = SEFAZSelectors()
    
    async def check_pending_messages(self, page: Page) -> bool:
        """
        Verifica se há mensagens aguardando ciência na tela inicial
        
        Args:
            page: Página do Playwright
            
        Returns:
            bool: True se há mensagens aguardando ciência
        """
        try:
            # Procurar pelo texto de aviso de mensagens
            warning_text = "VOCÊ POSSUI"
            awaiting_text = "AGUARDANDO CIÊNCIA"
            
            # Verificar se o texto de aviso está presente
            page_content = await page.content()
            
            if warning_text in page_content and awaiting_text in page_content:
                logger.info("📨 Detectadas mensagens aguardando ciência")
                return True
                
            return False
            
        except Exception as e:
            logger.warning(f"Erro ao verificar mensagens pendentes: {e}")
            return False
    
    async def click_message_link(self, page: Page) -> bool:
        """
        Clica no link da mensagem aguardando ciência
        
        Args:
            page: Página do Playwright
            
        Returns:
            bool: True se clicou com sucesso
        """
        try:
            # Procurar pelo link da mensagem
            message_selectors = [
                "a[href*='abrirMensagemDomicilio.do']",
                "a[href*='abrirMensagem']",
                "img[src*='ic_msg_nova.png']"
            ]
            
            for selector in message_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        logger.info(f"🎯 Clicando no link da mensagem: {selector}")
                        
                        # Se for uma imagem, clicar no link pai
                        if "img" in selector:
                            parent_link = await element.query_selector("xpath=..")
                            if parent_link:
                                await HumanBehavior.human_click(page, parent_link)
                            else:
                                await HumanBehavior.human_click(page, element)
                        else:
                            await HumanBehavior.human_click(page, element)
                        
                        await page.wait_for_timeout(HumanBehavior.random_delay(1000, 2000))
                        logger.info("✅ Link da mensagem clicado com sucesso")
                        return True
                        
                except Exception as e:
                    logger.debug(f"Tentativa com seletor {selector} falhou: {e}")
                    continue
            
            logger.warning("❌ Não foi possível encontrar link da mensagem")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao clicar no link da mensagem: {e}")
            return False
    
    async def open_sistemas_menu(self, page: Page) -> bool:
        """
        Abre o menu 'Sistemas' usando diferentes estratégias
        
        Args:
            page: Página do Playwright
            
        Returns:
            bool: True se menu foi aberto com sucesso
        """
        try:
            logger.info("🔍 Abrindo menu 'Sistemas'...")
            
            # Estratégia 1: Seletor CSS específico
            menu_selectors = self.selectors.get_menu_selectors()
            
            for selector_key, selector in menu_selectors.items():
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        await HumanBehavior.human_click(page, element)
                        await page.wait_for_timeout(HumanBehavior.random_delay(500, 1000))
                        logger.info(f"✅ Menu 'Sistemas' aberto via: {selector_key}")
                        return True
                except Exception as e:
                    logger.debug(f"Falha no seletor {selector_key}: {e}")
                    continue
            
            # Estratégia final: JavaScript direto
            menu_found = await page.evaluate("""
                () => {
                    const dropdowns = document.querySelectorAll('a.dropdown-toggle');
                    for (let dropdown of dropdowns) {
                        if (dropdown.textContent.includes('Sistemas') || 
                            dropdown.querySelector('i.glyphicon-cog')) {
                            dropdown.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            
            if menu_found:
                await page.wait_for_timeout(HumanBehavior.random_delay(500, 1000))
                logger.info("✅ Menu 'Sistemas' aberto via JavaScript")
                return True
            
            logger.warning("❌ Não foi possível abrir menu 'Sistemas'")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao abrir menu 'Sistemas': {e}")
            return False
    
    async def click_todas_areas_negocio(self, page: Page) -> bool:
        """
        Clica no botão 'Todas as Áreas de Negócio'
        
        Args:
            page: Página do Playwright
            
        Returns:
            bool: True se clicou com sucesso
        """
        try:
            logger.info("📍 Clicando em 'Todas as Áreas de Negócio'...")
            
            menu_selectors = self.selectors.get_menu_selectors()
            
            # Procurar o botão
            todas_areas_button = await page.query_selector(menu_selectors['todas_areas_negocio'])
            if not todas_areas_button:
                todas_areas_button = await page.query_selector(menu_selectors['todas_areas_onclick'])
            
            if not todas_areas_button:
                logger.error("❌ Botão 'Todas as Áreas de Negócio' não encontrado")
                return False
            
            # Verificar visibilidade
            is_visible = await todas_areas_button.is_visible()
            logger.info(f"Botão encontrado, visível: {is_visible}")
            
            if not is_visible:
                # Forçar visibilidade via JavaScript
                await page.evaluate("""
                    () => {
                        const link = document.querySelector("a[onclick*=\\"listMenu(document.menuForm,this,'all')\\"]");
                        if (link) {
                            link.style.display = 'block';
                            link.style.visibility = 'visible';
                        }
                    }
                """)
                await page.wait_for_timeout(500)
            
            # Tentar clicar
            try:
                await HumanBehavior.human_click(page, todas_areas_button)
                logger.info("✅ Clicado em 'Todas as Áreas de Negócio'")
            except Exception:
                # Fallback para onclick via JavaScript
                click_success = await page.evaluate("""
                    () => {
                        const link = document.querySelector("a[onclick*=\\"listMenu(document.menuForm,this,'all')\\"]");
                        if (link && link.onclick) {
                            link.onclick.call(link);
                            return true;
                        }
                        return false;
                    }
                """)
                if not click_success:
                    logger.error("❌ Não foi possível acionar onclick")
                    return False
                logger.info("✅ onclick acionado via JavaScript")
            
            # Aguardar carregamento
            await HumanBehavior.wait_for_page_stability(page)
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao clicar em 'Todas as Áreas de Negócio': {e}")
            return False
    
    async def expand_conta_fiscal_node(self, page: Page) -> bool:
        """
        Expande o nó 'Conta Fiscal' na árvore jstree
        
        Args:
            page: Página do Playwright
            
        Returns:
            bool: True se expandiu com sucesso
        """
        try:
            logger.info("📍 Expandindo nó 'Conta Fiscal'...")
            
            # Aguardar a árvore jstree carregar
            await page.wait_for_selector(SEFAZSelectors.JSTREE['container'], timeout=10000)
            await page.wait_for_timeout(1000)
            
            # Expandir o nó Conta Fiscal
            conta_fiscal_expandido = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a.jstree-anchor');
                    for (let link of links) {
                        const texto = link.textContent.trim();
                        if (texto === 'Conta Fiscal') {
                            const li = link.closest('li');
                            if (li && li.classList.contains('jstree-closed')) {
                                const ocl = li.querySelector('.jstree-ocl');
                                if (ocl) {
                                    ocl.click();
                                    return 'expandido';
                                }
                            }
                            return li.classList.contains('jstree-open') ? 'ja_aberto' : 'sem_ocl';
                        }
                    }
                    return 'nao_encontrado';
                }
            """)
            
            if conta_fiscal_expandido == 'nao_encontrado':
                logger.error("❌ Nó 'Conta Fiscal' não encontrado")
                return False
            
            logger.info(f"✅ Nó 'Conta Fiscal' {conta_fiscal_expandido}")
            await page.wait_for_timeout(HumanBehavior.random_delay(2000, 3000))
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao expandir nó 'Conta Fiscal': {e}")
            return False
    
    async def click_consultar_conta_corrente(self, page: Page) -> bool:
        """
        Clica no link 'Consultar Conta-Corrente Fiscal'
        
        Args:
            page: Página do Playwright
            
        Returns:
            bool: True se clicou com sucesso
        """
        try:
            logger.info("📍 Clicando em 'Consultar Conta-Corrente Fiscal'...")
            
            # Aguardar submenu carregar
            await page.wait_for_timeout(HumanBehavior.random_delay(1000, 1500))
            
            # Clicar no link
            consultar_clicado = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a.jstree-anchor');
                    
                    for (let link of links) {
                        const texto = link.textContent.trim();
                        const li = link.closest('li');
                        
                        // Verificar se está visível
                        const isVisible = li && !li.classList.contains('jstree-hidden') && link.offsetParent !== null;
                        
                        if (isVisible && texto.toLowerCase().includes('consultar') && 
                            texto.toLowerCase().includes('conta') && 
                            texto.toLowerCase().includes('corrente')) {
                            link.click();
                            return texto;
                        }
                    }
                    
                    // Fallback para qualquer link com essas palavras
                    const allLinks = document.querySelectorAll('a');
                    for (let link of allLinks) {
                        const texto = link.textContent.trim();
                        if (texto.toLowerCase().includes('consultar') && 
                            texto.toLowerCase().includes('conta') && 
                            texto.toLowerCase().includes('corrente')) {
                            link.click();
                            return texto;
                        }
                    }
                    return null;
                }
            """)
            
            if not consultar_clicado:
                logger.error("❌ Link 'Consultar Conta-Corrente Fiscal' não encontrado")
                return False
            
            logger.info(f"✅ Clicado em: '{consultar_clicado}'")
            
            # Aguardar navegação completar antes de prosseguir
            logger.info("⏳ Aguardando navegação para página de consulta...")
            await page.wait_for_load_state("networkidle", timeout=30000)
            await HumanBehavior.wait_for_page_stability(page)
            
            logger.info("✅ Página de consulta carregada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao clicar em 'Consultar Conta-Corrente Fiscal': {e}")
            return False
    
    async def fill_inscricao_estadual_form(self, page: Page, inscricao_estadual: Optional[str] = None) -> bool:
        """
        Preenche o formulário de inscrição estadual se necessário
        
        Args:
            page: Página do Playwright
            inscricao_estadual: Número da IE
            
        Returns:
            bool: True se preencheu/confirmou com sucesso, ou se não era necessário
        """
        try:
            logger.info("📋 Verificando necessidade de preencher IE...")
            
            # Aguardar página estabilizar após navegação
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
                await page.wait_for_timeout(1000)
            except Exception as e:
                logger.warning(f"⚠️ Timeout aguardando página: {e}")
            
            # Verificar se campo existe usando wait_for_selector com timeout curto
            form_selectors = self.selectors.get_form_selectors()
            
            try:
                # Tentar esperar pelo campo por 3 segundos
                ie_input = await page.wait_for_selector(
                    form_selectors['inscricao_estadual_input'], 
                    timeout=3000,
                    state="visible"
                )
                logger.info("⚠️ Campo de IE encontrado - múltiplas IEs")
            except Exception:
                # Campo não existe - CPF tem apenas uma IE
                logger.info("✅ Campo de IE não encontrado - CPF possui apenas uma IE")
                return True
            
            # Se chegou aqui, campo existe e IE é necessária
            if not inscricao_estadual:
                logger.warning("❌ IE é necessária mas não foi fornecida")
                return False
            
            # Limpar IE (apenas números)
            ie_limpa = ''.join(filter(str.isdigit, str(inscricao_estadual)))
            logger.info(f"📝 Preenchendo IE: {ie_limpa}")
            
            # Preencher campo
            await HumanBehavior.human_click(page, ie_input)
            await page.wait_for_timeout(1000)
            await ie_input.fill("")
            await page.wait_for_timeout(500)
            await ie_input.type(ie_limpa, delay=HumanBehavior.random_delay(50, 150))
            
            # Confirmar IE
            confirmar_link = await page.query_selector(form_selectors['confirmar_ie_link'])
            if not confirmar_link:
                confirmar_img = await page.query_selector(form_selectors['confirmar_ie_img'])
                if confirmar_img:
                    confirmar_link = await confirmar_img.evaluate_handle("element => element.closest('a')")
            
            if confirmar_link:
                await HumanBehavior.human_click(page, confirmar_link)
                await page.wait_for_timeout(HumanBehavior.random_delay(2000, 3000))
                
                # Verificar se Razão Social foi preenchida
                razao_social = await page.query_selector(form_selectors['razao_social_input'])
                if razao_social:
                    razao_value = await razao_social.get_attribute("value")
                    if razao_value and razao_value.strip():
                        logger.info(f"✅ IE confirmada! Razão Social: {razao_value}")
                        return True
                    else:
                        logger.warning("⚠️ IE pode estar incorreta")
                        return False
            else:
                logger.error("❌ Botão de confirmar IE não encontrado")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao preencher IE: {e}")
            # Se der erro por navegação, considerar que não precisa de IE
            if "Execution context was destroyed" in str(e):
                logger.info("ℹ️ Contexto destruído - provavelmente não precisa de IE")
                return True
            return False
    
    async def click_continuar_button(self, page: Page) -> bool:
        """
        Clica no botão 'Continuar' do formulário
        
        Args:
            page: Página do Playwright
            
        Returns:
            bool: True se clicou com sucesso
        """
        try:
            logger.info("🔍 Procurando botão 'Continuar'...")
            
            continuar_selectors = self.selectors.get_continuar_button_selectors()
            
            for selector in continuar_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button and await button.is_visible():
                        logger.info("✅ Botão 'Continuar' encontrado!")
                        await HumanBehavior.human_click(page, button)
                        logger.info(f"✅ Botão 'Continuar' clicado")
                        
                        # Aguardar carregamento
                        await HumanBehavior.wait_for_page_stability(page)
                        await page.wait_for_timeout(HumanBehavior.random_delay(2000, 3000))
                        
                        # Verificar se página carregou
                        page_content = await page.content()
                        if "Inscrição Estadual" in page_content or "Situação Cadastral" in page_content:
                            logger.info("✅ Página de dados carregada com sucesso!")
                        
                        return True
                except Exception:
                    continue
            
            logger.warning("❌ Botão 'Continuar' não encontrado")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao clicar em 'Continuar': {e}")
            return False
    
    async def navigate_to_conta_corrente_complete(self, page: Page, inscricao_estadual: Optional[str] = None) -> bool:
        """
        Executa a navegação completa até a Conta Corrente
        
        Args:
            page: Página do Playwright
            inscricao_estadual: IE opcional para preenchimento
            
        Returns:
            bool: True se navegação foi bem-sucedida
        """
        try:
            logger.info("="*80)
            logger.info("🚀 INICIANDO NAVEGAÇÃO COMPLETA PARA CONTA-CORRENTE")
            logger.info("="*80)
            
            # Passo 1: Abrir menu Sistemas
            if not await self.open_sistemas_menu(page):
                logger.error("❌ Falha ao abrir menu Sistemas")
                return False
            
            # Passo 2: Clicar em Todas as Áreas de Negócio
            if not await self.click_todas_areas_negocio(page):
                logger.error("❌ Falha ao clicar em 'Todas as Áreas de Negócio'")
                return False
            
            # Passo 3: Expandir nó Conta Fiscal
            if not await self.expand_conta_fiscal_node(page):
                logger.error("❌ Falha ao expandir nó 'Conta Fiscal'")
                return False
            
            # Passo 4: Clicar em Consultar Conta-Corrente Fiscal
            if not await self.click_consultar_conta_corrente(page):
                logger.error("❌ Falha ao clicar em 'Consultar Conta-Corrente Fiscal'")
                return False
            
            # Passo 5: Preencher IE se necessário
            if not await self.fill_inscricao_estadual_form(page, inscricao_estadual):
                logger.error("❌ Falha ao preencher/confirmar IE")
                return False
            
            # Passo 6: Clicar em Continuar
            if not await self.click_continuar_button(page):
                logger.warning("⚠️ Problema ao clicar em Continuar, mas pode estar na página correta")
            
            logger.info("="*80)
            logger.info("✅ NAVEGAÇÃO COMPLETA CONCLUÍDA COM SUCESSO!")
            logger.info("="*80)
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na navegação completa: {e}")
            return False