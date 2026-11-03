"""Parse tokens with PHP without executing the generated controller."""
import json
import re
import subprocess
from .spec import validate_spec


class StaticEnvironmentError(RuntimeError):
    pass


# Candidate bytes are STDIN data only; never interpolate into -r or use eval/include.
TOKENIZER = r'''
try {
 $tokens = token_get_all(stream_get_contents(STDIN), TOKEN_PARSE);
 $out = []; $line = 1;
 foreach ($tokens as $t) {
  if (is_array($t)) { $out[] = [token_name($t[0]), $t[1], $t[2]]; $line = $t[2] + substr_count($t[1], "\n"); }
  else { $out[] = [$t, $t, $line]; }
 }
 echo json_encode(['tokens' => $out], JSON_THROW_ON_ERROR);
} catch (ParseError $e) {
 echo json_encode(['error' => $e->getMessage(), 'line' => $e->getLine()], JSON_THROW_ON_ERROR);
}
'''


def analyze(code: str, spec: dict, php='php') -> dict:
    validate_spec(spec)
    try:
        lint = subprocess.run([php, '-n', '-l'], input=code.encode('utf-8'),
                              capture_output=True, timeout=15, shell=False)
        process = subprocess.run([php, '-n', '-r', TOKENIZER], input=code.encode('utf-8'),
                                 capture_output=True, timeout=15, shell=False)
        if process.returncode:
            raise StaticEnvironmentError('PHP tokenizer gagal: '+process.stderr.decode('utf-8', errors='replace'))
        parsed = json.loads(process.stdout)
        if lint.returncode and 'error' not in parsed:
            message = (lint.stdout+lint.stderr).decode('utf-8', errors='replace').strip()
            line = re.search(r'on line (\d+)', message)
            parsed = {'error': message, 'line': int(line.group(1)) if line else 1}
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise StaticEnvironmentError(f'Tidak dapat menjalankan PHP tokenizer: {exc}') from exc
    findings = []

    def finding(check, explanation, token=None, method=None):
        location = {'method': method} if method else {'class': spec['controller']}
        if token:
            location['line'] = token[2]
        findings.append({'source': 'static', 'check': check, 'location': location,
                         'explanation': explanation, 'evidence': token[1] if token else 'Elemen tidak ditemukan pada token PHP.'})

    if 'error' in parsed:
        finding('syntax', parsed['error'], ['error', parsed['error'], parsed['line']])
    else:
        ignored = {'T_WHITESPACE', 'T_COMMENT', 'T_DOC_COMMENT'}
        tokens = [t for t in parsed['tokens'] if t[0] not in ignored]
        namespace = ''
        namespaces = 0
        aliases = {}
        for i, token in enumerate(tokens):
            if token[0] == 'T_NAMESPACE':
                namespaces += 1
                namespace = ''
                j = i+1
                while j < len(tokens) and tokens[j][1] not in (';', '{'):
                    namespace += tokens[j][1]
                    j += 1
            if token[0] == 'T_USE':
                j = i+1
                parts = []
                while j < len(tokens) and tokens[j][1] != ';':
                    parts.append(tokens[j][1])
                    j += 1
                if parts and parts[0].lstrip('\\') == 'Illuminate\\Http\\Request':
                    aliases[parts[-1] if len(parts) > 1 and parts[-2].lower() == 'as' else 'Request'] = 'Illuminate\\Http\\Request'
        if namespaces != 1 or namespace != 'App\\Http\\Controllers':
            finding('namespace', 'Namespace harus App\\Http\\Controllers.')
        classes = [(i, tokens[i+1]) for i, t in enumerate(tokens[:-1])
                   if t[0] == 'T_CLASS' and tokens[i+1][0] == 'T_STRING']
        selected = [(i, t) for i, t in classes if t[1] == spec['controller']]
        if len(classes) != 1 or len(selected) != 1:
            finding('class', f"Harus ada tepat satu class bernama {spec['controller']}.")
        else:
            start = selected[0][0]
            if start and tokens[start-1][0] == 'T_ABSTRACT':
                finding('class', 'Controller harus berupa class konkret.', selected[0][1])
            while start < len(tokens) and tokens[start][1] != '{':
                start += 1
            depth, methods = 1, {}
            i = start+1
            boundary = i
            while i < len(tokens) and depth:
                token = tokens[i]
                if token[0] == 'T_FUNCTION' and depth == 1:
                    j = i+1
                    if tokens[j][1] == '&':
                        j += 1
                    if tokens[j][0] == 'T_STRING':
                        name_token = tokens[j]
                        j += 2  # name, then opening parenthesis
                        params = []
                        while j < len(tokens) and tokens[j][1] != ')':
                            params.append(tokens[j][1])
                            j += 1
                        modifiers = {t[1].lower() for t in tokens[boundary:i]}
                        methods[name_token[1]] = (name_token, params, modifiers)
                if token[0] in ('{', 'T_CURLY_OPEN', 'T_DOLLAR_OPEN_CURLY_BRACES'):
                    depth += 1
                elif token[1] == '}' and token[0] == '}':
                    depth -= 1
                    if depth == 1:
                        boundary = i+1
                elif token[1] == ';' and depth == 1:
                    boundary = i+1
                i += 1
            expected = {'index': [], 'store': ['Illuminate\\Http\\Request', '$request'], 'show': ['$id'],
                        'update': ['Illuminate\\Http\\Request', '$request', ',', '$id'], 'destroy': ['$id']}
            for method, signature in expected.items():
                if method not in methods:
                    finding('method', f'Method {method} tidak ditemukan.', method=method)
                    continue
                token, params, modifiers = methods[method]
                normalized = [aliases.get(p, p[1:] if p.startswith('\\') else p) for p in params]
                if {'private', 'protected', 'static', 'abstract'} & modifiers:
                    finding('visibility', f'{method} harus public, nonstatic, dan konkret.', token, method)
                if normalized != signature:
                    finding('signature', f'Parameter {method} harus mengikuti kontrak.', token, method)
    return {'status': 'STATIC_FAIL' if findings else 'AWAITING_DYNAMIC_TESTS',
            'dynamic_tests': 'not_run', 'findings': findings}
