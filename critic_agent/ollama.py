"""Local Ollama client; HTTP transport is injectable for deterministic tests."""
import json
import math
import socket
import time
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
                 temperature=0.2, seed=42, timeout=300, transport=http_json, metadata_transport=None):
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
        self.metadata_transport = metadata_transport
        if metadata_transport is None and transport is http_json:
            self.metadata_transport = http_json
        self.last_transport_attempts = []

    def model_identity(self):
        identity = {'status': 'unavailable', 'requested_name': self.model, 'ollama_version': None,
                    'resolved_name': None, 'digest': None, 'quantization': None, 'issues': []}
        if self.metadata_transport is None:
            identity['issues'].append('metadata_transport_unavailable')
            return identity
        for endpoint in ('version', 'tags'):
            try:
                payload = self.metadata_transport(Request(f'{self.base_url}/api/{endpoint}'), min(self.timeout, 3))
                if endpoint == 'version':
                    version = payload['version']
                    if not isinstance(version, str) or not version:
                        raise ValueError('Versi Ollama tidak valid.')
                    identity['ollama_version'] = version
                else:
                    name = self.model if ':' in self.model.rsplit('/', 1)[-1] else self.model+':latest'
                    match = next(row for row in payload['models'] if row.get('name', row.get('model')) == name)
                    identity.update(resolved_name=name, digest=match.get('digest'),
                                    quantization=(match.get('details') or {}).get('quantization_level'))
            except StopIteration:
                identity['issues'].append('model_not_listed')
            except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
                identity['issues'].append(f'{endpoint}: {type(exc).__name__}')
        for key in ('ollama_version', 'digest', 'quantization'):
            if not isinstance(identity[key], str) or not identity[key]:
                identity[key] = None
                identity['issues'].append(f'{key}_unavailable')
        if not identity['issues']:
            identity['status'] = 'observed'
        elif any(identity[key] for key in ('ollama_version', 'digest', 'quantization')):
            identity['status'] = 'partial'
        return identity

    def generate(self, prompt: str) -> dict:
        self.last_transport_attempts = []
        body = {'model': self.model, 'prompt': prompt, 'stream': False, 'options': self.options}
        request = Request(self.base_url+'/api/generate', data=json.dumps(body).encode('utf-8'),
                          headers={'Content-Type': 'application/json'}, method='POST')
        for attempt in range(2):
            started = time.monotonic()
            event = {'attempt': attempt+1, 'outcome': 'interrupted'}
            try:
                result = self.transport(request, self.timeout)
                event['outcome'] = 'invalid_response'
                if not isinstance(result, dict) or result.get('done') is not True or not isinstance(result.get('response'), str):
                    raise ModelError('Respons Ollama tidak lengkap atau formatnya tidak valid.', result)
                if result.get('error') or result.get('done_reason') == 'length':
                    raise ModelError('Ollama gagal atau keluaran terpotong karena batas token.', result)
                event['outcome'] = 'ok'
                return result
            except (URLError, socket.timeout, TimeoutError, OSError) as exc:
                # Retry transient transport/server errors once; avoid retrying client errors.
                event.update(outcome='retryable_error', error_type=type(exc).__name__)
                if isinstance(exc, HTTPError):
                    event['http_status'] = exc.code
                if isinstance(exc, HTTPError) and exc.code < 500:
                    event['outcome'] = 'non_retryable_error'
                    raise ModelError(f'Ollama HTTP {exc.code}; periksa layanan dan model.') from exc
                if attempt == 1:
                    raise ModelError(f'Ollama tidak dapat dihubungi setelah 2 percobaan: {exc}') from exc
            except (json.JSONDecodeError, UnicodeError) as exc:
                event.update(outcome='invalid_response', error_type=type(exc).__name__)
                raise ModelError('Respons Ollama bukan JSON UTF-8 yang valid.') from exc
            finally:
                event['elapsed_seconds'] = round(time.monotonic()-started, 6)
                self.last_transport_attempts.append(event)
        raise AssertionError('unreachable')
