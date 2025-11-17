"""
Módulo de extração de dados para o bot SEFAZ.

Este módulo contém as funcionalidades relacionadas à extração de dados
das páginas do sistema SEFAZ.
"""

import re
import logging
from typing import Dict, Any, Optional
from playwright.async_api import Page

from src.bot.utils.selectors import SEFAZSelectors
from src.bot.utils.human_behavior import HumanBehavior
from src.bot.exceptions.base import (
    ExtractionException,
    TimeoutException
)

logger = logging.getLogger(__name__)


class DataExtractor:
    """Classe responsável pela extração de dados do sistema SEFAZ"""
    
    def __init__(self):
        self.selectors = SEFAZSelectors()
    
    async def extract_company_data(self, page: Page) -> Dict[str, Any]:
        """
        Extrai os dados da página conta corrente após login
        
        Args:
            page: Página do Playwright
            
        Returns:
            Dict: Dados extraídos da empresa
        """
        logger.info("="*80)
        logger.info("🔍 INICIANDO EXTRAÇÃO DE DADOS")
        logger.info("="*80)
        
        dados = {}
        
        try:
            # Aguardar carregamento completo da página
            await self._wait_for_page_load(page)
            
            # Verificar se estamos na página correta
            if not await self._validate_correct_page(page):
                return dados
            
            # Extrair dados específicos
            await self._extract_basic_company_info(page, dados)
            await self._extract_pending_status_flags(page, dados)
            
            # Verificar TVIs e dívidas
            dados['tem_tvi'] = await self._check_tvis(page)
            dados['valor_debitos'] = await self._check_pending_debts(page)
            
            # Campos não utilizados no momento - manter por compatibilidade
            dados['cnpj'] = None
            dados['cpf_socio'] = None
            dados['chave_acesso'] = None
            
            logger.info(f"📊 Dados extraídos: {dados}")
            return dados
            
        except Exception as e:
            logger.error(f"❌ Erro inesperado na extração: {e}")
            raise ExtractionException(f"Falha na extração de dados: {e}") from e
    
    async def _wait_for_page_load(self, page: Page) -> None:
        """Aguarda carregamento completo da página"""
        logger.info("⏳ Aguardando carregamento completo da página...")
        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
        except TimeoutError as e:
            raise TimeoutException(f"Timeout aguardando carregamento da página: {e}") from e
    
    async def _validate_correct_page(self, page: Page) -> bool:
        """Valida se estamos na página correta"""
        url = page.url
        title = await page.title()
        logger.info(f"📍 URL atual na extração: {url}")
        logger.info(f"📄 Título da página na extração: {title}")
        
        page_content = await page.content()
        logger.info(f"📏 Tamanho do HTML: {len(page_content)} bytes")
        
        if "Inscrição Estadual" not in page_content:
            logger.warning("⚠️ Não parece estar na página de Conta Corrente")
            return await self._handle_incorrect_page(page)
        else:
            logger.info("✅ Página de Conta Corrente detectada corretamente!")
            return True
    
    async def _handle_incorrect_page(self, page: Page) -> bool:
        """Tenta corrigir quando não está na página correta"""
        logger.warning("🔍 Verificando se há botão Continuar ainda...")
        
        continuar_btn = await page.query_selector("button:has-text('Continuar')")
        if continuar_btn:
            logger.info("❗ Encontrado botão Continuar, clicando novamente...")
            await continuar_btn.click()
            await page.wait_for_load_state('networkidle')
            
            page_content = await page.content()
            if "Inscrição Estadual" in page_content:
                logger.info("✅ Página correta carregada após segundo clique!")
                return True
        
        logger.error("❌ Ainda não está na página correta")
        await page.screenshot(path="debug_extracao_falha.png")
        with open("debug_extracao_falha.html", "w", encoding="utf-8") as f:
            f.write(await page.content())
        return False
    
    async def _extract_basic_company_info(self, page: Page, dados: Dict[str, Any]) -> None:
        """Extrai informações básicas da empresa"""
        data_selectors = self.selectors.get_data_extraction_selectors()
        
        # Inscrição Estadual
        await self._extract_field_with_fallbacks(
            page, dados, 'inscricao_estadual',
            self.selectors.get_all_ie_selectors()
        )
        
        # Razão Social
        await self._extract_field_with_fallbacks(
            page, dados, 'nome_empresa',
            self.selectors.get_all_razao_selectors()
        )
        
        # Situação Cadastral
        await self._extract_field_with_fallbacks(
            page, dados, 'status_ie',
            self.selectors.get_all_situacao_selectors()
        )
    
    async def _extract_field_with_fallbacks(
        self, 
        page: Page, 
        dados: Dict[str, Any], 
        field_name: str, 
        selectors: list
    ) -> None:
        """Extrai um campo usando múltiplos seletores como fallback"""
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text_content = await element.text_content()
                    dados[field_name] = text_content.strip() if text_content else None
                    if dados[field_name]:  # Se conseguiu extrair, para de tentar
                        break
            except Exception as e:
                logger.debug(f"Falha no seletor {selector} para {field_name}: {e}")
                continue
    
    async def _extract_pending_status_flags(self, page: Page, dados: Dict[str, Any]) -> None:
        """Extrai flags de status pendentes (checkboxes)"""
        try:
            data_selectors = self.selectors.get_data_extraction_selectors()
            
            # Dívida Pendente
            divida_checkbox = await page.query_selector(data_selectors['divida_pendente_checkbox'])
            dados['tem_divida_pendente'] = 'SIM' if divida_checkbox else 'NÃO'
            
            # Omisso de Declaração
            omisso_checkbox = await page.query_selector(data_selectors['omisso_declaracao_checkbox'])
            dados['omisso_declaracao'] = 'SIM' if omisso_checkbox else 'NÃO'
            
            # Inscrito em Cadastro Restritivo
            serasa_checkbox = await page.query_selector(data_selectors['inscrito_restritivo_checkbox'])
            dados['inscrito_restritivo'] = 'SIM' if serasa_checkbox else 'NÃO'
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar checkboxes: {e}")
            dados['tem_divida_pendente'] = 'NÃO VERIFICADO'
            dados['omisso_declaracao'] = 'NÃO VERIFICADO'
            dados['inscrito_restritivo'] = 'NÃO VERIFICADO'
    
    async def _check_tvis(self, page: Page) -> str:
        """Verifica TVIs clicando no botão e analisando a página"""
        try:
            await HumanBehavior.simulate_reading_pause(page, 1, 2)
            
            # Clicar no botão TVIs
            action_buttons = SEFAZSelectors.ACTION_BUTTONS
            tvi_button = await page.query_selector(action_buttons['tvis_button'])
            
            if tvi_button:
                await HumanBehavior.human_click(page, tvi_button)
                logger.info("Clicado no botão TVIs")
                
                # Aguardar carregamento
                await HumanBehavior.wait_for_page_stability(page)
                await page.wait_for_timeout(HumanBehavior.random_delay(2000, 3000))
                
                # Extrair dados de TVI
                tvi_data = await self._extract_tvi_data(page)
                
                # Voltar para página anterior
                await self._go_back_safely(page)
                
                return tvi_data
            else:
                logger.warning("Botão TVIs não encontrado")
                return "NÃO VERIFICADO"
                
        except Exception as e:
            logger.error(f"Erro ao verificar TVIs: {e}")
            try:
                await self._go_back_safely(page)
            except:
                pass
            return "ERRO"
    
    async def _extract_tvi_data(self, page: Page) -> str:
        """Extrai dados específicos da página de TVIs"""
        try:
            await page.wait_for_timeout(HumanBehavior.random_delay(2000, 3000))
            
            # Capturar screenshot para debug
            await page.screenshot(path="debug_tvi_page.png")
            logger.info("Screenshot da página de TVI salvo")
            
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
                    logger.info(f"TVI: Encontrada mensagem '{message}'")
                    return "0.0"
            
            # Verificar tabela com saldos devedores
            tvi_rows = await page.query_selector_all("table.table.table-striped tbody tr")
            
            if tvi_rows and len(tvi_rows) > 0:
                logger.info(f"TVI: Encontradas {len(tvi_rows)} linha(s) na tabela")
                
                for idx, row in enumerate(tvi_rows, 1):
                    try:
                        cells = await row.query_selector_all("td")
                        
                        if len(cells) >= 6:
                            # Coluna 5 (índice 4) contém o saldo devedor
                            saldo_cell = cells[4]
                            saldo_text = await saldo_cell.text_content()
                            saldo_text = saldo_text.strip() if saldo_text else "0,00"
                            
                            # Converter para float
                            valor_tvi = self._extract_monetary_value(saldo_text)
                            
                            if valor_tvi > 0:
                                logger.info(f"TVI: ❌ Encontrado saldo devedor: R$ {valor_tvi:.2f}")
                                return str(valor_tvi)
                            else:
                                logger.info("TVI: ✅ Saldo zero encontrado")
                    
                    except Exception as row_error:
                        logger.warning(f"Erro ao processar linha TVI {idx}: {row_error}")
                        continue
                
                return "0.0"  # Todas as linhas com saldo zero
            
            return "0.0"  # Nenhuma TVI encontrada
                
        except Exception as e:
            logger.error(f"Erro ao extrair dados de TVI: {e}")
            return "ERRO"
    
    async def _check_pending_debts(self, page: Page) -> float:
        """Verifica dívidas pendentes clicando no botão e analisando"""
        try:
            await HumanBehavior.simulate_reading_pause(page, 1, 2)
            
            # Clicar no botão Dívidas Pendentes
            action_buttons = SEFAZSelectors.ACTION_BUTTONS
            divida_button = await page.query_selector(action_buttons['dividas_pendentes_button'])
            
            if divida_button:
                await HumanBehavior.human_click(page, divida_button)
                logger.info("Clicado no botão Dívidas Pendentes")
                
                # Aguardar carregamento
                await HumanBehavior.wait_for_page_stability(page)
                await page.wait_for_timeout(HumanBehavior.random_delay(2000, 3000))
                
                # Extrair dados de dívidas
                divida_data = await self._extract_debt_data(page)
                
                # Voltar para página anterior
                await self._go_back_safely(page)
                
                return divida_data
            else:
                logger.warning("Botão Dívidas Pendentes não encontrado")
                return 0.0
                
        except Exception as e:
            logger.error(f"Erro ao verificar dívidas pendentes: {e}")
            try:
                await self._go_back_safely(page)
            except:
                pass
            return 0.0
    
    async def _extract_debt_data(self, page: Page) -> float:
        """Extrai dados específicos da página de Dívidas Pendentes"""
        try:
            await page.wait_for_timeout(HumanBehavior.random_delay(2000, 3000))
            
            # Capturar screenshot para debug
            await page.screenshot(path="debug_dividas_page.png")
            logger.info("Screenshot da página de Dívidas salvo")
            
            page_content = await page.content()
            
            # Verificar mensagens de ausência de dados
            no_data_messages = [
                "Nenhum resultado foi encontrado",
                "Nenhum registro encontrado",
                "Sem dados disponíveis",
                "Não há dívidas",
                "Sem débitos pendentes"
            ]
            
            for message in no_data_messages:
                if message in page_content:
                    logger.info(f"DÍVIDAS: Encontrada mensagem '{message}'")
                    return 0.0
            
            # Procurar valores monetários na página
            valores_encontrados = self._extract_all_monetary_values(page_content)
            
            if valores_encontrados:
                valor_total = max(valores_encontrados)
                logger.info(f"DÍVIDAS: Valor máximo encontrado: R$ {valor_total:.2f}")
                return valor_total
            
            return 0.0
                
        except Exception as e:
            logger.error(f"Erro ao extrair dados de dívida: {e}")
            return 0.0
    
    def _extract_monetary_value(self, text: str) -> float:
        """Extrai valor monetário de um texto com maior precisão"""
        try:
            if not text:
                return 0.0
            
            clean_text = text.strip()
            
            # Padrões para valores monetários brasileiros
            patterns = [
                r'R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})',  # R$ 1.234.567,89
                r'R?\$?\s*(\d{4,7},\d{2})(?!\d)',        # R$ 123456,78
                r'R?\$?\s*(\d{1,7}\.\d{2})(?!\d)',       # R$ 123456.78
                r'R?\$?\s*(\d{1,3}(?:\.\d{3})+)(?!\d|,)', # R$ 1.234.567
                r'R?\$?\s*(\d{5,})(?!\d)',               # R$ 1234567
                r'R?\$?\s*(\d{1,4})(?!\d)'               # R$ 123
            ]
            
            for pattern in patterns:
                match = re.search(pattern, clean_text)
                if match:
                    value_str = match.group(1)
                    
                    # Converter baseado no formato
                    if ',' in value_str and value_str.count(',') == 1:
                        # Formato brasileiro: 1.234,56
                        value_str = value_str.replace('.', '').replace(',', '.')
                    elif value_str.count('.') > 1:
                        # Múltiplos pontos = separadores de milhares: 1.234.567
                        value_str = value_str.replace('.', '')
                    
                    return float(value_str)
            
            return 0.0
            
        except (ValueError, AttributeError) as e:
            logger.debug(f"Erro ao extrair valor monetário de '{text}': {e}")
            return 0.0
    
    def _extract_all_monetary_values(self, content: str) -> list:
        """Extrai todos os valores monetários encontrados no conteúdo"""
        valores_encontrados = []
        
        # Padrões para valores monetários
        money_patterns = [
            r'R\$\s*[\d.,]+',
            r'[\d.,]+\s*(?:reais?|R\$)',
            r'(?:valor|total|débito|dívida)[:\s]*R\$?\s*[\d.,]+',
            r'[\d]{1,3}(?:\.[\d]{3})*(?:,[\d]{2})?'
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                valor = self._extract_monetary_value(match)
                if valor > 0:
                    valores_encontrados.append(valor)
                    logger.info(f"DÍVIDAS: Valor encontrado: R$ {valor:.2f} (padrão: {match})")
        
        return valores_encontrados
    
    async def _go_back_safely(self, page: Page) -> None:
        """Volta para a página anterior de forma segura"""
        try:
            # Tentar usar botão "Voltar" primeiro
            voltar_selectors = self.selectors.get_voltar_button_selectors()
            
            for selector in voltar_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button and await button.is_visible():
                        await HumanBehavior.human_click(page, button)
                        await HumanBehavior.wait_for_page_stability(page, 15000)
                        logger.info("Voltou usando botão Voltar")
                        return
                except Exception:
                    continue
            
            # Fallback para navegação do browser
            await page.go_back()
            await HumanBehavior.wait_for_page_stability(page, 15000)
            logger.info("Voltou usando navegação do browser")
            
        except Exception as e:
            logger.warning(f"Erro ao voltar: {e}")


class MessageExtractor:
    """Classe especializada para extração de dados de mensagens SEFAZ"""
    
    def __init__(self):
        self.selectors = SEFAZSelectors()
    
    async def extract_message_data(self, page: Page, inscricao_estadual_contexto: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Extrai todos os dados de uma mensagem SEFAZ aberta
        
        Args:
            page: Página do Playwright
            inscricao_estadual_contexto: IE da empresa (contexto)
            
        Returns:
            Dict com dados extraídos ou None se erro
        """
        try:
            dados = {}
            
            # Usar IE do contexto como padrão
            if inscricao_estadual_contexto:
                dados['inscricao_estadual'] = inscricao_estadual_contexto
            
            # Extrair dados da tabela de informações
            await self._extract_message_table_data(page, dados)
            
            # Extrair conteúdo HTML completo
            await self._extract_message_content(page, dados)
            
            # Extrair dados específicos da DIEF do conteúdo
            self._extract_dief_data_from_content(dados)
            
            return dados
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados da mensagem: {e}")
            return None
    
    async def _extract_message_table_data(self, page: Page, dados: Dict[str, Any]) -> None:
        """Extrai dados da tabela de informações da mensagem"""
        message_selectors = self.selectors.get_message_selectors()
        message_data_selectors = SEFAZSelectors.MESSAGE_DATA
        
        # Mapear campos para seletores
        campo_seletor_map = {
            'enviada_por': message_data_selectors['enviada_por'],
            'data_envio': message_data_selectors['data_envio'],
            'assunto': message_data_selectors['assunto'],
            'classificacao': message_data_selectors['classificacao'],
            'tributo': message_data_selectors['tributo'],
            'tipo_mensagem': message_data_selectors['tipo_mensagem'],
            'numero_documento': message_data_selectors['numero_documento'],
            'vencimento': message_data_selectors['vencimento'],
            'data_leitura': message_data_selectors['data_leitura']
        }
        
        # Extrair cada campo
        for campo, seletor in campo_seletor_map.items():
            try:
                element = await page.query_selector(seletor)
                if element:
                    dados[campo] = (await element.text_content()).strip()
            except Exception:
                pass
        
        # Extrair IE e nome da empresa
        try:
            ie_element = await page.query_selector(message_data_selectors['ie_mensagem'])
            if ie_element:
                ie_texto = (await ie_element.text_content()).strip()
                if " - " in ie_texto:
                    dados['inscricao_estadual'] = ie_texto.split(" - ")[0].strip()
                    dados['nome_empresa'] = ie_texto.split(" - ")[1].strip()
                else:
                    dados['inscricao_estadual'] = ie_texto
        except Exception:
            pass
    
    async def _extract_message_content(self, page: Page, dados: Dict[str, Any]) -> None:
        """Extrai o conteúdo HTML completo da mensagem"""
        try:
            message_data_selectors = SEFAZSelectors.MESSAGE_DATA
            conteudo_element = await page.query_selector(message_data_selectors['conteudo_mensagem'])
            
            if conteudo_element:
                conteudo_html = await conteudo_element.inner_html()
                dados['conteudo_html'] = conteudo_html
                
                conteudo_texto = await conteudo_element.text_content()
                dados['conteudo_mensagem'] = conteudo_texto.strip()
                
                logger.info(f"HTML extraído: {len(conteudo_html)} caracteres")
                logger.info(f"Texto extraído: {len(conteudo_texto)} caracteres")
        except Exception as e:
            logger.warning(f"Erro ao extrair conteúdo HTML: {e}")
    
    def _extract_dief_data_from_content(self, dados: Dict[str, Any]) -> None:
        """Extrai dados específicos da DIEF do conteúdo da mensagem"""
        conteudo_texto = dados.get('conteudo_mensagem', '')
        
        if not conteudo_texto:
            return
        
        # Patterns para extrair dados da DIEF
        patterns = {
            'competencia_dief': r'Período da DIEF:\s*(\d{6})',
            'status_dief': r'Situação:\s*([^\n]+)',
            'chave_dief': r'Chave de segurança:\s*([\d-]+)',
            'protocolo_dief': r'Protocolo DIEF:\s*(\d+)'
        }
        
        for campo, pattern in patterns.items():
            try:
                match = re.search(pattern, conteudo_texto)
                if match:
                    dados[campo] = match.group(1).strip()
                    logger.info(f"✓ {campo}: {dados[campo]}")
                else:
                    logger.warning(f"⚠️ {campo} não encontrado")
            except Exception as e:
                logger.warning(f"Erro ao extrair {campo}: {e}")