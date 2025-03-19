"""
Модуль для розных LLM правайдэраў.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple
from grammar_db import GrammarInfo

class BaseProvider(ABC):
    """Базавы клас для ўсіх LLM правайдэраў."""

    @abstractmethod
    async def disambiguate(self, text: str, variants: List[GrammarInfo]) -> List[float]:
        """
        Дызамбігуацыя граматычнай інфармацыі з выкарыстаннем LLM.
        
        Args:
            text: Тэкст для дызамбігуацыі
            variants: Спіс магчымых варыянтаў граматычнай інфармацыі
            
        Returns:
            Спіс верагоднасьцяў для кожнага варыянту ў тым жа парадку, што і ўваходны спіс variants
        """
        pass 

    async def get_usage(self) -> Tuple[int, int, int]:
        """
        Get the usage of the provider.

        Returns:
            Tuple[int, int, int]: Выкарыстаныя токены ўводу, кэшу і вываду
        """
        return 0, 0, 0
