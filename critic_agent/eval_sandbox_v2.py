"""Separate final-package images and bound Docker observations."""
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path
import re
import subprocess
from uuid import uuid4

from .eval_package_v2 import PACKAGE, ROOT, package_manifest, suite_cases, test_id
from .final_controls import _source
from .process import bounded_run
from .resources import render_resource
from .sandbox import DockerRunner, SandboxError

LABEL_PACKAGE='org.critic.final-package-sha256'
LABEL_ROLE='org.critic.final-role'
LABEL_SUITE='org.critic.final-suite-sha256'
LABEL_SPEC='org.critic.final-spec-sha256'


def runtime_expectations():
    raw=(ROOT/'harness/laravel/composer.lock').read_bytes()
    lock=json.loads(raw)
    versions={p['name']:p['version'] for p in lock['packages']+lock.get('packages-dev',[])
              if p['name'] in ('laravel/framework','phpunit/phpunit')}
    return {'packages':versions,'lock_sha256':hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()}


def verify_base(base_image, output, *, timeout=600, execute=subprocess.run):
    """Inspect one immutable base and probe trusted installed packages only."""
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    raw=execute(['docker','image','inspect','--format','{{json .}}',base_image],capture_output=True,timeout=timeout,shell=False)
    if raw.returncode:raise SandboxError('Base image tidak dapat diperiksa: '+(raw.stderr or b'').decode(errors='replace')[:2000])
    base=json.loads(raw.stdout);config=base.get('Config') or {};labels=config.get('Labels') or {}
    forbidden={'org.critic.reference-suite-sha256','org.critic.resource-contract-sha256',LABEL_PACKAGE}
    if config.get('Entrypoint')!=['php','/opt/critic-entrypoint.php'] or not isinstance(labels,dict) or forbidden.intersection(labels):
        raise SandboxError('Base harus harness internal asli, bukan evaluator/resource/final.')
    pinned=base.get('Id','')
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',pinned):raise SandboxError('Base image ID invalid.')
    if base_image.startswith('sha256:') and base_image!=pinned:raise SandboxError('Base image ID berubah.')
    script=r'''require '/opt/harness/vendor/autoload.php'; echo json_encode(['php_version'=>PHP_VERSION,'lock_sha256'=>hash('sha256',str_replace("\r\n","\n",file_get_contents('/opt/harness/composer.lock'))),'packages'=>['laravel/framework'=>Composer\InstalledVersions::getPrettyVersion('laravel/framework'),'phpunit/phpunit'=>Composer\InstalledVersions::getPrettyVersion('phpunit/phpunit')]]);'''
    name='critic-final-runtime-'+uuid4().hex
    command=DockerRunner(image=pinned).command(name,output)[:-2]+['--entrypoint','php',pinned,'-r',script]
    result={'image_id':pinned,'command':command,'status':'ERROR'}
    try:
        probe=execute(command,capture_output=True,timeout=timeout,shell=False)
        (output/'stdout.log').write_bytes(probe.stdout or b'');(output/'stderr.log').write_bytes(probe.stderr or b'')
        if probe.returncode:raise SandboxError('Trusted runtime probe gagal.')
        observed=json.loads(probe.stdout);result['observed']=observed
        expected=runtime_expectations()
        if not str(observed.get('php_version','')).startswith('8.3.') or observed.get('lock_sha256')!=expected['lock_sha256'] or observed.get('packages')!=expected['packages']:
            raise SandboxError('Installed runtime tidak cocok PHP 8.3 / Composer lock Laravel/PHPUnit.')
        result['status']='VERIFIED'
    finally:
        try:
            cleanup=execute(['docker','rm','--force',name],capture_output=True,timeout=timeout,shell=False)
            result['cleanup_exit_code']=cleanup.returncode
            if cleanup.returncode:result.update(status='ERROR',reason='cleanup_failed')
        finally:_write(output/'runtime.json',result)
    if result['status']!='VERIFIED':raise SandboxError('Runtime probe cleanup gagal.')
    return result


def _write(path, value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def image_tag(resource, role):
    meta=package_manifest(resource)
    if role not in ('internal','reference'):
        raise ValueError('Role final harus internal/reference.')
    return 'critic-final-v2-'+resource+'-'+role+':'+meta[role+'_sha256'][:16]


def render_final(resource, role):
    if role not in ('internal','reference'):
        raise ValueError('Role final harus internal/reference.')
    meta=package_manifest(resource)
    spec=meta['spec']
    scaffold=render_resource(spec)
    files={name:source for name,source in scaffold.items()
           if name.startswith(('app/','routes/','database/')) or name=='runtime.php'}
    files['app/Http/Controllers/'+spec['controller']+'.php']=_source(spec)
    config=(ROOT/'harness/laravel/phpunit.xml').read_text(encoding='utf-8')
    start,end=config.index('  <testsuites>'),config.index('  </testsuites>')+len('  </testsuites>')
    class_file='FinalInternalTest.php' if role=='internal' else 'FinalReferenceTest.php'
    config=config[:start]+'  <testsuites><testsuite name="Final"><file>final/'+class_file+'</file></testsuite></testsuites>'+config[end:]
    files['phpunit-final.xml']=config
    for name in ('Assertions.php','Suite.php'):
        files['final/'+(class_file if name=='Suite.php' else name)]=(PACKAGE/role/name).read_text(encoding='utf-8')
    files['final/profile.json']=json.dumps({'spec':spec,
        'fixtures':meta['internal_fixtures'] if role=='internal' else meta['profile']['fixtures'],
        'cases':suite_cases(spec,meta['profile'],role=='internal')},indent=2)+'\n'
    files['entrypoint.php']='''<?php
declare(strict_types=1);
$mode=$argv[1] ?? '';
if (!in_array($mode, ['final-ROLE-readiness','final-ROLE-candidate'],true)) {
    fwrite(STDERR,"Wrong final package role/mode\\n"); exit(2);
}
require '/opt/critic-runtime.php';
runHarness($mode==='final-ROLE-candidate','phpunit-final.xml','Final');
'''.replace('ROLE',role)
    files['Dockerfile']='''ARG BASE_IMAGE
FROM ${BASE_IMAGE}
USER root
RUN rm -rf /opt/harness/database/migrations /opt/harness/tests/Feature /opt/harness/tests/Support /opt/harness/reference /opt/harness/critic /opt/harness/final \\
    && mkdir -p /opt/harness/database/migrations
COPY app/ /opt/harness/app/
COPY database/ /opt/harness/database/
COPY routes/ /opt/harness/routes/
COPY final/ /opt/harness/final/
COPY phpunit-final.xml /opt/harness/phpunit-final.xml
COPY runtime.php /opt/critic-runtime.php
COPY entrypoint.php /opt/critic-final-entrypoint.php
LABEL org.critic.final-package-sha256="PACKAGE_HASH" \\
      org.critic.final-spec-sha256="SPEC_HASH" \\
      org.critic.final-suite-sha256="SUITE_HASH" \\
      org.critic.final-role="ROLE"
RUN chmod -R a+rX /opt/harness /opt/critic-runtime.php /opt/critic-final-entrypoint.php
USER 10001:10001
ENTRYPOINT ["php", "/opt/critic-final-entrypoint.php"]
CMD ["final-ROLE-readiness"]
'''.replace('PACKAGE_HASH',meta['package_sha256']).replace('SPEC_HASH',meta['spec_sha256']).replace(
        'SUITE_HASH',meta[role+'_sha256']).replace('ROLE',role)
    return files


def build_final(resource, role, output_root, *, base_image='critic-laravel:dev', timeout=600, execute=subprocess.run):
    meta=package_manifest(resource)
    target=image_tag(resource,role)
    DockerRunner(image=base_image,timeout=timeout)
    folder=Path(output_root)/('build_'+uuid4().hex)
    context=folder/'context'; context.mkdir(parents=True,exist_ok=False)
    result={'status':'ERROR','stage':'inspect_base','resource':resource,'role':role,'image':target,
            'package_sha256':meta['package_sha256'],'suite_sha256':meta[role+'_sha256'],
            'spec_sha256':meta['spec_sha256'],'base_image':base_image,'timeout_seconds':timeout}
    temporary=None
    try:
        files=render_final(resource,role)
        for name,source in files.items():
            path=context/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(source.encode())
        verified=verify_base(base_image,folder/'base-runtime',timeout=timeout,execute=execute)
        result['base_runtime']=verified
        result['base_image_id']=verified['image_id'];result['stage']='lint'
        for name,source in files.items():
            if name.endswith('.php'):
                lint=subprocess.run(['php','-n','-l'],input=source.encode(),capture_output=True,timeout=15,shell=False)
                if lint.returncode:raise SandboxError('Lint scaffold gagal: '+name+' '+(lint.stdout+lint.stderr).decode(errors='replace'))
        result['stage']='pin_base';temporary='critic-final-base-'+uuid4().hex+':validation'
        result['base_pin_command']=['docker','image','tag',verified['image_id'],temporary]
        pinned=execute(result['base_pin_command'],capture_output=True,timeout=timeout,shell=False)
        if pinned.returncode:raise SandboxError('Gagal mem-pin base image.')
        result['stage']='build'
        result['command']=['docker','build','--pull=false','--tag',target,'--build-arg','BASE_IMAGE='+temporary,str(context.resolve())]
        built=execute(result['command'],capture_output=True,timeout=timeout,shell=False)
        (folder/'stdout.log').write_bytes(built.stdout or b'');(folder/'stderr.log').write_bytes(built.stderr or b'')
        result['exit_code']=built.returncode
        if built.returncode:raise SandboxError('Docker build gagal; lihat log build.')
        inspected=execute(['docker','image','inspect','--format','{{json .}}',target],capture_output=True,timeout=timeout,shell=False)
        if inspected.returncode:raise SandboxError('Image hasil build tidak dapat diperiksa.')
        actual=json.loads(inspected.stdout)
        labels=(actual.get('Config') or {}).get('Labels') or {}
        expected={LABEL_PACKAGE:meta['package_sha256'],LABEL_ROLE:role,LABEL_SUITE:meta[role+'_sha256'],LABEL_SPEC:meta['spec_sha256']}
        if not re.fullmatch(r'sha256:[a-f0-9]{64}',actual.get('Id','')) or any(labels.get(k)!=v for k,v in expected.items()):
            raise SandboxError('Image hasil build tidak terikat paket/role.')
        result['image_id']=actual['Id']
        result.update(status='BUILT',stage='completed')
    except subprocess.TimeoutExpired as exc:
        result.update(reason='timeout',detail=str(exc))
        if exc.output:(folder/'stdout.log').write_bytes(exc.output)
        if exc.stderr:(folder/'stderr.log').write_bytes(exc.stderr)
    except (OSError,ValueError,TypeError,AttributeError,SandboxError) as exc:
        result.update(reason='build_error',detail=str(exc))
    finally:
        if temporary is not None:
            try:
                result['base_cleanup_command']=['docker','image','rm',temporary]
                cleaned=execute(result['base_cleanup_command'],capture_output=True,timeout=timeout,shell=False)
                result['base_cleanup_exit_code']=cleaned.returncode
                if cleaned.returncode and result['status']=='BUILT':result.update(status='ERROR',reason='cleanup_failed')
            except (OSError,subprocess.TimeoutExpired) as exc:
                result['cleanup_detail']=str(exc)
                if result['status']=='BUILT':result.update(status='ERROR',reason='cleanup_failed')
        _write(folder/'build_result.json',result)
    return folder


class FinalRunner(DockerRunner):
    def __init__(self, resource, role, *, image=None, execute=bounded_run, **kwargs):
        self.meta=package_manifest(resource)
        if role not in ('internal','reference'):raise ValueError('Role final invalid.')
        self.resource,self.role=resource,role
        self.reference_mode='final-'+role+'-readiness';self.candidate_mode='final-'+role+'-candidate'
        self.reference_tests=self.candidate_tests=self.meta[role+'_tests']
        self.candidate_pass_status='PASSED_INTERNAL' if role=='internal' else 'PASSED_REFERENCE'
        self.candidate_fail_status='FAILED_INTERNAL' if role=='internal' else 'FAILED_REFERENCE'
        super().__init__(image=image or image_tag(resource,role),execute=execute,**kwargs)
        self._readiness=None

    def check_reference(self):
        result=self._run(None)
        self._readiness=result if result.get('status')=='READY' else None
        if self._readiness:self.image=result['image_id']
        return result

    def check_candidate(self, candidate):
        candidate=Path(candidate).resolve(strict=True)
        if not candidate.is_file() or candidate.stat().st_size>1_000_000 or ',' in str(candidate):
            raise SandboxError('Controller harus berupa file maksimal 1 MB dengan path tanpa koma.')
        ready=self._readiness
        if ready is None or ready.get('image_id')!=self.image:ready=self.check_reference()
        if ready.get('status')!='READY':
            return {'status':'ERROR','reason':'reference_not_ready','readiness':ready}
        result=self._run(candidate,image=ready['image_id'])
        result['readiness_directory']=ready['run_directory']
        if result.get('run_directory'):self._write_result(Path(result['run_directory']),result)
        return result

    def _error(self, reason, detail):
        folder=self.output_root/('critic-final-'+uuid4().hex);folder.mkdir(parents=True,exist_ok=False)
        result={'status':'ERROR','reason':reason,'detail':detail,'run_directory':str(folder.resolve())}
        self._write_result(folder,result);return result

    def _run(self, candidate, image=None):
        try:
            if package_manifest(self.resource)['package_sha256']!=self.meta['package_sha256']:
                raise SandboxError('Paket berubah selama validasi.')
            inspected=self.execute(['docker','image','inspect','--format','{{json .}}',image or self.image],capture_output=True,timeout=10,shell=False)
            if inspected.returncode:raise SandboxError((inspected.stderr or b'').decode(errors='replace')[:2000])
            identity=json.loads(inspected.stdout)
            config=identity.get('Config') or {};labels=config.get('Labels') or {}
            expected={LABEL_PACKAGE:self.meta['package_sha256'],LABEL_ROLE:self.role,
                      LABEL_SUITE:self.meta[self.role+'_sha256'],LABEL_SPEC:self.meta['spec_sha256']}
            if config.get('Entrypoint')!=['php','/opt/critic-final-entrypoint.php'] or not isinstance(labels,dict) or any(labels.get(k)!=v for k,v in expected.items()):
                raise SandboxError('Label/role/entrypoint image tidak cocok paket final.')
            pinned=identity.get('Id','')
            if not re.fullmatch(r'sha256:[a-f0-9]{64}',pinned):raise SandboxError('Image ID invalid.')
            if image and image.startswith('sha256:') and image!=pinned:raise SandboxError('Image ID berubah.')
        except (OSError,ValueError,TypeError,AttributeError,subprocess.TimeoutExpired,SandboxError) as exc:
            return self._error('image_binding_error',str(exc))
        result=super()._run(candidate,image=pinned)
        result.update(package='final-v2',package_sha256=self.meta['package_sha256'],
                      spec_sha256=self.meta['spec_sha256'],suite_sha256=self.meta[self.role+'_sha256'],role=self.role)
        if result.get('status')!='ERROR':
            summary=result.get('summary',{})
            expected_ids={(test_id(self.role,c['case_id'])['class'],test_id(self.role,c['case_id'])['name'])
                          for c in suite_cases(self.meta['spec'],self.meta['profile'],self.role=='internal')}
            actual={(c.get('class'),c.get('name')) for c in summary.get('cases',[])}
            if result.get('cleanup_exit_code')!=0:
                result.update(status='ERROR',reason='cleanup_failed')
            elif result.get('image_id')!=pinned or actual!=expected_ids or summary.get('error') or summary.get('skipped'):
                result.update(status='ERROR',reason='incomplete_or_wrong_cases')
        if result.get('run_directory'):self._write_result(Path(result['run_directory']),result)
        return result
