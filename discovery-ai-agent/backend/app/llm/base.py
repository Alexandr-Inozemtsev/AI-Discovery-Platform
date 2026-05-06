from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Генерирует текстовый ответ для переданного prompt."""
        raise NotImplementedError
