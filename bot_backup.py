import asyncio
from playwright.async_api import async_playwright
import sqlite3
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SEFAZBot:
    def __init__(self, db_path=None):
        self.db_path = db_path or os.getenv('DB_PATH', 'sefaz_consulta.db')
        self.sefaz_url = os.getenv('SEFAZ_URL', 'https://sefaznet.sefaz.ma.gov.br/sefaznet/login.do?method=prepareLogin')
        self.timeout = int(os.getenv('TIMEOUT', '30000'))
        self.headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        # SMTP configuration for notifications
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587')) if os.getenv('SMTP_PORT') else None
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_pass = os.getenv('SMTP_PASS')
        self.smtp_from = os.getenv('SMTP_FROM')
        self.smtp_use_tls = os.getenv('SMTP_TLS', 'true').lower() == 'true'

        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela existe e criar com todas as colunas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_empresa TEXT,
                cnpj TEXT,
                inscricao_estadual TEXT,
                cpf_socio TEXT,
                chave_acesso TEXT,
                status_ie TEXT,
                tem_tvi TEXT,
                valor_debitos REAL,
                tem_divida_pendente TEXT,
                omisso_declaracao TEXT,
                inscrito_restritivo TEXT,
                data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Adicionar colunas se não existirem (para bancos existentes)
        try:
            cursor.execute('ALTER TABLE consultas ADD COLUMN tem_divida_pendente TEXT')
        except sqlite3.OperationalError:
            pass  # Coluna já existe
            
        try:
            cursor.execute('ALTER TABLE consultas ADD COLUMN omisso_declaracao TEXT')
        except sqlite3.OperationalError:
            pass  # Coluna já existe
            
        try:
            cursor.execute('ALTER TABLE consultas ADD COLUMN inscrito_restritivo TEXT')
        except sqlite3.OperationalError:
            pass  # Coluna já existe
        
        conn.commit()
        conn.close()
    
    def salvar_resultado(self, dados):
        """Salva os dados no banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO consultas 
            (nome_empresa, cnpj, inscricao_estadual, cpf_socio, chave_acesso, 
             status_ie, tem_tvi, valor_debitos, tem_divida_pendente, 
             omisso_declaracao, inscrito_restritivo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            dados.get('nome_empresa'),
            dados.get('cnpj'),
            dados.get('inscricao_estadual'),
            dados.get('cpf_socio'),
            dados.get('chave_acesso'),
            dados.get('status_ie'),
            dados.get('tem_tvi'),
            dados.get('valor_debitos'),
            dados.get('tem_divida_pendente'),
            dados.get('omisso_declaracao'),
            dados.get('inscrito_restritivo')
        ))
        
        conn.commit()
        conn.close()
        logger.info("Dados salvos no banco de dados")
    
    async def fazer_login(self, page, usuario, senha):
        """Realiza o login no sistema"""
        try:
            # Configurar timeout mais longo para navegação inicial
            page.set_default_timeout(60000)  # 60 segundos
            
            await page.goto(self.sefaz_url, wait_until="domcontentloaded")
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # Simular comportamento humano - aguardar um pouco antes de começar a preencher
            await page.wait_for_timeout(self.random_delay(1000, 3000))
            
            # Preencher usuário (identificação) simulando digitação humana
            usuario_field = await page.query_selector('input[name="identificacao"]')
            if usuario_field:
                await self.human_type(page, usuario_field, usuario)
            
            # Pausa entre os campos
            await page.wait_for_timeout(self.random_delay(500, 1500))
            
            # Preencher senha simulando digitação humana
            senha_field = await page.query_selector('input[name="senha"]')
            if senha_field:
                await self.human_type(page, senha_field, senha)
            
            # Pausa antes de clicar no botão
            await page.wait_for_timeout(self.random_delay(800, 2000))
            
            # Clicar no botão de login com comportamento humano
            login_button = await page.query_selector('button[type="submit"]')
            if login_button:
                await self.human_click(page, login_button)
            
            await page.wait_for_load_state("networkidle", timeout=30000)
            
            # Restaurar timeout padrão
            page.set_default_timeout(self.timeout)
            
            logger.info("Login realizado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro no login: {e}")
            return False
    
    async def human_type(self, page, element, text):
        """Simula digitação humana com velocidade variável"""
        try:
            # Clicar no campo primeiro
            await self.human_click(page, element)
            await page.wait_for_timeout(self.random_delay(100, 300))
            
            # Limpar campo
            await element.fill("")
            await page.wait_for_timeout(self.random_delay(100, 200))
            
            # Digitar caractere por caractere com intervalos aleatórios
            for char in text:
                await element.type(char)
                await page.wait_for_timeout(self.random_delay(50, 200))
                
        except Exception:
            # Fallback para preenchimento normal
            await element.fill(text)
    
    async def extrair_dados(self, page):
        """Extrai os dados da página conta corrente após login"""
        dados = {}
        
        try:
            # Aguardar carregamento completo da nova página
            await page.wait_for_load_state("networkidle", timeout=30000)
            await page.wait_for_timeout(2000)  # Aguardar mais um pouco para garantir
            
            # Verificar se estamos na página correta
            url = page.url
            title = await page.title()
            logger.info(f"URL atual na extração: {url}")
            logger.info(f"Título da página na extração: {title}")
            
            page_content = await page.content()
            if "Inscrição Estadual" not in page_content:
                logger.warning("Não parece estar na página de Conta Corrente")
                # Verificar se há botão "Continuar" para clicar
                continuar_btn = await page.query_selector("button:has-text('Continuar')")
                if continuar_btn:
                    logger.info("Encontrado botão Continuar, clicando...")
                    await continuar_btn.click()
                    await page.wait_for_load_state('networkidle')
                    page_content = await page.content()
                    if "Inscrição Estadual" not in page_content:
                        logger.warning("Ainda não está na página correta após clicar Continuar")
                        return dados
                else:
                    logger.warning("Botão Continuar não encontrado")
                    return dados
            
            # Extrair dados específicos da tabela na página Conta Corrente
            # Inscrição Estadual
            ie_selectors = [
                "td.texto_negrito:has-text('Inscrição Estadual') + td span.texto",
                "td:has-text('Inscrição Estadual') + td span",
                "td:has-text('Inscrição Estadual') + td"
            ]
            
            for selector in ie_selectors:
                try:
                    ie_element = await page.query_selector(selector)
                    if ie_element:
                        dados['inscricao_estadual'] = await ie_element.text_content()
                        dados['inscricao_estadual'] = dados['inscricao_estadual'].strip() if dados['inscricao_estadual'] else None
                        break
                except Exception:
                    continue
            
            # Razão Social  
            razao_selectors = [
                "td.texto_negrito:has-text('Razão Social') + td span.texto",
                "td:has-text('Razão Social') + td span",
                "td:has-text('Razão Social') + td"
            ]
            
            for selector in razao_selectors:
                try:
                    razao_element = await page.query_selector(selector)
                    if razao_element:
                        dados['nome_empresa'] = await razao_element.text_content()
                        dados['nome_empresa'] = dados['nome_empresa'].strip() if dados['nome_empresa'] else None
                        break
                except Exception:
                    continue
            
            # Situação Cadastral
            situacao_selectors = [
                "td.texto_negrito:has-text('Situação Cadastral') + td span.texto",
                "td:has-text('Situação Cadastral') + td span",
                "td:has-text('Situação Cadastral') + td"
            ]
            
            for selector in situacao_selectors:
                try:
                    situacao_element = await page.query_selector(selector)
                    if situacao_element:
                        dados['status_ie'] = await situacao_element.text_content()
                        dados['status_ie'] = dados['status_ie'].strip() if dados['status_ie'] else None
                        break
                except Exception:
                    continue
            
            # Verificar checkboxes de pendências
            try:
                # Dívida Pendente
                divida_checkbox = await page.query_selector("input[name='indicadorInadimplente']:checked")
                dados['tem_divida_pendente'] = 'SIM' if divida_checkbox else 'NÃO'
                
                # Omisso de Declaração
                omisso_checkbox = await page.query_selector("input[name='indicadorOmisso']:checked")
                dados['omisso_declaracao'] = 'SIM' if omisso_checkbox else 'NÃO'
                
                # Inscrito em Cadastro Restritivo
                serasa_checkbox = await page.query_selector("input[name='indicadorSerasa']:checked")
                dados['inscrito_restritivo'] = 'SIM' if serasa_checkbox else 'NÃO'
            except Exception as e:
                logger.warning(f"Erro ao verificar checkboxes: {e}")
                dados['tem_divida_pendente'] = 'NÃO VERIFICADO'
                dados['omisso_declaracao'] = 'NÃO VERIFICADO'
                dados['inscrito_restritivo'] = 'NÃO VERIFICADO'
            
            # Verificar TVIs
            dados['tem_tvi'] = await self.verificar_tvis(page)
            
            # Verificar dívidas pendentes e obter valor total
            dados['valor_debitos'] = await self.verificar_dividas_pendentes(page)
            
            # Campos não utilizados no momento - manter por compatibilidade
            dados['cnpj'] = None
            dados['cpf_socio'] = None
            dados['chave_acesso'] = None
            
            logger.info(f"Dados extraídos: {dados}")
            return dados
            
        except Exception as e:
            logger.error(f"Erro na extração de dados: {e}")
            return dados
    
    async def extrair_texto(self, page, selector):
        """Helper para extrair texto de um elemento"""
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            return await element.text_content()
        except:
            return None

    async def check_and_open_sistemas_menu(self, page):
        """Verifica se o botão 'Sistemas' (ícone cog) está visível e abre o menu.

        Retorna True se o menu foi aberto, False caso contrário.
        """
        try:
            logger.info("Verificando menu 'Sistemas'...")
            
            # Aguardar página carregar completamente
            await page.wait_for_load_state("networkidle", timeout=10000)
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Tentar várias estratégias para encontrar o menu Sistemas
            
            # Estratégia 1: Seletor CSS específico
            logger.info("Estratégia 1: Procurando por seletor CSS...")
            selector = "a.dropdown-toggle:has(i.glyphicon-cog)"
            el = await page.query_selector(selector)
            if el:
                await self.human_click(page, el)
                await page.wait_for_timeout(self.random_delay(500, 1000))
                logger.info("Menu 'Sistemas' aberto via seletor CSS")
                return True
            
            # Estratégia 2: Por texto "Sistemas"
            logger.info("Estratégia 2: Procurando por texto 'Sistemas'...")
            el = await page.query_selector("a:has-text('Sistemas')")
            if el:
                await self.human_click(page, el)
                await page.wait_for_timeout(self.random_delay(500, 1000))
                logger.info("Menu 'Sistemas' aberto via texto")
                return True
            
            # Estratégia 3: Por ícone glyphicon-cog
            logger.info("Estratégia 3: Procurando por ícone cog...")
            el = await page.query_selector("i.glyphicon-cog")
            if el:
                # Clicar no elemento pai (link)
                link = await el.evaluate_handle("element => element.closest('a')")
                if link:
                    await self.human_click(page, link)
                    await page.wait_for_timeout(self.random_delay(500, 1000))
                    logger.info("Menu 'Sistemas' aberto via ícone")
                    return True
            
            # Estratégia 4: JavaScript direto para encontrar menu (com timeout)
            logger.info("Estratégia 4: Usando JavaScript para encontrar menu...")
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
                logger.info("Menu 'Sistemas' aberto via JavaScript")
                return True
                
            logger.warning("Menu 'Sistemas' não encontrado em nenhuma estratégia")
                
        except Exception as e:
            logger.warning(f"Erro ao tentar abrir menu 'Sistemas': {e}")
        
        # Se chegou até aqui, não conseguiu abrir o menu
        logger.info("Tentando acesso direto à Conta Corrente sem menu")
        return await self.try_direct_conta_corrente_access(page)
    
    async def try_direct_conta_corrente_access(self, page):
        """Tenta acessar Conta Corrente diretamente sem passar pelo menu Sistemas"""
        try:
            # Procurar por link direto para Conta Corrente
            selectors = [
                "a:has-text('Consultar Conta-Corrente Fiscal')",
                "a:has-text('Conta-Corrente Fiscal')",
                "a:has-text('Conta Corrente')",
                "a.jstree-anchor:has-text('Consultar Conta-Corrente Fiscal')"
            ]
            
            for selector in selectors:
                el = await page.query_selector(selector)
                if el:
                    await el.click()
                    await page.wait_for_load_state('networkidle')
                    logger.info(f"Acesso direto à Conta Corrente via: {selector}")
                    return True
            
            # Se não encontrou, verificar se já está na página correta
            page_content = await page.content()
            if "Consultar Conta-Corrente Fiscal" in page_content or "Inscrição Estadual" in page_content:
                logger.info("Já está na página de Conta Corrente")
                return True
                
        except Exception as e:
            logger.error(f"Erro no acesso direto à Conta Corrente: {e}")
        
        return False

    async def handle_inbox_and_notify(self, page):
        """Caso haja mensagem na caixa de entrada que precise de ciência, extrai o conteúdo e notifica por e-mail.

        Retorna True se uma mensagem foi processada (enviada/assinada), False caso contrário.
        """
        try:
            logger.info("Verificando mensagens pendentes...")
            
            # Aguardar página carregar antes de verificar mensagens
            await page.wait_for_load_state("networkidle", timeout=5000)
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Capturar screenshot para debug
            await page.screenshot(path="debug_inbox.png")
            logger.info("Screenshot da página salvo em debug_inbox.png")
            
            # Primeiro, verificar se há algum modal ou alert visível (com timeout curto)
            modal_selectors = [
                ".modal.show",
                ".modal[style*='display: block']",
                ".alert.show",
                ".swal2-popup",
                ".ui-dialog",
                ".modal.fade.in"
            ]
            
            for modal_sel in modal_selectors:
                try:
                    # Usar timeout curto para não travar
                    modal = await page.wait_for_selector(modal_sel, timeout=2000, state="visible")
                    if modal:
                        text = await modal.text_content()
                        if text and text.strip():
                            logger.info(f"Modal/alerta encontrado: {text[:100]}...")
                            subject = "Mensagem SEFAZ - modal/alerta"
                            body = text.strip()
                            sent = self.send_email(subject, body)
                            
                            # Tentar fechar o modal com várias estratégias
                            closed = await self.close_modal(page, modal)
                            if closed:
                                return True
                except:
                    # Se timeout, continua para próximo seletor
                    continue
            
            # Verificar se há mensagens em elementos específicos da página (com timeout)
            message_selectors = [
                ".alert:not(.hide):not(.hidden)",
                ".notification",
                ".message",
                ".msg"
            ]

            for sel in message_selectors:
                try:
                    # Timeout curto para não travar
                    elements = await page.query_selector_all(sel)
                    for el in elements:
                        # Verificar se o elemento é visível
                        try:
                            is_visible = await el.is_visible()
                            if not is_visible:
                                continue
                                
                            text = await el.text_content()
                            if text and len(text.strip()) > 10:  # Só processar se tiver conteúdo relevante
                                logger.info(f"Mensagem encontrada: {text[:50]}...")
                                # Processar mensagem se necessário
                                return True
                        except:
                            continue
                            
                except Exception as e:
                    logger.debug(f"Erro ao verificar seletor {sel}: {e}")
                    continue
            
            logger.info("Nenhuma mensagem pendente encontrada")
            return False
                
        except Exception as e:
            logger.warning(f"Erro ao processar mensagens: {e}")
            return False
                        if text and text.strip() and len(text.strip()) > 20:  # mensagem com conteúdo significativo
                            logger.info(f"Mensagem encontrada: {text[:100]}...")
                            subject = "Mensagem SEFAZ - ciência necessária"
                            body = text.strip()
                            sent = self.send_email(subject, body)
                            
                            # Tentar dar ciência
                            ack_given = await self.dar_ciencia_mensagem(page, el)
                            if ack_given:
                                return True
                            
                            return sent  # Pelo menos enviou e-mail
                except Exception as e:
                    logger.debug(f"Erro com seletor {sel}: {e}")
                    continue

            # Verificar por JavaScript se há mensagens pendentes
            has_messages = await page.evaluate("""
                () => {
                    // Procurar por textos que indiquem mensagens
                    const body = document.body.innerText || document.body.textContent || '';
                    const indicators = [
                        'mensagem pendente',
                        'caixa de entrada',
                        'você possui mensagens',
                        'dar ciência',
                        'cientificar',
                        'usuário já está conectado',
                        'sessão',
                        'ACEO005'
                    ];
                    
                    for (let indicator of indicators) {
                        if (body.toLowerCase().includes(indicator.toLowerCase())) {
                            return indicator;
                        }
                    }
                    return null;
                }
            """)
            
            if has_messages:
                logger.info(f"Indicador de mensagem encontrado: {has_messages}")
                
                # Se é erro de sessão ativa, tentar forçar nova sessão
                if 'usuário já está conectado' in has_messages.lower() or 'ACEO005' in has_messages:
                    logger.info("Erro de sessão ativa detectado, tentando forçar nova sessão...")
                    await self.handle_session_conflict(page)
                    return True
                
                # Tentar encontrar e clicar botões relacionados
                await self.try_acknowledge_buttons(page)
                return True

            logger.info("Nenhuma mensagem pendente encontrada")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagens: {e}")
            return False
    
    async def handle_session_conflict(self, page):
        """Trata conflito de sessão ativa"""
        try:
            logger.info("Tratando conflito de sessão ativa...")
            
            # Capturar screenshot para análise
            await page.screenshot(path="debug_session_conflict.png")
            
            # Procurar por botões que permitam continuar ou encerrar sessão anterior
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
            
            for btn_sel in session_buttons:
                try:
                    btn = await page.query_selector(btn_sel)
                    if btn:
                        is_visible = await btn.is_visible()
                        if is_visible:
                            logger.info(f"Encontrado botão de sessão: {btn_sel}")
                            await btn.click()
                            await page.wait_for_timeout(2000)
                            await page.wait_for_load_state("networkidle", timeout=15000)
                            logger.info(f"Botão de sessão clicado: {btn_sel}")
                            return True
                except Exception as e:
                    logger.debug(f"Erro com botão {btn_sel}: {e}")
                    continue
            
            # Tentar JavaScript para encontrar e clicar botões relacionados
            button_found = await page.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button, input[type="button"], input[type="submit"]');
                    for (let btn of buttons) {
                        const text = btn.textContent || btn.value || '';
                        if (text.toLowerCase().includes('continuar') || 
                            text.toLowerCase().includes('ok') ||
                            text.toLowerCase().includes('confirmar')) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            
            if button_found:
                await page.wait_for_timeout(2000)
                await page.wait_for_load_state("networkidle", timeout=15000)
                logger.info("Botão de sessão clicado via JavaScript")
                return True
            
            # Se nenhum botão encontrado, aguardar um pouco e tentar recarregar
            logger.info("Aguardando 5 segundos e recarregando página...")
            await page.wait_for_timeout(5000)
            await page.reload()
            await page.wait_for_load_state('networkidle', timeout=30000)
            logger.info("Página recarregada devido a conflito de sessão")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao tratar conflito de sessão: {e}")
            return False
    
    async def close_modal(self, page, modal):
        """Tenta fechar um modal usando várias estratégias"""
        try:
            # Procurar botões dentro do modal
            close_buttons = [
                "button:has-text('OK')",
                "button:has-text('Fechar')",
                "button:has-text('Confirmar')",
                "button:has-text('Dar ciência')",
                "button:has-text('Dar Ciência')",
                "button:has-text('Ciência')",
                ".btn-close",
                ".close",
                "button.close",
                "[data-dismiss='modal']"
            ]
            
            for btn_sel in close_buttons:
                try:
                    btn = await modal.query_selector(btn_sel)
                    if not btn:
                        btn = await page.query_selector(btn_sel)
                    if btn:
                        await btn.click()
                        await page.wait_for_timeout(1000)
                        logger.info(f"Modal fechado via: {btn_sel}")
                        return True
                except Exception:
                    continue
            
            # Tentar ESC
            await page.keyboard.press('Escape')
            await page.wait_for_timeout(500)
            return True
            
        except Exception as e:
            logger.error(f"Erro ao fechar modal: {e}")
            return False
    
    async def dar_ciencia_mensagem(self, page, element):
        """Tenta dar ciência em uma mensagem específica"""
        try:
            # Procurar botões próximos ao elemento da mensagem
            parent = await element.evaluate_handle("el => el.parentElement")
            if parent:
                ack_buttons = [
                    "button:has-text('Dar ciência')",
                    "button:has-text('Dar Ciência')",
                    "button:has-text('Ciência')",
                    "button:has-text('OK')",
                    "input[value*='ciência']"
                ]
                
                for btn_sel in ack_buttons:
                    btn = await parent.query_selector(btn_sel)
                    if btn:
                        await btn.click()
                        await page.wait_for_timeout(500)
                        logger.info(f"Ciência dada via: {btn_sel}")
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao dar ciência: {e}")
            return False
    
    async def try_acknowledge_buttons(self, page):
        """Tenta encontrar e clicar botões de ciência na página"""
        try:
            buttons = [
                "button:has-text('Dar ciência')",
                "button:has-text('Dar Ciência')",
                "button:has-text('Ciência')",
                "button:has-text('OK')",
                "button:has-text('Confirmar')",
                "input[type='button'][value*='ciência']",
                "input[type='submit'][value*='ciência']"
            ]
            
            for btn_sel in buttons:
                try:
                    btn = await page.query_selector(btn_sel)
                    if btn:
                        is_visible = await btn.is_visible()
                        if is_visible:
                            await btn.click()
                            await page.wait_for_timeout(1000)
                            logger.info(f"Botão de ciência clicado: {btn_sel}")
                            return True
                except Exception:
                    continue
            
            return False
        except Exception as e:
            logger.error(f"Erro ao clicar botões de ciência: {e}")
            return False

    def send_email(self, subject, body, to_addr=None):
        """Envia e-mail usando variáveis de ambiente SMTP configuradas.

        Retorna True se enviado, False caso contrário.
        """
        to_addr = to_addr or os.getenv('NOTIFY_TO', 'fiscal@exattacontabilidade.com.br')
        if not self.smtp_host or not self.smtp_port:
            logger.warning("SMTP não configurado; não foi possível enviar e-mail")
            return False

        try:
            msg = EmailMessage()
            msg["From"] = self.smtp_from or self.smtp_user or f"no-reply@{self.smtp_host}"
            msg["To"] = to_addr
            msg["Subject"] = subject
            msg.set_content(body)

            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20)

            if self.smtp_user and self.smtp_pass:
                server.login(self.smtp_user, self.smtp_pass)

            server.send_message(msg)
            server.quit()
            logger.info(f"E-mail enviado para {to_addr}")
            return True
        except Exception as e:
            logger.error(f"Falha ao enviar e-mail: {e}")
            return False

    async def click_conta_corrente(self, page):
        """Navega através do menu completo para acessar Consultar Conta-Corrente Fiscal"""
        try:
            # Passo 1: Clicar em "Todas as Áreas de Negócio"
            logger.info("Procurando por 'Todas as Áreas de Negócio'...")
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            todas_areas_button = await page.query_selector("a:has-text('Todas as Áreas de Negócio')")
            if not todas_areas_button:
                # Tentar pelo onclick
                todas_areas_button = await page.query_selector("a[onclick*=\"listMenu(document.menuForm,this,'all')\"]")
            
            if todas_areas_button:
                await self.human_click(page, todas_areas_button)
                logger.info("Clicado em 'Todas as Áreas de Negócio'")
                
                # Aguardar carregamento da página listMenu.do
                await page.wait_for_load_state("networkidle", timeout=30000)
                
                # Verificar se chegamos na página correta
                url = page.url
                if "listMenu.do" in url:
                    logger.info(f"Página listMenu.do carregada: {url}")
                else:
                    logger.warning(f"URL inesperada: {url}")
                
                await page.wait_for_timeout(self.random_delay(1500, 3000))
                
                # Passo 2: Clicar em "Conta Fiscal"
                logger.info("Procurando por 'Conta Fiscal'...")
                conta_fiscal_link = await page.query_selector("a.jstree-anchor:has-text('Conta Fiscal')")
                if not conta_fiscal_link:
                    # Tentar seletor mais genérico
                    conta_fiscal_link = await page.query_selector("a:has-text('Conta Fiscal')")
                
                if conta_fiscal_link:
                    await self.human_click(page, conta_fiscal_link)
                    logger.info("Clicado em 'Conta Fiscal'")
                    await page.wait_for_timeout(self.random_delay(1000, 2000))  # Aguardar submenu expandir
                    
                    # Passo 3: Clicar em "Consultar Conta-Corrente Fiscal"
                    logger.info("Procurando por 'Consultar Conta-Corrente Fiscal'...")
                    await page.wait_for_timeout(self.random_delay(500, 1000))
                    
                    consultar_link = await page.query_selector("a.jstree-anchor:has-text('Consultar Conta-Corrente Fiscal')")
                    if not consultar_link:
                        # Tentar seletor mais genérico
                        consultar_link = await page.query_selector("a:has-text('Consultar Conta-Corrente Fiscal')")
                    
                    if consultar_link:
                        await self.human_click(page, consultar_link)
                        logger.info("Clicado em 'Consultar Conta-Corrente Fiscal'")
                        
                        # Aguardar carregamento da página
                        await page.wait_for_load_state("networkidle", timeout=30000)
                        await page.wait_for_timeout(self.random_delay(2000, 4000))
                        
                        # Passo 4: Clicar no botão "Continuar"
                        continuar_success = await self.click_continuar_button(page)
                        if continuar_success:
                            return True
                        else:
                            logger.warning("Não foi possível clicar no botão Continuar, mas pode estar na página correta")
                            return True
                    else:
                        logger.error("Link 'Consultar Conta-Corrente Fiscal' não encontrado")
                        return False
                else:
                    logger.error("Link 'Conta Fiscal' não encontrado")
                    return False
            else:
                logger.error("Botão 'Todas as Áreas de Negócio' não encontrado")
                return False
                
        except Exception as e:
            logger.error(f"Erro na navegação para Conta Corrente: {e}")
            return False
    
    async def click_continuar_button(self, page):
        """Procura e clica no botão Continuar na página de Conta Corrente"""
        try:
            # Simular comportamento humano antes de procurar o botão
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Procurar pelo botão "Continuar" com diferentes seletores
            continuar_selectors = [
                "button:has-text('Continuar')",
                "button[onclick*='validateForm']",
                "button.btn-primary:has-text('Continuar')",
                "input[type='button']:has-text('Continuar')",
                "input[type='submit']:has-text('Continuar')"
            ]
            
            for selector in continuar_selectors:
                try:
                    button = await page.query_selector(selector)
                    if button:
                        is_visible = await button.is_visible()
                        if is_visible:
                            await self.human_click(page, button)
                            logger.info(f"Botão 'Continuar' clicado via: {selector}")
                            
                            # Aguardar carregamento após clicar
                            await page.wait_for_load_state("networkidle", timeout=30000)
                            await page.wait_for_timeout(self.random_delay(1000, 2000))
                            
                            return True
                except Exception:
                    continue
            
            logger.warning("Botão 'Continuar' não encontrado ou não visível")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao clicar no botão Continuar: {e}")
            return False

    async def verificar_tvis(self, page):
        """Clica no botão TVIs e verifica se existem TVIs cadastradas"""
        try:
            # Simular comportamento humano - pequena pausa antes de clicar
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Clicar no botão TVIs
            tvi_button = await page.query_selector("button:has-text('TVIs')")
            if tvi_button:
                # Simular movimento do mouse antes de clicar
                await self.human_click(page, tvi_button)
                logger.info("Clicado no botão TVIs")
                
                # Aguardar carregamento da nova página
                await page.wait_for_load_state("networkidle", timeout=30000)
                await page.wait_for_timeout(self.random_delay(2000, 3000))
                
                # Verificar se existem dados de TVI na página
                tvi_data = await self.extract_tvi_data(page)
                
                # Voltar para a página anterior usando botão Voltar ou navegação
                await self.go_back_safely(page)
                
                return tvi_data
            else:
                logger.warning("Botão TVIs não encontrado")
                return "NÃO VERIFICADO"
                
        except Exception as e:
            logger.error(f"Erro ao verificar TVIs: {e}")
            try:
                # Tentar voltar em caso de erro
                await self.go_back_safely(page)
            except:
                pass
            return "ERRO"
    
    async def extract_tvi_data(self, page):
        """Extrai dados específicos da página de TVIs"""
        try:
            # Aguardar página carregar completamente
            await page.wait_for_timeout(self.random_delay(2000, 3000))
            
            # Capturar screenshot para debug
            await page.screenshot(path="debug_tvi_page.png")
            logger.info("Screenshot da página de TVI salvo em debug_tvi_page.png")
            
            # Obter conteúdo completo da página para análise
            page_content = await page.content()
            
            # Verificar especificamente a mensagem "Nenhum resultado foi encontrado"
            if "Nenhum resultado foi encontrado" in page_content:
                logger.info("TVI: Encontrada mensagem 'Nenhum resultado foi encontrado'")
                return "NÃO"
            
            # Verificar outras mensagens de ausência de dados
            no_data_messages = [
                "Nenhum registro encontrado",
                "Sem dados disponíveis",
                "Não há TVIs",
                "Nenhuma TVI cadastrada",
                "Não foram encontrados registros"
            ]
            
            for message in no_data_messages:
                if message in page_content:
                    logger.info(f"TVI: Encontrada mensagem '{message}'")
                    return "NÃO"
            
            # Verificar se há tabela com dados de TVI usando seletores mais específicos
            tvi_table_selectors = [
                "table.cor_tabelamae tbody tr:has(td:not(.texto_header_pagination))",
                "table tbody tr:has(td):not(:has(td.texto_header_pagination))",
                "tr:has(td):not(:has(.texto_header_pagination)):not(:has(.texto_negrito))"
            ]
            
            has_data = False
            for selector in tvi_table_selectors:
                try:
                    rows = await page.query_selector_all(selector)
                    for row in rows:
                        row_text = await row.text_content()
                        if row_text and row_text.strip():
                            # Verificar se não é linha de cabeçalho ou mensagem
                            clean_text = row_text.strip().lower()
                            if (clean_text and 
                                "nenhum resultado" not in clean_text and 
                                "inscrição estadual" not in clean_text and
                                "razão social" not in clean_text and
                                len(clean_text) > 10):  # Linha com conteúdo significativo
                                logger.info(f"TVI: Dados encontrados na tabela: {row_text[:100]}...")
                                has_data = True
                                break
                    if has_data:
                        break
                except Exception:
                    continue
            
            if has_data:
                return "SIM"
            
            # Verificar por elementos específicos que indicam presença de TVIs
            tvi_indicators = [
                "Termo de Verificação",
                "TVI",
                "número do termo",
                "data do termo"
            ]
            
            for indicator in tvi_indicators:
                if indicator in page_content and "Nenhum resultado" not in page_content:
                    # Se encontrou indicadores mas não a mensagem de "nenhum resultado"
                    logger.info(f"TVI: Indicador encontrado '{indicator}' sem mensagem de ausência")
                    return "SIM"
            
            # Se chegou até aqui, provavelmente não há TVIs
            logger.info("TVI: Nenhum dado encontrado na página")
            return "NÃO"
                
        except Exception as e:
            logger.error(f"Erro ao extrair dados de TVI: {e}")
            return "ERRO"
    
    async def verificar_dividas_pendentes(self, page):
        """Clica no botão Dívidas Pendentes e extrai o valor total"""
        try:
            # Simular comportamento humano
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Clicar no botão Dívidas Pendentes
            divida_button = await page.query_selector("button:has-text('Dívidas Pendentes')")
            if divida_button:
                await self.human_click(page, divida_button)
                logger.info("Clicado no botão Dívidas Pendentes")
                
                # Aguardar carregamento da nova página
                await page.wait_for_load_state("networkidle", timeout=30000)
                await page.wait_for_timeout(self.random_delay(2000, 3000))
                
                # Extrair dados de dívidas
                divida_data = await self.extract_divida_data(page)
                
                # Voltar para a página anterior
                await self.go_back_safely(page)
                
                return divida_data
            else:
                logger.warning("Botão Dívidas Pendentes não encontrado")
                return 0.0
                
        except Exception as e:
            logger.error(f"Erro ao verificar dívidas pendentes: {e}")
            try:
                await self.go_back_safely(page)
            except:
                pass
            return 0.0
    
    async def extract_divida_data(self, page):
        """Extrai dados específicos da página de Dívidas Pendentes"""
        try:
            # Aguardar página carregar completamente
            await page.wait_for_timeout(self.random_delay(2000, 3000))
            
            # Capturar screenshot para debug
            await page.screenshot(path="debug_dividas_page.png")
            logger.info("Screenshot da página de Dívidas salvo em debug_dividas_page.png")
            
            # Obter conteúdo completo da página para análise
            page_content = await page.content()
            
            # Verificar especificamente a mensagem "Nenhum resultado foi encontrado"
            if "Nenhum resultado foi encontrado" in page_content:
                logger.info("DÍVIDAS: Encontrada mensagem 'Nenhum resultado foi encontrado'")
                return 0.0
            
            # Verificar outras mensagens de ausência de dados
            no_data_messages = [
                "Nenhum registro encontrado",
                "Sem dados disponíveis", 
                "Não há dívidas",
                "Nenhuma dívida pendente",
                "Não foram encontrados registros",
                "Sem débitos pendentes"
            ]
            
            for message in no_data_messages:
                if message in page_content:
                    logger.info(f"DÍVIDAS: Encontrada mensagem '{message}'")
                    return 0.0
            
            # Procurar por valores monetários na página usando regex mais robusto
            import re
            valor_total = 0.0
            valores_encontrados = []
            
            # Padrões para valores monetários brasileiros
            money_patterns = [
                r'R\$\s*[\d.,]+',
                r'[\d.,]+\s*(?:reais?|R\$)',
                r'(?:valor|total|débito|dívida)[:\s]*R\$?\s*[\d.,]+',
                r'[\d]{1,3}(?:\.[\d]{3})*(?:,[\d]{2})?'
            ]
            
            for pattern in money_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                for match in matches:
                    # Extrair apenas os números do match
                    valor_str = re.sub(r'[^\d,.]', '', match)
                    if valor_str:
                        valor = self.extract_monetary_value(valor_str)
                        if valor > 0:
                            valores_encontrados.append(valor)
                            logger.info(f"DÍVIDAS: Valor encontrado: R$ {valor:.2f} (padrão: {match})")
            
            # Se encontrou valores, usar o maior (pode ser o total)
            if valores_encontrados:
                valor_total = max(valores_encontrados)
                logger.info(f"DÍVIDAS: Valor máximo selecionado: R$ {valor_total:.2f}")
                return valor_total
            
            # Verificar se há tabelas com dados que possam conter valores
            table_selectors = [
                "table.cor_tabelamae tbody tr:has(td:not(.texto_header_pagination))",
                "table tbody tr:has(td):not(:has(td.texto_header_pagination))",
                "tr:has(td):not(:has(.texto_header_pagination)):not(:has(.texto_negrito))"
            ]
            
            has_debt_data = False
            for selector in table_selectors:
                try:
                    rows = await page.query_selector_all(selector)
                    for row in rows:
                        row_text = await row.text_content()
                        if row_text and row_text.strip():
                            clean_text = row_text.strip().lower()
                            # Verificar se a linha contém dados de dívida (não cabeçalhos)
                            if (clean_text and 
                                "nenhum resultado" not in clean_text and
                                "inscrição estadual" not in clean_text and
                                "razão social" not in clean_text and
                                len(clean_text) > 10):
                                
                                # Tentar extrair valor da linha
                                valor = self.extract_monetary_value(row_text)
                                if valor > 0:
                                    valores_encontrados.append(valor)
                                    logger.info(f"DÍVIDAS: Valor encontrado na tabela: R$ {valor:.2f}")
                                    has_debt_data = True
                                elif any(word in clean_text for word in ['débito', 'dívida', 'pendente', 'valor']):
                                    has_debt_data = True
                except Exception:
                    continue
            
            # Se encontrou dados de dívida mas sem valores específicos
            if has_debt_data and not valores_encontrados:
                logger.info("DÍVIDAS: Dados de dívida encontrados, mas valores não identificados")
                return -1.0  # Indica que há dívida mas valor não foi identificado
            
            # Se encontrou valores, retornar a soma total
            if valores_encontrados:
                valor_total = sum(valores_encontrados)
                logger.info(f"DÍVIDAS: Valor total calculado: R$ {valor_total:.2f}")
                return valor_total
            
            # Verificar indicadores de dívidas mesmo sem valores específicos
            debt_indicators = [
                "débito",
                "dívida",
                "pendente", 
                "inadimplente",
                "valor devido"
            ]
            
            for indicator in debt_indicators:
                if indicator in page_content.lower() and "nenhum resultado" not in page_content.lower():
                    logger.info(f"DÍVIDAS: Indicador encontrado '{indicator}' sem mensagem de ausência")
                    return -1.0  # Há indicação de dívida mas valor não identificado
            
            # Se chegou até aqui, não há dívidas
            logger.info("DÍVIDAS: Nenhuma dívida encontrada")
            return 0.0
                
        except Exception as e:
            logger.error(f"Erro ao extrair dados de dívida: {e}")
            return 0.0
    
    def extract_monetary_value(self, text):
        """Extrai valor monetário de um texto com maior precisão"""
        try:
            import re
            
            if not text:
                return 0.0
            
            # Remover R$ e espaços extras, mas manter números, vírgulas e pontos
            clean_text = text.strip()
            
            # Padrão 1: R$ 1.234.567,89 ou 1.234.567,89 (formato brasileiro com pontos de milhares)
            pattern1 = r'R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})'
            match1 = re.search(pattern1, clean_text)
            if match1:
                value_str = match1.group(1).replace('.', '').replace(',', '.')
                return float(value_str)
            
            # Padrão 2: R$ 123456,78 ou 123456,78 (formato brasileiro sem pontos de milhares)
            pattern2 = r'R?\$?\s*(\d{4,7},\d{2})(?!\d)'
            match2 = re.search(pattern2, clean_text)
            if match2:
                value_str = match2.group(1).replace(',', '.')
                return float(value_str)
            
            # Padrão 3: R$ 123456.78 ou 123456.78 (formato americano)
            pattern3 = r'R?\$?\s*(\d{1,7}\.\d{2})(?!\d)'
            match3 = re.search(pattern3, clean_text)
            if match3:
                return float(match3.group(1))
            
            # Padrão 4: R$ 1.234.567 (sem centavos, com pontos de milhares)
            pattern4 = r'R?\$?\s*(\d{1,3}(?:\.\d{3})+)(?!\d|,)'
            match4 = re.search(pattern4, clean_text)
            if match4:
                value_str = match4.group(1).replace('.', '')
                return float(value_str)
            
            # Padrão 5: R$ 1234567 (apenas números grandes, sem separadores)
            pattern5 = r'R?\$?\s*(\d{5,})(?!\d)'
            match5 = re.search(pattern5, clean_text)
            if match5:
                return float(match5.group(1))
            
            # Padrão 6: números menores (R$ 123 ou 123)
            pattern6 = r'R?\$?\s*(\d{1,4})(?!\d)'
            match6 = re.search(pattern6, clean_text)
            if match6:
                value = float(match6.group(1))
                # Se é um número pequeno sozinho, pode ser reais
                if value < 1000:
                    return value
                else:
                    return value
            
            return 0.0
            
        except (ValueError, AttributeError) as e:
            logger.debug(f"Erro ao extrair valor monetário de '{text}': {e}")
            return 0.0
    
    async def human_click(self, page, element):
        """Simula clique humano com movimento de mouse"""
        try:
            # Obter posição do elemento
            box = await element.bounding_box()
            if box:
                # Calcular posição aleatória dentro do elemento
                x = box['x'] + self.random_delay(10, box['width'] - 10)
                y = box['y'] + self.random_delay(10, box['height'] - 10)
                
                # Mover mouse para a posição
                await page.mouse.move(x, y)
                await page.wait_for_timeout(self.random_delay(100, 300))
                
                # Clicar
                await page.mouse.click(x, y)
            else:
                # Fallback para clique normal
                await element.click()
        except Exception:
            # Fallback para clique normal
            await element.click()
    
    async def go_back_safely(self, page):
        """Volta para a página anterior de forma segura"""
        try:
            # Tentar usar botão "Voltar" primeiro
            voltar_selectors = [
                "button:has-text('Voltar')",
                "input[type='button'][value*='Voltar']",
                "a:has-text('Voltar')",
                ".btn-voltar",
                "#voltar"
            ]
            
            for selector in voltar_selectors:
                button = await page.query_selector(selector)
                if button:
                    is_visible = await button.is_visible()
                    if is_visible:
                        await self.human_click(page, button)
                        await page.wait_for_load_state("networkidle", timeout=15000)
                        logger.info("Voltou usando botão Voltar")
                        return
            
            # Se não encontrou botão, usar navegação do browser
            await page.go_back()
            await page.wait_for_load_state("networkidle", timeout=15000)
            logger.info("Voltou usando navegação do browser")
            
        except Exception as e:
            logger.warning(f"Erro ao voltar: {e}")
    
    async def fazer_logout(self, page):
        """Realiza logout do sistema SEFAZ"""
        try:
            logger.info("Iniciando logout do sistema...")
            
            # Simular comportamento humano antes do logout
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Procurar pelo botão de logout usando diferentes seletores
            logout_selectors = [
                "a[href*='logoff.do?method=efetuarLogoff']",
                "a[href*='logoff.do']",
                "a[title*='Sair do sistema']",
                "a:has(img[src*='exit.png'])",
                "a:has-text('Sair')",
                "a:has-text('Logout')",
                "img[src*='exit.png']"
            ]
            
            logout_success = False
            for selector in logout_selectors:
                try:
                    logout_element = await page.query_selector(selector)
                    if logout_element:
                        # Verificar se é uma imagem, neste caso clicar no link pai
                        if selector == "img[src*='exit.png']":
                            logout_link = await logout_element.evaluate_handle("img => img.closest('a')")
                            if logout_link:
                                await self.human_click(page, logout_link)
                            else:
                                await self.human_click(page, logout_element)
                        else:
                            await self.human_click(page, logout_element)
                        
                        logger.info(f"Logout executado via: {selector}")
                        logout_success = True
                        break
                except Exception as e:
                    logger.debug(f"Erro com seletor {selector}: {e}")
                    continue
            
            if logout_success:
                # Aguardar redirecionamento para página de login ou logout
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    await page.wait_for_timeout(self.random_delay(1000, 2000))
                    
                    # Verificar se foi redirecionado para página de login
                    current_url = page.url
                    if "login" in current_url.lower() or "logoff" in current_url.lower():
                        logger.info("Logout realizado com sucesso - redirecionado para página de login")
                    else:
                        logger.info(f"Logout executado - URL atual: {current_url}")
                except Exception:
                    logger.info("Logout executado - timeout no redirecionamento (normal)")
                
                return True
            else:
                logger.warning("Botão de logout não encontrado")
                return False
                
        except Exception as e:
            logger.error(f"Erro durante logout: {e}")
            return False
    
    def random_delay(self, min_ms, max_ms):
        """Gera delay aleatório para simular comportamento humano"""
        import random
        return random.randint(min_ms, max_ms)
    
    async def executar_consulta(self, usuario=None, senha=None):
        """Executa a consulta completa"""
        # Usar credenciais do .env se não fornecidas
        usuario = usuario or os.getenv('USUARIO')
        senha = senha or os.getenv('SENHA')
        
        if not usuario or not senha:
            logger.error("Credenciais não fornecidas")
            return None
            
        async with async_playwright() as p:
            # Configurar browser com comportamento mais humano
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-gpu",
                    "--disable-extensions",
                    "--window-size=1920,1080"
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            # Adicionar scripts para evitar detecção
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en-US', 'en'],
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
            """)
            
            try:
                # Fazer login
                if await self.fazer_login(page, usuario, senha):
                    # Simular pausa humana após login
                    await page.wait_for_timeout(self.random_delay(2000, 4000))
                    
                    # Após login, verificar se o menu 'Sistemas' está visível
                    menu_opened = await self.check_and_open_sistemas_menu(page)

                    if not menu_opened:
                        # Pode haver uma mensagem na caixa de entrada que precisa ser cientificada
                        processed = await self.handle_inbox_and_notify(page)
                        if processed:
                            logger.info("Mensagem processada, tentando abrir menu novamente")
                            await page.wait_for_timeout(self.random_delay(1000, 2000))
                            # tentar abrir o menu novamente
                            menu_opened = await self.check_and_open_sistemas_menu(page)

                    if menu_opened:
                        # Com o menu aberto, navegar até Conta Corrente
                        ok = await self.click_conta_corrente(page)
                        if not ok:
                            logger.error("Não foi possível acessar 'Conta Corrente'")
                            return None
                    else:
                        # Se ainda não conseguiu abrir menu, tentar acesso direto
                        logger.info("Tentando acesso direto sem menu")
                        ok = await self.try_direct_conta_corrente_access(page)
                        if not ok:
                            logger.error("Não foi possível acessar Conta Corrente nem por menu nem diretamente")
                            return None

                    # Extrair dados da página Conta Corrente
                    dados = await self.extrair_dados(page)

                    # Salvar no banco
                    if dados:
                        self.salvar_resultado(dados)
                        
                        # Realizar logout antes de finalizar
                        logger.info("Dados extraídos com sucesso, realizando logout...")
                        await self.fazer_logout(page)
                        
                        return dados
                    else:
                        logger.warning("Nenhum dado foi extraído")
                        # Tentar logout mesmo sem dados
                        await self.fazer_logout(page)
                        return None
                else:
                    logger.error("Falha no login")
                    return None
                    
            except Exception as e:
                logger.error(f"Erro na execução: {e}")
                return None
                
            finally:
                await browser.close()

# Exemplo de uso
async def main():
    bot = SEFAZBot()
    
    # As credenciais agora vêm do arquivo .env
    resultado = await bot.executar_consulta()
    
    if resultado:
        print("Consulta realizada com sucesso!")
        print(resultado)
    else:
        print("Falha na consulta")

if __name__ == "__main__":
    asyncio.run(main())