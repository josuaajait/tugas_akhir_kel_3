
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from critic_agent.pilot import create_pilot_manifest


class PilotManifestTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

        self.root = Path(self.temp.name)
        self.spec = self.root / "products.json"
        self.spec.write_text('{"resource": "products"}', encoding="utf-8")
        self.output = self.root / "manifest.json"

    @patch("critic_agent.pilot.load_spec")
    def test_grid_generation(self, mock_load_spec):
        result = create_pilot_manifest(
            [self.spec],
            seeds=[41, 42, 43],
            temperatures=[0, 0.2, 0.5],
            output=self.output,
        )

        data = json.loads(self.output.read_text(encoding="utf-8"))

        self.assertEqual(result["status"], "PLANNED")
        self.assertEqual(data["total_jobs"], 9)
        self.assertEqual(len(data["jobs"]), 9)
        self.assertEqual(
            data["estimated_max_model_calls_before_retry"], 36
        )
        self.assertEqual(
            len({job["config_sha256"] for job in data["jobs"]}), 9
        )
        self.assertTrue(
            all(job["status"] == "PLANNED" for job in data["jobs"])
        )
        mock_load_spec.assert_called_once()

    @patch("critic_agent.pilot.load_spec")
    def test_invalid_temperature(self, mock_load_spec):
        with self.assertRaises(ValueError):
            create_pilot_manifest(
                [self.spec],
                seeds=[42],
                temperatures=[-0.5],
                output=self.output,
            )

        self.assertFalse(self.output.exists())

    @patch("critic_agent.pilot.load_spec")
    def test_manifest_not_overwritten(self, mock_load_spec):
        self.output.write_text("existing data", encoding="utf-8")

        with self.assertRaises(FileExistsError):
            create_pilot_manifest(
                [self.spec],
                seeds=[42],
                temperatures=[0.2],
                output=self.output,
            )

        self.assertEqual(
            self.output.read_text(encoding="utf-8"), "existing data"
        )


if __name__ == "__main__":
    unittest.main()
