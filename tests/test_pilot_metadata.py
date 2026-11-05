
import json
import tempfile
import unittest
from pathlib import Path

from critic_agent.pilot_metadata import collect_pilot_metadata


class PilotMetadataTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.root = Path(self.temp.name)
        self.job = self.root / "pilot-0001"
        self.run = self.job / "runs" / "test-run"
        self.run.mkdir(parents=True)

        self.result = {
            "job_id": "pilot-0001",
            "kind": "products",
            "status": "LOLOS",
            "stop_reason": "all_checks_passed",
            "revision_count": 0,
            "run_directory": str(self.run),
            "config_sha256": "config-hash",
            "spec_sha256": "source-spec-hash",
        }

        self.history = {
            "run_id": "test-run",
            "status": "LOLOS",
            "stop_reason": "all_checks_passed",
            "revision_count": 0,
            "attempts": [
                {
                    "iteration": 0,
                    "model_called": True,
                    "code_sha256": "hash-a",
                    "dynamic_status": "PASSED_INTERNAL",
                    "dynamic": {
                        "status": "PASSED_INTERNAL",
                        "summary": {
                            "total": 14,
                            "passed": 14,
                            "failure": 0,
                            "error": 0,
                            "skipped": 0,
                        },
                    },
                    "elapsed_seconds": 2.5,
                }
            ],
        }

        self.manifest = {
            "run_id": "test-run",
            "status": "LOLOS",
            "stop_reason": "all_checks_passed",
            "revision_count": 0,
            "model": "qwen2.5:7b-instruct",
            "options": {
                "temperature": 0.2,
                "seed": 41,
            },
            "max_revisions": 3,
            "spec_id": "products_basic",
            "spec_sha256": "archived-spec-hash",
            "expected_internal_tests": 14,
            "prototype_version": "0.5.0",
            "model_timeout_seconds": 300,
            "environment": {
                "python": "3.13.7",
                "platform": "test-platform",
            },
            "image_id": "sha256:test-image",
        }

        self.save_sources()

    def save_sources(self):
        files = (
            (self.job / "pilot_result.json", self.result),
            (self.run / "history.json", self.history),
            (self.run / "run_manifest.json", self.manifest),
        )

        for path, value in files:
            path.write_text(
                json.dumps(value),
                encoding="utf-8",
            )

    def collect(self):
        output = collect_pilot_metadata(self.job)
        return json.loads(output.read_text(encoding="utf-8"))

    def test_normal_metadata(self):
        data = self.collect()

        self.assertEqual(data["job_id"], "pilot-0001")
        self.assertEqual(data["outcome"]["status"], "LOLOS")
        self.assertEqual(data["outcome"]["revision_count"], 0)

        self.assertEqual(data["tests"]["initial"]["passed"], 14)
        self.assertEqual(data["tests"]["final"]["passed"], 14)
        self.assertTrue(data["tests"]["initial"]["executed"])
        self.assertFalse(data["tests"]["final"]["reused"])

        self.assertEqual(data["execution"]["model_call_count"], 1)
        self.assertEqual(data["execution"]["total_attempt_seconds"], 2.5)
        self.assertIsNone(data["execution"]["token_usage"])

        self.assertEqual(
            data["specification"]["source_file_sha256"],
            "source-spec-hash",
        )
        self.assertEqual(
            data["specification"]["archived_spec_sha256"],
            "archived-spec-hash",
        )

    def test_existing_metadata_not_overwritten(self):
        output = collect_pilot_metadata(self.job)
        original = output.read_bytes()

        with self.assertRaises(FileExistsError):
            collect_pilot_metadata(self.job)

        self.assertEqual(output.read_bytes(), original)

    def test_inconsistent_revision_rejected(self):
        self.manifest["revision_count"] = 2
        self.save_sources()

        with self.assertRaisesRegex(ValueError, "Jumlah revisi"):
            collect_pilot_metadata(self.job)

        self.assertFalse((self.job / "metadata.json").exists())

    def test_reused_code_not_counted_as_new_test(self):
        self.history.update(
            status="BELUM LOLOS",
            stop_reason="identical_code",
            revision_count=1,
        )

        self.result.update(
            status="BELUM LOLOS",
            stop_reason="identical_code",
            revision_count=1,
        )

        self.manifest.update(
            status="BELUM LOLOS",
            stop_reason="identical_code",
            revision_count=1,
        )

        self.history["attempts"].append({
            "iteration": 1,
            "model_called": True,
            "code_sha256": "hash-a",
            "dynamic_status": "reused",
            "reused_from": 0,
            "elapsed_seconds": 1.25,
        })

        self.save_sources()
        data = self.collect()

        self.assertEqual(data["outcome"]["attempt_count"], 2)
        self.assertEqual(data["execution"]["model_call_count"], 2)
        self.assertEqual(data["execution"]["total_attempt_seconds"], 3.75)

        self.assertTrue(data["tests"]["final"]["reused"])
        self.assertFalse(data["tests"]["final"]["executed"])
        self.assertEqual(data["tests"]["final"]["reused_from"], 0)
        self.assertIsNone(data["tests"]["final"]["passed"])

        self.assertEqual(data["code"]["unique_hash_count"], 1)
        self.assertEqual(data["code"]["duplicate_hash_count"], 1)
        self.assertTrue(data["code"]["identical_code_stop"])

    def test_inconsistent_iteration_rejected(self):
        self.history["attempts"][0]["iteration"] = 5
        self.save_sources()

        with self.assertRaisesRegex(ValueError, "Urutan iterasi"):
            collect_pilot_metadata(self.job)

        self.assertFalse((self.job / "metadata.json").exists())

    def test_missing_dynamic_results(self):
        attempt = self.history["attempts"][0]
        attempt.pop("dynamic")
        attempt["dynamic_status"] = "skipped"

        self.save_sources()
        data = self.collect()

        self.assertFalse(data["tests"]["initial"]["executed"])
        self.assertIsNone(data["tests"]["initial"]["passed"])
        self.assertIsNone(data["tests"]["final"]["total"])


if __name__ == "__main__":
    unittest.main()
