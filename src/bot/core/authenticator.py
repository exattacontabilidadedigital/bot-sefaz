"""
Módulo de autenticação para o bot SEFAZ.

Este módulo contém as funcionalidades relacionadas à autenticação
no sistema SEFAZ.
"""

import logging
import random
from typing import Tuple
from playwright.async_api import Page

from src.bot.utils.selectors import SEFAZSelectors
from src.bot.utils.human_behavior import HumanBehavior
from src.bot.exceptions.base import (
    ValidationException,
    LoginFailedException,
    ElementNotFoundException,
    PageLoadException,
    NavigationException,
    TimeoutException
)
from src.bot.utils.validators import SEFAZValidator
from src.bot.utils.constants import (
    TIMEOUT_NAVIGATION,
    TIMEOUT_NETWORK_IDLE,
    DEBUG_FILE_POST_LOGIN
)

logger = logging.getLogger(__name__)


class SEFAZAuthenticator:
    """Classe responsável pela autenticação no sistema SEFAZ"""
    
    def __init__(self, timeout: int = 60000):  # Aumentado para 60s
        self.timeout = timeout
        self.selectors = SEFAZSelectors()
    
    async def perform_login(self, page: Page, usuario: str, senha: str, sefaz_url: str) -> bool:
        """
        Realiza o login no sistema SEFAZ com comportamento humano
        
        Args:
            page: Página do Playwright
            usuario: CPF do usuário (com ou sem formatação)
            senha: Senha do usuário
            sefaz_url: URL do sistema SEFAZ
            
        Returns:
            bool: True se login foi bem-sucedido
            
        Raises:
            ValidationException: Se credenciais inválidas
            LoginFailedException: Se login falhar
        """
        # Validar credenciais antes de tentar login
        is_valid, errors = SEFAZValidator.validate_all(usuario, senha)
        if not is_valid:
            error_msg = "Credenciais inválidas:\\n" + "\\n".join(errors)
            logger.error(error_msg)
            raise ValidationException(error_msg)
        
        try:
            # Limpar CPF (remover formatação)
            usuario_limpo = SEFAZValidator.limpar_cpf(usuario)
            
            logger.info("=" * 80)
            logger.info("🔐 BOT - AUTENTICAÇÃO - CREDENCIAIS VALIDADAS")
            logger.info("=" * 80)
            logger.debug(f"   - Usuario original: '{usuario}'")
            logger.debug(f"   - Usuario limpo: '{usuario_limpo}'")
            logger.debug(f"   - Senha: {'*' * len(senha)}")
            logger.info("=" * 80)
            
            # Não configurar timeout da página aqui - será gerenciado individualmente
            
            # Navegar para a página
            await self._navigate_to_login_page(page, sefaz_url)
            
            # Simular leitura da página
            await self._simulate_page_reading(page)
            
            # Preencher formulário de login
            await self._fill_login_form(page, usuario_limpo, senha)
            
            # Submeter formulário
            await self._submit_login_form(page)
            
            # Aguardar e validar login
            await self._wait_and_validate_login(page)
            
            # Timeout será gerenciado individualmente por operação
            
            logger.info("✅ Login realizado com sucesso")
            return True
            
        except (ValidationException, LoginFailedException, ElementNotFoundException, 
                PageLoadException, NavigationException):
            # Re-lançar exceções já tratadas
            raise
        except TimeoutError as e:
            logger.error(f"❌ Timeout durante login: {e}")
            raise LoginFailedException(f"Timeout durante login: {e}") from e
        except Exception as e:
            logger.error(f"❌ Erro inesperado no login: {e}")
            raise LoginFailedException(f"Falha inesperada no login: {e}") from e
    
    async def _navigate_to_login_page(self, page: Page, sefaz_url: str) -> None:
        """Navega para a página de login com retry automático e comportamento humano"""
        max_retries = 3
        retry_delay = 10  # 10 segundos entre tentativas
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🌐 Tentativa {attempt + 1}/{max_retries}: Navegando para página de login...")
                
                # Simular delay humano antes da navegação
                if attempt > 0:
                    import random
                    human_delay = random.uniform(2.0, 5.0)
                    logger.info(f"😴 Aguardando {human_delay:.1f}s (comportamento humano)...")
                    import asyncio
                    await asyncio.sleep(human_delay)
                
                # Navegar com timeout estendido
                await page.goto(sefaz_url, wait_until="domcontentloaded", timeout=120000)
                
                # Simular leitura humana da página
                import random
                reading_time = random.uniform(1.5, 3.0)
                logger.debug(f"👁️ Simulando leitura da página ({reading_time:.1f}s)...")
                import asyncio
                await asyncio.sleep(reading_time)
                
                # Aguardar carregamento completo com timeout estendido
                await page.wait_for_load_state("networkidle", timeout=60000)
                
                logger.info("✅ Página de login carregada com sucesso")
                return
                
            except Exception as e:
                logger.warning(f"⚠️ Tentativa {attempt + 1} falhou: {e}")
                
                if attempt == max_retries - 1:
                    # Última tentativa - lançar exceção
                    if "Timeout" in str(e):
                        raise NavigationException(
                            f"Timeout ao navegar para página de login após {max_retries} tentativas. "
                            f"Possível instabilidade do servidor SEFAZ: {e}"
                        ) from e
                    else:
                        raise NavigationException(f"Erro ao navegar para página de login: {e}") from e
                else:
                    # Aguardar antes da próxima tentativa com variação humana
                    import random
                    wait_time = retry_delay + random.uniform(-2, 3)  # Variação humana
                    logger.info(f"🕑 Aguardando {wait_time:.1f} segundos antes da próxima tentativa...")
                    import asyncio
                    await asyncio.sleep(wait_time)
    
    async def _simulate_page_reading(self, page: Page) -> None:
        """Simula comportamento humano de leitura da página"""
        logger.debug("👁️ Simulando leitura da página...")
        await HumanBehavior.simulate_reading_pause(page, 2, 4)
        await HumanBehavior.simulate_page_scanning(page, random.randint(2, 4))
    
    async def _fill_login_form(self, page: Page, usuario: str, senha: str) -> None:
        """Preenche os campos do formulário de login"""
        login_selectors = self.selectors.get_login_selectors()
        
        # Campo de usuário
        logger.debug("👤 Preenchendo campo de usuário...")
        usuario_field = await page.query_selector(login_selectors['username_field'])
        if not usuario_field:
            raise ElementNotFoundException("Campo de usuário não encontrado")
        
        await self._focus_and_move_to_field(page, usuario_field)
        await HumanBehavior.human_type_text(page, usuario_field, usuario)
        
        # Pausa entre campos
        logger.debug("⏸️ Pausa entre campos...")
        await page.wait_for_timeout(HumanBehavior.random_delay(1000, 2500))
        
        # Campo de senha
        logger.debug("🔑 Preenchendo campo de senha...")
        senha_field = await page.query_selector(login_selectors['password_field'])
        if not senha_field:
            raise ElementNotFoundException("Campo de senha não encontrado")
        
        await self._focus_and_move_to_field(page, senha_field)
        await HumanBehavior.human_type_text(page, senha_field, senha)
        
        # Verificar se senha foi digitada corretamente
        valor_digitado = await senha_field.input_value()
        if valor_digitado != senha:
            logger.warning("⚠️ Senha digitada difere da senha fornecida")
    
    async def _focus_and_move_to_field(self, page: Page, field_element) -> None:
        """Simula movimento natural do mouse até um campo"""
        box = await field_element.bounding_box()
        if box:
            # Mover para próximo do campo
            await page.mouse.move(
                box['x'] - random.randint(50, 150),
                box['y'] + random.randint(-30, 30)
            )
            await page.wait_for_timeout(HumanBehavior.random_delay(400, 900))
            
            # Mover para o campo
            await page.mouse.move(
                box['x'] + box['width']/2 + random.randint(-20, 20),
                box['y'] + box['height']/2 + random.randint(-5, 5)
            )
            await page.wait_for_timeout(HumanBehavior.random_delay(200, 500))
    
    async def _submit_login_form(self, page: Page) -> None:
        """Submete o formulário de login"""
        login_selectors = self.selectors.get_login_selectors()
        
        # Pausa antes de clicar
        logger.debug("🎯 Preparando para clicar no botão de login...")
        await page.wait_for_timeout(HumanBehavior.random_delay(1500, 3000))
        
        # Localizar e clicar no botão de login
        login_button = await page.query_selector(login_selectors['submit_button'])
        if not login_button:
            raise ElementNotFoundException("Botão de login não encontrado")
        
        await self._hover_and_click_button(page, login_button)
        logger.debug("🖱️ Botão de login clicado")
    
    async def _hover_and_click_button(self, page: Page, button_element) -> None:
        """Simula hover e clique em um botão"""
        box = await button_element.bounding_box()
        if box:
            # Mover mouse até próximo do botão
            await page.mouse.move(
                box['x'] - random.randint(100, 200),
                box['y'] + random.randint(-50, 50)
            )
            await page.wait_for_timeout(HumanBehavior.random_delay(400, 800))
            
            # Mover para o botão
            await page.mouse.move(
                box['x'] + box['width']/2 + random.randint(-30, 30),
                box['y'] + box['height']/2 + random.randint(-10, 10)
            )
            await page.wait_for_timeout(HumanBehavior.random_delay(300, 600))
        
        await HumanBehavior.human_click(page, button_element)
    
    async def _wait_and_validate_login(self, page: Page) -> None:
        """Aguarda carregamento e valida se login foi bem-sucedido"""
        logger.info("⏳ Aguardando carregamento após login...")
        
        # Aguardar carregamentos
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_NAVIGATION)
            logger.debug("  ✅ DOM carregado")
        except TimeoutError as e:
            logger.debug(f"  ⚠️ Timeout no DOM: {e}")
        
        try:
            await page.wait_for_load_state("networkidle", timeout=TIMEOUT_NETWORK_IDLE)
            logger.debug("  ✅ Network idle")
        except TimeoutError as e:
            logger.debug(f"  ⚠️ Timeout no network idle: {e}")
        
        # Aguardar JavaScript executar
        logger.debug("⏳ Aguardando JavaScript executar...")
        await page.wait_for_timeout(HumanBehavior.random_delay(3000, 5000))
        
        # Validar login
        await self._validate_login_success(page)
    
    async def _validate_login_success(self, page: Page) -> None:
        """Valida se o login foi bem-sucedido"""
        try:
            logger.debug(f"📍 URL após login: {page.url}")
            logger.debug(f"📄 Título: {await page.title()}")
            
            content = await page.content()
            logger.debug(f"📊 Tamanho do HTML: {len(content)} bytes")
            
            # Verificar se login foi bem-sucedido (HTML > 1000 bytes)
            if len(content) < 1000:
                raise LoginFailedException(f"Página muito pequena após login ({len(content)} bytes)")
            
            # Salvar arquivos de debug
            await self._save_debug_files(page, content)
            
        except LoginFailedException:
            raise
        except Exception as e:
            logger.warning(f"⚠️ Erro ao validar login: {e}")
    
    async def _save_debug_files(self, page: Page, content: str) -> None:
        """Salva arquivos de debug do login"""
        try:
            with open(DEBUG_FILE_POST_LOGIN, "w", encoding="utf-8") as f:
                f.write(content)
            
            await page.screenshot(path=DEBUG_FILE_POST_LOGIN.replace('.html', '.png'), full_page=True)
            logger.debug(f"💾 Debug files salvos: {DEBUG_FILE_POST_LOGIN}")
        except PermissionError as e:
            logger.warning(f"⚠️ Sem permissão para salvar debug: {e}")
        except OSError as e:
            logger.warning(f"⚠️ Erro de I/O ao salvar debug: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Erro inesperado ao salvar debug: {e}")
    
    async def perform_logout(self, page: Page) -> bool:
        """
        Realiza logout do sistema SEFAZ
        
        Args:
            page: Página do Playwright
            
        Returns:
            bool: True se logout foi bem-sucedido
        """
        try:
            logger.info("🚪 Iniciando logout do sistema...")
            
            # Comportamento humano antes do logout
            await page.wait_for_timeout(HumanBehavior.random_delay(1000, 2000))
            
            # Tentar diferentes seletores de logout
            logout_selectors = self.selectors.get_logout_selectors()
            
            logout_success = False
            for selector in logout_selectors:
                try:
                    logout_element = await page.query_selector(selector)
                    if logout_element and await logout_element.is_visible():
                        # Se for imagem de exit, clicar no link pai
                        if "exit.png" in selector:
                            logout_link = await logout_element.evaluate_handle("img => img.closest('a')")
                            if logout_link:
                                await HumanBehavior.human_click(page, logout_link)
                            else:
                                await HumanBehavior.human_click(page, logout_element)
                        else:
                            await HumanBehavior.human_click(page, logout_element)
                        
                        logger.info(f"✅ Logout executado via: {selector}")
                        logout_success = True
                        break
                except Exception as e:
                    logger.debug(f"⚠️ Erro com seletor {selector}: {e}")
                    continue
            
            if logout_success:
                await self._wait_for_logout_completion(page)
                return True
            else:
                logger.warning("⚠️ Botão de logout não encontrado")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro durante logout: {e}")
            return False
    
    async def _wait_for_logout_completion(self, page: Page) -> None:
        """Aguarda conclusão do logout"""
        try:
            await page.wait_for_load_state("networkidle", timeout=10000)
            await page.wait_for_timeout(HumanBehavior.random_delay(1000, 2000))
            
            current_url = page.url
            if "login" in current_url.lower() or "logoff" in current_url.lower():
                logger.info("✅ Logout realizado com sucesso - redirecionado para login")
            else:
                logger.info(f"✅ Logout executado - URL: {current_url}")
        except Exception:
            logger.info("✅ Logout executado (timeout no redirecionamento é normal)")