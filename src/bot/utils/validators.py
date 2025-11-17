"""
Validadores e exceções customizadas para o bot SEFAZ
"""
import re
from typing import Optional
from src.bot.utils.constants import REGEX_CPF, REGEX_IE


# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class SEFAZBotException(Exception):
    """Exceção base para erros do SEFAZ Bot"""
    pass


class ValidationException(SEFAZBotException):
    """Exceção para erros de validação de dados"""
    pass


class LoginFailedException(SEFAZBotException):
    """Exceção quando o login falha"""
    pass


class NavigationException(SEFAZBotException):
    """Exceção para erros de navegação"""
    pass


class ExtractionException(SEFAZBotException):
    """Exceção para erros na extração de dados"""
    pass


class SessionConflictException(SEFAZBotException):
    """Exceção quando há conflito de sessão"""
    pass


class MenuNotFoundException(NavigationException):
    """Exceção quando o menu não é encontrado"""
    pass


class ElementNotFoundException(NavigationException):
    """Exceção quando um elemento não é encontrado"""
    pass


class TimeoutException(NavigationException):
    """Exceção para timeout durante operação"""
    pass


class PageLoadException(NavigationException):
    """Exceção quando falha ao carregar página"""
    pass


# Exceções de Browser
class BrowserException(SEFAZBotException):
    """Exceção relacionada ao navegador"""
    pass


class BrowserLaunchException(BrowserException):
    """Falha ao iniciar navegador"""
    pass


class BrowserCloseException(BrowserException):
    """Falha ao fechar navegador"""
    pass


# Exceções de Banco de Dados
class DatabaseException(SEFAZBotException):
    """Exceção relacionada ao banco de dados"""
    pass


class ConnectionException(DatabaseException):
    """Falha na conexão com banco"""
    pass


class QueryException(DatabaseException):
    """Erro ao executar query"""
    pass


class DuplicateException(DatabaseException):
    """Registro duplicado"""
    pass


# Exceções de Criptografia
class CryptographyException(SEFAZBotException):
    """Exceção relacionada à criptografia"""
    pass


class DecryptionException(CryptographyException):
    """Falha ao descriptografar"""
    pass


class EncryptionException(CryptographyException):
    """Falha ao criptografar"""
    pass


class MissingKeyException(CryptographyException):
    """Chave de criptografia ausente"""
    pass


# Exceções de CAPTCHA
class CaptchaException(SEFAZBotException):
    """Exceção quando CAPTCHA é detectado"""
    pass


# Exceções de Sessão
class SessionExpiredException(SEFAZBotException):
    """Sessão expirada"""
    pass


# Exceções de Validação específicas
class InvalidCPFException(ValidationException):
    """CPF inválido"""
    pass


class InvalidIEException(ValidationException):
    """Inscrição Estadual inválida"""
    pass


class InvalidPasswordException(ValidationException):
    """Senha inválida"""
    pass


# ============================================================================
# VALIDADORES
# ============================================================================

class SEFAZValidator:
    """Classe com métodos de validação"""
    
    @staticmethod
    def validate_cpf(cpf: Optional[str]) -> tuple[bool, str]:
        """
        Valida formato do CPF
        
        Args:
            cpf: CPF a ser validado (com ou sem formatação)
            
        Returns:
            tuple: (is_valid: bool, message: str)
        """
        if not cpf:
            return False, "CPF não pode ser vazio"
        
        # Remover formatação
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        
        # Validar tamanho
        if len(cpf_limpo) != 11:
            return False, f"CPF deve ter 11 dígitos. Encontrado: {len(cpf_limpo)}"
        
        # Validar se não é sequência repetida (000.000.000-00, 111.111.111-11, etc)
        if cpf_limpo == cpf_limpo[0] * 11:
            return False, "CPF não pode ser uma sequência de números iguais"
        
        return True, "CPF válido"
    
    @staticmethod
    def validate_ie(ie: Optional[str]) -> tuple[bool, str]:
        """
        Valida formato da Inscrição Estadual
        
        Args:
            ie: IE a ser validada (com ou sem formatação)
            
        Returns:
            tuple: (is_valid: bool, message: str)
        """
        if not ie:
            # IE é opcional
            return True, "IE não fornecida (opcional)"
        
        # Remover formatação
        ie_limpa = ''.join(filter(str.isdigit, ie))
        
        # Validar tamanho (máximo 9 dígitos para MA)
        if len(ie_limpa) > 9:
            return False, f"IE deve ter no máximo 9 dígitos. Encontrado: {len(ie_limpa)}"
        
        if len(ie_limpa) == 0:
            return False, "IE não pode ser vazia após limpeza"
        
        return True, "IE válida"
    
    @staticmethod
    def validate_senha(senha: Optional[str]) -> tuple[bool, str]:
        """
        Valida senha
        
        Args:
            senha: Senha a ser validada
            
        Returns:
            tuple: (is_valid: bool, message: str)
        """
        if not senha:
            return False, "Senha não pode ser vazia"
        
        if len(senha) < 3:
            return False, "Senha muito curta (mínimo 3 caracteres)"
        
        if len(senha) > 50:
            return False, "Senha muito longa (máximo 50 caracteres)"
        
        return True, "Senha válida"
    
    @staticmethod
    def limpar_cpf(cpf: str) -> str:
        """Remove formatação do CPF, mantendo apenas dígitos"""
        return ''.join(filter(str.isdigit, cpf))
    
    @staticmethod
    def limpar_ie(ie: str) -> str:
        """Remove formatação da IE, mantendo apenas dígitos"""
        return ''.join(filter(str.isdigit, ie))
    
    @staticmethod
    def validate_all(cpf: Optional[str], senha: Optional[str], ie: Optional[str] = None) -> tuple[bool, list[str]]:
        """
        Valida todas as credenciais de uma vez
        
        Args:
            cpf: CPF do usuário
            senha: Senha do usuário
            ie: Inscrição Estadual (opcional)
            
        Returns:
            tuple: (all_valid: bool, errors: list[str])
        """
        errors = []
        
        # Validar CPF
        cpf_valid, cpf_msg = SEFAZValidator.validate_cpf(cpf)
        if not cpf_valid:
            errors.append(f"CPF: {cpf_msg}")
        
        # Validar senha
        senha_valid, senha_msg = SEFAZValidator.validate_senha(senha)
        if not senha_valid:
            errors.append(f"Senha: {senha_msg}")
        
        # Validar IE (se fornecida)
        if ie:
            ie_valid, ie_msg = SEFAZValidator.validate_ie(ie)
            if not ie_valid:
                errors.append(f"IE: {ie_msg}")
        
        return len(errors) == 0, errors


# ============================================================================
# HELPERS
# ============================================================================

def formatar_cpf(cpf: str) -> str:
    """Formata CPF para exibição (XXX.XXX.XXX-XX)"""
    cpf_limpo = ''.join(filter(str.isdigit, cpf))
    if len(cpf_limpo) == 11:
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
    return cpf


def formatar_ie(ie: str) -> str:
    """Formata IE para exibição"""
    ie_limpa = ''.join(filter(str.isdigit, ie))
    # Formato padrão do MA: XX.XXXXXX-X (2.6-1)
    if len(ie_limpa) == 9:
        return f"{ie_limpa[:2]}.{ie_limpa[2:8]}-{ie_limpa[8]}"
    return ie


def is_session_conflict_message(text: str) -> bool:
    """Verifica se o texto indica conflito de sessão"""
    if not text:
        return False
    
    text_lower = text.lower()
    return 'já está conectado' in text_lower or 'outra sessão' in text_lower
