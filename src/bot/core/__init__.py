"""
Componentes core do Bot SEFAZ.

Contém as classes principais responsáveis por:
- Autenticação no sistema SEFAZ
- Navegação entre páginas
- Extração de dados
- Processamento de mensagens
"""

from .authenticator import SEFAZAuthenticator
from .navigator import SEFAZNavigator
from .data_extractor import DataExtractor, MessageExtractor
from .message_processor import SEFAZMessageProcessor

__all__ = [
    'SEFAZAuthenticator',
    'SEFAZNavigator',
    'DataExtractor',
    'MessageExtractor',
    'SEFAZMessageProcessor',
]
