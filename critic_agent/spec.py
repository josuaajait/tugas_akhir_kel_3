"""Supported v1 JSON contract. Unsupported input is never silently ignored."""
import json
from pathlib import Path
import re


class SpecError(ValueError):
    pass


OPERATIONS = {
    'index': {'success_status': 200},
    'store': {'success_status': 201, 'validation_error_status': 422},
    'show': {'success_status': 200, 'not_found_status': 404},
    'update': {'success_status': 200, 'validation_error_status': 422, 'not_found_status': 404},
    'destroy': {'success_status': 204, 'not_found_status': 404},
}


def _require(condition, message):
    if not condition:
        raise SpecError(message)


def validate_spec(data: dict) -> dict:
    _require(isinstance(data, dict), 'Spesifikasi harus berupa objek JSON.')
    keys = {'spec_id', 'spec_version', 'resource', 'model', 'controller', 'fields', 'operations'}
    _require(set(data) == keys, f'Field wajib dan yang didukung: {sorted(keys)}.')
    for key in ['spec_id', 'resource']:
        _require(isinstance(data[key], str) and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', data[key]),
                 f'{key}: gunakan huruf kecil, angka, dan underscore; maksimal 64 karakter.')
    _require(isinstance(data['spec_version'], str) and re.fullmatch(r'\d+\.\d+(?:\.\d+)?', data['spec_version']),
             'spec_version harus seperti 1.0.')
    for key in ['model', 'controller']:
        _require(isinstance(data[key], str) and re.fullmatch(r'[A-Z][A-Za-z0-9]{0,63}', data[key]),
                 f'{key}: nama class tidak valid.')
    _require(data['controller'].endswith('Controller'), 'Nama controller harus berakhiran Controller.')
    fields = data['fields']
    _require(isinstance(fields, list) and 1 <= len(fields) <= 20, 'fields: diperlukan 1–20 field.')
    names = set()
    for field in fields:
        _require(isinstance(field, dict) and set(field) == {'name', 'type', 'rules'},
                 'Setiap field hanya memiliki name, type, rules.')
        name, kind, rules = field['name'], field['type'], field['rules']
        _require(isinstance(name, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', name), 'Nama field tidak valid.')
        _require(name not in names and name not in {'id', 'created_at', 'updated_at'}, 'Field duplikat atau dicadangkan.')
        names.add(name)
        _require(kind in ('string', 'integer'), 'Versi dasar mendukung string dan integer.')
        _require(isinstance(rules, list) and rules and all(isinstance(r, str) for r in rules), 'rules harus berupa daftar string.')
        _require(len(rules) == len(set(rules)), 'Aturan field tidak boleh duplikat.')
        _require('required' in rules and kind in rules, f'{name}: wajib memuat required dan {kind}.')
        bounds = {}
        for rule in rules:
            if rule in ('required', kind):
                continue
            bound = re.fullmatch(r'(min|max):(-?\d+)', rule)
            if bound:
                label, value = bound.group(1), int(bound.group(2))
                _require(label not in bounds and abs(value) <= 1000000, f'{name}: batas invalid/duplikat.')
                _require(kind != 'string' or value >= 0, f'{name}: panjang string harus nonnegatif.')
                bounds[label] = value
            else:
                _require(rule == f"unique:{data['resource']},{name}", f'{name}: aturan tidak didukung: {rule}')
        _require(not {'min', 'max'} <= bounds.keys() or bounds['min'] <= bounds['max'], f'{name}: min melebihi max.')
    ops = data['operations']
    _require(isinstance(ops, dict) and set(ops) == set(OPERATIONS), 'Kelima operasi CRUD wajib tersedia.')
    for method, expected in OPERATIONS.items():
        actual = ops[method]
        _require(isinstance(actual, dict) and set(actual) == set(expected), f'{method}: field status tidak sesuai kontrak dasar.')
        for key, value in expected.items():
            _require(type(actual[key]) is int and actual[key] == value, f'{method}.{key}: kontrak dasar menetapkan {value}.')
    return data


def load_spec(path: Path) -> dict:
    try:
        return validate_spec(json.loads(path.read_text(encoding='utf-8-sig')))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SpecError(f'Tidak dapat membaca spesifikasi: {exc}') from exc
