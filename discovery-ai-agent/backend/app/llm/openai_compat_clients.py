import json
from urllib import request

from app.llm.base import BaseLLMClient


class _OpenAICompat(BaseLLMClient):
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 60, temperature: float = 0.2, extra_headers: dict | None = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.temperature = temperature
        self.extra_headers = extra_headers or {}

    def generate(self, prompt: str) -> str:
        payload = {
            'model': self.model,
            'messages': [{'role': 'system', 'content': 'Ты assistant для Discovery.'}, {'role': 'user', 'content': prompt}],
            'temperature': self.temperature,
        }
        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode(),
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self.api_key}', **self.extra_headers},
            method='POST'
        )
        with request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode())
            return data['choices'][0]['message']['content']


class CorporateLLMClient(_OpenAICompat):
    pass


class OpenRouterLLMClient(_OpenAICompat):
    def __init__(self, *args, **kwargs):
        kwargs['extra_headers'] = {'HTTP-Referer': 'http://localhost:5173', 'X-Title': 'AI Discovery Platform'}
        super().__init__(*args, **kwargs)
