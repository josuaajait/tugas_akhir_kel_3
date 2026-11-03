"""Local Ollama client; HTTP transport is injectable for deterministic tests."""
import json
import math
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class ModelError(RuntimeError):
    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


def http_json(request, timeout):
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


class OllamaClient:
    def __init__(self, *, base_url='http://127.0.0.1:11434', model='qwen2.5:7b-instruct',
                 temperature=0.2, seed=42, timeout=300, transport=http_json):
        parsed = urlparse(base_url)
        if parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1', '::1') or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('', '/'):
            raise ValueError('Ollama harus menggunakan endpoint HTTP lokal tanpa path/kredensial.')
        if not math.isfinite(timeout) or timeout <= 0 or not math.isfinite(temperature) or not 0 <= temperature <= 2:
            raise ValueError('Timeout harus positif dan suhu harus antara 0–2.')
        if not model.strip():
            raise ValueError('Nama model tidak boleh kosong.')
        self.base_url, self.model = base_url.rstrip('/'), model
        self.options = {'temperature': temperature, 'seed': seed, 'num_ctx': 8192, 'num_predict': 4096}
        self.timeout, self.transport = timeout, transport

    def generate(self, prompt: str) -> dict:
        body = {'model': self.model, 'prompt': prompt, 'stream': False, 'options': self.options}
        request = Request(self.base_url+'/api/generate', data=json.dumps(body).encode('utf-8'),
                          headers={'Content-Type': 'application/json'}, method='POST')
        for attempt in range(2):
            try:
                result = self.transport(request, self.timeout)
                if not isinstance(result, dict) or result.get('done') is not True or not isinstance(result.get('response'), str):
                    raise ModelError('Respons Ollama tidak lengkap atau formatnya tidak valid.', result)
                if result.get('error') or result.get('done_reason') == 'length':
                    raise ModelError('Ollama gagal atau keluaran terpotong karena batas token.', result)
                return result
            except (URLError, socket.timeout, TimeoutError, OSError) as exc:
                # Retry transient transport/server errors once; avoid retrying client errors.
                if isinstance(exc, HTTPError) and exc.code < 500:
                    raise ModelError(f'Ollama HTTP {exc.code}; periksa layanan dan model.') from exc
                if attempt == 1:
                    raise ModelError(f'Ollama tidak dapat dihubungi setelah 2 percobaan: {exc}') from exc
            except (json.JSONDecodeError, UnicodeError) as exc:
                raise ModelError('Respons Ollama bukan JSON UTF-8 yang valid.') from exc
        raise AssertionError('unreachable')
