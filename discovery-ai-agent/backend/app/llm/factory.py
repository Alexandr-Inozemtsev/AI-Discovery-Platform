import os

from sqlalchemy.orm import Session

from app.llm.mock_client import MockLLMClient
from app.llm.openai_compat_clients import CorporateLLMClient, OpenRouterLLMClient
from app.models.llm_settings import LLMSettings


def create_llm(db: Session):
    s = db.query(LLMSettings).filter(LLMSettings.is_active == True).order_by(LLMSettings.id.desc()).first()  # noqa
    provider = (s.provider if s else os.getenv('LLM_PROVIDER', 'mock')).lower()
    if provider == 'openrouter':
        return OpenRouterLLMClient(base_url=s.base_url or os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1'), api_key=s.api_key or os.getenv('OPENROUTER_API_KEY', ''), model=s.model or os.getenv('OPENROUTER_MODEL', 'deepseek/deepseek-chat-v3-0324:free'), timeout=s.timeout_seconds if s else 60, temperature=s.temperature if s else 0.2)
    if provider == 'corporate':
        return CorporateLLMClient(base_url=s.base_url or os.getenv('CORPORATE_LLM_BASE_URL', ''), api_key=s.api_key or os.getenv('CORPORATE_LLM_API_KEY', ''), model=s.model or os.getenv('CORPORATE_LLM_MODEL', ''), timeout=s.timeout_seconds if s else 60, temperature=s.temperature if s else 0.2)
    return MockLLMClient()
