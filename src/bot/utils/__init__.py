"""
Utilitários do Bot SEFAZ.

Contém ferramentas reutilizáveis:
- Comportamento humano e anti-detecção
- Seletores CSS/XPath
- Validadores de dados
- Decoradores de retry
- Constantes globais
"""

from .human_behavior import HumanBehavior, AntiDetection
from .selectors import SEFAZSelectors
from .validators import SEFAZValidator
from .retry import retry, retry_on_timeout, retry_on_network, RetryExhaustedException
from .constants import *

__all__ = [
    'HumanBehavior',
    'AntiDetection',
    'SEFAZSelectors',
    'SEFAZValidator',
    'retry',
    'retry_on_timeout',
    'retry_on_network',
    'RetryExhaustedException',
]
