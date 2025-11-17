"""
Sistema de exceções customizadas do Bot SEFAZ.

Contém todas as exceções específicas do domínio e mensagens de erro
amigáveis para o usuário.
"""

from .base import (
    # Exceções base
    SEFAZBotException,
    ValidationException,
    
    # Exceções de autenticação
    LoginFailedException,
    SessionConflictException,
    SessionExpiredException,
    InvalidCPFException,
    InvalidIEException,
    InvalidPasswordException,
    
    # Exceções de navegação
    NavigationException,
    MenuNotFoundException,
    ElementNotFoundException,
    PageLoadException,
    
    # Exceções de extração
    ExtractionException,
    
    # Exceções de timeout
    TimeoutException,
    
    # Exceções de browser
    BrowserException,
    BrowserLaunchException,
    BrowserCloseException,
    
    # Exceções de banco de dados
    DatabaseException,
    ConnectionException,
    QueryException,
    DuplicateException,
    
    # Exceções de criptografia
    CryptographyException,
    DecryptionException,
    EncryptionException,
    MissingKeyException,
    
    # Exceções de captcha
    CaptchaException,
    
    # Funções auxiliares
    is_session_conflict_message,
    create_user_friendly_error_message,
    log_exception_details,
)

from .error_messages import (
    get_user_friendly_error_message,
    get_error_category,
)

__all__ = [
    # Exceções
    'SEFAZBotException',
    'ValidationException',
    'LoginFailedException',
    'SessionConflictException',
    'SessionExpiredException',
    'InvalidCPFException',
    'InvalidIEException',
    'InvalidPasswordException',
    'NavigationException',
    'MenuNotFoundException',
    'ElementNotFoundException',
    'PageLoadException',
    'ExtractionException',
    'TimeoutException',
    'BrowserException',
    'BrowserLaunchException',
    'BrowserCloseException',
    'DatabaseException',
    'ConnectionException',
    'QueryException',
    'DuplicateException',
    'CryptographyException',
    'DecryptionException',
    'EncryptionException',
    'MissingKeyException',
    'CaptchaException',
    'is_session_conflict_message',
    'create_user_friendly_error_message',
    'log_exception_details',
    
    # Mensagens de erro
    'get_user_friendly_error_message',
    'get_error_category',
]
