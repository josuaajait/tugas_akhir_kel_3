
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from critic_agent.pilot_runner import (
    run_pilot,
    validate_pilot_manifest,
)


class PilotRunnerTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.root = Path(self.temp.name)
        self.spec = self.root / "products.json"
        self.spec.write_text("{}", encoding="utf-8")

        self.spec_hash = hashlib.sha256(
            self.spec.read_bytes()
        ).hexdigest()

        self.manifest_path = self.root / "manifest.json"

    def make_job(self, number):
        config = {
            "spec_sha256": self.spec_hash,
            "model": "qwen2.5:7b-instruct",
            "temperature": 0.2,
            "seed": number,
            "max_revisions": 3,
        }

        config_hash = hashlib.sha256(
            json.dumps(config, sort_keys=True).encode("utf-8")
        ).hexdigest()

        return {
            "job_id": f"pilot-{number:04d}",
            "config_sha256": config_hash,
            "spec": str(self.spec),
            "status": "PLANNED",
            **config,
        }

    def save_manifest(self, jobs):
        self.manifest_path.write_text(
            json.dumps({
                "schema_version": "1.0",
                "total_jobs": len(jobs),
                "jobs": jobs,
            }),
            encoding="utf-8",
        )

    def fake_execution(
        self,
        spec,
        output,
        client,
        runner,
        *,
        max_revisions,
    ):
        run_dir = Path(output) / "fake-run"
        run_dir.mkdir(parents=True)

        (run_dir / "history.json").write_text(
            json.dumps({
                "status": "LOLOS",
                "stop_reason": "all_checks_passed",
                "revision_count": 0,
                "attempts": [],
            }),
            encoding="utf-8",
        )

        return run_dir

    @patch("critic_agent.pilot_runner.load_spec")
    def test_manifest_valid(self, mock_load_spec):
        self.save_manifest([self.make_job(1)])

        result = validate_pilot_manifest(
            self.manifest_path
        )

        self.assertEqual(result["total_jobs"], 1)
        mock_load_spec.assert_called_once()

    @patch("critic_agent.pilot_runner.load_spec")
    def test_changed_spec_rejected(self, mock_load_spec):
        self.save_manifest([self.make_job(1)])

        self.spec.write_text(
            '{"changed":true}',
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Hash spesifikasi",
        ):
            validate_pilot_manifest(
                self.manifest_path
            )

        mock_load_spec.assert_not_called()

    @patch("critic_agent.pilot_runner.load_spec")
    def test_invalid_job_id_rejected(self, mock_load_spec):
        job = self.make_job(1)
        job["job_id"] = "../unsafe"

        self.save_manifest([job])

        with self.assertRaisesRegex(
            ValueError,
            "Job ID tidak valid",
        ):
            validate_pilot_manifest(
                self.manifest_path
            )

        self.assertFalse(
            (self.root / "executions").exists()
        )

        mock_load_spec.assert_not_called()

    @patch("critic_agent.pilot_runner.validate_products_contract")
    @patch("critic_agent.pilot_runner.run_products")
    @patch("critic_agent.pilot_runner.DockerRunner")
    @patch("critic_agent.pilot_runner.OllamaClient")
    @patch("critic_agent.pilot_runner.load_spec")
    def test_limit_and_skip_existing(
        self,
        mock_spec,
        mock_client,
        mock_docker,
        mock_run,
        mock_validate,
    ):
        self.save_manifest([
            self.make_job(1),
            self.make_job(2),
        ])

        mock_spec.return_value = {
            "spec_id": "products"
        }

        mock_run.side_effect = self.fake_execution

        # Eksekusi job pertama.
        first = run_pilot(
            self.manifest_path,
            limit=1,
        )

        # Eksekusi berikutnya harus melewati
        # job pertama dan memilih job kedua.
        second = run_pilot(
            self.manifest_path,
            limit=1,
        )

        self.assertEqual(
            first["executed_jobs"],
            1,
        )

        self.assertEqual(
            second["executed_jobs"],
            1,
        )

        self.assertEqual(
            second["skipped_existing"],
            1,
        )

        self.assertEqual(
            mock_run.call_count,
            2,
        )

        # Validasi kontrak dipanggil
        # untuk kedua job baru.
        self.assertEqual(
            mock_validate.call_count,
            2,
        )

        self.assertTrue(
            (
                self.root
                / "executions"
                / "pilot-0001"
                / "pilot_result.json"
            ).is_file()
        )

        self.assertTrue(
            (
                self.root
                / "executions"
                / "pilot-0002"
                / "pilot_result.json"
            ).is_file()
        )

    @patch("critic_agent.pilot_runner.validate_products_contract")
    @patch("critic_agent.pilot_runner.run_products")
    @patch("critic_agent.pilot_runner.DockerRunner")
    @patch("critic_agent.pilot_runner.OllamaClient")
    @patch("critic_agent.pilot_runner.load_spec")
    def test_execution_error_preserves_result(
        self,
        mock_spec,
        mock_client,
        mock_docker,
        mock_run,
        mock_validate,
    ):
        self.save_manifest([
            self.make_job(1)
        ])

        mock_spec.return_value = {
            "spec_id": "products"
        }

        mock_run.side_effect = RuntimeError(
            "simulated failure"
        )

        result = run_pilot(
            self.manifest_path,
            limit=1,
        )

        # Kegagalan harus dilaporkan.
        self.assertEqual(
            result["status"],
            "ERROR",
        )

        path = (
            self.root
            / "executions"
            / "pilot-0001"
            / "pilot_result.json"
        )

        # Bukti error harus tetap tersimpan.
        self.assertTrue(
            path.is_file()
        )

        saved = json.loads(
            path.read_text(encoding="utf-8")
        )

        self.assertEqual(
            saved["status"],
            "ERROR",
        )

        self.assertIn(
            "simulated failure",
            saved["error"],
        )

        mock_validate.assert_called_once()

        # Job yang gagal tidak boleh
        # dieksekusi ulang secara otomatis.
        repeated = run_pilot(
            self.manifest_path,
            limit=1,
        )

        self.assertEqual(
            repeated["executed_jobs"],
            0,
        )

        self.assertEqual(
            repeated["skipped_existing"],
            1,
        )

        self.assertEqual(
            mock_run.call_count,
            1,
        )


if __name__ == "__main__":
    unittest.main()
