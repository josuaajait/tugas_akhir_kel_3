import argparse
import json
from pathlib import Path
import sys
import shutil
import subprocess
import tempfile

from .doctor import doctor
from .generation import generate
from .ollama import OllamaClient
from .prompts import build_prompt
from .spec import load_spec, SpecError
from .static import analyze, StaticEnvironmentError
from .sandbox import DockerRunner, SandboxError, validate_products_contract
from .orchestrator import run_products, run_resource
from .reference import ReferenceDockerRunner, evaluate_products, reference_suite_hash
from .resources import ResourceDockerRunner, build_resource
from .resource_reference import ResourceReferenceRunner, build_resource_reference, evaluate_resource

from .pilot import create_pilot_manifest
from.pilot_runner import run_pilot
from .component_corpus import prepare_development_corpus, load_corpus
from .component_evaluation import run_components, collect_component_evidence
from .component_report import component_report


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog='critic-agent', description='Fondasi Critic Agent untuk controller Laravel.')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor', help='Periksa Python, PHP, Docker, dan Ollama.')

    pilot = sub.add_parser(
        'pilot-plan',
        help='Buat manifest eksperimen temperature dan seed tanpa menjalankan model.'
    )

    pilot_runner = sub.add_parser(
        'pilot-run',
        help='Jalankan eksperimen pilot secara bertahap dari manifest.'
    )
    pilot_runner.add_argument('manifest', type=Path)
    pilot_runner.add_argument('--limit', type=int, default=1)
    pilot_runner.add_argument(
        '--kind',
        choices=('products', 'resource'),
        default='products',
    )
    pilot_runner.add_argument('--image', default=None)
    pilot_runner.add_argument('--timeout', type=float, default=300)
    pilot_runner.add_argument('--test-timeout', type=float, default=120)

    pilot.add_argument('specs', nargs='+', type=Path)
    pilot.add_argument('--seeds', nargs='+', type=int, required=True)
    pilot.add_argument('--temperatures', nargs='+', type=float, required=True)
    pilot.add_argument('--model', default='qwen2.5:7b-instruct')
    pilot.add_argument('--max-revisions', type=int, choices=range(4), default=3)
    pilot.add_argument(
        '--output',
        type=Path,
        default=Path('runs/pilot-development/manifest.json'),
    )

    corpus = sub.add_parser('component-corpus-init', help='Siapkan korpus development berlabel draf, tanpa Qwen.')
    corpus.add_argument('--output', type=Path, default=Path('corpora/development'))
    corpus.add_argument('--synthetic-only', action='store_true')
    corpus.add_argument('--runs-root', type=Path)
    for name in ('component-evidence', 'component-run'):
        component = sub.add_parser(name, help='Kumpulkan bukti acuan atau prediksi Critic tanpa memanggil Qwen.')
        component.add_argument('corpus', type=Path)
        component.add_argument('--output', type=Path, default=Path('component-evidence' if name=='component-evidence' else 'component-runs'))
        component.add_argument('--timeout', type=float, default=120)
    component_summary = sub.add_parser('component-report', help='Metrik per kode/per korpus; draf hanya melalui --provisional.')
    component_summary.add_argument('run_directory', type=Path)
    component_summary.add_argument('--provisional', action='store_true')
    build_evaluation = sub.add_parser('evaluation-build', help='Bangun image evaluator acuan terpisah.')
    build_evaluation.add_argument('--image', default='critic-laravel-evaluation:dev')
    build_evaluation.add_argument('--base-image', default='critic-laravel:dev')
    build_evaluation.add_argument('--timeout', type=float, default=600)
    evaluation = sub.add_parser('evaluate-products', help='Evaluasi kode awal/akhir arsip loop tanpa memanggil Qwen.')
    evaluation.add_argument('loop_directory', type=Path)
    evaluation.add_argument('--image', default='critic-laravel-evaluation:dev')
    evaluation.add_argument('--output', type=Path, default=Path('evaluations'))
    evaluation.add_argument('--timeout', type=float, default=120)
    resource_evaluation = sub.add_parser('resource-evaluation-build', help='Bangun evaluator acuan terpisah books/inventory.')
    resource_evaluation.add_argument('spec', type=Path)
    resource_evaluation.add_argument('--image', default=None)
    resource_evaluation.add_argument('--base-image', default=None)
    resource_evaluation.add_argument('--timeout', type=float, default=600)
    resource_evaluation.add_argument('--output', type=Path, default=Path('builds/resource-evaluation'))
    resource_pair = sub.add_parser('evaluate-resource', help='Evaluasi acuan kode awal/akhir books/inventory tanpa Qwen.')
    resource_pair.add_argument('loop_directory', type=Path)
    resource_pair.add_argument('--image', default=None)
    resource_pair.add_argument('--timeout', type=float, default=120)
    resource_pair.add_argument('--output', type=Path, default=Path('evaluations'))
    for name in ('resource-build', 'resource-check'):
        resource = sub.add_parser(name, help='Bangun/periksa harness yang dibentuk dari spesifikasi JSON.')
        resource.add_argument('spec', type=Path)
        resource.add_argument('--image', default=None)
        resource.add_argument('--timeout', type=float, default=600 if name == 'resource-build' else 120)
        resource.add_argument('--output', type=Path, default=Path('builds/resources') if name == 'resource-build' else Path('runs/resource-harness'))
        if name == 'resource-build':
            resource.add_argument('--base-image', default='critic-laravel:dev')
        else:
            resource.add_argument('--code', type=Path, help='Tanpa --code, periksa kesiapan controller acuan.')
    loop = sub.add_parser('run-products', aliases=['run-resource'], help='Periksa dan revisi controller hingga maksimal 3 revisi; run-resource memakai harness spesifikasinya.')
    loop.add_argument('spec', type=Path)
    loop.add_argument('--initial-run', type=Path, help='Arsip generate yang menjadi kode percobaan ke-0.')
    loop.add_argument('--output', type=Path, default=Path('runs'))
    loop.add_argument('--model', default='qwen2.5:7b-instruct')
    loop.add_argument('--temperature', type=float, default=0.2)
    loop.add_argument('--seed', type=int, default=42)
    loop.add_argument('--timeout', type=float, default=300, help='Timeout tiap permintaan model.')
    loop.add_argument('--test-timeout', type=float, default=120)
    loop.add_argument('--image', default=None)
    loop.add_argument('--max-revisions', type=int, choices=range(4), default=3)
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

        if args.command == 'pilot-run':
            result = run_pilot(
                args.manifest,
                limit=args.limit,
                kind=args.kind,
                image=args.image,
                model_timeout=args.timeout,
                test_timeout=args.test_timeout,
            )
            emit(result)
            return 3 if result['status'] == 'ERROR' else 0

        if args.command == 'pilot-plan':
            result = create_pilot_manifest(
                specs=args.specs,
                seeds=args.seeds,
                temperatures=args.temperatures,
                output=args.output,
                model=args.model,
                max_revisions=args.max_revisions,
            )
            emit(result)
            return 0
        if args.command == 'component-corpus-init':
            options = {'runs_root':args.runs_root} if args.runs_root is not None else {}
            folder = prepare_development_corpus(args.output, synthetic_only=args.synthetic_only, **options)
            loaded = load_corpus(folder/'corpus.json')
            emit({'status':'PREPARED_DRAFT','case_count':len(loaded['records']),
                  'corpus_manifest':str((folder/'corpus.json').resolve()),'human_labels_reviewed':False})
            return 0
        if args.command in ('component-evidence','component-run'):
            if args.command == 'component-evidence':
                folder = collect_component_evidence(args.corpus,args.output,timeout=args.timeout)
                result = json.loads((folder/'evidence_manifest.json').read_text(encoding='utf-8'))
                emit({'status':result['status'],'case_count':len(result['cases']),
                      'corpus_manifest':str((folder/'corpus.json').resolve()),
                      'review_packet':str((folder/'review').resolve()),'labels_promoted':False})
            else:
                folder = run_components(args.corpus,args.output,timeout=args.timeout)
                result = json.loads((folder/'run_manifest.json').read_text(encoding='utf-8'))
                emit({'status':result['status'],'case_count':result['case_count'],
                      'prediction_errors':result['prediction_errors'],'run_directory':str(folder.resolve())})
            return 0 if result['status']=='COMPLETE' else 3
        if args.command == 'component-report':
            emit(component_report(args.run_directory,provisional=args.provisional))
            return 0
        if args.command == 'doctor':
            result = doctor()
            emit(result)
            return 0 if result['ready'] else 3
        if args.command == 'resource-evaluation-build':
            folder = build_resource_reference(load_spec(args.spec), args.output, image=args.image,
                                              base_image=args.base_image, timeout=args.timeout)
            result = json.loads((folder/'build_result.json').read_text(encoding='utf-8'))
            emit({key: result[key] for key in ('status', 'image', 'suite_sha256', 'expected_tests')} |
                 {'build_directory': str(folder.resolve()), 'failed_stage': result.get('failed_stage'),
                  'reason': result.get('reason'), 'detail': result.get('detail'),
                  'timeout_seconds': result['timeout_seconds']})
            return 0 if result['status'] == 'BUILT' else 3
        if args.command == 'resource-build':
            folder = build_resource(load_spec(args.spec), args.output, image=args.image,
                                    base_image=args.base_image, timeout=args.timeout)
            result = json.loads((folder/'build_result.json').read_text(encoding='utf-8'))
            emit({key: result[key] for key in ('status', 'image', 'contract_sha256', 'internal_tests', 'reference_tests')} |
                 {'build_directory': str(folder.resolve()), 'detail': result.get('detail'),
                  'failed_stage': result.get('failed_stage'), 'reason': result.get('reason'),
                  'timeout_seconds': result.get('timeout_seconds')})
            return 0 if result['status'] == 'BUILT' else 3
        if args.command == 'resource-check':
            runner = ResourceDockerRunner(load_spec(args.spec), image=args.image, output_root=args.output, timeout=args.timeout)
            result = runner.check_candidate(args.code) if args.code else runner.check_reference()
            emit(result)
            return 0 if result['status'] in ('READY', 'PASSED_INTERNAL') else (3 if result['status'] == 'ERROR' else 1)
        if args.command == 'evaluation-build':
            DockerRunner(image=args.image, timeout=args.timeout)
            DockerRunner(image=args.base_image, timeout=args.timeout)
            if args.image == args.base_image:
                raise ValueError('Image evaluator harus berbeda dari image harness internal.')
            if not shutil.which('docker'):
                raise SandboxError('Docker belum ditemukan; image evaluator belum bisa dibangun.')
            context = Path(__file__).resolve().parents[1]/'evaluation'
            work = context.parent/'work'
            work.mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='evaluation-build-', dir=work) as temporary:
                staged = Path(temporary)/'evaluation'
                shutil.copytree(context, staged)
                shutil.copyfile(context.parent/'harness'/'runtime.php', staged/'runtime.php')
                result = subprocess.run(['docker', 'build', '--tag', args.image,
                                         '--build-arg', 'HARNESS_IMAGE='+args.base_image,
                                         '--build-arg', 'SUITE_SHA256='+reference_suite_hash(), str(staged)],
                                        timeout=args.timeout, shell=False)
            return 0 if result.returncode == 0 else 3
        if args.command in ('evaluate-products', 'evaluate-resource'):
            if args.command == 'evaluate-resource':
                runner = ResourceReferenceRunner(load_spec(args.loop_directory/'spec.json'), image=args.image,
                                                 output_root=args.output/'harness', timeout=args.timeout)
                folder = evaluate_resource(args.loop_directory, args.output, runner)
            else:
                runner = ReferenceDockerRunner(image=args.image, output_root=args.output/'harness', timeout=args.timeout)
                folder = evaluate_products(args.loop_directory, args.output, runner)
            result = json.loads((folder/'evaluation_result.json').read_text(encoding='utf-8'))
            positions = {name: ({key: value for key, value in result[name].items() if key != 'runner_result'}
                                if result[name] is not None else None) for name in ('initial', 'final')}
            emit({key: result[key] for key in ('status', 'reason', 'source_run_id',
                                               'uplift_pp', 'repair', 'regression')} | positions |
                 {'evaluation_directory': str(folder.resolve()),
                  'report': str((folder/'evaluation_result.json').resolve())})
            return 0 if result['status'] == 'EVALUATED' else 3
        if args.command in ('run-products', 'run-resource'):
            spec = load_spec(args.spec)
            client = OllamaClient(model=args.model, temperature=args.temperature, seed=args.seed, timeout=args.timeout)
            if args.command == 'run-resource':
                runner = ResourceDockerRunner(spec, image=args.image, output_root=args.output/'resource-harness', timeout=args.test_timeout)
                run = run_resource
            else:
                runner = DockerRunner(image=args.image or 'critic-laravel:dev', output_root=args.output/'harness', timeout=args.test_timeout)
                run = run_products
            folder = run(spec, args.output, client, runner, initial_run=args.initial_run,
                                  max_revisions=args.max_revisions)
            result = json.loads((folder/'history.json').read_text(encoding='utf-8'))
            summary = []
            for entry in result['attempts']:
                tests = entry.get('dynamic', {}).get('summary', {})
                summary.append({'attempt': entry['iteration'], 'dynamic_status': entry['dynamic_status'],
                                'passed': tests.get('passed'), 'total': tests.get('total'),
                                'findings': len(entry['findings']), 'error': entry.get('error')})
            emit({'status': result['status'], 'stop_reason': result['stop_reason'],
                  'revision_count': result['revision_count'], 'run_directory': str(folder.resolve()),
                  'final_controller': str((folder/'final_controller.php').resolve()) if (folder/'final_controller.php').is_file() else None,
                  'history': summary})
            return {'LOLOS': 0, 'BELUM LOLOS': 1, 'ERROR': 3}[result['status']]
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
                validate_products_contract(spec)
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
