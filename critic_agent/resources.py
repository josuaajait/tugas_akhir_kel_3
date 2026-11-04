"""Bounded spec-driven development harnesses. Final evaluation stays separate."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from uuid import uuid4

from .process import bounded_run
from .sandbox import DockerRunner, SandboxError
from .spec import validate_spec, SpecError

ROOT = Path(__file__).resolve().parents[1]
LABEL = 'org.critic.resource-contract-sha256'
ROLES = ('new', 'target', 'other', 'updated', 'missing')
RESERVED = set('abstract and array as bool break callable case catch class clone const continue declare default die do echo else elseif empty enddeclare endfor endforeach endif endswitch endwhile enum eval exit extends false final finally float fn for foreach function global goto if implements include include_once instanceof insteadof int interface isset iterable list match mixed namespace never new null object or parent print private protected public readonly require require_once return self static string switch throw trait true try unset use var void while xor yield'.split())


def _bounds(field):
    return {rule.split(':')[0]: int(rule.split(':')[1]) for rule in field['rules']
            if rule.startswith(('min:', 'max:'))}


def validate_resource_spec(spec):
    validate_spec(spec)
    if spec['controller'].lower() == 'controller' or spec['model'].lower() in RESERVED:
        raise SpecError('Nama class berbenturan dengan scaffold atau keyword PHP.')
    if spec['resource'] == 'migrations' or spec['resource'].startswith('sqlite_'):
        raise SpecError('Nama tabel dicadangkan untuk migration/SQLite.')
    for field in spec['fields']:
        bounds = _bounds(field)
        if field['type'] == 'string':
            if any(value > 256 for value in bounds.values()) or bounds.get('max', 256) < 1:
                raise SpecError(f"{field['name']}: harness mendukung panjang string valid 1–256; batas ini tidak didukung.")
        elif any(rule.startswith('unique:') for rule in field['rules']):
            if 'min' in bounds and 'max' in bounds and bounds['max']-bounds['min']+1 < len(ROLES):
                raise SpecError(f"{field['name']}: unique memerlukan domain minimal lima nilai untuk fixture.")
    return spec


def resource_contract(spec):
    validate_resource_spec(spec)
    spec = copy.deepcopy(spec)
    fixtures = {role: {} for role in ROLES}
    for field in spec['fields']:
        name, bounds = field['name'], _bounds(field)
        for index, role in enumerate(ROLES):
            if field['type'] == 'string':
                length = max(1, bounds.get('min', 1), min(12, bounds.get('max', 256)))
                value = chr(97+index)+'x'*(length-1)
            else:
                low = bounds.get('min', min(-10, bounds.get('max', 14)-4))
                high = bounds.get('max', max(14, low+4))
                start = max(low, min(10, high-4))
                value = low+(start-low+index) % (high-low+1)
            fixtures[role][name] = value
    invalid, valid = [], [{'name': 'base', 'payload': fixtures['new']}]
    for field in spec['fields']:
        name, bounds, string = field['name'], _bounds(field), field['type'] == 'string'
        variants = [('type', ['bad'] if string else 'not-an-integer')]
        for label, value in bounds.items():
            if string:
                # required forbids an empty value even if min:0 was declared.
                if label == 'min' and value == 0:
                    continue
                boundary = 'z'*value
                outside = 'z'*(value-1 if label == 'min' else value+1)
            else:
                boundary = value
                outside = value-1 if label == 'min' else value+1
            if not string or value > 0:
                valid.append({'name': name+'_'+label, 'payload': dict(fixtures['new'], **{name: boundary})})
            variants.append((label, outside))
        if any(rule.startswith('unique:') for rule in field['rules']):
            variants.append(('unique', fixtures['other'][name]))
        invalid.extend({'name': name+'_'+label, 'field': name,
                        'payload': dict(fixtures['new'], **{name: value})} for label, value in variants)
    digest = hashlib.sha256(json.dumps(spec, sort_keys=True, separators=(',', ':')).encode())
    paths = sorted((ROOT/'resource_templates').glob('*.php')) + [Path(__file__), ROOT/'harness'/'runtime.php', ROOT/'harness'/'laravel'/'phpunit.xml']
    for path in paths:
        digest.update(path.relative_to(ROOT).as_posix().encode()+b'\0')
        digest.update(path.read_text(encoding='utf-8').replace('\r\n', '\n').encode()+b'\0')
    return {'spec': spec, 'fixtures': fixtures, 'internal_tests': 8+2*len(spec['fields']),
            'readiness_tests': 2*len(invalid)+len(valid)+1,
            'readiness_invalid': invalid, 'readiness_valid': valid,
            'contract_sha256': digest.hexdigest(), 'stage': 'development'}


def _php(value):
    if isinstance(value, str):
        return "'"+value.replace('\\', '\\\\').replace("'", "\\'")+"'"
    if isinstance(value, list):
        return '['+', '.join(_php(item) for item in value)+']'
    if isinstance(value, dict):
        return '['+', '.join(_php(key)+' => '+_php(item) for key, item in value.items())+']'
    return str(value)


def render_resource(spec):
    contract = resource_contract(spec)
    table, model, controller = spec['resource'], spec['model'], spec['controller']
    fields = spec['fields']
    rules = {field['name']: field['rules'] for field in fields}
    store_rules = _php(rules)
    update_rules = []
    for field in fields:
        values = [f"Rule::unique({_php(table)}, {_php(field['name'])})->ignore($record->getKey())"
                  if rule.startswith('unique:') else _php(rule) for rule in field['rules']]
        update_rules.append(_php(field['name'])+' => ['+', '.join(values)+']')
    trusted = f'''<?php
namespace App\\Http\\Controllers;
use App\\Models\\{model} as ResourceModel;
use Illuminate\\Http\\Request;
use Illuminate\\Validation\\Rule;
// Trusted readiness controller, never a generated candidate.
class {controller} extends Controller
{{
    public function index() {{ return response()->json(['data' => ResourceModel::all()], 200); }}
    public function store(Request $request)
    {{
        $body = $request->validate({store_rules});
        return response()->json(['data' => ResourceModel::create($body)], 201);
    }}
    public function show($id) {{ return response()->json(['data' => ResourceModel::findOrFail($id)], 200); }}
    public function update(Request $request, $id)
    {{
        $record = ResourceModel::findOrFail($id);
        $body = $request->validate([{', '.join(update_rules)}]);
        $record->update($body);
        return response()->json(['data' => $record->fresh()], 200);
    }}
    public function destroy($id) {{ ResourceModel::findOrFail($id)->delete(); return response()->noContent(); }}
}}
'''
    model_code = f'''<?php
namespace App\\Models;
class {model} extends \\Illuminate\\Database\\Eloquent\\Model
{{
    protected $table = {_php(table)};
    protected $fillable = {_php([field['name'] for field in fields])};
    protected $casts = {_php({field['name']: 'integer' for field in fields if field['type'] == 'integer'})};
}}
'''
    columns = []
    for field in fields:
        expression = f"$table->{'text' if field['type'] == 'string' else 'integer'}({_php(field['name'])})"
        if any(rule.startswith('unique:') for rule in field['rules']):
            expression += '->unique()'
        columns.append(expression+';')
    migration = '''<?php
use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Database\\Schema\\Blueprint;
use Illuminate\\Support\\Facades\\Schema;
return new class extends Migration {
    public function up(): void {
        Schema::create('''+_php(table)+''', function (Blueprint $table) {
            $table->id();
            '''+'\n            '.join(columns)+'''
            $table->timestamps();
        });
    }
    public function down(): void { Schema::dropIfExists('''+_php(table)+'''); }
};
'''
    routes = '<?php\nuse App\\Http\\Controllers\\'+controller+';\nuse Illuminate\\Support\\Facades\\Route;\n'
    for verb, operation in [('get', 'index'), ('post', 'store'), ('get', 'show'), ('put', 'update'), ('delete', 'destroy')]:
        url = '/'+table+('/{id}' if operation in ('show', 'update', 'destroy') else '')
        routes += f'Route::{verb}({_php(url)}, [{controller}::class, {_php(operation)}]);\n'
    runtime = (ROOT/'harness'/'runtime.php').read_text(encoding='utf-8')
    old = 'app/Http/Controllers/ProductController.php'
    if runtime.count(old) != 1:
        raise ValueError('Template runtime berubah; lokasi kandidat perlu ditinjau.')
    runtime = runtime.replace(old, f'app/Http/Controllers/{controller}.php')
    configuration = (ROOT/'harness'/'laravel'/'phpunit.xml').read_text(encoding='utf-8')
    start, end = configuration.index('  <testsuites>'), configuration.index('  </testsuites>')+len('  </testsuites>')
    configuration = configuration[:start]+'''  <testsuites>
    <testsuite name="ResourceInternal"><file>tests/Feature/ResourceContractTest.php</file></testsuite>
    <testsuite name="ResourceReadiness"><file>tests/Feature/ResourceReadinessTest.php</file></testsuite>
  </testsuites>'''+configuration[end:]
    result = {f'app/Models/{model}.php': model_code, f'app/Http/Controllers/{controller}.php': trusted,
              'routes/api.php': routes, 'database/migrations/2026_11_04_000000_create_resource.php': migration,
              'critic/contract.json': json.dumps(contract, indent=2)+'\n', 'phpunit.xml': configuration,
              'runtime.php': runtime,
              'entrypoint.php': '''<?php
declare(strict_types=1);
$mode = $argv[1] ?? '';
if (!in_array($mode, ['resource-reference', 'resource-candidate'], true)) {
    fwrite(STDERR, "Resource image accepts resource modes only\\n"); exit(2);
}
require '/opt/critic-runtime.php';
runHarness($mode === 'resource-candidate', 'phpunit.xml', $mode === 'resource-candidate' ? 'ResourceInternal' : null);
''',
              'Dockerfile': '''ARG HARNESS_IMAGE=critic-laravel:dev
FROM ${HARNESS_IMAGE}
USER root
RUN rm -f /opt/harness/database/migrations/*.php
COPY app/ /opt/harness/app/
COPY database/ /opt/harness/database/
COPY routes/ /opt/harness/routes/
COPY tests/ /opt/harness/tests/
COPY critic/ /opt/harness/critic/
COPY phpunit.xml /opt/harness/phpunit.xml
COPY runtime.php /opt/critic-runtime.php
COPY entrypoint.php /opt/critic-resource-entrypoint.php
ARG CONTRACT_SHA256
LABEL org.critic.resource-contract-sha256="${CONTRACT_SHA256}"
RUN chmod -R a+rX /opt/harness /opt/critic-runtime.php /opt/critic-resource-entrypoint.php
USER 10001:10001
ENTRYPOINT ["php", "/opt/critic-resource-entrypoint.php"]
CMD ["resource-reference"]
'''}
    for name, destination in [('ResourceFixtures.php', 'tests/Support/ResourceFixtures.php'),
                              ('ResourceContractTest.php', 'tests/Feature/ResourceContractTest.php'),
                              ('ResourceReadinessTest.php', 'tests/Feature/ResourceReadinessTest.php')]:
        result[destination] = (ROOT/'resource_templates'/name).read_text(encoding='utf-8')
    return result


def _canonical_image_name(value):
    parts = value.split('/')
    if len(parts) == 1 or ('.' not in parts[0] and ':' not in parts[0] and parts[0] != 'localhost'):
        parts.insert(0, 'docker.io')
    if parts[0].lower() == 'index.docker.io':
        parts[0] = 'docker.io'
    if parts[0].lower() == 'docker.io' and len(parts) == 2:
        parts.insert(1, 'library')
    if ':' not in parts[-1] and '@' not in parts[-1]:
        parts[-1] += ':latest'
    return '/'.join(parts)


def build_resource(spec, output_root, *, image=None, base_image='critic-laravel:dev', timeout=600,
                   execute=subprocess.run):
    contract = resource_contract(spec)
    image = image or 'critic-resource-'+spec['resource']+':dev'
    DockerRunner(image=image, timeout=timeout)
    DockerRunner(image=base_image, timeout=timeout)
    protected = (base_image, 'critic-laravel:dev', 'critic-laravel-evaluation:dev')
    if _canonical_image_name(image) in {_canonical_image_name(name) for name in protected}:
        raise ValueError('Image resource harus terpisah dari image dasar/evaluator.')
    folder = Path(output_root)/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid4().hex)
    context = folder/'context'
    context.mkdir(parents=True, exist_ok=False)
    files = render_resource(spec)
    for name, source in files.items():
        path = context/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(source.encode('utf-8'))
    result = {'status': 'ERROR', 'image': image, 'base_image': base_image,
              'timeout_seconds': timeout, 'stage': 'inspect_base',
              'contract_sha256': contract['contract_sha256'], 'internal_tests': contract['internal_tests'],
              'reference_tests': contract['internal_tests']+contract['readiness_tests'],
              'context': str(context.resolve()),
              'files': {name: hashlib.sha256(source.encode()).hexdigest() for name, source in files.items()}}
    command = ['docker', 'build', '--tag', image, '--build-arg', 'HARNESS_IMAGE='+base_image,
               '--build-arg', 'CONTRACT_SHA256='+contract['contract_sha256'], str(context.resolve())]
    result['command'] = command
    temporary_base = None
    try:
        inspection = execute(['docker', 'image', 'inspect', '--format', '{{json .}}', base_image],
                             capture_output=True, timeout=timeout, shell=False)
        if inspection.returncode:
            raise SandboxError('Image dasar tidak dapat diperiksa: '+
                               (inspection.stderr or b'').decode('utf-8', errors='replace')[:2000])
        try:
            base = json.loads(inspection.stdout)
        except (ValueError, TypeError) as exc:
            raise SandboxError('Metadata image dasar tidak valid.') from exc
        config = base.get('Config', {}) if isinstance(base, dict) else {}
        labels = config.get('Labels') or {}
        if (not isinstance(labels, dict) or config.get('Entrypoint') != ['php', '/opt/critic-entrypoint.php']
                or 'org.critic.reference-suite-sha256' in labels or LABEL in labels):
            raise SandboxError('Image dasar harus harness internal; image evaluator/resource dan aliasnya ditolak.')
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', base.get('Id', '')):
            raise SandboxError('Identitas image dasar tidak valid.')
        result['base_image_id'] = base['Id']
        result['stage'] = 'lint_scaffold'
        for name, source in files.items():
            if name.endswith('.php'):
                lint = subprocess.run(['php', '-n', '-l'], input=source.encode(), capture_output=True,
                                      timeout=15, shell=False)
                if lint.returncode:
                    raise SandboxError('Generated scaffold gagal lint: '+name+'\n'+
                                       (lint.stdout+lint.stderr).decode('utf-8', errors='replace'))
        # BuildKit FROM resolution differs for image IDs and manifest digests.
        # Own an unguessable temporary reference to the inspected ID instead of
        # resolving the user's mutable tag a second time during the build.
        pinned = 'critic-build-base-'+uuid4().hex+':dev'
        result['base_pin_command'] = ['docker', 'image', 'tag', base['Id'], pinned]
        result['base_build_reference'] = temporary_base = pinned
        result['stage'] = 'pin_base'
        # A client timeout does not prove the daemon failed to create the tag.
        # Register ownership before the call so finally still attempts cleanup.
        tagged = execute(result['base_pin_command'], capture_output=True, timeout=timeout, shell=False)
        if tagged.returncode:
            raise SandboxError('Image dasar tidak dapat dipertahankan untuk build.')
        command[command.index('HARNESS_IMAGE='+base_image)] = 'HARNESS_IMAGE='+pinned
        result['stage'] = 'build'
        built = execute(command, timeout=timeout, shell=False)
        result.update(status='BUILT' if built.returncode == 0 else 'ERROR', exit_code=built.returncode)
        if built.returncode:
            result.update(failed_stage='build', reason='docker_build_failed')
        else:
            result.update(stage='completed', reason='build_completed')
    except subprocess.TimeoutExpired as exc:
        result.update(failed_stage=result['stage'], reason='timeout', detail=str(exc))
    except (OSError, SandboxError) as exc:
        result.update(failed_stage=result['stage'], reason='build_error', detail=str(exc))
    finally:
        if temporary_base is not None:
            cleanup_command = ['docker', 'image', 'rm', temporary_base]
            result['base_cleanup_command'] = cleanup_command
            try:
                cleanup = execute(cleanup_command, capture_output=True, timeout=timeout, shell=False)
                result['base_cleanup_exit_code'] = cleanup.returncode
                if cleanup.returncode:
                    result['base_cleanup_detail'] = (cleanup.stderr or b'').decode('utf-8', errors='replace')[:2000]
                    if result['status'] == 'BUILT':
                        result.update(status='ERROR', failed_stage='cleanup_base', reason='cleanup_failed',
                                      detail='Build selesai tetapi tag dasar sementara gagal dibersihkan.')
            except (OSError, subprocess.TimeoutExpired) as exc:
                result['base_cleanup_detail'] = str(exc)
                if result['status'] == 'BUILT':
                    result.update(status='ERROR', failed_stage='cleanup_base', reason='cleanup_failed',
                                  detail='Pembersihan tag dasar sementara gagal: '+str(exc))
        (folder/'build_result.json').write_bytes((json.dumps(result, indent=2)+'\n').encode())
    return folder


class ResourceDockerRunner(DockerRunner):
    reference_mode = 'resource-reference'
    candidate_mode = 'resource-candidate'

    def __init__(self, spec, *, image=None, execute=bounded_run, **kwargs):
        contract = resource_contract(spec)
        self.spec = copy.deepcopy(spec)
        self.contract_sha256 = contract['contract_sha256']
        self.candidate_tests = contract['internal_tests']
        self.reference_tests = self.candidate_tests+contract['readiness_tests']
        super().__init__(image=image or 'critic-resource-'+spec['resource']+':dev', execute=execute, **kwargs)

    def check_reference(self):
        result = super().check_reference()
        if result['status'] != 'READY':
            return result
        try:
            label = self.execute(['docker', 'image', 'inspect', '--format',
                                  '{{ index .Config.Labels "'+LABEL+'" }}', result['image_id']],
                                 capture_output=True, timeout=10, shell=False)
            actual = label.stdout.decode('utf-8', errors='replace').strip()
            result.update(resource_contract_sha256=actual, expected_contract_sha256=self.contract_sha256)
            if label.returncode or actual != self.contract_sha256:
                result.update(status='ERROR', reason='contract_mismatch')
        except (OSError, subprocess.TimeoutExpired, SandboxError) as exc:
            result.update(status='ERROR', reason='contract_inspection_error', detail=str(exc))
        self._write_result(Path(result['run_directory']), result)
        return result
