"""
Módulo principal do Bot SEFAZ.

Este módulo contém todas as funcionalidades de automação do sistema SEFAZ,
incluindo autenticação, navegação, extração de dados e processamento de mensagens.
"""

from .sefaz_bot import SEFAZBot, BrowserManager
from .core.authenticator import SEFAZAuthenticator
from .core.navigator import SEFAZNavigator
from .core.data_extractor import DataExtractor, MessageExtractor
from .core.message_processor import SEFAZMessageProcessor

__all__ = [
    'SEFAZBot',
    'BrowserManager',
    'SEFAZAuthenticator',
    'SEFAZNavigator',
    'DataExtractor',
    'MessageExtractor',
    'SEFAZMessageProcessor',
]

__version__ = '2.0.0'
