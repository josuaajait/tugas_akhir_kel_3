"""Final-v1 bindings for the common pair loop, plus explicitly synthetic smoke."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import uuid4

from .ab_archive import ROOT, artifact_index, engine_manifest, read_json, relative, sha
from .final_package import PACKAGE, RESOURCES, package_manifest
from .final_sandbox import FinalRunner
from .eval_registry import get_package_api,get_sandbox_api
from .generation import extract_php, ExtractionError
from .orchestrator import _run_loop, _write_json
from .reference import _evaluate_pair
from .sandbox import DockerRunner, SandboxError
from .process import OutputLimitError


class SyntheticClient:
    """Fixed local fixtures. No HTTP transport or Ollama connection exists."""
    def __init__(self,resource,*,scenario='repair',seed=101,package='final-v1'):
        if resource not in RESOURCES or scenario not in ('repair','format_fail','syntax_fail','already_valid'):
            raise ValueError('Unknown synthetic scenario/resource.')
        self.resource,self.scenario,self.package=resource,scenario,package
        api=get_package_api(package)
        self.model='synthetic-fixture-'+package;self.base_url='http://127.0.0.1:11434';self.timeout=300
        self.options={'temperature':0.2,'seed':seed,'num_ctx':8192,'num_predict':4096}
        self.metadata_transport=None;self.last_transport_attempts=[];self.requests=[]
        self.good=(api.PACKAGE/'controls'/resource/'explicit.php').read_text(encoding='utf-8')
        self.initial=(api.PACKAGE/'controls'/resource/'store_status.php').read_text(encoding='utf-8')
        if scenario=='already_valid':self.initial=self.good
        elif scenario=='format_fail':self.initial='Synthetic response without PHP code.'
        elif scenario=='syntax_fail':self.initial='<?php\nBROKEN_SYNTAX'

    def model_identity(self):
        return {'status':'synthetic','requested_name':self.model,'digest':None,'quantization':None,
                'ollama_version':None,'issues':['controlled_fixture_not_ollama']}

    def generate(self,prompt):
        first=not self.requests
        self.requests.append({'prompt':prompt,'options':dict(self.options)})
        generic='"message": "Keluaran ini belum lolos pemeriksaan.' in prompt
        return {'response':self.initial if first or generic else self.good,'done':True,
                'model':self.model,'synthetic_fixture':True}


class ReferenceSyntaxMixin:
    """Lint untrusted syntax inside the same pinned PHP image, never on host."""
    def check_candidate(self,candidate):
        candidate=Path(candidate).resolve(strict=True)
        if not candidate.is_file() or candidate.stat().st_size>1_000_000 or ',' in str(candidate):
            raise SandboxError('Invalid candidate file/path.')
        ready=self._readiness
        if ready is None or ready.get('image_id')!=self.image:ready=self.check_reference()
        if ready.get('status')!='READY':return {'status':'ERROR','reason':'reference_not_ready','readiness':ready}
        if get_package_api(self.meta['package']).package_manifest(self.resource)['package_sha256']!=self.meta['package_sha256']:
            return self._error('package_changed','Final package changed before syntax preflight.')
        name='critic-ab-syntax-'+uuid4().hex
        folder=self.output_root/name;folder.mkdir(parents=True,exist_ok=False)
        snapshot=folder/'candidate.php';snapshot.write_bytes(candidate.read_bytes())
        image=ready['image_id']
        command=DockerRunner(image=image).command(name,folder,snapshot)[:-2]+[
            '--entrypoint','php',image,'-n','-l','/input/controller.php']
        result={'status':'ERROR','reason':'syntax_preflight_incomplete','executed':False,'image_id':image,
                'candidate_sha256':sha(snapshot),'suite_sha256':self.meta['reference_sha256'],
                'package_sha256':self.meta['package_sha256'],'run_directory':str(folder.resolve()),'command':command}
        try:
            run=self.execute(command,capture_output=True,timeout=self.timeout,shell=False)
            (folder/'stdout.log').write_bytes(run.stdout or b'');(folder/'stderr.log').write_bytes(run.stderr or b'')
            result['exit_code']=run.returncode
            if run.returncode==0:result.update(status='SYNTAX_OK',reason='syntax_valid')
            elif b'Errors parsing /input/controller.php' in (run.stdout or b''):
                result.update(status='UNLOADABLE_CODE',reason='invalid_syntax',diagnostic=(run.stdout+run.stderr).decode(errors='replace')[:16000])
        except OutputLimitError as exc:
            (folder/'stdout.log').write_bytes(exc.output);(folder/'stderr.log').write_bytes(exc.stderr)
            result.update(reason='output_limit')
        except (OSError,subprocess.TimeoutExpired) as exc:
            result.update(reason='syntax_preflight_environment_error',detail=str(exc))
        finally:
            try:
                clean=self.execute(['docker','rm','--force',name],capture_output=True,timeout=10,shell=False)
                result['cleanup_exit_code']=clean.returncode
                if clean.returncode:result.update(status='ERROR',reason='cleanup_failed')
            except (OSError,subprocess.TimeoutExpired) as exc:
                result.update(status='ERROR',reason='cleanup_failed',detail=str(exc))
            self._write_result(folder,result)
        if result['status']!='SYNTAX_OK':return result
        observed=super().check_candidate(snapshot)
        observed['syntax_preflight_directory']=str(folder.resolve())
        if observed.get('run_directory'):self._write_result(Path(observed['run_directory']),observed)
        return observed


class FinalReference(ReferenceSyntaxMixin,FinalRunner):
    """Historical final-v1 reference runner."""


def reference_runner(package,resource,**kwargs):
    if package=='final-v1':return FinalReference(resource,'reference',**kwargs)
    base=get_sandbox_api(package).FinalRunner
    class VersionedReference(ReferenceSyntaxMixin,base):pass
    return VersionedReference(resource,'reference',**kwargs)


class FinalABAdapter:
    def __init__(self,spec,client,runner,reference,context):
        self.api=get_package_api((context or {}).get('package','final-v1'))
        self.meta=self.api.package_manifest(spec['resource'])
        if spec!=self.meta['spec']:raise ValueError('Final spec must match its registered contract.')
        for role,current in [('internal',runner),('reference',reference)]:
            if (getattr(current,'role',None)!=role or getattr(current,'meta',{}).get('package_sha256')!=self.meta['package_sha256']
                    or getattr(current,'candidate_tests',None)!=self.meta[role+'_tests']
                    or getattr(current,'resource',None)!=spec['resource']
                    or current.meta.get('spec')!=spec
                    or current.meta.get(role+'_sha256')!=self.meta[role+'_sha256']):
                raise ValueError('Final runner is not bound to the correct package/role/count.')
        self.context=dict(context or {})
        if self.context.get('origin')=='synthetic_validation':
            if not isinstance(client,SyntheticClient) or self.context.get('stage')!='synthetic_validation':
                raise ValueError('Synthetic context requires the built-in no-network fixture client.')
            if client.package!=self.meta['package']:raise ValueError('Synthetic package binding differs.')
            self.context['scenario']=client.scenario
        else:
            from .ab_protocol import validate_final_context
            self.context=validate_final_context(self.context,spec,client,runner,reference)
        self.client,self.runner,self.reference=client,runner,reference

    def metadata(self):
        return {'schema_version':'1.0','ab_protocol_version':'1.0',**self.context,
                'package':self.meta['package'],'package_sha256':self.meta['package_sha256'],
                'package_spec_sha256':self.meta['spec_sha256'],
                'internal_suite_sha256':self.meta['internal_sha256'],
                'reference_suite_sha256':self.meta['reference_sha256'],
                'expected_internal_tests':self.meta['internal_tests'],
                'expected_reference_tests':self.meta['reference_tests'],
                'qwen_calls':0 if self.context['origin']=='synthetic_validation' else None}

    def validate_schedule(self,order_seed,seeds,repetition):
        if self.context['origin']!='synthetic_validation':
            expected=self.context['schedule']
            if (order_seed!=expected['order_seed'] or seeds!=expected['revision_seeds']
                    or repetition!=expected['repetition']):
                raise ValueError('Requested seeds/order/repetition differ from frozen schedule.')

    def snapshot(self,folder,report):
        digest,sources=engine_manifest();report['engine_source_sha256']=digest;report['engine_sources']=sources
        self.folder=folder
        if self.context.get('frozen_engine_source_sha256') and digest!=self.context['frozen_engine_source_sha256']:
            raise ValueError('Prototype changed after protocol validation.')
        for name,expected in sources.items():
            source=ROOT/name;target=folder/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(source.read_bytes())
            if sha(target)!=expected:raise ValueError('Prototype source changed while snapshotting.')
        _write_json(folder/'package_manifest.json',self.meta)
        self.runner.output_root=folder/'harness/internal';self.reference.output_root=folder/'harness/reference'
        if self.context.get('protocol_path'):
            source=Path(self.context['protocol_path']);target=folder/'protocol.json'
            target.write_bytes(source.read_bytes());report['protocol_snapshot']='protocol.json'
            if sha(target)!=self.context['protocol_sha256']:raise ValueError('Protocol changed after validation.')
            protocol=read_json(target)
            from .ab_archive import local_path
            for artifact in protocol['artifacts']:
                original=local_path(ROOT,artifact['path'])
                saved=local_path(folder,'protocol_evidence/'+artifact['path']);saved.parent.mkdir(parents=True,exist_ok=True)
                saved.write_bytes(original.read_bytes())
                if sha(saved)!=artifact['sha256']:raise ValueError('Protocol evidence changed during snapshot.')

    def loop(self,spec,output_root,client,runner,**kwargs):
        from .static import analyze
        before=set(Path(output_root).glob('*_loop_*')) if Path(output_root).exists() else set()
        try:
            path=_run_loop(spec,output_root,client,runner,expected_tests=self.meta['internal_tests'],
                stage='final_ab_loop',contract_sha256=self.meta['internal_sha256'],
                initial_run=kwargs.get('initial_run'),max_revisions=kwargs.get('max_revisions',3),
                static_analyzer=kwargs.get('static_analyzer',analyze),ab=kwargs.get('ab'))
        except KeyboardInterrupt as exc:
            fresh=set(Path(output_root).glob('*_loop_*'))-before
            if len(fresh)==1:
                path=fresh.pop()
                for name in ('run_manifest.json','history.json'):
                    try:
                        if not (path/name).is_file():continue
                        data=read_json(path/name);data.update(status='ERROR',stop_reason='user_cancelled')
                        if name=='run_manifest.json':data['final_code_available']=(path/'final_controller.php').is_file()
                        _write_json(path/name,data)
                    except (OSError,ValueError):pass
                exc.run_directory=str(path)
            raise
        manifest=read_json(path/'run_manifest.json')
        manifest.update(package=self.meta['package'],package_sha256=self.meta['package_sha256'],origin=self.context['origin'])
        _write_json(path/'run_manifest.json',manifest)
        return path

    def evaluate(self,source,output,evaluator,*,shared_initial):
        def validate(spec):
            if spec!=self.meta['spec']:raise ValueError('Final source spec changed.')
        folder=_evaluate_pair(source,output,evaluator,expected_tests=self.meta['reference_tests'],
            suite_sha256=self.meta['reference_sha256'],validate_contract=validate,shared_initial=shared_initial)
        result=read_json(folder/'evaluation_result.json')
        if shared_initial and result.get('initial',{}).get('shared_from'):
            result['initial']['shared_from_path']=relative(self.folder,shared_initial)
        result.update(suite_stage=self.meta['package'],evaluation_stage=self.context['stage'],package_sha256=self.meta['package_sha256'])
        _write_json(folder/'evaluation_result.json',result)
        return folder

    def finalize(self,folder,report):
        source=Path(report['initial_generation']) if report.get('initial_generation') else None
        if source is None:
            candidates=list((folder/'initial').glob('*/run_manifest.json'))
            if len(candidates)==1:
                source=candidates[0].parent;report['initial_generation']=str(source)
                manifest=read_json(source/'run_manifest.json')
                if manifest.get('model_request'):
                    from .ab import _cost
                    report['initial_cost']=_cost([manifest['model_request']],[source/'response.json'],None)
                    _write_json(folder/'initial_cost.json',{'imported':False,'cost':report['initial_cost']})
        if source and source.is_dir():
            target=folder/'initial_evidence';target.mkdir(exist_ok=True)
            for name in ('run_manifest.json','spec.json','prompt.txt','response.json','response.txt','initial_controller.php'):
                if (source/name).is_file():(target/name).write_bytes((source/name).read_bytes())
            report['initial_archive_path']='initial_evidence'
        for branch in report['branches'].values():
            if branch.get('run_directory'):branch['run_path']=relative(folder,branch['run_directory'])
            if branch.get('evaluation',{}).get('report'):
                branch['evaluation']['report_path']=relative(folder,branch['evaluation']['report'])
        if engine_manifest()[0]!=report.get('engine_source_sha256'):
            report.update(status='ERROR',reason='prototype_source_changed',n_ab=0,delta_final_pp=None)
        report['artifacts']=artifact_index(folder)


def run_synthetic_pair(resource,output_root,*,scenario='repair',order_seed=7,timeout=120,package='final-v1'):
    from .ab import run_ab
    api=get_package_api(package);meta=api.package_manifest(resource);client=SyntheticClient(resource,scenario=scenario,package=package)
    runner=get_sandbox_api(package).FinalRunner(resource,'internal',output_root=Path(output_root)/'preflight',timeout=timeout)
    reference=reference_runner(package,resource,output_root=Path(output_root)/'preflight-reference',timeout=timeout)
    return run_ab(meta['spec'],output_root,client,runner,reference,kind='final',order_seed=order_seed,
                  revision_seeds=[102,103,104],final_context={'package':package,'stage':'synthetic_validation','origin':'synthetic_validation',
                                                          'scenario':scenario})
