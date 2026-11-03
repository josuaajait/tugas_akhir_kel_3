import argparse
import json
from pathlib import Path
import sys
import shutil
import subprocess

from .doctor import doctor
from .generation import generate
from .ollama import OllamaClient
from .prompts import build_prompt
from .spec import load_spec, SpecError
from .static import analyze, StaticEnvironmentError
from .sandbox import DockerRunner, SandboxError


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='critic-agent', description='Fondasi Critic Agent untuk controller Laravel.')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor', help='Periksa Python, PHP, Docker, dan Ollama.')
    for name in ('harness-build', 'harness-check', 'check-products'):
        child = sub.add_parser(name)
        child.add_argument('--image', default='critic-laravel:dev')
        child.add_argument('--timeout', type=float, default=600 if name == 'harness-build' else 120)
        child.add_argument('--output', type=Path, default=Path('runs/harness'))
        if name == 'check-products':
            child.add_argument('spec', type=Path)
            child.add_argument('code', type=Path)
    for name in ('validate', 'prompt', 'generate', 'analyze'):
        child = sub.add_parser(name)
        child.add_argument('spec', type=Path)
        if name == 'analyze':
            child.add_argument('code', type=Path)
            child.add_argument('--php', default='php')
        if name == 'generate':
            child.add_argument('--output', type=Path, default=Path('runs'))
            child.add_argument('--model', default='qwen2.5:7b-instruct')
            child.add_argument('--temperature', type=float, default=0.2)
            child.add_argument('--seed', type=int, default=42)
            child.add_argument('--timeout', type=float, default=300)
    args = parser.parse_args(argv)
    try:
        if args.command == 'doctor':
            result = doctor()
            emit(result)
            return 0 if result['ready'] else 3
        if args.command in ('harness-build', 'harness-check', 'check-products'):
            runner = DockerRunner(image=args.image, output_root=args.output, timeout=args.timeout)
            if args.command == 'harness-build':
                if not shutil.which('docker'):
                    raise SandboxError('Docker belum ditemukan; image belum bisa dibangun.')
                context = Path(__file__).resolve().parents[1]/'harness'
                result = subprocess.run(['docker', 'build', '--tag', args.image, str(context)],
                                        timeout=args.timeout, shell=False)
                return 0 if result.returncode == 0 else 3
            if args.command == 'harness-check':
                result = runner.check_reference()
            else:
                spec = load_spec(args.spec)
                supported = load_spec(Path(__file__).resolve().parents[1]/'harness'/'products-contract.json')
                if any(spec[key] != supported[key] for key in ('resource', 'model', 'controller', 'fields', 'operations')):
                    raise SpecError('Harness contoh ini hanya mendukung kontrak products yang disediakan; variasi lain belum tersedia.')
                result = runner.check_candidate(args.code)
            emit(result)
            return 0 if result['status'] in ('READY', 'PASSED_INTERNAL') else (3 if result['status'] == 'ERROR' else 1)
        spec = load_spec(args.spec)
        if args.command == 'validate':
            emit({'valid': True, 'spec_id': spec['spec_id'], 'contract': 'v1-basic'})
        elif args.command == 'prompt':
            print(build_prompt(spec))
        elif args.command == 'analyze':
            result = analyze(args.code.read_text(encoding='utf-8-sig'), spec, php=args.php)
            emit(result)
            return 1 if result['findings'] else 0
        else:
            client = OllamaClient(model=args.model, temperature=args.temperature, seed=args.seed, timeout=args.timeout)
            folder = generate(spec, args.output, client)
            manifest = json.loads((folder/'run_manifest.json').read_text(encoding='utf-8'))
            emit({'run_directory': str(folder.resolve()), 'status': manifest['status'],
                  'message': 'Generasi saja; test dinamis dan loop revisi belum tersedia.'})
            return 0 if manifest['status'] == 'AWAITING_DYNAMIC_TESTS' else (3 if manifest['status'] == 'ERROR' else 1)
        return 0
    except (SpecError, ValueError, UnicodeError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    except (StaticEnvironmentError, SandboxError, subprocess.TimeoutExpired) as exc:
        print(f'ERROR lingkungan: {exc}', file=sys.stderr)
        return 3
