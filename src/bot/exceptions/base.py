"""
Exceções customizadas melhoradas para o bot SEFAZ.

Este módulo define hierarquia de exceções mais específicas e com melhor
rastreabilidade para diferentes tipos de erro.
"""

from typing import Optional


class SEFAZBotException(Exception):
    """Exceção base para todas as exceções do bot SEFAZ"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[str] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details
        self.message = message
    
    def __str__(self) -> str:
        parts = [self.message]
        if self.error_code:
            parts.append(f"[Código: {self.error_code}]")
        if self.details:
            parts.append(f"Detalhes: {self.details}")
        return " - ".join(parts)


# ============================================================================
# EXCEÇÕES DE VALIDAÇÃO
# ============================================================================

class ValidationException(SEFAZBotException):
    """Exceção para erros de validação de dados"""
    pass


class InvalidCPFException(ValidationException):
    """CPF inválido ou malformado"""
    
    def __init__(self, cpf: str, reason: str = "formato inválido"):
        message = f"CPF inválido: {cpf}"
        super().__init__(message, "CPF_INVALID", reason)


class InvalidIEException(ValidationException):
    """Inscrição Estadual inválida"""
    
    def __init__(self, ie: str, reason: str = "formato inválido"):
        message = f"IE inválida: {ie}"
        super().__init__(message, "IE_INVALID", reason)


class InvalidPasswordException(ValidationException):
    """Senha inválida ou muito fraca"""
    
    def __init__(self, reason: str = "senha não atende critérios"):
        message = "Senha inválida"
        super().__init__(message, "PASSWORD_INVALID", reason)


# ============================================================================
# EXCEÇÕES DE NAVEGADOR
# ============================================================================

class BrowserException(SEFAZBotException):
    """Exceção base para problemas do navegador"""
    pass


class BrowserLaunchException(BrowserException):
    """Falha ao iniciar o navegador"""
    
    def __init__(self, message: str, browser_type: str = "chromium"):
        super().__init__(f"Falha ao iniciar navegador {browser_type}: {message}", "BROWSER_LAUNCH_FAILED")


class BrowserCloseException(BrowserException):
    """Falha ao fechar o navegador"""
    
    def __init__(self, message: str):
        super().__init__(f"Falha ao fechar navegador: {message}", "BROWSER_CLOSE_FAILED")


class PageLoadException(BrowserException):
    """Falha no carregamento de página"""
    
    def __init__(self, url: str, message: str, timeout_seconds: Optional[int] = None):
        details = f"URL: {url}"
        if timeout_seconds:
            details += f" | Timeout: {timeout_seconds}s"
        super().__init__(f"Falha ao carregar página: {message}", "PAGE_LOAD_FAILED", details)


# ============================================================================
# EXCEÇÕES DE AUTENTICAÇÃO
# ============================================================================

class AuthenticationException(SEFAZBotException):
    """Exceção base para problemas de autenticação"""
    pass


class LoginFailedException(AuthenticationException):
    """Falha no processo de login"""
    
    def __init__(self, message: str, username: Optional[str] = None, step: Optional[str] = None):
        details = []
        if username:
            details.append(f"Usuário: {username}")
        if step:
            details.append(f"Etapa: {step}")
        
        super().__init__(f"Falha no login: {message}", "LOGIN_FAILED", " | ".join(details))


class SessionConflictException(AuthenticationException):
    """Sessão já ativa ou conflito de sessão"""
    
    def __init__(self, message: str = "Sessão já está ativa"):
        super().__init__(message, "SESSION_CONFLICT", "Aguarde alguns minutos ou encerre a sessão anterior")


class SessionExpiredException(AuthenticationException):
    """Sessão expirou durante o uso"""
    
    def __init__(self, message: str = "Sessão expirou"):
        super().__init__(message, "SESSION_EXPIRED", "Necessário fazer login novamente")


class CaptchaException(AuthenticationException):
    """CAPTCHA encontrado e não pode ser resolvido automaticamente"""
    
    def __init__(self, message: str = "CAPTCHA detectado"):
        super().__init__(message, "CAPTCHA_REQUIRED", "Intervenção manual necessária")


# ============================================================================
# EXCEÇÕES DE NAVEGAÇÃO
# ============================================================================

class NavigationException(SEFAZBotException):
    """Exceção base para problemas de navegação"""
    pass


class MenuNotFoundException(NavigationException):
    """Menu esperado não foi encontrado"""
    
    def __init__(self, menu_name: str, page_url: Optional[str] = None):
        message = f"Menu não encontrado: {menu_name}"
        details = f"URL: {page_url}" if page_url else None
        super().__init__(message, "MENU_NOT_FOUND", details)


class ElementNotFoundException(NavigationException):
    """Elemento esperado não foi encontrado na página"""
    
    def __init__(self, selector: str, element_type: str = "elemento", timeout: Optional[int] = None):
        message = f"{element_type.title()} não encontrado"
        details = f"Seletor: {selector}"
        if timeout:
            details += f" | Timeout: {timeout}s"
        super().__init__(message, "ELEMENT_NOT_FOUND", details)


class TimeoutException(NavigationException):
    """Operação excedeu tempo limite"""
    
    def __init__(self, operation: str, timeout_seconds: int, details: Optional[str] = None):
        message = f"Timeout na operação: {operation}"
        timeout_details = f"Limite: {timeout_seconds}s"
        if details:
            timeout_details += f" | {details}"
        super().__init__(message, "OPERATION_TIMEOUT", timeout_details)


# ============================================================================
# EXCEÇÕES DE EXTRAÇÃO DE DADOS
# ============================================================================

class ExtractionException(SEFAZBotException):
    """Exceção base para problemas de extração de dados"""
    pass


class DataNotFoundException(ExtractionException):
    """Dados esperados não foram encontrados"""
    
    def __init__(self, data_type: str, page_context: Optional[str] = None):
        message = f"Dados não encontrados: {data_type}"
        super().__init__(message, "DATA_NOT_FOUND", page_context)


class DataParsingException(ExtractionException):
    """Erro ao fazer parsing dos dados extraídos"""
    
    def __init__(self, data_type: str, raw_data: Optional[str] = None, parsing_error: Optional[str] = None):
        message = f"Erro ao processar dados: {data_type}"
        details = []
        if raw_data:
            details.append(f"Dados brutos: {raw_data[:100]}...")
        if parsing_error:
            details.append(f"Erro: {parsing_error}")
        super().__init__(message, "DATA_PARSING_FAILED", " | ".join(details))


# ============================================================================
# EXCEÇÕES DE BANCO DE DADOS
# ============================================================================

class DatabaseException(SEFAZBotException):
    """Exceção base para problemas de banco de dados"""
    pass


class ConnectionException(DatabaseException):
    """Falha na conexão com banco de dados"""
    
    def __init__(self, db_path: str, error_details: str):
        message = "Falha na conexão com banco de dados"
        super().__init__(message, "DB_CONNECTION_FAILED", f"Caminho: {db_path} | Erro: {error_details}")


class QueryException(DatabaseException):
    """Erro na execução de query SQL"""
    
    def __init__(self, query: str, error_details: str):
        message = "Erro na execução de query"
        super().__init__(message, "QUERY_EXECUTION_FAILED", f"Query: {query[:100]}... | Erro: {error_details}")


class DuplicateException(DatabaseException):
    """Tentativa de inserir registro duplicado"""
    
    def __init__(self, table: str, key_field: Optional[str] = None, key_value: Optional[str] = None):
        message = f"Registro duplicado na tabela {table}"
        details = None
        if key_field and key_value:
            details = f"Campo: {key_field} | Valor: {key_value}"
        super().__init__(message, "DUPLICATE_RECORD", details)


# ============================================================================
# EXCEÇÕES DE CRIPTOGRAFIA
# ============================================================================

class CryptographyException(SEFAZBotException):
    """Exceção base para problemas de criptografia"""
    pass


class EncryptionException(CryptographyException):
    """Falha na criptografia de dados"""
    
    def __init__(self, data_type: str = "dados"):
        message = f"Falha ao criptografar {data_type}"
        super().__init__(message, "ENCRYPTION_FAILED")


class DecryptionException(CryptographyException):
    """Falha na descriptografia de dados"""
    
    def __init__(self, data_type: str = "dados"):
        message = f"Falha ao descriptografar {data_type}"
        super().__init__(message, "DECRYPTION_FAILED")


class MissingKeyException(CryptographyException):
    """Chave de criptografia não encontrada"""
    
    def __init__(self, key_type: str = "chave"):
        message = f"Chave não encontrada: {key_type}"
        super().__init__(message, "KEY_NOT_FOUND")


# ============================================================================
# EXCEÇÕES DE RETRY
# ============================================================================

class RetryExhaustedException(SEFAZBotException):
    """Esgotadas todas as tentativas de retry"""
    
    def __init__(self, operation: str, max_attempts: int, last_error: Optional[str] = None):
        message = f"Esgotadas {max_attempts} tentativas para: {operation}"
        super().__init__(message, "RETRY_EXHAUSTED", last_error)


# ============================================================================
# EXCEÇÕES DE REDE
# ============================================================================

class NetworkException(SEFAZBotException):
    """Exceção base para problemas de rede"""
    pass


class ConnectionTimeoutException(NetworkException):
    """Timeout de conexão de rede"""
    
    def __init__(self, url: str, timeout_seconds: int):
        message = "Timeout de conexão"
        super().__init__(message, "CONNECTION_TIMEOUT", f"URL: {url} | Timeout: {timeout_seconds}s")


class ServerErrorException(NetworkException):
    """Erro do servidor (5xx)"""
    
    def __init__(self, status_code: int, url: str, response_text: Optional[str] = None):
        message = f"Erro do servidor: {status_code}"
        details = f"URL: {url}"
        if response_text:
            details += f" | Resposta: {response_text[:200]}..."
        super().__init__(message, "SERVER_ERROR", details)


class ClientErrorException(NetworkException):
    """Erro do cliente (4xx)"""
    
    def __init__(self, status_code: int, url: str):
        message = f"Erro do cliente: {status_code}"
        super().__init__(message, "CLIENT_ERROR", f"URL: {url}")


# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================

def is_session_conflict_message(text: str) -> bool:
    """
    Verifica se uma mensagem indica conflito de sessão
    
    Args:
        text: Texto a ser verificado
        
    Returns:
        bool: True se indica conflito de sessão
    """
    if not text:
        return False
    
    text_lower = text.lower()
    conflict_indicators = [
        'já está conectado',
        'outra sessão',
        'sessão ativa',
        'usuário logado',
        'login simultâneo',
        'multiple sessions',
        'session conflict'
    ]
    
    return any(indicator in text_lower for indicator in conflict_indicators)


def create_user_friendly_error_message(exception: SEFAZBotException) -> str:
    """
    Cria mensagem de erro amigável para o usuário final
    
    Args:
        exception: Exceção do bot SEFAZ
        
    Returns:
        str: Mensagem amigável para o usuário
    """
    error_messages = {
        "CPF_INVALID": "❌ CPF inválido. Verifique o formato (000.000.000-00).",
        "IE_INVALID": "❌ Inscrição Estadual inválida. Verifique o número.",
        "PASSWORD_INVALID": "❌ Senha inválida. Verifique se atende aos critérios.",
        "BROWSER_LAUNCH_FAILED": "❌ Não foi possível iniciar o navegador. Verifique se o Chrome está instalado.",
        "PAGE_LOAD_FAILED": "❌ Página não carregou. Verifique sua conexão com a internet.",
        "LOGIN_FAILED": "❌ Falha no login. Verifique suas credenciais.",
        "SESSION_CONFLICT": "⚠️ Você já está logado em outra sessão. Aguarde alguns minutos.",
        "SESSION_EXPIRED": "⚠️ Sua sessão expirou. Faça login novamente.",
        "CAPTCHA_REQUIRED": "🔍 CAPTCHA detectado. Intervenção manual necessária.",
        "MENU_NOT_FOUND": "❌ Menu não encontrado. O site pode ter mudado.",
        "ELEMENT_NOT_FOUND": "❌ Elemento não encontrado na página.",
        "OPERATION_TIMEOUT": "⏰ Operação demorou muito tempo. Tente novamente.",
        "DATA_NOT_FOUND": "❌ Dados não encontrados na página.",
        "DB_CONNECTION_FAILED": "❌ Erro no banco de dados. Contate o suporte.",
        "DUPLICATE_RECORD": "⚠️ Registro já existe no banco de dados.",
        "RETRY_EXHAUSTED": "❌ Máximo de tentativas atingido. Tente mais tarde.",
        "CONNECTION_TIMEOUT": "❌ Timeout de conexão. Verifique sua internet.",
        "SERVER_ERROR": "❌ Erro no servidor SEFAZ. Tente mais tarde."
    }
    
    return error_messages.get(exception.error_code, f"❌ Erro: {exception.message}")


def log_exception_details(exception: SEFAZBotException, logger) -> None:
    """
    Loga detalhes completos de uma exceção para debug
    
    Args:
        exception: Exceção a ser logada
        logger: Logger para saída
    """
    logger.error(f"=== ERRO DETALHADO ===")
    logger.error(f"Tipo: {type(exception).__name__}")
    logger.error(f"Código: {exception.error_code}")
    logger.error(f"Mensagem: {exception.message}")
    if exception.details:
        logger.error(f"Detalhes: {exception.details}")
    logger.error(f"=====================")