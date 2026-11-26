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
from .reference import PRODUCTS_REFERENCE_IMAGES, ReferenceDockerRunner, evaluate_products, reference_suite_hash
from .resources import ResourceDockerRunner, _canonical_image_name, build_resource
from .resource_reference import ResourceReferenceRunner, build_resource_reference, evaluate_resource

from .pilot import create_pilot_manifest
from.pilot_runner import run_pilot
from .pilot_metadata import collect_pilot_metadata
from .pilot_report import pilot_report
from .freeze_draft import check_draft, prepare_project_draft
from .component_corpus import prepare_development_corpus, load_corpus
from .component_evaluation import run_components, collect_component_evidence
from .component_report import component_report
from .interactive import start_interactive
from .ab import run_ab
from .console import Console, current_console
from .final_validation import validate_final
from .final_package import RESOURCES as FINAL_RESOURCES
from .ab_protocol import check_protocol, execute_protocol_pair
from .ab_final import run_synthetic_pair
from .ab_report import ab_report
from .eval_registry import VERSIONS,get_validation_api


def emit(value):
    console = current_console()
    if console is None:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        console.result(value)


def main(argv=None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    # Help exits inside argparse, before the complete command is dispatched.
    # Read presentation preferences first so help honors the same flags.
    preferences = argparse.ArgumentParser(add_help=False)
    preferences.add_argument('--pretty', dest='output_format', action='store_const', const='pretty', default='auto')
    preferences.add_argument('--json', dest='output_format', action='store_const', const='json')
    preferences.add_argument('--no-color', action='store_true')
    early, _ = preferences.parse_known_args(arguments[:arguments.index('--')] if '--' in arguments else arguments)
    with Console(mode=early.output_format, no_color=early.no_color) as console:
        return _main(arguments, console)


class PresentationParser(argparse.ArgumentParser):
    def print_help(self, file=None):
        console = current_console()
        if console is not None and (file is None or file is sys.stdout):
            console.header(self.prog)
        super().print_help(file)


def _main(argv, console) -> int:
    parser = PresentationParser(prog='critic-agent', description='Critic Agent untuk controller Laravel.')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor', help='Periksa Python, PHP, Docker, dan Ollama.')
    ab_smoke=sub.add_parser('ab-smoke',help='Uji adaptor final dengan fixture sintetis, tanpa Ollama.')
    ab_smoke.add_argument('--resource',choices=FINAL_RESOURCES,default='categories')
    ab_smoke.add_argument('--package',choices=VERSIONS,default='final-v1')
    ab_smoke.add_argument('--scenario',choices=('repair','format_fail','syntax_fail','already_valid'),default='repair')
    ab_smoke.add_argument('--output',type=Path,default=Path('runs/ab-synthetic'))
    ab_smoke.add_argument('--order-seed',type=int,default=7)
    ab_smoke.add_argument('--timeout',type=float,default=120)
    ab_check=sub.add_parser('ab-plan-check',help='Periksa integritas/gerbang protokol A/B tanpa model.')
    ab_check.add_argument('manifest',type=Path)
    ab_run=sub.add_parser('ab-run',help='Jalankan satu slot A/B dari protokol final yang sudah beku.')
    ab_run.add_argument('manifest',type=Path)
    ab_run.add_argument('--pair',required=True)
    ab_run.add_argument('--output',type=Path,default=Path('runs/ab-final'))
    ab_summary=sub.add_parser('ab-report',help='Agregasi arsip A/B per soal/kondisi/cohort tanpa model.')
    ab_summary.add_argument('runs',type=Path)
    ab_summary.add_argument('--plan',type=Path)
    final = sub.add_parser('final-validate', help='Validasi paket soal/evaluator berversi tanpa Qwen; bukan pembekuan.')
    final.add_argument('--package', choices=VERSIONS, required=True)
    final.add_argument('--resource', choices=FINAL_RESOURCES, nargs='+')
    final.add_argument('--output', type=Path, default=Path('evaluations/final-validation'))
    final.add_argument('--local-only', action='store_true')
    final.add_argument('--build', action='store_true')
    final.add_argument('--base-image', default='critic-laravel:dev')
    final.add_argument('--timeout', type=float, default=120)
    final.add_argument('--build-timeout', type=float, default=600)
    start = sub.add_parser('start', help='Tanya spesifikasi CRUD, siapkan Docker, lalu jalankan self-debugging.')
    start.add_argument('--output', type=Path, default=Path('runs'))
    start.add_argument('--model', default='qwen2.5:7b-instruct')
    start.add_argument('--temperature', type=float, default=0.2)
    start.add_argument('--seed', type=int, default=42)
    start.add_argument('--timeout', type=float, default=300)
    start.add_argument('--test-timeout', type=float, default=120)
    start.add_argument('--build-timeout', type=float, default=600)
    start.add_argument('--max-revisions', type=int, choices=range(4), default=3)

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

    pilot_metadata = sub.add_parser(
        'pilot-metadata',
        help='Ekstrak metadata dari arsip eksperimen pilot.'
    )
    pilot_metadata.add_argument(
        'job_directory',
        type=Path,
        help='Folder job pilot yang berisi pilot_result.json.'
    )

    report = sub.add_parser('pilot-report', help='Ringkas status dan metrik dari satu atau beberapa manifest pilot.')
    report.add_argument('manifests', nargs='+', type=Path)
    report.add_argument('--evaluations', type=Path, help='Direktori arsip evaluator untuk metrik awal–akhir.')
    freeze = sub.add_parser('freeze-draft', help='Siapkan manifest draf FR-19 dari bukti development.')
    freeze.add_argument('pilot_report', type=Path)
    freeze.add_argument('--output', type=Path, required=True)
    check_freeze = sub.add_parser('freeze-check', help='Periksa integritas draf dan syarat pembekuan FR-19.')
    check_freeze.add_argument('manifest', type=Path)

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
    build_evaluation.add_argument('--image')
    build_evaluation.add_argument('--suite', choices=('v1', 'v2'), default='v1')
    build_evaluation.add_argument('--base-image', default='critic-laravel:dev')
    build_evaluation.add_argument('--timeout', type=float, default=600)
    evaluation = sub.add_parser('evaluate-products', help='Evaluasi kode awal/akhir arsip loop tanpa memanggil Qwen.')
    evaluation.add_argument('loop_directory', type=Path)
    evaluation.add_argument('--image')
    evaluation.add_argument('--suite', choices=('v1', 'v2'), default='v1')
    evaluation.add_argument('--output', type=Path, default=Path('evaluations'))
    evaluation.add_argument('--timeout', type=float, default=120)
    reference_check = sub.add_parser('reference-check-products', help='Periksa readiness atau satu controller dengan evaluator products.')
    reference_check.add_argument('--image')
    reference_check.add_argument('--suite', choices=('v1', 'v2'), default='v1')
    reference_check.add_argument('--code', type=Path)
    reference_check.add_argument('--output', type=Path, default=Path('evaluations/products-check'))
    reference_check.add_argument('--timeout', type=float, default=120)
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
    ab = sub.add_parser('run-ab', help='Jalankan pembanding spesifik/generik FR-20 untuk satu pasangan development.')
    ab.add_argument('spec', type=Path)
    ab.add_argument('--order-seed', type=int, required=True)
    ab.add_argument('--revision-seeds', type=int, nargs='*', required=True)
    ab.add_argument('--repetition', type=int, default=1)
    ab.add_argument('--output', type=Path, default=Path('runs/ab-development'))
    ab.add_argument('--initial-run', type=Path)
    ab.add_argument('--image', default=None)
    ab.add_argument('--reference-image', default=None)
    ab.add_argument('--reference-suite', choices=('v1', 'v2'), default='v1', help='Versi evaluator khusus products.')
    ab.add_argument('--model', default='qwen2.5:7b-instruct')
    ab.add_argument('--temperature', type=float, default=0.2)
    ab.add_argument('--seed', type=int, default=42)
    ab.add_argument('--timeout', type=float, default=300)
    ab.add_argument('--test-timeout', type=float, default=120)
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
    for command_parser in [parser, *dict.fromkeys(sub.choices.values())]:
        presentation = command_parser.add_argument_group('Tampilan')
        formats = presentation.add_mutually_exclusive_group()
        formats.add_argument('--pretty', dest='output_format', action='store_const', const='pretty',
                             default=argparse.SUPPRESS, help='Tampilkan header, tabel, dan kemajuan proses.')
        formats.add_argument('--json', dest='output_format', action='store_const', const='json',
                             default=argparse.SUPPRESS, help='Keluarkan JSON murni (otomatis saat stdout dialihkan).')
        presentation.add_argument('--no-color', action='store_true', default=argparse.SUPPRESS,
                                  help='Matikan warna ANSI; juga menghormati NO_COLOR.')
    args = parser.parse_args(argv)
    console.configure(getattr(args, 'output_format', 'auto'), getattr(args, 'no_color', False))
    if args.command != 'prompt':
        console.header(args.command)
    if args.command not in ('start', 'prompt', 'validate', 'pilot-plan', 'pilot-metadata',
                            'pilot-report', 'component-report', 'freeze-draft', 'freeze-check'):
        console.progress(f'Menjalankan {args.command}...')
    try:
        if args.command=='ab-report':
            emit(ab_report(args.runs,plan=args.plan));return 0
        if args.command=='ab-plan-check':
            checked=check_protocol(args.manifest)
            emit({k:v for k,v in checked.items() if k!='plan'})
            return 0 if checked['status']=='READY' else 3
        if args.command=='ab-run':
            result=execute_protocol_pair(args.manifest,args.pair,args.output)
            emit(result)
            return 0 if result['status']=='EVALUATED' else 3
        if args.command=='ab-smoke':
            folder=run_synthetic_pair(args.resource,args.output,scenario=args.scenario,
                                      order_seed=args.order_seed,timeout=args.timeout,package=args.package)
            result=json.loads((folder/'pair.json').read_bytes())
            emit({k:result.get(k) for k in ('pair_id','status','origin','package_sha256','n_ab','delta_final_pp','qwen_calls')}|
                 {'run_directory':str(folder)})
            return 0 if result['status']=='EVALUATED' else 3
        if args.command == 'final-validate':
            validator=validate_final if args.package=='final-v1' else get_validation_api(args.package).validate_final
            folder = validator(args.output, resources=args.resource, build=args.build, local_only=args.local_only,
                                    base_image=args.base_image, timeout=args.timeout, build_timeout=args.build_timeout)
            result = json.loads((folder/'validation.json').read_text(encoding='utf-8'))
            emit({key: result[key] for key in ('status', 'package', 'package_sha256', 'functional_validation',
                                              'ready_for_final', 'counts', 'run_directory')})
            return 0 if result['status'] in ('VALIDATED','LOCAL_VALIDATED') else 1 if result['status']=='FAILED' else 3
        if args.command == 'start':
            result = start_interactive(args.output, model=args.model, temperature=args.temperature,
                                       seed=args.seed, timeout=args.timeout, test_timeout=args.test_timeout,
                                       build_timeout=args.build_timeout, max_revisions=args.max_revisions)
            if result.get('run_directory') and result['status'] != 'CANCELLED':
                result.update(loop_summary(Path(result['run_directory'])))
            emit(result)
            return {'LOLOS': 0, 'BELUM LOLOS': 1, 'ERROR': 3, 'CANCELLED': 130}[result['status']]

        if args.command == 'pilot-report':
            emit(pilot_report(args.manifests, evaluations=args.evaluations))
            return 0

        if args.command == 'run-ab':
            spec = load_spec(args.spec)
            client = OllamaClient(model=args.model, temperature=args.temperature, seed=args.seed, timeout=args.timeout)
            settings = {'output_root': args.output/'harness', 'timeout': args.test_timeout}
            evaluator_settings = {'output_root': args.output/'reference-harness', 'timeout': args.test_timeout}
            if spec['resource'] == 'products':
                kind = 'products'
                runner = DockerRunner(image=args.image or 'critic-laravel:dev', **settings)
                reference = ReferenceDockerRunner(image=args.reference_image, suite_version=args.reference_suite,
                                                  **evaluator_settings)
            else:
                if args.reference_suite != 'v1':
                    raise ValueError('--reference-suite hanya tersedia untuk products.')
                kind = 'resource'
                runner = ResourceDockerRunner(spec, image=args.image, **settings)
                reference = ResourceReferenceRunner(spec, image=args.reference_image, **evaluator_settings)
            folder = run_ab(spec, args.output, client, runner, reference, kind=kind, order_seed=args.order_seed,
                            revision_seeds=args.revision_seeds, initial_run=args.initial_run, repetition=args.repetition)
            result = json.loads((folder/'pair.json').read_bytes())
            emit(dict(result, report=str(folder/'pair.json')))
            return 0 if result['status'] == 'EVALUATED' else 3

        if args.command == 'freeze-draft':
            path = prepare_project_draft(args.output, Path.cwd(), args.pilot_report)
            emit({'status': 'DRAFT', 'manifest': str(path), 'ready_for_final': False})
            return 0

        if args.command == 'freeze-check':
            emit(check_draft(args.manifest, Path.cwd()))
            return 3

        if args.command == 'pilot-metadata':
            output = collect_pilot_metadata(args.job_directory)
            emit({
                'status': 'METADATA_COLLECTED',
                'job_directory': str(args.job_directory.resolve()),
                'metadata_file': str(output),
            })
            return 0

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
            image = args.image or PRODUCTS_REFERENCE_IMAGES[args.suite]
            DockerRunner(image=image, timeout=args.timeout)
            DockerRunner(image=args.base_image, timeout=args.timeout)
            if _canonical_image_name(image) == _canonical_image_name(args.base_image):
                raise ValueError('Image evaluator harus berbeda dari image harness internal.')
            other_version = 'v1' if args.suite == 'v2' else 'v2'
            if _canonical_image_name(image) == _canonical_image_name(PRODUCTS_REFERENCE_IMAGES[other_version]):
                raise ValueError('Tag default evaluator versi lain tidak boleh ditimpa.')
            if not shutil.which('docker'):
                raise SandboxError('Docker belum ditemukan; image evaluator belum bisa dibangun.')
            context = Path(__file__).resolve().parents[1]/'evaluation'
            work = context.parent/'work'
            work.mkdir(exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='evaluation-build-', dir=work) as temporary:
                staged = Path(temporary)/'evaluation'
                shutil.copytree(context, staged)
                shutil.copyfile(context.parent/'harness'/'runtime.php', staged/'runtime.php')
                if args.suite == 'v2':
                    shutil.copyfile(staged/'products-v2'/'phpunit-evaluation.xml', staged/'phpunit-evaluation.xml')
                    shutil.copyfile(staged/'products-v2'/'ProductsReferenceV2Test.php',
                                    staged/'reference-tests'/'ProductsReferenceV2Test.php')
                console.stop()
                result = subprocess.run(['docker', 'build', '--tag', image,
                                         '--build-arg', 'HARNESS_IMAGE='+args.base_image,
                                         '--build-arg', 'SUITE_SHA256='+reference_suite_hash(args.suite), str(staged)],
                                        timeout=args.timeout, shell=False, stdout=sys.stderr, stderr=sys.stderr)
            emit({'status': 'BUILT' if result.returncode == 0 else 'ERROR',
                  'image': image, 'exit_code': result.returncode, 'suite': args.suite})
            return 0 if result.returncode == 0 else 3
        if args.command == 'reference-check-products':
            runner = ReferenceDockerRunner(image=args.image, suite_version=args.suite,
                                           output_root=args.output, timeout=args.timeout)
            result = runner.check_candidate(args.code) if args.code else runner.check_reference()
            emit(result)
            return 0 if result['status'] in ('READY', 'PASSED_REFERENCE') else (3 if result['status'] == 'ERROR' else 1)
        if args.command in ('evaluate-products', 'evaluate-resource'):
            if args.command == 'evaluate-resource':
                runner = ResourceReferenceRunner(load_spec(args.loop_directory/'spec.json'), image=args.image,
                                                 output_root=args.output/'harness', timeout=args.timeout)
                folder = evaluate_resource(args.loop_directory, args.output, runner)
            else:
                runner = ReferenceDockerRunner(image=args.image, suite_version=args.suite,
                                               output_root=args.output/'harness', timeout=args.timeout)
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
            result = loop_summary(folder)
            emit(result)
            return {'LOLOS': 0, 'BELUM LOLOS': 1, 'ERROR': 3}[result['status']]
        if args.command in ('harness-build', 'harness-check', 'check-products'):
            runner = DockerRunner(image=args.image, output_root=args.output, timeout=args.timeout)
            if args.command == 'harness-build':
                if not shutil.which('docker'):
                    raise SandboxError('Docker belum ditemukan; image belum bisa dibangun.')
                context = Path(__file__).resolve().parents[1]/'harness'
                console.stop()
                result = subprocess.run(['docker', 'build', '--tag', args.image, str(context)],
                                        timeout=args.timeout, shell=False, stdout=sys.stderr, stderr=sys.stderr)
                emit({'status': 'BUILT' if result.returncode == 0 else 'ERROR',
                      'image': args.image, 'exit_code': result.returncode})
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
        console.error(f'ERROR: {exc}')
        return 2
    except (StaticEnvironmentError, SandboxError, subprocess.TimeoutExpired) as exc:
        console.error(f'ERROR lingkungan: {exc}')
        return 3


def loop_summary(folder):
    result = json.loads((folder/'history.json').read_text(encoding='utf-8'))
    summary = []
    for entry in result['attempts']:
        tests = entry.get('dynamic', {}).get('summary', {})
        summary.append({'attempt': entry['iteration'], 'dynamic_status': entry['dynamic_status'],
                        'passed': tests.get('passed'), 'total': tests.get('total'),
                        'findings': len(entry['findings']), 'error': entry.get('error')})
    return {'status': result['status'], 'stop_reason': result['stop_reason'],
            'revision_count': result['revision_count'], 'run_directory': str(folder.resolve()),
            'final_controller': str((folder/'final_controller.php').resolve()) if (folder/'final_controller.php').is_file() else None,
            'history': summary}
