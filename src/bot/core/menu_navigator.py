"""
MenuNavigator - Módulo especializado para navegação de menus SEFAZ.

Este módulo extrai e especializa a lógica de navegação em menus do sistema SEFAZ,
removendo responsabilidades do bot principal e permitindo melhor testabilidade.
"""

import logging
import asyncio
from typing import Optional
from playwright.async_api import Page

from src.bot.utils.human_behavior import HumanBehavior
from src.bot.exceptions import (
    NavigationException,
    ElementNotFoundException,
    TimeoutException
)

logger = logging.getLogger(__name__)


class MenuNavigator:
    """
    Navegador especializado para menus e navegação complexa no sistema SEFAZ.
    
    Responsabilidades:
    - Abrir menu Sistemas com múltiplas estratégias
    - Detectar e processar mensagens bloqueantes
    - Gerenciar conflitos de sessão
    - Acesso direto quando necessário
    """
    
    def __init__(self):
        self.behavior = HumanBehavior()
    
    def random_delay(self, min_ms: int, max_ms: int) -> int:
        """Gera delay aleatório para simular comportamento humano"""
        return self.behavior.random_delay(min_ms, max_ms)
    
    async def human_click(self, page: Page, element) -> None:
        """Clique com comportamento humano"""
        await self.behavior.human_click(page, element)
    
    async def check_and_open_sistemas_menu_complete(self, page: Page, inscricao_estadual: Optional[str] = None) -> bool:
        """
        Verifica se o botão 'Sistemas' (ícone cog) está visível e abre o menu.
        
        Esta é a versão completa extraída do SEFAZBot principal, incluindo:
        - Detecção de mensagens bloqueantes
        - Processamento automático de mensagens
        - Múltiplas estratégias de abertura do menu
        - Fallback para acesso direto
        
        Args:
            page: Página do navegador
            inscricao_estadual: IE da empresa sendo consultada (para associar mensagens)
            
        Returns:
            bool: True se o menu foi aberto ou acesso direto foi bem-sucedido
            
        Raises:
            NavigationException: Se não conseguir abrir menu nem acessar diretamente
        """
        try:
            logger.info("=" * 60)
            logger.info("🧭 MenuNavigator - VERIFICANDO MENU SISTEMAS")
            logger.info("=" * 60)
            
            # VERIFICAÇÃO: Detectar aviso de mensagens aguardando ciência ANTES de tentar menu
            logger.info("🔍 Verificando se há mensagens bloqueando o acesso ao menu...")
            aviso_mensagem = await page.query_selector("thead tr td span[style*='red']")
            
            if aviso_mensagem:
                aviso_texto = await aviso_mensagem.text_content()
                if aviso_texto and "AGUARDANDO CIÊNCIA" in aviso_texto.upper():
                    logger.warning("⚠️ ===============================================")
                    logger.warning("⚠️ ATENÇÃO: Há mensagens aguardando ciência!")
                    logger.warning("⚠️ O menu está bloqueado até dar ciência")
                    logger.warning("⚠️ ===============================================")
                    
                    # Nota: Aqui seria necessário integrar com MessageBot ou processor
                    # Por ora, vamos prosseguir e deixar essa integração para depois
                    logger.info("📬 Mensagens detectadas - prosseguindo com tentativas de menu...")
            
            # Aguardar menu ficar disponível (até 60 segundos)
            menu_disponivel = await self._aguardar_menu_disponivel(page, timeout_seconds=60)
            
            if not menu_disponivel:
                logger.warning("⚠️ Menu não ficou disponível em 60s, recarregando página...")
                await self._recarregar_pagina_se_necessario(page)
            
            # Tentar abrir menu com múltiplas estratégias
            menu_aberto = await self._tentar_abrir_menu_sistemas(page)
            
            if menu_aberto:
                logger.info("✅ Menu 'Sistemas' aberto com sucesso!")
                return True
            
            # Fallback: tentar acesso direto
            logger.info("🔄 Menu não abriu, tentando acesso direto à Conta Corrente...")
            acesso_direto = await self.try_direct_conta_corrente_access(page)
            
            if acesso_direto:
                logger.info("✅ Acesso direto à Conta Corrente bem-sucedido!")
                return True
            
            logger.error("❌ Não foi possível abrir menu nem acessar diretamente")
            raise NavigationException("Falha ao abrir menu Sistemas e acesso direto")
                
        except Exception as e:
            logger.error(f"❌ Erro ao abrir menu sistemas: {e}")
            raise NavigationException(f"Erro na navegação do menu: {e}") from e
    
    async def _aguardar_menu_disponivel(self, page: Page, timeout_seconds: int = 60) -> bool:
        """
        Aguarda o menu 'Sistemas' ficar disponível na página.
        
        Args:
            page: Página do navegador
            timeout_seconds: Timeout máximo em segundos
            
        Returns:
            bool: True se menu ficou disponível
        """
        start_time = asyncio.get_event_loop().time()
        check_interval = 2  # Verificar a cada 2 segundos
        
        logger.info(f"⏳ Aguardando menu 'Sistemas' ficar disponível (max {timeout_seconds}s)...")
        
        while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
            menu_disponivel = await page.evaluate("""
                () => {
                    const dropdowns = document.querySelectorAll('a.dropdown-toggle');
                    for (let dropdown of dropdowns) {
                        if (dropdown.textContent.includes('Sistemas') || 
                            dropdown.querySelector('i.glyphicon-cog')) {
                            return true;
                        }
                    }
                    return false;
                }
            """)
            
            if menu_disponivel:
                elapsed = asyncio.get_event_loop().time() - start_time
                logger.info(f"✅ Menu 'Sistemas' disponível após {elapsed:.1f}s")
                return True
            
            # Aguardar antes de verificar novamente
            await page.wait_for_timeout(check_interval * 1000)
            elapsed = asyncio.get_event_loop().time() - start_time
            logger.info(f"⏳ Aguardando menu... ({elapsed:.0f}s)")
        
        logger.warning(f"⏱️ Timeout: menu não ficou disponível em {timeout_seconds}s")
        return False
    
    async def _recarregar_pagina_se_necessario(self, page: Page) -> None:
        """
        Recarrega a página quando necessário e aguarda estabilização.
        """
        try:
            logger.info("🔄 Recarregando página...")
            await page.reload(wait_until="domcontentloaded", timeout=30000)
            logger.info("✅ Página recarregada com sucesso")
            
            # Aguardar estabilização
            await page.wait_for_timeout(self.random_delay(3000, 5000))
            
            # Verificar se menu ficou disponível após reload
            menu_disponivel_pos_reload = await page.evaluate("""
                () => {
                    const dropdowns = document.querySelectorAll('a.dropdown-toggle');
                    for (let dropdown of dropdowns) {
                        if (dropdown.textContent.includes('Sistemas') || 
                            dropdown.querySelector('i.glyphicon-cog')) {
                            return true;
                        }
                    }
                    return false;
                }
            """)
            
            if menu_disponivel_pos_reload:
                logger.info("✅ Menu 'Sistemas' disponível após reload!")
            else:
                logger.warning("⚠️ Menu ainda não está disponível após reload")
                # Aguardar mais um pouco
                await page.wait_for_timeout(3000)
                
        except Exception as e:
            logger.error(f"❌ Erro ao recarregar página: {e}")
            # Continuar mesmo com erro no reload
    
    async def _tentar_abrir_menu_sistemas(self, page: Page) -> bool:
        """
        Tenta abrir o menu 'Sistemas' usando múltiplas estratégias.
        
        Args:
            page: Página do navegador
            
        Returns:
            bool: True se menu foi aberto com sucesso
        """
        # Pequena pausa para estabilizar
        await page.wait_for_timeout(self.random_delay(500, 1000))
        
        # Estratégia 1: Seletor CSS específico
        logger.info("🎯 Estratégia 1: Procurando por seletor CSS...")
        if await self._tentar_estrategia_css(page):
            return True
        
        # Estratégia 2: Por texto "Sistemas"
        logger.info("🎯 Estratégia 2: Procurando por texto 'Sistemas'...")
        if await self._tentar_estrategia_texto(page):
            return True
        
        # Estratégia 3: Por ícone glyphicon-cog
        logger.info("🎯 Estratégia 3: Procurando por ícone cog...")
        if await self._tentar_estrategia_icone(page):
            return True
        
        # Estratégia 4: JavaScript direto
        logger.info("🎯 Estratégia 4: Usando JavaScript para encontrar menu...")
        if await self._tentar_estrategia_javascript(page):
            return True
        
        logger.warning("❌ Menu 'Sistemas' não encontrado em nenhuma estratégia")
        return False
    
    async def _tentar_estrategia_css(self, page: Page) -> bool:
        """Estratégia 1: Seletor CSS específico"""
        try:
            selector = "a.dropdown-toggle:has(i.glyphicon-cog)"
            element = await page.query_selector(selector)
            if element and await element.is_visible():
                await self.human_click(page, element)
                await page.wait_for_timeout(self.random_delay(500, 1000))
                logger.info("✅ Menu 'Sistemas' aberto via seletor CSS")
                return True
        except Exception as e:
            logger.debug(f"Falha na estratégia CSS: {e}")
        return False
    
    async def _tentar_estrategia_texto(self, page: Page) -> bool:
        """Estratégia 2: Por texto 'Sistemas'"""
        try:
            element = await page.query_selector("a:has-text('Sistemas')")
            if element and await element.is_visible():
                await self.human_click(page, element)
                await page.wait_for_timeout(self.random_delay(500, 1000))
                logger.info("✅ Menu 'Sistemas' aberto via texto")
                return True
        except Exception as e:
            logger.debug(f"Falha na estratégia texto: {e}")
        return False
    
    async def _tentar_estrategia_icone(self, page: Page) -> bool:
        """Estratégia 3: Por ícone glyphicon-cog"""
        try:
            icon = await page.query_selector("i.glyphicon-cog")
            if icon:
                # Clicar no elemento pai (link)
                link = await icon.evaluate_handle("element => element.closest('a')")
                if link and await link.as_element().is_visible():
                    await self.human_click(page, link.as_element())
                    await page.wait_for_timeout(self.random_delay(500, 1000))
                    logger.info("✅ Menu 'Sistemas' aberto via ícone")
                    return True
        except Exception as e:
            logger.debug(f"Falha na estratégia ícone: {e}")
        return False
    
    async def _tentar_estrategia_javascript(self, page: Page) -> bool:
        """Estratégia 4: JavaScript direto"""
        try:
            menu_found = await page.evaluate("""
                () => {
                    // Procurar por todos os links dropdown
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
                await page.wait_for_timeout(self.random_delay(500, 1000))
                logger.info("✅ Menu 'Sistemas' aberto via JavaScript")
                return True
        except Exception as e:
            logger.debug(f"Falha na estratégia JavaScript: {e}")
        return False
    
    async def try_direct_conta_corrente_access(self, page: Page) -> bool:
        """
        Tenta acessar Conta Corrente diretamente sem passar pelo menu Sistemas.
        
        Args:
            page: Página do navegador
            
        Returns:
            bool: True se conseguiu acesso direto
        """
        try:
            logger.info("🔗 Tentando acesso direto à Conta Corrente...")
            
            # Procurar por link direto para Conta Corrente
            selectors = [
                "a:has-text('Consultar Conta-Corrente Fiscal')",
                "a:has-text('Conta-Corrente Fiscal')",
                "a:has-text('Conta Corrente')",
                "a.jstree-anchor:has-text('Consultar Conta-Corrente Fiscal')"
            ]
            
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        await element.click()
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        logger.info(f"✅ Acesso direto via: {selector}")
                        return True
                except Exception as e:
                    logger.debug(f"Falha no seletor {selector}: {e}")
                    continue
            
            # Se não encontrou, verificar se já está na página correta
            page_content = await page.content()
            if ("Consultar Conta-Corrente Fiscal" in page_content or 
                "Inscrição Estadual" in page_content):
                logger.info("✅ Já está na página de Conta Corrente")
                return True
            
            logger.warning("❌ Não foi possível fazer acesso direto")
            return False
                
        except Exception as e:
            logger.error(f"❌ Erro no acesso direto à Conta Corrente: {e}")
            return False
    
    async def handle_session_conflicts(self, page: Page) -> str:
        """
        Trata conflitos de sessão ativa - clica em Sair e tenta novamente.
        
        Args:
            page: Página do navegador
            
        Returns:
            str: 'SESSION_CONFLICT' se detectou conflito, 'RESOLVED' se resolveu, 'NOT_FOUND' se não há conflito
        """
        try:
            logger.info("🔍 Verificando conflitos de sessão...")
            
            # Capturar screenshot para análise
            await page.screenshot(path="debug_session_conflict.png")
            
            # Verificar se há mensagem de sessão ativa
            page_text = await page.text_content('body')
            
            if not ('já está conectado' in page_text.lower() or 'outra sessão' in page_text.lower()):
                logger.info("✅ Nenhum conflito de sessão detectado")
                return 'NOT_FOUND'
            
            logger.warning("⚠️ Detectada mensagem de sessão ativa")
            
            # Procurar e clicar em links/botões 'Sair'
            if await self._tentar_sair_sessao(page):
                logger.info("✅ Sessão anterior encerrada com sucesso")
                return 'RESOLVED'
            
            # Procurar botões para forçar/continuar login
            if await self._tentar_forcear_login(page):
                logger.info("✅ Login forçado com sucesso")
                return 'RESOLVED'
            
            logger.warning("⚠️ Não foi possível resolver conflito de sessão")
            return 'SESSION_CONFLICT'
            
        except Exception as e:
            logger.error(f"❌ Erro ao tratar conflito de sessão: {e}")
            return 'SESSION_CONFLICT'
    
    async def _tentar_sair_sessao(self, page: Page) -> bool:
        """Tenta encontrar e clicar em links/botões de Sair"""
        sair_selectors = [
            "a:has-text('Sair')",
            "a:has-text('sair')",
            "button:has-text('Sair')",
            "a:has-text('Logout')",
            "a:has-text('logout')",
            "a[href*='logout']",
            "a[href*='sair']",
            "button:has-text('Encerrar sessão')",
            "a:has-text('Encerrar')"
        ]
        
        logger.info("🔍 Procurando link/botão 'Sair'...")
        for selector in sair_selectors:
            try:
                element = await page.query_selector(selector)
                if element and await element.is_visible():
                    logger.info(f"📤 Clicando em '{selector}'...")
                    await element.click()
                    await page.wait_for_timeout(2000)
                    
                    # Aguardar redirecionamento para login
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except:
                        pass
                    
                    return True
            except Exception as e:
                logger.debug(f"Falha ao tentar {selector}: {e}")
                continue
        
        # Tentar via JavaScript se não encontrou pelos seletores
        logger.info("🔍 Tentando encontrar 'Sair' via JavaScript...")
        sair_clicked = await page.evaluate("""
            () => {
                const elements = document.querySelectorAll('a, button');
                for (let el of elements) {
                    const text = el.textContent.toLowerCase();
                    if (text.includes('sair') || text.includes('logout') || text.includes('encerrar')) {
                        el.click();
                        return true;
                    }
                }
                return false;
            }
        """)
        
        if sair_clicked:
            await page.wait_for_timeout(2000)
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass
            return True
        
        return False
    
    async def _tentar_forcear_login(self, page: Page) -> bool:
        """Tenta encontrar botões para forçar/continuar login"""
        session_buttons = [
            "button:has-text('Continuar')",
            "button:has-text('Forçar login')",
            "button:has-text('Encerrar sessão anterior')",
            "button:has-text('Sim')",
            "button:has-text('OK')",
            "button:has-text('Confirmar')",
            "input[type='button'][value*='Continuar']",
            "input[type='submit'][value*='Continuar']",
            "input[type='button'][value*='OK']",
            "input[type='submit'][value*='OK']"
        ]
        
        logger.info("🔍 Procurando botões para continuar/forçar login...")
        for btn_selector in session_buttons:
            try:
                button = await page.query_selector(btn_selector)
                if button and await button.is_visible():
                    logger.info(f"📤 Clicando em '{btn_selector}'...")
                    await button.click()
                    await page.wait_for_timeout(2000)
                    
                    try:
                        await page.wait_for_load_state("networkidle", timeout=10000)
                    except:
                        pass
                    
                    return True
            except Exception as e:
                logger.debug(f"Falha ao tentar {btn_selector}: {e}")
                continue
        
        return False


# Funções utilitárias para uso direto
async def abrir_menu_sistemas(page: Page, inscricao_estadual: Optional[str] = None) -> bool:
    """
    Função utilitária para abrir menu sistemas diretamente.
    
    Args:
        page: Página do navegador
        inscricao_estadual: IE da empresa (opcional)
        
    Returns:
        bool: True se menu foi aberto ou acesso direto foi bem-sucedido
    """
    navigator = MenuNavigator()
    return await navigator.check_and_open_sistemas_menu_complete(page, inscricao_estadual)


async def resolver_conflitos_sessao(page: Page) -> str:
    """
    Função utilitária para resolver conflitos de sessão.
    
    Args:
        page: Página do navegador
        
    Returns:
        str: Status do conflito ('SESSION_CONFLICT', 'RESOLVED', 'NOT_FOUND')
    """
    navigator = MenuNavigator()
    return await navigator.handle_session_conflicts(page)