"""
Decorator @retry para retry automático inteligente
"""
import asyncio
import functools
import logging
from typing import Callable, Type, Union, Tuple, Optional, List
import time
from bot_validators import (
    SEFAZBotException,
    TimeoutException,
    PageLoadException,
    NavigationException,
    BrowserLaunchException,
    DatabaseException,
    ConnectionException,
    SessionExpiredException,
    CaptchaException,
    # Exceções que NÃO devem ter retry
    ValidationException,
    InvalidCPFException,
    InvalidIEException,
    InvalidPasswordException,
    LoginFailedException,
    SessionConflictException,
    DuplicateException
)

logger = logging.getLogger(__name__)

# Exceções que devem ter retry (erros temporários)
RETRYABLE_EXCEPTIONS = (
    TimeoutException,
    PageLoadException,
    NavigationException,
    ConnectionException,
    SessionExpiredException,
    TimeoutError,  # Python built-in
    ConnectionError,  # Python built-in
    OSError,  # Erros de I/O temporários
)

# Exceções que NÃO devem ter retry (erros permanentes)
NON_RETRYABLE_EXCEPTIONS = (
    ValidationException,
    InvalidCPFException,
    InvalidIEException,
    InvalidPasswordException,
    LoginFailedException,
    SessionConflictException,
    DuplicateException,
    CaptchaException,
    PermissionError,
    FileNotFoundError,
)


class RetryExhaustedException(SEFAZBotException):
    """Exceção lançada quando todas as tentativas de retry foram esgotadas"""
    pass


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    max_delay: float = 60.0,
    on: Optional[Union[Type[Exception], Tuple[Type[Exception], ...]]] = None,
    exclude: Optional[Union[Type[Exception], Tuple[Type[Exception], ...]]] = None,
    jitter: bool = True,
    on_retry: Optional[Callable] = None,
    raise_on_exhausted: bool = True
):
    """
    Decorator para retry automático com backoff exponencial
    
    Args:
        max_attempts: Número máximo de tentativas (incluindo a primeira)
        delay: Delay inicial entre tentativas (segundos)
        backoff: Fator de multiplicação do delay a cada tentativa (exponencial)
        max_delay: Delay máximo entre tentativas (segundos)
        on: Exceções que devem ter retry (None = usar RETRYABLE_EXCEPTIONS padrão)
        exclude: Exceções que NÃO devem ter retry
        jitter: Adicionar jitter aleatório ao delay (evita thundering herd)
        on_retry: Callback chamado antes de cada retry: on_retry(attempt, exception, delay)
        raise_on_exhausted: Se True, lança RetryExhaustedException após esgotar tentativas
    
    Returns:
        Decorator function
        
    Example:
        @retry(max_attempts=3, delay=2, backoff=2)
        async def fazer_consulta():
            # Retry automático em TimeoutException, PageLoadException, etc.
            pass
        
        @retry(on=(TimeoutError,), max_attempts=5, delay=1)
        async def operacao_rapida():
            # Retry apenas em TimeoutError
            pass
    """
    # Determinar quais exceções devem ter retry
    if on is not None:
        # Usar exceções fornecidas explicitamente
        retryable = on if isinstance(on, tuple) else (on,)
    else:
        # Usar padrão
        retryable = RETRYABLE_EXCEPTIONS
    
    # Determinar quais exceções devem ser excluídas
    if exclude is not None:
        excluded = exclude if isinstance(exclude, tuple) else (exclude,)
    else:
        excluded = NON_RETRYABLE_EXCEPTIONS
    
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    # Tentar executar a função
                    result = await func(*args, **kwargs)
                    
                    # Se chegou aqui, sucesso!
                    if attempt > 1:
                        logger.info(f"✅ {func.__name__} sucesso na tentativa {attempt}/{max_attempts}")
                    
                    return result
                    
                except excluded as e:
                    # Exceção não-retryable - não fazer retry
                    logger.warning(f"🚫 {func.__name__}: Exceção não-retryable: {type(e).__name__}: {e}")
                    raise
                    
                except retryable as e:
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        # Esgotou tentativas
                        logger.error(
                            f"❌ {func.__name__}: Esgotadas {max_attempts} tentativas. "
                            f"Última exceção: {type(e).__name__}: {e}"
                        )
                        
                        if raise_on_exhausted:
                            raise RetryExhaustedException(
                                f"Esgotadas {max_attempts} tentativas em {func.__name__}. "
                                f"Última exceção: {type(e).__name__}: {e}"
                            ) from e
                        else:
                            raise
                    
                    # Calcular delay para próxima tentativa
                    current_delay = min(delay * (backoff ** (attempt - 1)), max_delay)
                    
                    # Adicionar jitter (variação aleatória)
                    if jitter:
                        import random
                        current_delay = current_delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"⚠️ {func.__name__}: Tentativa {attempt}/{max_attempts} falhou. "
                        f"Exceção: {type(e).__name__}: {e}. "
                        f"Retry em {current_delay:.1f}s..."
                    )
                    
                    # Chamar callback se fornecido
                    if on_retry:
                        try:
                            if asyncio.iscoroutinefunction(on_retry):
                                await on_retry(attempt, e, current_delay)
                            else:
                                on_retry(attempt, e, current_delay)
                        except Exception as callback_error:
                            logger.warning(f"⚠️ Erro no callback on_retry: {callback_error}")
                    
                    # Aguardar antes de retry
                    await asyncio.sleep(current_delay)
                    
                except Exception as e:
                    # Exceção não esperada - não fazer retry por segurança
                    logger.error(
                        f"❌ {func.__name__}: Exceção não esperada (sem retry): "
                        f"{type(e).__name__}: {e}"
                    )
                    raise
            
            # Não deveria chegar aqui, mas por segurança
            if last_exception:
                raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    # Tentar executar a função
                    result = func(*args, **kwargs)
                    
                    # Se chegou aqui, sucesso!
                    if attempt > 1:
                        logger.info(f"✅ {func.__name__} sucesso na tentativa {attempt}/{max_attempts}")
                    
                    return result
                    
                except excluded as e:
                    # Exceção não-retryable - não fazer retry
                    logger.warning(f"🚫 {func.__name__}: Exceção não-retryable: {type(e).__name__}: {e}")
                    raise
                    
                except retryable as e:
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        # Esgotou tentativas
                        logger.error(
                            f"❌ {func.__name__}: Esgotadas {max_attempts} tentativas. "
                            f"Última exceção: {type(e).__name__}: {e}"
                        )
                        
                        if raise_on_exhausted:
                            raise RetryExhaustedException(
                                f"Esgotadas {max_attempts} tentativas em {func.__name__}. "
                                f"Última exceção: {type(e).__name__}: {e}"
                            ) from e
                        else:
                            raise
                    
                    # Calcular delay para próxima tentativa
                    current_delay = min(delay * (backoff ** (attempt - 1)), max_delay)
                    
                    # Adicionar jitter (variação aleatória)
                    if jitter:
                        import random
                        current_delay = current_delay * (0.5 + random.random())
                    
                    logger.warning(
                        f"⚠️ {func.__name__}: Tentativa {attempt}/{max_attempts} falhou. "
                        f"Exceção: {type(e).__name__}: {e}. "
                        f"Retry em {current_delay:.1f}s..."
                    )
                    
                    # Chamar callback se fornecido
                    if on_retry:
                        try:
                            on_retry(attempt, e, current_delay)
                        except Exception as callback_error:
                            logger.warning(f"⚠️ Erro no callback on_retry: {callback_error}")
                    
                    # Aguardar antes de retry
                    time.sleep(current_delay)
                    
                except Exception as e:
                    # Exceção não esperada - não fazer retry por segurança
                    logger.error(
                        f"❌ {func.__name__}: Exceção não esperada (sem retry): "
                        f"{type(e).__name__}: {e}"
                    )
                    raise
            
            # Não deveria chegar aqui, mas por segurança
            if last_exception:
                raise last_exception
        
        # Retornar wrapper apropriado (async ou sync)
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Atalhos para casos comuns
def retry_on_timeout(max_attempts: int = 3, delay: float = 2.0):
    """Atalho para retry apenas em TimeoutException e TimeoutError"""
    return retry(
        max_attempts=max_attempts,
        delay=delay,
        backoff=2.0,
        on=(TimeoutException, TimeoutError),
        jitter=True
    )


def retry_on_network(max_attempts: int = 3, delay: float = 5.0):
    """Atalho para retry em erros de rede/navegação"""
    return retry(
        max_attempts=max_attempts,
        delay=delay,
        backoff=2.0,
        on=(TimeoutException, PageLoadException, NavigationException, ConnectionError),
        jitter=True
    )


def retry_on_database(max_attempts: int = 3, delay: float = 1.0):
    """Atalho para retry em erros de banco de dados (exceto duplicados)"""
    return retry(
        max_attempts=max_attempts,
        delay=delay,
        backoff=1.5,
        on=(DatabaseException, ConnectionException),
        exclude=(DuplicateException,),
        jitter=True
    )
