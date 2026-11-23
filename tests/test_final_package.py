import copy
import hashlib
import json
from pathlib import Path
import unittest

from critic_agent.final_package import load_package, package_manifest, traceability, validate_profile

ROOT = Path(__file__).resolve().parents[1]


class FinalPackageTests(unittest.TestCase):
    def test_junit_class_identity_and_field_distinct_internal_fixtures(self):
        from critic_agent.final_package import test_id
        from critic_agent.sandbox import parse_junit
        case=parse_junit(b'<testsuite><testcase classname="FinalEvaluation.FinalInternalTest" class="FinalEvaluation\\FinalInternalTest" name="test_contract with data set &quot;index&quot;"/></testsuite>')['cases'][0]
        self.assertEqual(case['class'],test_id('internal','index')['class'])
        for meta in load_package():
            strings=[f['name'] for f in meta['spec']['fields'] if f['type']=='string']
            for body in meta['internal_fixtures'].values():
                self.assertEqual(len({body[f] for f in strings}),len(strings))

    def test_five_fixed_specs_and_counts(self):
        packages = load_package()
        self.assertEqual([p['spec']['resource'] for p in packages],
                         ['categories', 'rooms', 'assets', 'courses', 'shipments'])
        self.assertEqual([p['internal_tests'] for p in packages], [12, 12, 14, 14, 18])
        for p in packages:
            self.assertEqual(p['stage'], 'pre_freeze_validation')
            self.assertEqual(p, package_manifest(p['spec']['resource']))
            self.assertFalse(p['ready_for_final'])
            self.assertNotEqual(p['profile']['fixtures'], p['internal_fixtures'])

    def test_every_dataset_and_constraint_has_traceability(self):
        for p in load_package():
            rows = traceability(p['spec']['resource'])
            self.assertEqual(len({r['case_id'] for r in rows}), len(rows))
            self.assertEqual(sum(bool(r['reference_test_id']) for r in rows), p['reference_tests'])
            self.assertEqual(sum(bool(r['internal_test_id']) for r in rows), p['internal_tests'])
            self.assertTrue(all(r['review_status'] == 'pending' for r in rows))
            for field in p['spec']['fields']:
                for verb in ('POST', 'PUT'):
                    for variant in ('missing', 'null', 'empty', 'whitespace', 'type'):
                        self.assertTrue(any(r['field'] == field['name'] and r['operation'] == verb
                                            and r['vector'] == variant for r in rows))
                    for rule in field['rules']:
                        if rule.startswith(('min:', 'max:', 'unique:')):
                            variant = rule.split(':')[0]
                            self.assertTrue(any(r['field'] == field['name'] and r['operation'] == verb
                                                and r['vector'] == variant for r in rows))

    def test_profiles_reject_malformed_fixtures_and_wrong_rules(self):
        p = package_manifest('assets')
        bad = copy.deepcopy(p['profile'])
        bad['fixtures']['new']['value'] = -1
        with self.assertRaises(ValueError):
            validate_profile(p['spec'], bad)
        bad = copy.deepcopy(p['profile'])
        bad['spec']['fields'][0]['rules'].remove('required')
        with self.assertRaises(ValueError):
            validate_profile(p['spec'], bad)
        with self.assertRaises(ValueError):
            package_manifest('../books')

    def test_legacy_fingerprints_unchanged(self):
        from critic_agent.spec import load_spec
        from critic_agent.resources import resource_contract
        from critic_agent.resource_reference import resource_reference_manifest
        from critic_agent.reference import reference_suite_hash
        audit = json.loads((ROOT/'docs/evidence/final-evaluator-audit-2026-11-23.json').read_text())
        for name, expected in audit['sources_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), expected, name)
        for resource in ('books', 'inventory_items'):
            spec = load_spec(ROOT/'examples'/(resource+'.json'))
            self.assertEqual(resource_contract(spec)['contract_sha256'], audit['legacy_fingerprints'][resource]['internal'])
            self.assertEqual(resource_reference_manifest(spec)['suite_sha256'], audit['legacy_fingerprints'][resource]['reference'])
        for version in ('v1', 'v2'):
            self.assertEqual(reference_suite_hash(version), audit['legacy_fingerprints']['products_reference_'+version])
