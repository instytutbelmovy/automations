"""
Модуль для розных LLM правайдэраў.
"""

from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """Базавы клас для ўсіх LLM правайдэраў."""
    
    @abstractmethod
    async def tag_text(self, text: str) -> list:
        """
        Разметка тэксту з выкарыстаннем LLM.
        
        Args:
            text: Тэкст для разметкі
            
        Returns:
            Спіс кортэжаў (слова, тэг)
        """
        pass 