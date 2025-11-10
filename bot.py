import asyncio
from playwright.async_api import async_playwright, Page, Browser
import sqlite3
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import smtplib
from email.message import EmailMessage
from typing import Optional, Dict, Any, Tuple

# Importar módulos customizados
from bot_constants import *
from bot_validators import (
    SEFAZValidator,
    ValidationException,
    LoginFailedException,
    NavigationException,
    ExtractionException,
    SessionConflictException,
    MenuNotFoundException,
    ElementNotFoundException,
    TimeoutException,
    PageLoadException,
    BrowserException,
    BrowserLaunchException,
    BrowserCloseException,
    DatabaseException,
    ConnectionException,
    QueryException,
    DuplicateException,
    CryptographyException,
    DecryptionException,
    EncryptionException,
    MissingKeyException,
    CaptchaException,
    SessionExpiredException,
    InvalidCPFException,
    InvalidIEException,
    InvalidPasswordException,
    is_session_conflict_message
)
from bot_retry import retry, retry_on_timeout, retry_on_network, RetryExhaustedException

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserManager:
    """Context manager para gestão segura do navegador Playwright"""
    
    def __init__(self, headless: bool = False, user_data_dir: Optional[str] = None):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def __aenter__(self):
        """Inicializa o navegador ao entrar no contexto"""
        try:
            logger.info("🌐 Iniciando navegador...")
            self.playwright = await async_playwright().start()
            
            # Configurar opções do navegador
            launch_options = {
                'headless': self.headless,
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials'
                ]
            }
            
            # Se user_data_dir foi fornecido, usa navegador persistente
            if self.user_data_dir:
                logger.info(f"🔧 Usando perfil do Chrome em: {self.user_data_dir}")
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    **launch_options
                )
                self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            else:
                # Navegador padrão
                self.browser = await self.playwright.chromium.launch(**launch_options)
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                self.page = await self.context.new_page()
            
            logger.info("✅ Navegador iniciado com sucesso")
            return self.page
            
        except TimeoutError as e:
            logger.error(f"❌ Timeout ao iniciar navegador: {e}")
            await self._cleanup()
            raise BrowserLaunchException(f"Timeout ao iniciar navegador: {e}") from e
        except FileNotFoundError as e:
            logger.error(f"❌ Chrome não encontrado: {e}")
            await self._cleanup()
            raise BrowserLaunchException(f"Navegador Chrome não encontrado: {e}") from e
        except PermissionError as e:
            logger.error(f"❌ Permissão negada ao acessar perfil: {e}")
            await self._cleanup()
            raise BrowserLaunchException(f"Sem permissão para acessar perfil do navegador: {e}") from e
        except (ConnectionError, OSError) as e:
            logger.error(f"❌ Erro de conexão ao iniciar navegador: {e}")
            await self._cleanup()
            raise BrowserLaunchException(f"Erro de conexão: {e}") from e
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao iniciar navegador: {e}")
            await self._cleanup()
            raise BrowserLaunchException(f"Erro inesperado: {e}") from e
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Garante que o navegador seja fechado ao sair do contexto"""
        await self._cleanup()
        
        # Se houve exceção, loga mas não suprime
        if exc_type:
            logger.error(f"❌ Exceção capturada durante execução: {exc_type.__name__}: {exc_val}")
        
        return False  # Não suprime exceções
    
    async def _cleanup(self):
        """Limpa todos os recursos do navegador"""
        errors = []
        
        # Fechar página
        if self.page:
            try:
                logger.debug("Fechando página...")
                await self.page.close()
                self.page = None
            except Exception as e:
                error_msg = f"Erro ao fechar página: {e}"
                logger.warning(f"⚠️ {error_msg}")
                errors.append(error_msg)
        
        # Fechar contexto
        if self.context and not self.user_data_dir:
            try:
                logger.debug("Fechando contexto...")
                await self.context.close()
                self.context = None
            except Exception as e:
                error_msg = f"Erro ao fechar contexto: {e}"
                logger.warning(f"⚠️ {error_msg}")
                errors.append(error_msg)
        
        # Fechar navegador
        if self.browser:
            try:
                logger.debug("Fechando navegador...")
                await self.browser.close()
                self.browser = None
            except Exception as e:
                error_msg = f"Erro ao fechar navegador: {e}"
                logger.warning(f"⚠️ {error_msg}")
                errors.append(error_msg)
        
        # Parar Playwright
        if self.playwright:
            try:
                logger.debug("Parando Playwright...")
                await self.playwright.stop()
                self.playwright = None
            except Exception as e:
                error_msg = f"Erro ao parar Playwright: {e}"
                logger.warning(f"⚠️ {error_msg}")
                errors.append(error_msg)
        
        if errors:
            logger.warning(f"⚠️ Limpeza concluída com {len(errors)} erro(s)")
        else:
            logger.info("🧹 Recursos do navegador liberados com sucesso")
        
        # Se houve erros críticos durante cleanup, lança exceção
        if len(errors) >= 3:  # Mais de 3 erros indica problema sério
            raise BrowserCloseException(f"Múltiplos erros durante cleanup: {'; '.join(errors)}")

class SEFAZBot:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv('DB_PATH', 'sefaz_consulta.db')
        self.sefaz_url = os.getenv('SEFAZ_URL', URL_SEFAZ_LOGIN)
        self.timeout = int(os.getenv('TIMEOUT', str(TIMEOUT_DEFAULT)))
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
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tabela de consultas
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
            
            # Tabela de mensagens SEFAZ
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
                    tipo_ciencia TEXT,
                    data_ciencia TEXT,
                    conteudo_mensagem TEXT,
                    data_leitura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            
        except sqlite3.DatabaseError as e:
            raise DatabaseException(f"Erro ao inicializar banco de dados: {e}") from e
        except PermissionError as e:
            raise ConnectionException(f"Sem permissão para acessar banco de dados: {e}") from e
        except OSError as e:
            raise ConnectionException(f"Erro de I/O ao acessar banco: {e}") from e
        except Exception as e:
            raise DatabaseException(f"Erro inesperado ao inicializar banco: {e}") from e
    
    def salvar_resultado(self, dados):
        """Salva os dados no banco"""
        try:
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
            
        except sqlite3.IntegrityError as e:
            raise DuplicateException(f"Registro duplicado: {e}") from e
        except sqlite3.OperationalError as e:
            raise QueryException(f"Erro na operação SQL: {e}") from e
        except sqlite3.DatabaseError as e:
            raise DatabaseException(f"Erro no banco de dados: {e}") from e
        except Exception as e:
            raise DatabaseException(f"Erro inesperado ao salvar dados: {e}") from e
    
    @retry_on_network(max_attempts=2, delay=3.0)
    async def fazer_login(self, page: Page, usuario: str, senha: str) -> bool:
        """
        Realiza o login no sistema SEFAZ com comportamento humano
        
        Args:
            page: Página do Playwright
            usuario: CPF do usuário (com ou sem formatação)
            senha: Senha do usuário
            
        Returns:
            bool: True se login foi bem-sucedido, False caso contrário
            
        Raises:
            ValidationException: Se credenciais inválidas
            LoginFailedException: Se login falhar
        """
        import random
        
        # Validar credenciais antes de tentar login
        is_valid, errors = SEFAZValidator.validate_all(usuario, senha)
        if not is_valid:
            error_msg = "Credenciais inválidas:\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ValidationException(error_msg)
        
        try:
            # Limpar CPF (remover formatação)
            usuario_limpo = SEFAZValidator.limpar_cpf(usuario)
            
            logger.info("=" * 80)
            logger.info("🔐 BOT - FAZER_LOGIN - CREDENCIAIS VALIDADAS")
            logger.info("=" * 80)
            logger.debug(f"   - Usuario original: '{usuario}'")
            logger.debug(f"   - Usuario limpo: '{usuario_limpo}'")
            logger.debug(f"   - Senha: {'*' * len(senha)}")
            logger.info("=" * 80)
            
            # Configurar timeout mais longo para navegação inicial
            page.set_default_timeout(TIMEOUT_NAVIGATION * 2)  # 60 segundos
            
            # Navegar para a página
            logger.info("🌐 Navegando para página de login...")
            try:
                await page.goto(self.sefaz_url, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle", timeout=TIMEOUT_NETWORK_IDLE)
            except TimeoutError as e:
                raise PageLoadException(f"Timeout ao carregar página de login: {e}") from e
            except Exception as e:
                raise NavigationException(f"Erro ao navegar para página de login: {e}") from e
            
            # COMPORTAMENTO HUMANO: Aguardar e mover o mouse pela página
            logger.debug("👁️ Simulando leitura da página...")
            await page.wait_for_timeout(self.random_delay(2000, 4000))
            
            # Mover mouse para posições aleatórias (simular leitura)
            for _ in range(random.randint(2, 4)):
                await page.mouse.move(
                    random.randint(100, 800),
                    random.randint(100, 600)
                )
                await page.wait_for_timeout(self.random_delay(300, 800))
            
            # Campo de usuário
            logger.debug("👤 Preenchendo campo de usuario...")
            usuario_field = await page.query_selector(SELECTOR_LOGIN_IDENTIFICACAO)
            if not usuario_field:
                raise ElementNotFoundException("Campo de usuário não encontrado")
                
            box = await usuario_field.bounding_box()
            if box:
                # Mover para próximo do campo
                await page.mouse.move(
                    box['x'] - random.randint(50, 150),
                    box['y'] + random.randint(-30, 30)
                )
                await page.wait_for_timeout(self.random_delay(400, 900))
                
                # Mover para o campo
                await page.mouse.move(
                    box['x'] + box['width']/2 + random.randint(-20, 20),
                    box['y'] + box['height']/2 + random.randint(-5, 5)
                )
                await page.wait_for_timeout(self.random_delay(200, 500))
            
            await self.human_type(page, usuario_field, usuario_limpo)
            
            # Pausa entre campos
            logger.debug("⏸️ Pausa entre campos...")
            await page.wait_for_timeout(self.random_delay(1000, 2500))
            
            # Campo de senha
            logger.debug("🔑 Preenchendo campo de senha...")
            senha_field = await page.query_selector(SELECTOR_LOGIN_SENHA)
            if not senha_field:
                raise ElementNotFoundException("Campo de senha não encontrado")
                
            box = await senha_field.bounding_box()
            if box:
                await page.mouse.move(
                    box['x'] + box['width']/2 + random.randint(-25, 25),
                    box['y'] + box['height']/2 + random.randint(-8, 8)
                )
                await page.wait_for_timeout(self.random_delay(300, 700))
            
            await self.human_type(page, senha_field, senha)
            
            # Verificar o valor digitado
            valor_digitado = await senha_field.input_value()
            if valor_digitado != senha:
                logger.warning(f"⚠️ Senha digitada difere da senha fornecida")
            
            # Pausa antes de clicar
            logger.debug("🎯 Preparando para clicar no botão de login...")
            await page.wait_for_timeout(self.random_delay(1500, 3000))
            
            # Botão de login
            login_button = await page.query_selector(SELECTOR_LOGIN_SUBMIT)
            if not login_button:
                raise ElementNotFoundException("Botão de login não encontrado")
                
            box = await login_button.bounding_box()
            if box:
                # Mover mouse até próximo do botão
                await page.mouse.move(
                    box['x'] - random.randint(100, 200),
                    box['y'] + random.randint(-50, 50)
                )
                await page.wait_for_timeout(self.random_delay(400, 800))
                
                # Mover para o botão
                await page.mouse.move(
                    box['x'] + box['width']/2 + random.randint(-30, 30),
                    box['y'] + box['height']/2 + random.randint(-10, 10)
                )
                await page.wait_for_timeout(self.random_delay(300, 600))
            
            logger.debug("🖱️ Clicando no botão de login...")
            await self.human_click(page, login_button)
            
            # Aguardar carregamento
            logger.info("⏳ Aguardando carregamento após login...")
            
            try:
                await page.wait_for_load_state("domcontentloaded", timeout=TIMEOUT_NAVIGATION)
                logger.debug("  ✅ DOM carregado")
            except TimeoutError as e:
                logger.debug(f"  ⚠️ Timeout no DOM: {e}")
            except Exception as e:
                logger.warning(f"  ⚠️ Erro inesperado aguardando DOM: {e}")
            
            try:
                await page.wait_for_load_state("networkidle", timeout=TIMEOUT_NETWORK_IDLE)
                logger.debug("  ✅ Network idle")
            except TimeoutError as e:
                logger.debug(f"  ⚠️ Timeout no network idle: {e}")
            except Exception as e:
                logger.warning(f"  ⚠️ Erro inesperado aguardando network: {e}")
            
            # Aguardar JavaScript executar
            logger.debug("⏳ Aguardando JavaScript executar...")
            await page.wait_for_timeout(self.random_delay(3000, 5000))
            
            # Salvar informações de debug
            try:
                logger.debug(f"📍 URL após login: {page.url}")
                logger.debug(f"📄 Título: {await page.title()}")
                
                content = await page.content()
                logger.debug(f"📊 Tamanho do HTML: {len(content)} bytes")
                
                # Verificar se login foi bem-sucedido (HTML > 1000 bytes)
                if len(content) < 1000:
                    raise LoginFailedException(f"Página muito pequena após login ({len(content)} bytes)")
                
                with open(DEBUG_FILE_POST_LOGIN, "w", encoding="utf-8") as f:
                    f.write(content)
                    
                await page.screenshot(path=DEBUG_FILE_POST_LOGIN.replace('.html', '.png'), full_page=True)
                logger.debug(f"💾 Debug files salvos: {DEBUG_FILE_POST_LOGIN}")
            except LoginFailedException:
                raise
            except PermissionError as e:
                logger.warning(f"⚠️ Sem permissão para salvar debug: {e}")
            except OSError as e:
                logger.warning(f"⚠️ Erro de I/O ao salvar debug: {e}")
            except Exception as e:
                logger.warning(f"⚠️ Erro inesperado ao salvar debug: {e}")
            
            # Restaurar timeout padrão
            page.set_default_timeout(self.timeout)
            
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
    
    async def human_type(self, page: Page, element, text: str) -> None:
        """
        Simula digitação humana realista com velocidade variável
        
        Args:
            page: Página do Playwright
            element: Elemento onde digitar
            text: Texto a ser digitado
            
        Note:
            - Velocidade varia por tipo de caractere
            - Incluí pausas e movimentos de mouse ocasionais
            - Fallback para preenchimento normal em caso de erro
        """
        import random
        try:
            # Clicar no campo primeiro
            await self.human_click(page, element)
            await page.wait_for_timeout(self.random_delay(300, 800))
            
            # Limpar campo de forma humana
            await page.keyboard.press("Control+A")
            await page.wait_for_timeout(self.random_delay(50, 150))
            await page.keyboard.press("Backspace")
            await page.wait_for_timeout(self.random_delay(200, 500))
            
            # Simular "pensamento" antes de começar a digitar
            await page.wait_for_timeout(self.random_delay(500, 1500))
            
            # Digitar caractere por caractere com variação REALISTA
            for i, char in enumerate(text):
                # Velocidade variável baseada no tipo de caractere
                if char.isdigit():
                    delay = self.random_delay(80, 200)
                elif char in ".-@":
                    delay = self.random_delay(200, 500)
                elif char.isupper():
                    delay = self.random_delay(150, 350)
                else:
                    delay = self.random_delay(100, 280)
                
                # Burst typing ocasional (30% de chance)
                if i > 0 and random.random() < 0.3:
                    delay = int(delay * 0.6)
                
                # Pausa mais longa ocasional (5% de chance)
                if random.random() < 0.05:
                    delay = self.random_delay(800, 2000)
                
                await element.type(char, delay=0)
                await page.wait_for_timeout(delay)
                
                # Movimentos de mouse ocasionais (15% de chance)
                if random.random() < 0.15:
                    box = await element.bounding_box()
                    if box:
                        await page.mouse.move(
                            box['x'] + random.randint(-50, int(box['width']) + 50),
                            box['y'] + random.randint(-30, int(box['height']) + 30)
                        )
            
            # Pausa após terminar (usuário revisa)
            await page.wait_for_timeout(self.random_delay(300, 800))
                
        except Exception as e:
            logger.warning(f"⚠️ Erro na digitação humana, usando fallback: {e}")
            await element.fill(text)
            await page.wait_for_timeout(self.random_delay(500, 1000))
    
    @retry(max_attempts=2, delay=2.0, on=(TimeoutException, ExtractionException))
    async def extrair_dados(self, page):
        """Extrai os dados da página conta corrente após login"""
        logger.info("="*80)
        logger.info("🔍 INICIANDO EXTRAÇÃO DE DADOS")
        logger.info("="*80)
        dados = {}
        
        try:
            # Aguardar carregamento completo da nova página
            logger.info("⏳ Aguardando carregamento completo da página...")
            try:
                await page.wait_for_load_state("networkidle", timeout=30000)
                await page.wait_for_timeout(2000)  # Aguardar mais um pouco para garantir
            except TimeoutError as e:
                raise TimeoutException(f"Timeout aguardando carregamento da página: {e}") from e
            
            # Verificar se estamos na página correta
            url = page.url
            title = await page.title()
            logger.info(f"📍 URL atual na extração: {url}")
            logger.info(f"📄 Título da página na extração: {title}")
            
            page_content = await page.content()
            logger.info(f"📏 Tamanho do HTML: {len(page_content)} bytes")
            
            if "Inscrição Estadual" not in page_content:
                logger.warning("⚠️ Não parece estar na página de Conta Corrente")
                logger.warning("🔍 Verificando se há botão Continuar ainda...")
                # Verificar se há botão "Continuar" para clicar
                continuar_btn = await page.query_selector("button:has-text('Continuar')")
                if continuar_btn:
                    logger.info("❗ Encontrado botão Continuar, clicando novamente...")
                    await continuar_btn.click()
                    await page.wait_for_load_state('networkidle')
                    page_content = await page.content()
                    if "Inscrição Estadual" not in page_content:
                        logger.error("❌ Ainda não está na página correta após clicar Continuar")
                        logger.error("💾 Salvando HTML de debug...")
                        await page.screenshot(path="debug_extracao_falha.png")
                        with open("debug_extracao_falha.html", "w", encoding="utf-8") as f:
                            f.write(page_content)
                        return dados
                    else:
                        logger.info("✅ Página correta carregada após segundo clique!")
                else:
                    logger.error("❌ Botão Continuar não encontrado e página incorreta")
                    logger.error("💾 Salvando HTML de debug...")
                    await page.screenshot(path="debug_extracao_falha.png")
                    with open("debug_extracao_falha.html", "w", encoding="utf-8") as f:
                        f.write(page_content)
                    return dados
            else:
                logger.info("✅ Página de Conta Corrente detectada corretamente!")
            
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
                except TimeoutError:
                    continue
                except Exception as e:
                    logger.debug(f"Falha no seletor {selector}: {e}")
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
                except TimeoutError:
                    continue
                except Exception as e:
                    logger.debug(f"Falha no seletor {selector}: {e}")
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
                except TimeoutError:
                    continue
                except Exception as e:
                    logger.debug(f"Falha no seletor {selector}: {e}")
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
            except TimeoutError as e:
                logger.warning(f"⚠️ Timeout ao verificar checkboxes: {e}")
                dados['tem_divida_pendente'] = 'NÃO VERIFICADO'
                dados['omisso_declaracao'] = 'NÃO VERIFICADO'
                dados['inscrito_restritivo'] = 'NÃO VERIFICADO'
            except Exception as e:
                logger.warning(f"⚠️ Erro inesperado ao verificar checkboxes: {e}")
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
            
        except (TimeoutException, ExtractionException):
            # Re-lançar exceções já tratadas
            raise
        except TimeoutError as e:
            logger.error(f"❌ Timeout durante extração: {e}")
            raise TimeoutException(f"Timeout durante extração de dados: {e}") from e
        except Exception as e:
            logger.error(f"❌ Erro inesperado na extração: {e}")
            raise ExtractionException(f"Falha na extração de dados: {e}") from e
    
    async def extrair_texto(self, page: Page, selector: str) -> Optional[str]:
        """
        Helper para extrair texto de um elemento
        
        Args:
            page: Página do Playwright
            selector: Seletor CSS do elemento
            
        Returns:
            Optional[str]: Texto do elemento ou None se não encontrado
        """
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            return await element.text_content()
        except:
            return None

    @retry_on_network(max_attempts=2, delay=2.0)
    async def processar_mensagens_ciencia(self, page: Page, cpf_socio: str) -> bool:
        """
        Processa mensagens que precisam de ciência na caixa de entrada
        
        Args:
            page: Página do Playwright
            cpf_socio: CPF do usuário (para relacionar no banco)
            
        Returns:
            bool: True se processou mensagens, False se não havia mensagens
            
        Note:
            - Filtra mensagens "Aguardando Ciência"
            - Extrai dados e salva no banco
            - Dá ciência nas mensagens
            - Retorna à página principal
        """
        try:
            logger.info("📬 Verificando mensagens que precisam de ciência...")
            
            # Verificar se há select de filtro de mensagens na página
            filtro = await page.query_selector(SELECTOR_FILTRO_MENSAGENS)
            if not filtro:
                logger.info("ℹ️ Não há caixa de mensagens nesta página")
                return False
            
            # Selecionar filtro "Aguardando Ciência"
            logger.info("🔍 Filtrando mensagens 'Aguardando Ciência'...")
            await filtro.select_option(value="4")  # Aguardando Ciência
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Aguardar atualização da lista (função javascript:atualizarCaixaEntrada())
            await page.wait_for_load_state("networkidle", timeout=10000)
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Buscar todas as mensagens que precisam de ciência
            links_mensagens = await page.query_selector_all(SELECTOR_LINK_ABRIR_MENSAGEM)
            
            if not links_mensagens or len(links_mensagens) == 0:
                logger.info("✅ Não há mensagens aguardando ciência")
                return False
            
            logger.info(f"📨 Encontradas {len(links_mensagens)} mensagem(ns) aguardando ciência")
            
            # Processar cada mensagem
            mensagens_processadas = 0
            for idx, link in enumerate(links_mensagens, 1):
                try:
                    logger.info(f"📖 Processando mensagem {idx}/{len(links_mensagens)}...")
                    
                    # Clicar para abrir a mensagem
                    await self.human_click(page, link)
                    await page.wait_for_load_state("networkidle", timeout=15000)
                    await page.wait_for_timeout(self.random_delay(1000, 2000))
                    
                    # Extrair dados da mensagem
                    dados_msg = {}
                    
                    # Extrair IE da mensagem (formato: "124402780 - R L BARBOSA EMPREENDIMENTOS")
                    ie_element = await page.query_selector(SELECTOR_MSG_IE)
                    if ie_element:
                        ie_texto = await ie_element.text_content()
                        ie_texto = ie_texto.strip() if ie_texto else ""
                        # Extrair apenas o número da IE (antes do " - ")
                        if " - " in ie_texto:
                            dados_msg['inscricao_estadual'] = ie_texto.split(" - ")[0].strip()
                        else:
                            dados_msg['inscricao_estadual'] = ie_texto
                    
                    # Extrair outros campos
                    campos_map = {
                        'enviada_por': SELECTOR_MSG_ENVIADA_POR,
                        'data_envio': SELECTOR_MSG_DATA_ENVIO,
                        'assunto': SELECTOR_MSG_ASSUNTO,
                        'classificacao': SELECTOR_MSG_CLASSIFICACAO,
                        'tributo': SELECTOR_MSG_TRIBUTO,
                        'tipo_mensagem': SELECTOR_MSG_TIPO,
                        'numero_documento': SELECTOR_MSG_NUM_DOC,
                        'vencimento': SELECTOR_MSG_VENCIMENTO
                    }
                    
                    for campo, seletor in campos_map.items():
                        element = await page.query_selector(seletor)
                        if element:
                            texto = await element.text_content()
                            dados_msg[campo] = texto.strip() if texto else None
                    
                    # Extrair conteúdo da mensagem (último tr > td da segunda tabela)
                    conteudo_elements = await page.query_selector_all("table.table-tripped tbody tr td")
                    if conteudo_elements and len(conteudo_elements) > 0:
                        # Pegar o último elemento que contém a mensagem completa
                        ultimo_elemento = conteudo_elements[-1]
                        conteudo = await ultimo_elemento.inner_text()
                        dados_msg['conteudo_mensagem'] = conteudo.strip() if conteudo else None
                    
                    dados_msg['cpf_socio'] = cpf_socio
                    
                    # Salvar no banco de dados
                    self.salvar_mensagem(dados_msg)
                    logger.info(f"💾 Mensagem salva no banco: {dados_msg.get('assunto', 'Sem assunto')}")
                    
                    # Procurar botão "Dar Ciência"
                    botao_ciencia = await page.query_selector(SELECTOR_BOTAO_DAR_CIENCIA)
                    if botao_ciencia:
                        logger.info("✅ Dando ciência na mensagem...")
                        await self.human_click(page, botao_ciencia)
                        await page.wait_for_timeout(self.random_delay(1000, 2000))
                        
                        # Aguardar confirmação ou retorno
                        try:
                            await page.wait_for_load_state("networkidle", timeout=10000)
                        except:
                            pass
                        
                        mensagens_processadas += 1
                    else:
                        logger.warning("⚠️ Botão 'Dar Ciência' não encontrado")
                        
                        # Tentar voltar
                        botao_voltar = await page.query_selector(SELECTOR_BOTAO_VOLTAR_MENSAGEM)
                        if botao_voltar:
                            await self.human_click(page, botao_voltar)
                            await page.wait_for_timeout(self.random_delay(1000, 2000))
                    
                    await page.wait_for_timeout(self.random_delay(500, 1000))
                    
                except Exception as e:
                    logger.error(f"❌ Erro ao processar mensagem {idx}: {e}")
                    # Tentar voltar em caso de erro
                    try:
                        botao_voltar = await page.query_selector(SELECTOR_BOTAO_VOLTAR_MENSAGEM)
                        if botao_voltar:
                            await self.human_click(page, botao_voltar)
                            await page.wait_for_timeout(self.random_delay(1000, 2000))
                    except:
                        pass
                    continue
            
            logger.info(f"✅ Processadas {mensagens_processadas}/{len(links_mensagens)} mensagens com sucesso")
            return mensagens_processadas > 0
            
        except Exception as e:
            logger.error(f"❌ Erro ao processar mensagens de ciência: {e}")
            return False
    
    def salvar_mensagem(self, dados: Dict[str, Any]) -> None:
        """
        Salva dados de uma mensagem SEFAZ no banco
        
        Args:
            dados: Dicionário com os dados da mensagem
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO mensagens_sefaz 
                (inscricao_estadual, cpf_socio, enviada_por, data_envio, assunto, 
                 classificacao, tributo, tipo_mensagem, numero_documento, vencimento, 
                 conteudo_mensagem)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                dados.get('inscricao_estadual'),
                dados.get('cpf_socio'),
                dados.get('enviada_por'),
                dados.get('data_envio'),
                dados.get('assunto'),
                dados.get('classificacao'),
                dados.get('tributo'),
                dados.get('tipo_mensagem'),
                dados.get('numero_documento'),
                dados.get('vencimento'),
                dados.get('conteudo_mensagem')
            ))
            
            conn.commit()
            conn.close()
            logger.info("💾 Mensagem salva no banco de dados")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar mensagem: {e}")

    async def check_and_open_sistemas_menu(self, page):
        """Verifica se o botão 'Sistemas' (ícone cog) está visível e abre o menu.

        Retorna True se o menu foi aberto, False caso contrário.
        """
        try:
            logger.info("Verificando menu 'Sistemas'...")
            
            # Tempo máximo de espera: 60 segundos
            max_wait_time = 60
            start_time = asyncio.get_event_loop().time()
            menu_check_interval = 2  # Verificar menu a cada 2 segundos
            
            # Loop de verificação: tenta encontrar o menu enquanto a página carrega
            while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
                # Verificar se o menu já está disponível
                menu_available = await page.evaluate("""
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
                
                if menu_available:
                    logger.info("Menu 'Sistemas' detectado e disponível antes da página carregar completamente!")
                    break
                
                # Aguardar um pouco antes de verificar novamente
                await page.wait_for_timeout(menu_check_interval * 1000)
                elapsed = asyncio.get_event_loop().time() - start_time
                logger.info(f"Aguardando menu... ({elapsed:.0f}s)")
            
            # Se demorou mais de 60 segundos, dar F5
            elapsed_total = asyncio.get_event_loop().time() - start_time
            if elapsed_total >= max_wait_time:
                logger.warning("⚠️ Página demorou mais de 60 segundos para carregar. Dando F5...")
                try:
                    await page.reload(wait_until="domcontentloaded", timeout=30000)
                    logger.info("✅ Página recarregada com sucesso")
                    await page.wait_for_timeout(self.random_delay(3000, 5000))
                    
                    # APÓS F5, VERIFICAR SE O MENU ESTÁ DISPONÍVEL AGORA
                    logger.info("🔄 Verificando se menu está disponível após F5...")
                    menu_available_after_reload = await page.evaluate("""
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
                    
                    if menu_available_after_reload:
                        logger.info("✅ Menu 'Sistemas' disponível após reload!")
                    else:
                        logger.warning("⚠️ Menu ainda não está disponível após reload")
                        # Aguardar mais um pouco
                        await page.wait_for_timeout(3000)
                        
                except Exception as reload_error:
                    logger.error(f"❌ Erro ao dar F5: {reload_error}")
                    # Continuar mesmo com erro no reload
            
            # Pequena pausa para estabilizar
            await page.wait_for_timeout(self.random_delay(500, 1000))
            
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
            
            # Primeiro, verificar se há algum modal ou alert visível
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
                    modal = await page.wait_for_selector(modal_sel, timeout=2000, state="visible")
                    if modal:
                        text = await modal.text_content()
                        if text and text.strip():
                            logger.info(f"Modal/alerta encontrado: {text[:100]}...")
                            subject = "Mensagem SEFAZ - modal/alerta"
                            body = text.strip()
                            sent = self.send_email(subject, body)
                            
                            # Tentar fechar o modal
                            closed = await self.close_modal(page, modal)
                            if closed:
                                return True
                except:
                    continue
            
            # Verificar mensagens na página
            message_selectors = [
                ".alert:not(.hide):not(.hidden)",
                ".notification",
                ".message",
                ".msg"
            ]

            for sel in message_selectors:
                try:
                    elements = await page.query_selector_all(sel)
                    for el in elements:
                        try:
                            is_visible = await el.is_visible()
                            if not is_visible:
                                continue
                                
                            text = await el.text_content()
                            if text and len(text.strip()) > 10:
                                logger.info(f"Mensagem encontrada: {text[:50]}...")
                                
                                # VERIFICAR SE É MENSAGEM DE SESSÃO ATIVA
                                if 'já está conectado' in text.lower() or 'outra sessão' in text.lower():
                                    logger.warning("⚠️  SESSÃO JÁ ABERTA DETECTADA!")
                                    logger.warning("   Mensagem: " + text.strip()[:100])
                                    
                                    # Retornar código especial para indicar sessão ativa
                                    # Isso vai acionar o retry no executar_consulta
                                    return "SESSION_CONFLICT"
                                
                                # Mensagem normal (não é sessão ativa)
                                subject = "Mensagem SEFAZ - ciência necessária"
                                body = text.strip()
                                sent = self.send_email(subject, body)
                                
                                # Tentar dar ciência
                                ack_given = await self.dar_ciencia_mensagem(page, el)
                                if ack_given:
                                    return True
                                
                                return sent
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

    async def handle_session_conflict(self, page):
        """Trata conflito de sessão ativa - clica em Sair e tenta novamente"""
        try:
            logger.info("Tratando conflito de sessão ativa...")
            
            # Capturar screenshot para análise
            await page.screenshot(path="debug_session_conflict.png")
            
            # Verificar se há mensagem de sessão ativa
            page_text = await page.text_content('body')
            if 'já está conectado' in page_text.lower() or 'outra sessão' in page_text.lower():
                logger.info("Detectada mensagem de sessão ativa")
                
                # PROCURAR LINK "SAIR" OU BOTÕES SIMILARES
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
                
                logger.info("Procurando link/botão 'Sair'...")
                for selector in sair_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            is_visible = await element.is_visible()
                            if is_visible:
                                logger.info(f"Encontrado '{selector}', clicando...")
                                await element.click()
                                await page.wait_for_timeout(2000)
                                
                                # Aguardar redirecionamento para login
                                try:
                                    await page.wait_for_load_state("networkidle", timeout=10000)
                                except:
                                    pass
                                
                                logger.info("Clicou em 'Sair', sessão anterior encerrada")
                                return True
                    except Exception as e:
                        logger.debug(f"Erro ao tentar {selector}: {e}")
                        continue
                
                # Se não encontrou link Sair, tentar JavaScript
                logger.info("Tentando encontrar 'Sair' via JavaScript...")
                sair_clicked = await page.evaluate("""
                    () => {
                        // Procurar todos os links e botões
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
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    logger.info("Clicou em 'Sair' via JavaScript")
                    return True
            
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

    async def click_conta_corrente(self, page, inscricao_estadual=None):
        """Navega através do menu completo para acessar Consultar Conta-Corrente Fiscal
        
        Args:
            page: Página do Playwright
            inscricao_estadual: Número da IE (opcional). Se fornecido, será usado no formulário
        """
        try:
            logger.info("="*80)
            logger.info("🚀 INICIANDO NAVEGAÇÃO PARA CONTA-CORRENTE FISCAL")
            logger.info("="*80)
            
            # ============================================================================
            # PASSO 1: CLICAR EM "TODAS AS ÁREAS DE NEGÓCIO"
            # ============================================================================
            logger.info("📍 PASSO 1: Procurando 'Todas as Áreas de Negócio'...")
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Debug: Verificar se o menu dropdown está aberto
            menu_aberto = await page.evaluate("""
                () => {
                    const dropdown = document.querySelector('.dropdown.open');
                    return dropdown !== null;
                }
            """)
            logger.info(f"   Menu dropdown aberto: {menu_aberto}")
            
            # Se não estiver aberto, tentar abrir
            if not menu_aberto:
                logger.warning("   Menu não está aberto, tentando abrir menu Sistemas...")
                menu_opened = await self.check_and_open_sistemas_menu(page)
                if not menu_opened:
                    logger.error("   ❌ Não foi possível abrir menu Sistemas")
                    return False
                await page.wait_for_timeout(1000)
            
            # Debug: Listar links disponíveis no dropdown
            links_visiveis = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('.dropdown-menu a');
                    return Array.from(links).map(a => ({
                        texto: a.textContent.trim(),
                        visivel: a.offsetParent !== null,
                        onclick: a.getAttribute('onclick')
                    }));
                }
            """)
            logger.info(f"   Links disponíveis: {[l['texto'] for l in links_visiveis if l['visivel']]}")
            
            # Procurar o botão "Todas as Áreas de Negócio"
            todas_areas_button = await page.query_selector("a:has-text('Todas as Áreas de Negócio')")
            if not todas_areas_button:
                todas_areas_button = await page.query_selector("a[onclick*=\"listMenu(document.menuForm,this,'all')\"]")
            
            if not todas_areas_button:
                logger.error("   ❌ Botão 'Todas as Áreas de Negócio' não encontrado")
                return False
            
            # Verificar visibilidade
            is_visible = await todas_areas_button.is_visible()
            logger.info(f"   Botão encontrado, visível: {is_visible}")
            
            if not is_visible:
                logger.warning("   Forçando visibilidade via JavaScript...")
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
                await self.human_click(page, todas_areas_button)
                logger.info("   ✅ Clicado em 'Todas as Áreas de Negócio'")
            except Exception as click_error:
                logger.warning(f"   Erro ao clicar: {click_error}")
                logger.info("   Tentando onclick via JavaScript...")
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
                    logger.error("   ❌ Não foi possível acionar onclick")
                    return False
                logger.info("   ✅ onclick acionado via JavaScript")
            
            # Aguardar carregamento
            logger.info("   ⏳ Aguardando carregamento da página...")
            try:
                await page.wait_for_load_state("networkidle", timeout=30000)
            except Exception as e:
                logger.warning(f"   Timeout no networkidle: {e}")
            
            url = page.url
            logger.info(f"   URL atual: {url}")
            
            if "listMenu.do" not in url:
                logger.warning(f"   ⚠️ URL não contém listMenu.do, tentando aguardar navegação...")
                try:
                    await page.wait_for_url("**/listMenu.do**", timeout=10000)
                    logger.info("   ✅ Navegação para listMenu.do detectada")
                except Exception as e:
                    logger.warning(f"   ⚠️ Não navegou para listMenu.do: {e}")
                    # Verificar se o conteúdo da página mudou
                    page_content = await page.content()
                    if "jstree" in page_content.lower():
                        logger.info("   ✅ Conteúdo jstree detectado na página")
                    else:
                        logger.error("   ❌ Página não carregou o menu jstree")
                        await page.screenshot(path="debug_listmenu_erro.png")
                        return False
            else:
                logger.info(f"   ✅ Página listMenu.do carregada")
            
            # Aguardar mais tempo para a árvore jstree carregar completamente
            await page.wait_for_timeout(self.random_delay(2000, 3500))
            
            # Aguardar especificamente pelo jstree carregar
            logger.info("   ⏳ Aguardando árvore jstree carregar...")
            try:
                await page.wait_for_selector(".jstree", timeout=10000)
                logger.info("   ✅ Árvore jstree carregada")
            except Exception as e:
                logger.warning(f"   ⚠️ jstree não detectado: {e}")
            
            # ============================================================================
            # PASSO 2: CLICAR EM "CONTA FISCAL"
            # ============================================================================
            logger.info("📍 PASSO 2: Procurando 'Conta Fiscal'...")
            
            # No jstree, precisamos clicar no ícone de expandir, não no texto
            # O link com classe "jstree-ocl" é para expandir/colapsar
            
            # Debug: Listar todos os nós disponíveis
            nos_disponiveis = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a.jstree-anchor');
                    return Array.from(links).map(a => ({
                        texto: a.textContent.trim(),
                        classes: a.className
                    }));
                }
            """)
            logger.info(f"   Nós jstree disponíveis: {[n['texto'] for n in nos_disponiveis[:20]]}")
            
            # Aguardar a árvore carregar
            await page.wait_for_timeout(1000)
            
            # Tentar clicar no nó "Conta Fiscal" para expandi-lo
            conta_fiscal_expandido = await page.evaluate("""
                () => {
                    // Procurar pelo nó que contém "Conta Fiscal"
                    const links = document.querySelectorAll('a.jstree-anchor');
                    for (let link of links) {
                        const texto = link.textContent.trim();
                        console.log('Verificando nó:', texto);
                        if (texto === 'Conta Fiscal') {
                            // Verificar se já está expandido
                            const li = link.closest('li');
                            if (li) {
                                console.log('LI encontrado:', li.id, 'Classes:', li.className);
                                const isOpen = li.classList.contains('jstree-open');
                                const isClosed = li.classList.contains('jstree-closed');
                                
                                console.log('isOpen:', isOpen, 'isClosed:', isClosed);
                                
                                if (isClosed) {
                                    // Precisa expandir - clicar no ícone
                                    const ocl = li.querySelector('.jstree-ocl');
                                    if (ocl) {
                                        console.log('Clicando no OCL para expandir');
                                        ocl.click();
                                        return 'expandido';
                                    } else {
                                        console.log('OCL não encontrado');
                                        return 'sem_ocl';
                                    }
                                } else if (isOpen) {
                                    console.log('Já está aberto');
                                    return 'ja_aberto';
                                } else {
                                    console.log('Estado desconhecido');
                                    // Tentar expandir mesmo assim
                                    const ocl = li.querySelector('.jstree-ocl');
                                    if (ocl) {
                                        ocl.click();
                                        return 'expandido_forcado';
                                    }
                                }
                            } else {
                                console.log('LI não encontrado para:', texto);
                            }
                        }
                    }
                    return 'nao_encontrado';
                }
            """)
            
            logger.info(f"   Status Conta Fiscal: {conta_fiscal_expandido}")
            
            if conta_fiscal_expandido == 'nao_encontrado':
                logger.error("   ❌ Nó 'Conta Fiscal' não encontrado")
                return False
            
            logger.info("   ✅ Nó 'Conta Fiscal' expandido/aberto")
            await page.wait_for_timeout(self.random_delay(2000, 3000))  # Aguardar submenu carregar completamente
            
            # ============================================================================
            # PASSO 3: CLICAR EM "CONSULTAR CONTA-CORRENTE FISCAL"
            # ============================================================================
            logger.info("📍 PASSO 3: Procurando 'Consultar Conta-Corrente Fiscal'...")
            await page.wait_for_timeout(self.random_delay(1000, 1500))
            
            # Debug: Listar todos os links visíveis após expandir Conta Fiscal
            links_visiveis = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a.jstree-anchor');
                    return Array.from(links)
                        .filter(a => {
                            const li = a.closest('li');
                            // Verificar se o nó não está oculto
                            return li && !li.classList.contains('jstree-hidden') && a.offsetParent !== null;
                        })
                        .map(a => ({
                            texto: a.textContent.trim(),
                            href: a.getAttribute('href'),
                            onclick: a.getAttribute('onclick'),
                            visivel: a.offsetParent !== null
                        }));
                }
            """)
            logger.info(f"   Total de links visíveis: {len(links_visiveis)}")
            logger.info(f"   Links visíveis: {[l['texto'] for l in links_visiveis[:20]]}")
            
            # Agora precisamos CLICAR no link "Consultar Conta-Corrente Fiscal" para navegar
            # Este link deve ter um onclick ou href que vai para a página
            consultar_clicado = await page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a.jstree-anchor');
                    console.log('Total de links jstree:', links.length);
                    
                    for (let link of links) {
                        const texto = link.textContent.trim();
                        const li = link.closest('li');
                        
                        // Verificar se está visível
                        const isVisible = li && !li.classList.contains('jstree-hidden') && link.offsetParent !== null;
                        
                        console.log('Link:', texto, '| Visível:', isVisible);
                        
                        // Buscar por variações do texto
                        if (isVisible && texto.toLowerCase().includes('consultar') && 
                            texto.toLowerCase().includes('conta') && 
                            texto.toLowerCase().includes('corrente')) {
                            console.log('✅ MATCH! Clicando em:', texto);
                            link.click();
                            return texto;
                        }
                    }
                    return null;
                }
            """)
            
            if not consultar_clicado:
                logger.warning("   ⚠️ Link não encontrado em jstree-anchor, tentando fallback...")
                # Tentar sem o jstree-anchor
                consultar_clicado = await page.evaluate("""
                    () => {
                        const links = document.querySelectorAll('a');
                        for (let link of links) {
                            const texto = link.textContent.trim();
                            if (texto.toLowerCase().includes('consultar') && 
                                texto.toLowerCase().includes('conta') && 
                                texto.toLowerCase().includes('corrente')) {
                                console.log('Clicando em (fallback):', texto);
                                link.click();
                                return texto;
                            }
                        }
                        return null;
                    }
                """)
                
                if not consultar_clicado:
                    logger.error("   ❌ Não foi possível encontrar o link")
                    await page.screenshot(path="debug_consultar_nao_encontrado.png")
                    with open("debug_consultar_page.html", "w", encoding="utf-8") as f:
                        f.write(await page.content())
                    return False
            
            logger.info(f"   ✅ Clicado em: '{consultar_clicado}'")
            
            # Aguardar carregamento
            logger.info("   ⏳ Aguardando carregamento da página...")
            try:
                await page.wait_for_load_state("networkidle", timeout=30000)
            except Exception as e:
                logger.warning(f"   Timeout no networkidle: {e}")
            
            await page.wait_for_timeout(self.random_delay(2000, 4000))
            
            # ============================================================================
            # PASSO 4: PREENCHER IE E CLICAR EM "CONTINUAR"
            # ============================================================================
            logger.info("📍 PASSO 4: Preenchendo IE e clicando em Continuar...")
            continuar_success = await self.click_continuar_button(page, inscricao_estadual)
            
            if continuar_success:
                logger.info("="*80)
                logger.info("✅ NAVEGAÇÃO COMPLETA COM SUCESSO!")
                logger.info("="*80)
                return True
            else:
                logger.warning("="*80)
                logger.warning("⚠️ Problema ao clicar em Continuar, mas pode estar na página correta")
                logger.warning("="*80)
                return True
                
        except Exception as e:
            logger.error("="*80)
            logger.error(f"❌ ERRO NA NAVEGAÇÃO: {e}")
            logger.error("="*80)
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def preencher_inscricao_estadual(self, page, inscricao_estadual=None):
        """Preenche o campo de Inscrição Estadual e clica no botão confirmar
        
        Args:
            page: Página do Playwright
            inscricao_estadual: Número da IE (opcional). Se None, não preenche mas retorna se campo existe
        
        Returns:
            True se IE foi preenchida e confirmada com sucesso
            False se campo não existe ou não foi possível preencher
        """
        try:
            # SALVAR SCREENSHOT E HTML ANTES DE VERIFICAR
            logger.info("💾 Salvando screenshot ANTES de verificar campo IE...")
            await page.screenshot(path="debug_antes_ie.png")
            page_content = await page.content()
            with open("debug_antes_ie.html", "w", encoding="utf-8") as f:
                f.write(page_content)
            logger.info(f"📏 Tamanho do HTML: {len(page_content)} bytes")
            
            # Verificar se o campo de inscrição estadual está presente
            logger.info("🔍 Procurando campo input[name='inscricaoEstadual']...")
            ie_input = await page.query_selector("input[name='inscricaoEstadual']")
            if not ie_input:
                logger.info("✅ Campo de Inscrição Estadual NÃO encontrado - CPF possui apenas uma IE")
                return False
            
            # Verificar se o campo está visível
            is_visible = await ie_input.is_visible()
            if not is_visible:
                logger.info("⚠️ Campo de Inscrição Estadual existe mas não está visível")
                return False
            
            logger.info("⚠️ Campo de Inscrição Estadual ENCONTRADO - CPF possui múltiplas IEs")
            
            # Se IE não foi fornecida, avisar mas tentar continuar
            if not inscricao_estadual:
                logger.warning("❌ ATENÇÃO: Campo de IE existe mas nenhuma IE foi fornecida!")
                logger.warning("⚠️ O sistema pode exigir a IE para prosseguir")
                logger.warning("💡 Forneça a IE usando o parâmetro 'inscricao_estadual'")
                await page.screenshot(path="debug_ie_campo_vazio.png")
                return False
            
            # Limpar a IE - remover pontos, traços e espaços (apenas números)
            ie_limpa = ''.join(filter(str.isdigit, str(inscricao_estadual)))
            logger.info(f"📝 IE fornecida: '{inscricao_estadual}' → IE limpa: '{ie_limpa}'")
            
            # Limpar o campo primeiro
            logger.info("🖱️ Clicando no campo de IE...")
            await ie_input.click()
            await page.wait_for_timeout(1000)  # Aumentado de 300-500 para 1000
            
            logger.info("🧹 Limpando campo...")
            await ie_input.fill("")
            await page.wait_for_timeout(500)  # Aumentado de 200-400 para 500
            
            # Preencher o campo com a inscrição estadual limpa (apenas números)
            logger.info(f"⌨️ Digitando IE: '{ie_limpa}'...")
            await ie_input.type(ie_limpa, delay=self.random_delay(50, 150))
            logger.info(f"✅ Inscrição Estadual '{ie_limpa}' digitada no campo")
            
            await page.wait_for_timeout(self.random_delay(500, 1000))
            
            # Procurar pelo botão de confirmar (ícone ic_confirmar.gif)
            logger.info("🔍 Procurando botão Confirmar (✓)...")
            confirmar_link = await page.query_selector("a[href*='recuperarDadosInscricaoEstadual']")
            if not confirmar_link:
                # Tentar pelo img
                confirmar_img = await page.query_selector("img[src*='ic_confirmar.gif']")
                if confirmar_img:
                    # Pegar o link pai
                    confirmar_link = await confirmar_img.evaluate_handle("element => element.closest('a')")
            
            if confirmar_link:
                logger.info("🖱️ Clicando no botão Confirmar (✓)...")
                await self.human_click(page, confirmar_link)
                logger.info("✅ Botão Confirmar clicado")
                
                # Aguardar processamento
                logger.info("⏳ Aguardando carregamento dos dados da IE...")
                await page.wait_for_timeout(self.random_delay(2000, 3000))
                
                # Verificar se a Razão Social foi preenchida (sinal de sucesso)
                logger.info("🔍 Verificando se Razão Social foi preenchida...")
                razao_social = await page.query_selector("input[name='razaoSocial']")
                if razao_social:
                    razao_value = await razao_social.get_attribute("value")
                    if razao_value and razao_value.strip():
                        logger.info(f"✅ IE CONFIRMADA COM SUCESSO!")
                        logger.info(f"🏢 Razão Social: {razao_value}")
                        return True
                    else:
                        logger.warning("⚠️ Razão Social não foi preenchida após confirmar IE")
                        logger.warning("⚠️ A IE pode estar incorreta ou inválida")
                        return False
                else:
                    logger.warning("⚠️ Campo Razão Social não encontrado")
                
                return True
            else:
                logger.error("❌ Botão de confirmar Inscrição Estadual não encontrado")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao preencher Inscrição Estadual: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def click_continuar_button(self, page, inscricao_estadual=None):
        """Procura e clica no botão Continuar na página de Conta Corrente
        
        Args:
            page: Página do Playwright
            inscricao_estadual: Número da IE (opcional). Se fornecido E campo existir, preenche antes de continuar
        """
        try:
            # Simular comportamento humano antes de procurar o botão
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            logger.info("="*80)
            logger.info("📋 VERIFICANDO NECESSIDADE DE PREENCHER INSCRIÇÃO ESTADUAL")
            logger.info("="*80)
            
            # SEMPRE tentar preencher IE se houver campo (verifica automaticamente)
            ie_preenchida = await self.preencher_inscricao_estadual(page, inscricao_estadual)
            
            if ie_preenchida:
                logger.info("="*80)
                logger.info("✅ INSCRIÇÃO ESTADUAL PREENCHIDA E CONFIRMADA")
                logger.info("="*80)
                logger.info("⏳ Aguardando estabilização antes de Continuar...")
                await page.wait_for_timeout(self.random_delay(2000, 3000))
            else:
                logger.info("="*80)
                logger.info("ℹ️ Campo de IE não existe ou não foi preenchido")
                logger.info("➡️ Prosseguindo diretamente para Continuar")
                logger.info("="*80)
            
            # Procurar pelo botão "Continuar" com diferentes seletores
            logger.info("🔍 Procurando botão 'Continuar'...")
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
                            logger.info(f"✅ Botão 'Continuar' encontrado!")
                            logger.info(f"🖱️ Clicando no botão...")
                            await self.human_click(page, button)
                            logger.info(f"✅ Botão 'Continuar' clicado via: {selector}")
                            
                            # Aguardar carregamento após clicar
                            logger.info("⏳ Aguardando carregamento da página de dados...")
                            await page.wait_for_load_state("networkidle", timeout=30000)
                            await page.wait_for_timeout(self.random_delay(2000, 3000))
                            
                            # Verificar se a página carregou corretamente
                            url_atual = page.url
                            logger.info(f"📍 URL após clicar em Continuar: {url_atual}")
                            
                            # Verificar se há conteúdo de dados na página
                            page_content = await page.content()
                            if "Inscrição Estadual" in page_content or "Situação Cadastral" in page_content:
                                logger.info("✅ Página de dados carregada com sucesso!")
                            else:
                                logger.warning("⚠️ Página pode não ter carregado corretamente")
                            
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
            
            # ============================================================================
            # NOVA VERIFICAÇÃO: Verificar tabela de TVIs com saldo devedor
            # ============================================================================
            logger.info("TVI: Verificando tabela com saldos devedores...")
            try:
                # Procurar por linhas da tabela que contenham saldo devedor
                tvi_rows = await page.query_selector_all("table.table.table-striped tbody tr")
                
                if tvi_rows and len(tvi_rows) > 0:
                    logger.info(f"TVI: Encontradas {len(tvi_rows)} linha(s) na tabela")
                    tem_divida = False
                    
                    for idx, row in enumerate(tvi_rows, 1):
                        try:
                            # Extrair todas as células da linha
                            cells = await row.query_selector_all("td")
                            
                            if len(cells) >= 6:  # Deve ter no mínimo 6 colunas
                                # Coluna 5 (índice 4) contém o saldo devedor
                                saldo_cell = cells[4]
                                saldo_text = await saldo_cell.text_content()
                                saldo_text = saldo_text.strip() if saldo_text else "0,00"
                                
                                # Coluna 6 (índice 5) contém a situação
                                situacao_cell = cells[5]
                                situacao_text = await situacao_cell.text_content()
                                situacao_text = situacao_text.strip().upper() if situacao_text else ""
                                
                                logger.info(f"   Linha {idx}: Saldo={saldo_text}, Situação={situacao_text}")
                                
                                # Verificar se saldo é diferente de 0,00
                                # Remover formatação para comparar (R$ 1.234,56 -> 1234.56)
                                saldo_limpo = saldo_text.replace("R$", "").replace(".", "").replace(",", ".").strip()
                                
                                try:
                                    saldo_valor = float(saldo_limpo)
                                    if saldo_valor > 0:
                                        logger.info(f"   ⚠️ TVI com saldo devedor: R$ {saldo_text}")
                                        tem_divida = True
                                        break  # Já encontrou TVI com dívida
                                    else:
                                        logger.info(f"   ✅ TVI sem saldo devedor (SALDO ZERO)")
                                except ValueError:
                                    logger.warning(f"   ⚠️ Não foi possível converter saldo: {saldo_text}")
                                    # Se não conseguir converter, verificar pela situação
                                    if "SALDO ZERO" not in situacao_text and "QUITADO" not in situacao_text:
                                        tem_divida = True
                                        break
                                        
                        except Exception as row_error:
                            logger.warning(f"   Erro ao processar linha {idx}: {row_error}")
                            continue
                    
                    if tem_divida:
                        logger.info("TVI: ❌ Encontradas TVIs com saldo devedor > 0")
                        return "SIM"
                    else:
                        logger.info("TVI: ✅ Todas as TVIs têm saldo zero")
                        return "NÃO"
                        
            except Exception as table_error:
                logger.warning(f"TVI: Erro ao verificar tabela de saldos: {table_error}")
                # Continuar com verificações tradicionais em caso de erro
            
            # ============================================================================
            # VERIFICAÇÕES TRADICIONAIS (mantidas como fallback)
            # ============================================================================
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
    
    async def human_click(self, page: Page, element) -> None:
        """
        Simula clique humano com movimento de mouse
        
        Args:
            page: Página do Playwright
            element: Elemento a ser clicado
            
        Note:
            - Clica em posição aleatória dentro do elemento
            - Fallback para clique normal em caso de erro
        """
        try:
            box = await element.bounding_box()
            if box:
                # Posição aleatória dentro do elemento
                x = box['x'] + self.random_delay(10, int(box['width'] - 10))
                y = box['y'] + self.random_delay(10, int(box['height'] - 10))
                
                # Mover e clicar
                await page.mouse.move(x, y)
                await page.wait_for_timeout(self.random_delay(100, 300))
                await page.mouse.click(x, y)
            else:
                await element.click()
        except Exception as e:
            logger.debug(f"⚠️ Erro no clique humano, usando fallback: {e}")
            await element.click()
    
    def random_delay(self, min_ms: int = DELAY_MIN_HUMAN, max_ms: int = DELAY_MAX_HUMAN) -> int:
        """
        Gera delay aleatório para simular comportamento humano
        
        Args:
            min_ms: Tempo mínimo em milissegundos
            max_ms: Tempo máximo em milissegundos
            
        Returns:
            int: Delay em milissegundos
        """
        import random
        return random.randint(min_ms, max_ms)
    
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
    
    async def fazer_logout(self, page: Page) -> bool:
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
            await page.wait_for_timeout(self.random_delay(1000, 2000))
            
            # Tentar diferentes seletores
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
                        # Se for imagem, clicar no link pai
                        if selector == "img[src*='exit.png']":
                            logout_link = await logout_element.evaluate_handle("img => img.closest('a')")
                            if logout_link:
                                await self.human_click(page, logout_link)
                            else:
                                await self.human_click(page, logout_element)
                        else:
                            await self.human_click(page, logout_element)
                        
                        logger.info(f"✅ Logout executado via: {selector}")
                        logout_success = True
                        break
                except Exception as e:
                    logger.debug(f"⚠️ Erro com seletor {selector}: {e}")
                    continue
            
            if logout_success:
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                    await page.wait_for_timeout(self.random_delay(1000, 2000))
                    
                    current_url = page.url
                    if "login" in current_url.lower() or "logoff" in current_url.lower():
                        logger.info("✅ Logout realizado com sucesso - redirecionado para login")
                    else:
                        logger.info(f"✅ Logout executado - URL: {current_url}")
                except Exception:
                    logger.info("✅ Logout executado (timeout no redirecionamento é normal)")
                
                return True
            else:
                logger.warning("⚠️ Botão de logout não encontrado")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro durante logout: {e}")
            return False

    
    async def executar_consulta(self, usuario=None, senha=None, inscricao_estadual=None, _retry=0):
        """Executa a consulta completa com retry automático se detectar sessão ativa
        
        Args:
            usuario: CPF do usuário
            senha: Senha do usuário
            inscricao_estadual: Inscrição Estadual (opcional) - usado quando há múltiplas IEs para um CPF
            _retry: Contador interno de tentativas (não usar manualmente)
        """
        
        # Limite de tentativas
        MAX_RETRIES = 2
        
        logger.info("=" * 80)
        logger.info(f"BOT - EXECUTAR_CONSULTA - Tentativa {_retry + 1}/{MAX_RETRIES + 1}")
        logger.info("=" * 80)
        logger.debug(f"   - Usuario recebido: '{usuario}'")
        logger.debug(f"   - Senha recebida: {'*' * len(senha) if senha else 'None'}")
        logger.debug(f"   - IE recebida: '{inscricao_estadual}'")
        logger.info("=" * 80)
        
        # Usar credenciais do .env se não fornecidas
        usuario = usuario or os.getenv('USUARIO')
        senha = senha or os.getenv('SENHA')
        
        logger.debug("BOT - APOS APLICAR DEFAULTS DO .ENV")
        logger.debug(f"   - Usuario final: '{usuario}'")
        logger.debug(f"   - Senha final: {'*' * len(senha) if senha else 'None'}")
        logger.info("=" * 80)
        
        if not usuario or not senha:
            logger.error("Credenciais não fornecidas")
            return None
        
        # Detectar Chrome do sistema
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        user_data_dir = None
        
        if os.path.exists(chrome_path):
            logger.info("🌐 Usando Chrome do sistema")
            # Note: user_data_dir seria usado aqui se necessário
            # user_data_dir = r"C:\path\to\chrome\profile"
        
        # Usar BrowserManager para gestão segura de recursos
        async with BrowserManager(headless=self.headless, user_data_dir=user_data_dir) as page:
            
            # Configurar scripts anti-detecção
            await self._setup_anti_detection(page)
            
            try:
                # Fazer login
                if await self.fazer_login(page, usuario, senha):
                    logger.info("Login bem-sucedido, capturando screenshot...")
                    await page.screenshot(path="debug_login_success.png")
                    
                    # Verificar se a página ainda está ativa
                    try:
                        current_url = page.url
                        page_title = await page.title()
                        logger.info(f"Página após login - URL: {current_url}, Título: {page_title}")
                    except Exception as e:
                        logger.error(f"Erro ao verificar página após login: {e}")
                        return None
                    
                    # Simular pausa humana após login
                    logger.info("Aguardando pausa pós-login...")
                    await page.wait_for_timeout(self.random_delay(2000, 4000))
                    
                    # Verificar novamente se página ainda está ativa
                    try:
                        current_url = page.url
                        logger.info(f"Página após pausa - URL: {current_url}")
                        await page.screenshot(path="debug_after_pause.png")
                    except Exception as e:
                        logger.error(f"Página foi fechada durante pausa: {e}")
                        return None
                    
                    # Após login, verificar se o menu 'Sistemas' está visível
                    menu_opened = await self.check_and_open_sistemas_menu(page)

                    if not menu_opened:
                        logger.warning("⚠️ Menu não foi aberto na primeira tentativa")
                        
                        # Verificar se há mensagem de sessão conflitante
                        processed = await self.handle_inbox_and_notify(page)
                        
                        # VERIFICAR SE É CONFLITO DE SESSÃO
                        if processed == "SESSION_CONFLICT":
                            logger.warning("🚫 SESSÃO JÁ ABERTA - Iniciando processo de retry")
                            logger.info("🔄 Navegador será fechado automaticamente pelo context manager...")
                            
                            # Se ainda tem tentativas disponíveis
                            if _retry < MAX_RETRIES:
                                logger.info(f"⏳ Aguardando 5 segundos para sessão anterior expirar...")
                                await asyncio.sleep(5)
                                logger.info(f"🔄 RETRY {_retry + 2}/{MAX_RETRIES + 1} - Tentando novamente...")
                                return await self.executar_consulta(usuario, senha, inscricao_estadual, _retry + 1)
                            else:
                                logger.error("❌ Número máximo de tentativas atingido")
                                logger.error("💡 Aguarde alguns minutos e tente novamente")
                                return None
                        
                        # Processar mensagens que precisam de ciência
                        logger.info("📬 Verificando se há mensagens que precisam de ciência...")
                        cpf_limpo = SEFAZValidator.limpar_cpf(usuario) if usuario else ""
                        mensagens_processadas = await self.processar_mensagens_ciencia(page, cpf_limpo)
                        
                        if mensagens_processadas:
                            logger.info("✅ Mensagens processadas, tentando abrir menu novamente")
                            await page.wait_for_timeout(self.random_delay(1000, 2000))
                            menu_opened = await self.check_and_open_sistemas_menu(page)
                        else:
                            # Se não processou mensagem, tentar abrir menu novamente (pode ter sido F5)
                            logger.info("🔄 Tentando abrir menu novamente após falha inicial...")
                            await page.wait_for_timeout(self.random_delay(2000, 3000))
                            menu_opened = await self.check_and_open_sistemas_menu(page)

                    if menu_opened:
                        # Com o menu aberto, navegar até Conta Corrente
                        logger.info("🚀 Navegando para Conta Corrente com IE: %s", inscricao_estadual if inscricao_estadual else "NÃO FORNECIDA")
                        ok = await self.click_conta_corrente(page, inscricao_estadual)
                        if not ok:
                            logger.error("❌ Não foi possível acessar 'Conta Corrente'")
                            return None
                        logger.info("✅ Navegação para Conta Corrente concluída")
                    else:
                        # Se ainda não conseguiu abrir menu, tentar acesso direto
                        logger.info("🔄 Tentando acesso direto sem menu")
                        ok = await self.try_direct_conta_corrente_access(page)
                        if not ok:
                            logger.error("❌ Não foi possível acessar Conta Corrente nem por menu nem diretamente")
                            return None

                    # Extrair dados da página Conta Corrente
                    logger.info("="*80)
                    logger.info("📊 INICIANDO EXTRAÇÃO DE DADOS DA CONTA CORRENTE")
                    logger.info("="*80)
                    dados = await self.extrair_dados(page)

                    # Salvar no banco
                    if dados:
                        logger.info("="*80)
                        logger.info("✅ DADOS EXTRAÍDOS COM SUCESSO!")
                        logger.info("="*80)
                        for chave, valor in dados.items():
                            logger.info(f"   {chave}: {valor}")
                        logger.info("="*80)
                        
                        self.salvar_resultado(dados)
                        logger.info("💾 Dados salvos no banco de dados")
                        
                        # Realizar logout antes de finalizar
                        logger.info("🚪 Realizando logout...")
                        await self.fazer_logout(page)
                        
                        logger.info("🎉 CONSULTA CONCLUÍDA COM SUCESSO!")
                        return dados
                    else:
                        logger.warning("="*80)
                        logger.warning("⚠️ NENHUM DADO FOI EXTRAÍDO")
                        logger.warning("="*80)
                        # Tentar logout mesmo sem dados
                        await self.fazer_logout(page)
                        return None
                else:
                    logger.error("Falha no login")
                    return None
                    
            except Exception as e:
                logger.error(f"Erro na execução: {e}")
                return None
            # Navegador será fechado automaticamente ao sair do context manager
    
    async def _setup_anti_detection(self, page: Page):
        """Configura scripts anti-detecção no navegador"""
        await page.add_init_script("""
            // Remover webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Sobrescrever chrome runtime
            window.chrome = {
                runtime: {}
            };
            
            // Adicionar propriedades reais do navigator
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en'],
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: ""},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    }
                ],
            });
            
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
            });
            
            Object.defineProperty(navigator, 'vendor', {
                get: () => 'Google Inc.',
            });
            
            // Adicionar permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Sobrescrever toString para esconder traces
            const modifiedNavigator = Navigator.prototype;
            Object.getOwnPropertyNames(modifiedNavigator).forEach(prop => {
                if (prop !== 'userAgent') {
                    try {
                        const original = modifiedNavigator[prop];
                        modifiedNavigator.__defineGetter__(prop, function() {
                            if (prop === 'webdriver') return undefined;
                            return original;
                        });
                    } catch (e) {}
                }
            });
        """)

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