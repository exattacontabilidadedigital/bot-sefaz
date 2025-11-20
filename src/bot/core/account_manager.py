"""
AccountManager - Módulo especializado para gerenciamento de conta corrente e TVIs.

Este módulo extrai e especializa as lógicas de:
- Navegação para conta corrente
- Preenchimento de inscrição estadual
- Verificação de TVIs
- Extração de dados de TVIs

Remove responsabilidades do bot principal para melhor testabilidade e manutenção.
"""

import logging
from typing import Optional, Dict, Any
from playwright.async_api import Page

from src.bot.utils.human_behavior import HumanBehavior
from src.bot.exceptions import (
    NavigationException,
    ElementNotFoundException,
    TimeoutException,
    ExtractionException
)

logger = logging.getLogger(__name__)


class AccountManager:
    """
    Gerenciador especializado para conta corrente e TVIs no sistema SEFAZ.
    
    Responsabilidades:
    - Navegar para área de conta corrente
    - Preencher inscrição estadual quando necessário
    - Verificar e extrair dados de TVIs
    - Gerenciar formulários de empresa
    """
    
    def __init__(self):
        self.behavior = HumanBehavior()
    
    def random_delay(self, min_ms: int, max_ms: int) -> int:
        """Gera delay aleatório para simular comportamento humano"""
        return self.behavior.random_delay(min_ms, max_ms)
    
    async def human_click(self, page: Page, element) -> None:
        """Clique com comportamento humano"""
        await self.behavior.human_click(page, element)
    
    async def access_conta_corrente_complete(self, page: Page, inscricao_estadual: Optional[str] = None) -> bool:
        \"\"\"
        Acessa a área de conta corrente fiscal completa.
        
        Este método combina a navegação do menu com o acesso à área específica,
        incluindo preenchimento de inscrição estadual quando necessário.
        
        Args:
            page: Página do navegador
            inscricao_estadual: IE da empresa (necessária se CPF tem múltiplas IEs)
            
        Returns:
            bool: True se conseguiu acessar conta corrente
            
        Raises:
            NavigationException: Se não conseguir acessar
        \"\"\"
        try:
            logger.info("=" * 60)
            logger.info("🏦 AccountManager - ACESSANDO CONTA CORRENTE")
            logger.info("=" * 60)
            
            # Passo 1: Navegar através do menu para conta corrente
            if not await self._navegar_menu_conta_corrente(page, inscricao_estadual):
                raise NavigationException("Falha na navegação do menu para conta corrente")
            
            # Passo 2: Preencher inscrição estadual se necessário
            ie_preenchida = await self.preencher_inscricao_estadual(page, inscricao_estadual)
            
            # Passo 3: Clicar em Continuar para acessar dados
            if not await self._clicar_continuar(page):
                logger.warning("⚠️ Problema ao clicar em Continuar, mas pode estar na página correta")
            
            logger.info("✅ Acesso à conta corrente concluído com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao acessar conta corrente: {e}")
            raise NavigationException(f"Erro no acesso à conta corrente: {e}") from e
    
    async def _navegar_menu_conta_corrente(self, page: Page, inscricao_estadual: Optional[str] = None) -> bool:
        \"\"\"Navega através do menu completo para acessar conta corrente\"\"\"
        try:
            logger.info("📍 Navegando para 'Todas as Áreas de Negócio'...")
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Verificar se menu dropdown está aberto
            menu_aberto = await page.evaluate(\"\"\"
                () => {
                    const dropdown = document.querySelector('.dropdown.open');
                    return dropdown !== null;
                }
            \"\"\")
            
            if not menu_aberto:
                logger.warning("⚠️ Menu não está aberto - pode precisar abrir menu Sistemas primeiro")
                # Aqui seria interessante integrar com MenuNavigator
                # Por ora, continuamos e tentamos encontrar os elementos
            
            # Clicar em "Todas as Áreas de Negócio"
            if not await self._clicar_todas_areas_negocio(page):
                return False
            
            # Aguardar carregamento
            await page.wait_for_timeout(self.random_delay(2000, 3000))
            
            # Expandir "Conta Fiscal"
            if not await self._expandir_conta_fiscal(page):
                return False
            
            # Clicar em "Consultar Conta-Corrente Fiscal"
            if not await self._clicar_consultar_conta_corrente(page):
                return False
            
            logger.info("✅ Navegação do menu concluída")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na navegação do menu: {e}")
            return False
    
    async def _clicar_todas_areas_negocio(self, page: Page) -> bool:
        \"\"\"Clica no botão 'Todas as Áreas de Negócio'\"\"\"
        try:
            # Procurar o botão
            todas_areas_button = await page.query_selector("a:has-text('Todas as Áreas de Negócio')")
            if not todas_areas_button:
                todas_areas_button = await page.query_selector("a[onclick*=\\\"listMenu(document.menuForm,this,'all')\\\"]\")
            
            if not todas_areas_button:
                logger.error("❌ Botão 'Todas as Áreas de Negócio' não encontrado")
                return False
            
            # Verificar visibilidade
            is_visible = await todas_areas_button.is_visible()
            if not is_visible:
                logger.warning("⚠️ Forçando visibilidade do botão...")
                await page.evaluate(\"\"\"
                    () => {
                        const link = document.querySelector("a[onclick*=\\"listMenu(document.menuForm,this,'all')\\"]");
                        if (link) {
                            link.style.display = 'block';
                            link.style.visibility = 'visible';
                        }
                    }
                \"\"\")
            
            # Clicar no botão
            await self.human_click(page, todas_areas_button)
            logger.info("✅ Clicado em 'Todas as Áreas de Negócio'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao clicar em 'Todas as Áreas de Negócio': {e}")
            return False
    
    async def _expandir_conta_fiscal(self, page: Page) -> bool:
        \"\"\"Expande o item 'Conta Fiscal' no menu\"\"\"
        try:
            logger.info("📍 Expandindo 'Conta Fiscal'...")
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Procurar e clicar em "Conta Fiscal"
            conta_fiscal_selectors = [
                "a:has-text('Conta Fiscal')",
                "a[title='Conta Fiscal']",
                "a.jstree-anchor:has-text('Conta Fiscal')"
            ]
            
            for selector in conta_fiscal_selectors:
                try:
                    conta_fiscal_link = await page.query_selector(selector)
                    if conta_fiscal_link and await conta_fiscal_link.is_visible():
                        await self.human_click(page, conta_fiscal_link)
                        logger.info(f"✅ 'Conta Fiscal' expandida via {selector}")
                        return True
                except Exception as e:
                    logger.debug(f"Falha no seletor {selector}: {e}")
                    continue
            
            logger.error("❌ Não foi possível expandir 'Conta Fiscal'")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao expandir 'Conta Fiscal': {e}")
            return False
    
    async def _clicar_consultar_conta_corrente(self, page: Page) -> bool:
        \"\"\"Clica em 'Consultar Conta-Corrente Fiscal'\"\"\"
        try:
            logger.info("📍 Clicando em 'Consultar Conta-Corrente Fiscal'...")
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Procurar o link
            consultar_selectors = [
                "a:has-text('Consultar Conta-Corrente Fiscal')",
                "a[title*='Consultar Conta-Corrente Fiscal']",
                "a.jstree-anchor:has-text('Consultar Conta-Corrente Fiscal')"
            ]
            
            for selector in consultar_selectors:
                try:
                    consultar_link = await page.query_selector(selector)
                    if consultar_link and await consultar_link.is_visible():
                        await self.human_click(page, consultar_link)
                        logger.info(f"✅ 'Consultar Conta-Corrente Fiscal' clicado via {selector}")
                        
                        # Aguardar carregamento da página
                        await page.wait_for_load_state("networkidle", timeout=30000)
                        return True
                except Exception as e:
                    logger.debug(f"Falha no seletor {selector}: {e}")
                    continue
            
            logger.error("❌ Não foi possível clicar em 'Consultar Conta-Corrente Fiscal'")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao clicar em 'Consultar Conta-Corrente Fiscal': {e}")
            return False
    
    async def preencher_inscricao_estadual(self, page: Page, inscricao_estadual: Optional[str] = None) -> bool:
        \"\"\"
        Preenche o campo de Inscrição Estadual e clica no botão confirmar.
        
        Args:
            page: Página do navegador
            inscricao_estadual: Número da IE (opcional)
            
        Returns:
            bool: True se IE foi preenchida e confirmada, ou False se campo não existe
        \"\"\"
        try:
            logger.info("🔍 Verificando necessidade de preenchimento de IE...")
            
            # Salvar debug se necessário
            await page.screenshot(path="debug_antes_ie.png")
            
            # Verificar se campo existe
            ie_input = await page.query_selector("input[name='inscricaoEstadual']")
            if not ie_input:
                logger.info("✅ Campo de IE não encontrado - CPF possui apenas uma IE")
                return True  # Sucesso, não precisa preencher
            
            # Verificar visibilidade
            is_visible = await ie_input.is_visible()
            if not is_visible:
                logger.info("⚠️ Campo de IE existe mas não está visível")
                return True
            
            logger.info("⚠️ Campo de IE encontrado - CPF possui múltiplas IEs")
            
            # Validar se IE foi fornecida
            if not inscricao_estadual:
                logger.error("❌ Campo de IE existe mas nenhuma IE foi fornecida!")
                await page.screenshot(path="debug_ie_campo_vazio.png")
                return False
            
            # Limpar a IE (apenas números)
            ie_limpa = ''.join(filter(str.isdigit, str(inscricao_estadual)))
            logger.info(f"📝 IE fornecida: '{inscricao_estadual}' → IE limpa: '{ie_limpa}'")
            
            # Preencher campo
            logger.info("🖱️ Preenchendo campo de IE...")
            await ie_input.click()
            await page.wait_for_timeout(1000)
            
            await ie_input.fill("")
            await page.wait_for_timeout(500)
            
            await ie_input.type(ie_limpa, delay=self.random_delay(50, 150))
            logger.info(f"✅ IE '{ie_limpa}' digitada no campo")
            
            await page.wait_for_timeout(self.random_delay(500, 1000))
            
            # Procurar botão confirmar
            if not await self._clicar_confirmar_ie(page):
                logger.error("❌ Não foi possível confirmar IE")
                return False
            
            # Aguardar processamento
            logger.info("⏳ Aguardando carregamento dos dados da IE...")
            await page.wait_for_timeout(self.random_delay(2000, 3000))
            
            # Verificar se Razão Social foi preenchida (sucesso)
            razao_social = await page.query_selector("input[name='razaoSocial']")
            if razao_social:
                valor = await razao_social.get_attribute("value")
                if valor and valor.strip():
                    logger.info(f"✅ Razão Social preenchida: '{valor[:50]}...'")
                    return True
            
            logger.warning("⚠️ Razão Social não foi preenchida após confirmar IE")
            return True  # Continuar mesmo assim
            
        except Exception as e:
            logger.error(f"❌ Erro ao preencher IE: {e}")
            return False
    
    async def _clicar_confirmar_ie(self, page: Page) -> bool:
        \"\"\"Clica no botão confirmar da IE\"\"\"
        try:
            logger.info("🔍 Procurando botão Confirmar (✓)...")
            
            # Procurar pelo link de confirmar
            confirmar_link = await page.query_selector("a[href*='recuperarDadosInscricaoEstadual']")
            if not confirmar_link:
                # Tentar pelo img
                confirmar_img = await page.query_selector("img[src*='ic_confirmar.gif']")
                if confirmar_img:
                    confirmar_link = await confirmar_img.evaluate_handle("element => element.closest('a')")
            
            if confirmar_link:
                logger.info("🖱️ Clicando no botão Confirmar (✓)...")
                await self.human_click(page, confirmar_link)
                logger.info("✅ Botão Confirmar clicado")
                return True
            
            logger.warning("⚠️ Botão Confirmar não encontrado")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao clicar em confirmar IE: {e}")
            return False
    
    async def _clicar_continuar(self, page: Page) -> bool:
        \"\"\"Clica no botão Continuar para acessar os dados\"\"\"
        try:
            logger.info("🖱️ Procurando botão 'Continuar'...")
            
            # Aguardar um pouco antes de procurar
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Procurar botão Continuar
            continuar_selectors = [
                "button:has-text('Continuar')",
                "input[type='button'][value='Continuar']",
                "input[type='submit'][value='Continuar']",
                "a:has-text('Continuar')"
            ]
            
            for selector in continuar_selectors:
                try:
                    continuar_btn = await page.query_selector(selector)
                    if continuar_btn and await continuar_btn.is_visible():
                        logger.info(f"🖱️ Clicando em 'Continuar' via {selector}...")
                        await self.human_click(page, continuar_btn)
                        
                        # Aguardar carregamento
                        await page.wait_for_load_state("networkidle", timeout=30000)
                        logger.info("✅ Clicado em 'Continuar' com sucesso")
                        return True
                        
                except Exception as e:
                    logger.debug(f"Falha no seletor {selector}: {e}")
                    continue
            
            logger.warning("⚠️ Botão 'Continuar' não encontrado")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao clicar no botão Continuar: {e}")
            return False
    
    async def verify_tvis_complete(self, page: Page) -> Dict[str, Any]:
        \"\"\"
        Verifica TVIs de forma completa - clica no botão e extrai dados.
        
        Args:
            page: Página do navegador
            
        Returns:
            Dict com informações das TVIs: {
                'tem_tvi': 'SIM'|'NÃO'|'ERRO',
                'valor_tvi': float,
                'detalhes': str
            }
        \"\"\"
        try:
            logger.info("📊 Verificando TVIs...")
            
            # Aguardar estabilização
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Procurar botão TVIs
            tvi_button = await page.query_selector("button:has-text('TVIs')")
            if not tvi_button:
                logger.warning("⚠️ Botão TVIs não encontrado")
                return {
                    'tem_tvi': 'ERRO',
                    'valor_tvi': 0.0,
                    'detalhes': 'Botão TVIs não encontrado'
                }
            
            # Clicar no botão
            await self.human_click(page, tvi_button)
            logger.info("✅ Clicado no botão TVIs")
            
            # Aguardar carregamento
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_timeout(self.random_delay(2000, 3000))
            
            # Extrair dados das TVIs
            tvi_data = await self._extract_tvi_data(page)
            
            # Voltar para página anterior
            await self._go_back_safely(page)
            
            return tvi_data
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar TVIs: {e}")
            try:
                await self._go_back_safely(page)
            except:
                pass
                
            return {
                'tem_tvi': 'ERRO',
                'valor_tvi': 0.0,
                'detalhes': f'Erro: {e}'
            }
    
    async def _extract_tvi_data(self, page: Page) -> Dict[str, Any]:
        \"\"\"Extrai dados específicos da página de TVIs\"\"\"
        try:
            # Aguardar e capturar screenshot para debug
            await page.wait_for_timeout(self.random_delay(2000, 3000))
            await page.screenshot(path="debug_tvi_page.png")
            
            # Obter conteúdo da página
            page_content = await page.content()
            
            # Verificar mensagens de ausência de dados
            no_data_messages = [
                "Nenhum resultado foi encontrado",
                "Nenhum registro encontrado",
                "Sem dados disponíveis",
                "Não há TVIs",
                "Nenhuma TVI cadastrada"
            ]
            
            for message in no_data_messages:
                if message in page_content:
                    logger.info(f"📊 TVI: {message}")
                    return {
                        'tem_tvi': 'NÃO',
                        'valor_tvi': 0.0,
                        'detalhes': f'Sem TVIs: {message}'
                    }
            
            # Verificar tabela de TVIs
            tvi_rows = await page.query_selector_all("table.table.table-striped tbody tr")
            
            if not tvi_rows or len(tvi_rows) == 0:
                logger.info("📊 TVI: Nenhuma linha encontrada na tabela")
                return {
                    'tem_tvi': 'NÃO',
                    'valor_tvi': 0.0,
                    'detalhes': 'Tabela vazia'
                }
            
            logger.info(f"📊 TVI: Encontradas {len(tvi_rows)} linha(s) na tabela")
            
            valor_total_tvi = 0.0
            tvis_com_debito = 0
            
            for idx, row in enumerate(tvi_rows, 1):
                try:
                    cells = await row.query_selector_all("td")
                    
                    if len(cells) >= 6:
                        # Coluna 5: saldo devedor
                        saldo_cell = cells[4]
                        saldo_text = await saldo_cell.text_content()
                        saldo_text = saldo_text.strip() if saldo_text else "0,00"
                        
                        # Coluna 6: situação
                        situacao_cell = cells[5]
                        situacao_text = await situacao_cell.text_content()
                        situacao_text = situacao_text.strip().upper() if situacao_text else ""
                        
                        # Converter saldo para float
                        try:
                            # Remover "R$", espaços e converter vírgula para ponto
                            saldo_limpo = saldo_text.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
                            if saldo_limpo:
                                saldo_valor = float(saldo_limpo)
                            else:
                                saldo_valor = 0.0
                        except:
                            saldo_valor = 0.0
                        
                        logger.info(f"📊 TVI {idx}: Saldo='{saldo_text}' ({saldo_valor}), Situação='{situacao_text}'")
                        
                        # Verificar se tem débito e está ativa
                        if saldo_valor > 0 and situacao_text in ["ATIVO", "ATIVA", "PENDENTE"]:
                            valor_total_tvi += saldo_valor
                            tvis_com_debito += 1
                            
                except Exception as e:
                    logger.warning(f"⚠️ Erro ao processar linha {idx} da TVI: {e}")
                    continue
            
            # Resultado final
            if valor_total_tvi > 0:
                return {
                    'tem_tvi': 'SIM',
                    'valor_tvi': valor_total_tvi,
                    'detalhes': f'{tvis_com_debito} TVI(s) com débito total de R$ {valor_total_tvi:.2f}'
                }
            else:
                return {
                    'tem_tvi': 'NÃO',
                    'valor_tvi': 0.0,
                    'detalhes': f'{len(tvi_rows)} TVI(s) sem débito pendente'
                }
                
        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados de TVI: {e}")
            return {
                'tem_tvi': 'ERRO',
                'valor_tvi': 0.0,
                'detalhes': f'Erro na extração: {e}'
            }
    
    async def _go_back_safely(self, page: Page) -> None:
        \"\"\"Volta para página anterior de forma segura\"\"\"
        try:
            # Tentar botão Voltar primeiro
            voltar_selectors = [
                "button:has-text('Voltar')",
                "input[type='button'][value='Voltar']",
                "a:has-text('Voltar')",
                "button:has-text('← Voltar')"
            ]
            
            for selector in voltar_selectors:
                try:
                    voltar_btn = await page.query_selector(selector)
                    if voltar_btn and await voltar_btn.is_visible():
                        await self.human_click(page, voltar_btn)
                        await page.wait_for_timeout(self.random_delay(1000, 2000))
                        logger.info(f"✅ Voltou via botão: {selector}")
                        return
                except Exception as e:
                    logger.debug(f"Falha no botão voltar {selector}: {e}")
                    continue
            
            # Fallback: usar navegação do browser
            logger.info("🔄 Usando navegação do browser para voltar")
            await page.go_back()
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao voltar: {e}")


# Funções utilitárias para uso direto
async def acessar_conta_corrente(page: Page, inscricao_estadual: Optional[str] = None) -> bool:
    \"\"\"
    Função utilitária para acessar conta corrente diretamente.
    
    Args:
        page: Página do navegador
        inscricao_estadual: IE da empresa (opcional)
        
    Returns:
        bool: True se acesso foi bem-sucedido
    \"\"\"
    manager = AccountManager()
    return await manager.access_conta_corrente_complete(page, inscricao_estadual)


async def verificar_tvis(page: Page) -> Dict[str, Any]:
    \"\"\"
    Função utilitária para verificar TVIs diretamente.
    
    Args:
        page: Página do navegador
        
    Returns:
        Dict com dados das TVIs
    \"\"\"
    manager = AccountManager()
    return await manager.verify_tvis_complete(page)