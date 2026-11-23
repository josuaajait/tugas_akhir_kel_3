"""Trusted contract controls and one-change mutants, never model candidates."""
import difflib
import hashlib
import json
from pathlib import Path

from .final_package import package_manifest, traceability
from .resources import _php


def _rules(spec, operation, omit=None, own=None):
    lines = []
    for field in spec['fields']:
        values = []
        for rule in field['rules']:
            if omit == (field['name'], rule.split(':')[0]):
                continue
            if rule.startswith('unique:') and operation=='update':
                value = 'Rule::unique('+_php(spec['resource'])+', '+_php(field['name'])+')'
                if own != field['name']:
                    value += '->ignore($record->getKey())'
            else:
                value = _php(rule)
            values.append(value)
        lines.append('            '+_php(field['name'])+' => ['+', '.join(values)+'],')
    return '\n'.join(lines)


def _source(spec, style='eloquent'):
    lookup = ('return Model::findOrFail($id);' if style=='eloquent' else
              "$record = Model::query()->where('id', $id)->first(); if ($record === null) abort(404); return $record;")
    store = '$record = Model::create($body);' if style=='eloquent' else '$record = new Model; $record->fill($body); $record->save();'
    update = '$record->update($body);' if style=='eloquent' else '$record->fill($body); $record->save();'
    return '''<?php
namespace App\\Http\\Controllers;
use App\\Models\\MODEL as Model;
use Illuminate\\Http\\Request;
use Illuminate\\Validation\\Rule;
// AI-prepared trusted validation control; not Qwen output or human-reviewed evidence.
class CONTROLLER extends Controller
{
    private function load($id) { LOOKUP }
    public function index()
    {
        $data = Model::all()->toArray();
        return response()->json(['data'=>$data], 200); // index response
    }
    public function store(Request $request)
    {
        // store guards
        $body = $request->validate([
STORE_RULES
        ]);
        STORE_WRITE
        return response()->json(['data'=>$record->fresh()], 201); // store response
    }
    public function show($id)
    {
        $record = $this->load($id); // show lookup
        return response()->json(['data'=>$record], 200); // show response
    }
    public function update(Request $request, $id)
    {
        $record = $this->load($id); // update lookup
        // update guards
        $body = $request->validate([
UPDATE_RULES
        ]);
        UPDATE_WRITE
        return response()->json(['data'=>$record->fresh()], 200); // update response
    }
    public function destroy($id)
    {
        $record = $this->load($id); // destroy lookup
        $record->delete();
        return response()->noContent(); // destroy response
    }
}
'''.replace('MODEL',spec['model']).replace('CONTROLLER',spec['controller']).replace('LOOKUP',lookup).replace(
        'STORE_RULES',_rules(spec,'store')).replace('UPDATE_RULES',_rules(spec,'update')).replace(
        'STORE_WRITE',store).replace('UPDATE_WRITE',update)


def control_catalog(resource):
    meta = package_manifest(resource)
    spec = meta['spec']
    base = _source(spec)
    rows = traceability(resource)
    cases = {r['case_id']: r for r in rows}
    internal_ids={r['case_id'] for r in rows if r['internal_test_id']}
    catalog = []

    def add(cid, source, targets, expected='fail', internal='fail'):
        if expected=='fail' and source==base:
            raise ValueError('Mutasi tidak mengubah kontrol: '+cid)
        if not targets or any(t not in cases for t in targets):
            raise ValueError('Target mutasi tidak terpetakan: '+cid)
        evidence={}
        for target in targets if expected=='fail' else []:
            phase='status';status=200
            if cid.startswith('index_') and cid!='index_status':phase='body'
            elif cid=='store_no_write':phase='sequence.create' if target=='sequence' else 'body';status=201
            elif cid=='store_extra_write':phase='state';status=201
            elif cid=='update_no_write':phase='body'
            elif cid=='destroy_no_delete':phase='sequence.missing' if target=='sequence' else 'state';status=200 if target=='sequence' else 204
            elif cid=='destroy_body':phase='body';status=204
            elif cid=='missing_status':status=204 if target=='missing_DELETE' else 200
            elif cid=='show_write':phase='state'
            elif cid.endswith('_status'):status=202
            elif cid.endswith('_wrong_target'):phase='body' if cid.startswith('show') else 'state';status=204 if cid.startswith('destroy') else 200
            elif '_reject_' in cid:status=422
            elif '_omit_min_' in cid or '_omit_max_' in cid:status=201 if target.startswith('POST') else 200
            evidence[target]={'phase':phase,'http_status':status}
        mapped=sorted(internal_ids.intersection(targets))
        if expected=='fail' and internal=='fail' and not mapped:
            raise ValueError('Mutasi internal memerlukan testcase target eksplisit: '+cid)
        catalog.append({'control_id':cid,'expected':expected,'expected_internal':internal,
                        'source':source,'sha256':hashlib.sha256(source.encode()).hexdigest(),
                        'base_control':'eloquent' if expected=='fail' else None,
                        'target_case_ids':targets,
                        'internal_target_case_ids':mapped,'failure_evidence':evidence,
                        'diff':''.join(difflib.unified_diff(base.splitlines(True),source.splitlines(True),
                                                         fromfile='eloquent.php',tofile=cid+'.php')) if expected=='fail' else ''})

    for style in ('eloquent','explicit'):
        add(style,_source(spec,style),list(cases),'pass','pass')
    first = spec['fields'][0]['name']
    changes = [
        ('index_swapped', '$data = Model::all()->toArray();',
         '$data = Model::all()->toArray(); if (count($data)>1) { $v=$data[0]['+_php(first)+']; $data[0]['+_php(first)+']=$data[1]['+_php(first)+']; $data[1]['+_php(first)+']=$v; }', ['index']),
        ('index_object', "['data'=>$data]", "['data'=>(object)$data]", ['index','empty']),
        ('index_string_id', '$data = Model::all()->toArray();', '$data = Model::all()->toArray(); foreach ($data as &$r) $r[\'id\']=(string)$r[\'id\']; unset($r);', ['index']),
        ('index_missing_field', '$data = Model::all()->toArray();', '$data = Model::all()->toArray(); foreach ($data as &$r) unset($r['+_php(first)+']); unset($r);', ['index']),
        ('store_no_write','$record = Model::create($body);','$record = new Model($body); $record->id=9999;', ['store','sequence']),
        ('store_extra_write','$record = Model::create($body);','$record = Model::create($body); Model::query()->where(\'id\',\'!=\',$record->id)->delete();', ['store']),
        ('update_no_write','$record->update($body);','$record->fill($body);', ['update']),
        ('destroy_no_delete','$record->delete();','/* deletion omitted */', ['destroy','sequence']),
        ('destroy_body','return response()->noContent();',"return new class('unexpected', 204) extends \\Illuminate\\Http\\Response { public function prepare(\\Symfony\\Component\\HttpFoundation\\Request $request): static { return $this; } };", ['destroy']),
        ('missing_status','return Model::findOrFail($id);','return Model::find($id) ?? new Model;', ['missing_GET','missing_PUT','missing_DELETE']),
        ('show_write','$record = $this->load($id); // show lookup', '$record = $this->load($id); Model::query()->delete(); // show lookup',['show']),
    ]
    for op in ('index','store','show','update'):
        status=201 if op=='store' else 200
        old=', '+str(status)+'); // '+op+' response'
        changes.append((op+'_status',old,', 202); // '+op+' response',[op]))
    for op in ('show','update','destroy'):
        old='$record = $this->load($id); // '+op+' lookup'
        changes.append((op+'_wrong_target',old,"$record = Model::query()->where('id','!=',$id)->firstOrFail(); // "+op+' lookup',[op]))
    strings=[f['name'] for f in spec['fields'] if f['type']=='string']
    if len(strings)>1:
        left,right=map(_php,strings[:2])
        changes.append(('index_cross_field','$data = Model::all()->toArray();',
                        '$data = Model::all()->toArray(); foreach ($data as &$r) { $v=$r['+left+']; $r['+left+']=$r['+right+']; $r['+right+']=$v; } unset($r);',['index']))
    for cid,old,new,targets in changes:
        if base.count(old)!=1:
            raise ValueError('Anchor mutasi ambigu: '+cid)
        # Empty list is outside internal candidate test selection.
        add(cid,base.replace(old,new),targets,internal='fail')
    for operation,verb in [('store','POST'),('update','PUT')]:
        original=_rules(spec,operation)
        for field in spec['fields']:
            name=field['name']
            for rule in field['rules']:
                label=rule.split(':')[0]
                vectors = ['missing'] if label=='required' else (
                    ['type','object']+(['fraction'] if field['type']=='integer' else []) if label==field['type'] else [label])
                targets=[verb+'_'+v+'_'+name for v in vectors if verb+'_'+v+'_'+name in cases]
                if not targets:
                    continue
                changed=base.replace(original,_rules(spec,operation,omit=(name,label)),1)
                # Store and update rules can be byte-identical on specs without unique.
                start=base.index('public function '+operation+'(')
                changed=base[:start]+base[start:].replace(original,_rules(spec,operation,omit=(name,label)),1)
                marker='// '+operation+' guards'
                accepted=" return response()->json(['accepted'=>true], 200);"
                if label=='required' and operation=='store':
                    changed=base.replace(marker,marker+'\n        if (!$request->exists('+_php(name)+'))'+accepted)
                elif label=='unique':
                    query='Model::query()->where('+_php(name)+', $request->input('+_php(name)+'))'
                    if operation=='update':query+='->where(\'id\',\'!=\',$record->getKey())'
                    changed=base.replace(marker,marker+'\n        if (is_string($request->input('+_php(name)+')) && '+query+'->exists())'+accepted)
                elif label==field['type']:
                    value='$request->input('+_php(name)+')'
                    bad='is_array('+value+')' if field['type']=='string' else 'is_array('+value+') || is_float('+value+') || (is_string('+value+') && !preg_match(\'/^[+-]?[0-9]+$/\', '+value+'))'
                    changed=base.replace(marker,marker+'\n        if ($request->exists('+_php(name)+') && '+value+' !== null && ('+bad+'))'+accepted)
                mutation_name=(operation+'_accept_missing_'+name if label=='required' and operation=='store'
                               else operation+'_accept_duplicate_'+name if label=='unique'
                               else operation+'_accept_type_'+name if label==field['type']
                               else operation+'_omit_'+label+'_'+name)
                add(mutation_name,changed,targets,
                    internal='fail' if label=='required' else 'pass')
            marker='// '+operation+' guards'
            guard='if ($request->exists('+_php(name)+') && $request->input('+_php(name)+') === null) return response()->json([\'accepted\'=>true], 200);'
            add(operation+'_accept_null_'+name,base.replace(marker,marker+'\n        '+guard),
                [verb+'_'+v+'_'+name for v in ('null','empty','whitespace')],internal='pass')
            for rule in field['rules']:
                if not rule.startswith(('min:','max:')):
                    continue
                label,bound=rule.split(':');bound=int(bound)
                expression='is_string($request->input('+_php(name)+')) && strlen($request->input('+_php(name)+'))' if field['type']=='string' else '$request->input('+_php(name)+')'
                guard='if ('+expression+' === '+str(bound)+') abort(422);'
                # Numeric boundary input is an int in the boundary cases.
                marker='// '+operation+' guards'
                changed=base.replace(marker,marker+'\n        '+guard)
                target=verb+'_boundary_'+label+'_'+name
                bodies=[meta['internal_fixtures']['new']]
                if operation=='update':bodies.append(meta['internal_fixtures']['updated'])
                internal_match=any((len(body[name]) if field['type']=='string' else body[name])==bound for body in bodies)
                add(operation+'_reject_'+label+'_'+name,changed,[target],internal='fail' if internal_match else 'pass')
            if field['type']=='integer':
                marker='// '+operation+' guards'
                changed=base.replace(marker,marker+'\n        if (is_string($request->input('+_php(name)+'))) abort(422);')
                add(operation+'_reject_numeric_string_'+name,changed,[verb+'_numeric_string_'+name],internal='pass')
            if operation=='update' and any(r.startswith('unique:') for r in field['rules']):
                changed=base[:base.index('public function update(')]+base[base.index('public function update('):].replace(original,_rules(spec,'update',own=name),1)
                add('update_reject_own_'+name,changed,['PUT_own_'+name],internal='pass')
    return catalog


def matrix_rows(resource, controls=None):
    controls=control_catalog(resource) if controls is None else controls
    rows=traceability(resource)
    for row in rows:
        negatives=[c for c in controls if c['expected']=='fail' and row['case_id'] in c['target_case_ids']]
        row['negative_control_ids']=[c['control_id'] for c in negatives]
        row['negative_controls']=[{'control_id':c['control_id'],'sha256':c['sha256'],
                                   'expected_evidence':c['failure_evidence'][row['case_id']]} for c in negatives]
        row['positive_controls']=[{'control_id':c['control_id'],'sha256':c['sha256']} for c in controls if c['expected']=='pass']
    return rows


def materialize_controls(resource, destination):
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=True)
    catalog=control_catalog(resource)
    result={'resource':resource,'prepared_by':'OpenAI Codex','human_review_completed':False,'controls':[]}
    for control in catalog:
        path=destination/(control['control_id']+'.php')
        with path.open('x',encoding='utf-8',newline='\n') as stream:
            stream.write(control['source'])
        if control['diff']:
            with (destination/(control['control_id']+'.diff')).open('x',encoding='utf-8',newline='\n') as stream:
                stream.write(control['diff'])
        result['controls'].append({k:v for k,v in control.items() if k not in ('source','diff')}|{'path':path.name})
    with (destination/'catalog.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    return result
