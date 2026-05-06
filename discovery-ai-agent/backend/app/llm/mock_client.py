from app.llm.base import BaseLLMClient


class MockLLMClient(BaseLLMClient):
    """Русский детерминированный mock-клиент вместо реальной LLM."""

    def generate(self, prompt: str) -> str:
        return (
            "[MockLLM]\n"
            "Сформирован черновик артефакта на основе текущего контекста проекта.\n"
            "Ключевые вводные учтены, требуется уточнение спорных зон у PO.\n\n"
            f"PROMPT_HASH_SEED: {len(prompt)}"
        )
