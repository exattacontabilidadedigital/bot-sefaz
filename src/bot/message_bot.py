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
            
            # Configurar opções do navegador
            launch_options = {
                'headless': self.headless,
                'args': [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials'
                ]
            }
            
            self.browser = await self.playwright.chromium.launch(**launch_options)
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
                
                # Etapa 2: Navegar para sistemas/mensagens
                logger.info("🧭 Etapa 2/4: Navegando para área de mensagens...")
                
                # Abrir menu sistemas
                menu_opened = await self.navigator.open_sistemas_menu(page)
                if not menu_opened:
                    raise NavigationException("Não foi possível abrir menu Sistemas")
                
                # Navegar para todas as áreas de negócio
                areas_clicked = await self.navigator.click_todas_areas_negocio(page)
                if not areas_clicked:
                    raise NavigationException("Não foi possível acessar Todas as Áreas de Negócio")
                
                logger.info("✅ Navegação para área de mensagens concluída")
                
                # Etapa 3: Processar mensagens
                logger.info("📨 Etapa 3/4: Processando mensagens...")
                
                mensagens_processadas = await self.message_processor.processar_todas_mensagens(
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
                    'mensagem': f'Processamento concluído: {mensagens_processadas} mensagem(ns) processada(s)',
                    'detalhes': {
                        'empresa': inscricao_estadual,
                        'mensagens': mensagens_processadas,
                        'login_ok': True,
                        'navegacao_ok': True,
                        'processamento_ok': True,
                        'logout_ok': True
                    }
                })
                
                logger.info("=" * 80)
                logger.info("🎉 MessageBot - PROCESSAMENTO CONCLUÍDO COM SUCESSO")
                logger.info(f"   - Mensagens processadas: {mensagens_processadas}")
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
            log_exception_details(logger, e, "MessageBot")
            
            # Criar mensagem amigável
            error_message = create_user_friendly_error_message(e, "processamento de mensagens")
            
            resultado.update({
                'mensagem': error_message,
                'detalhes': {'erro_tipo': 'geral', 'erro_detalhes': str(e)}
            })
            
            raise ExtractionException(f"Erro inesperado durante processamento: {e}") from e
    
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
                        COUNT(CASE WHEN data_criacao >= datetime('now', '-1 day') THEN 1 END) as hoje,
                        COUNT(CASE WHEN data_criacao >= datetime('now', '-7 days') THEN 1 END) as semana
                    FROM mensagens_sefaz 
                    WHERE inscricao_estadual = ?
                """, (inscricao_estadual,))
            else:
                # Estatísticas globais
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN data_criacao >= datetime('now', '-1 day') THEN 1 END) as hoje,
                        COUNT(CASE WHEN data_criacao >= datetime('now', '-7 days') THEN 1 END) as semana
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