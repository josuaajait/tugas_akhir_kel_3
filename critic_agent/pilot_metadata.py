
"""Ekstraksi metadata eksperimen pilot tanpa mengubah arsip asli."""

import json
from datetime import datetime, timezone
from pathlib import Path


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))



def _test_summary(attempt):
    """Ringkas pengujian tanpa mengarang hasil yang tidak tersedia."""
    dynamic = attempt.get("dynamic")
    summary = dynamic.get("summary", {}) if isinstance(dynamic, dict) else {}

    status = attempt.get("dynamic_status")

    return {
        "status": status,
        "executed": isinstance(dynamic, dict),
        "reused": status == "reused",
        "reused_from": attempt.get("reused_from"),
        "passed": summary.get("passed"),
        "total": summary.get("total"),
        "failure": summary.get("failure"),
        "error": summary.get("error"),
        "skipped": summary.get("skipped"),
    }



def collect_pilot_metadata(job_directory):
    """Baca hasil job dan buat metadata baru tanpa overwrite."""
    job_directory = Path(job_directory).resolve()

    result_path = job_directory / "pilot_result.json"
    if not result_path.is_file():
        raise ValueError("pilot_result.json tidak ditemukan.")

    result = _read_json(result_path)

    run_directory = result.get("run_directory")
    if not run_directory:
        raise ValueError("Job tidak memiliki run_directory.")

    run_directory = Path(run_directory).resolve()

    # Pastikan folder run merupakan bagian dari job ini.
    if not run_directory.is_relative_to(job_directory / "runs"):
        raise ValueError("Run directory berada di luar folder job.")

    history_path = run_directory / "history.json"
    manifest_path = run_directory / "run_manifest.json"

    if not history_path.is_file() or not manifest_path.is_file():
        raise ValueError("Arsip history atau run manifest tidak lengkap.")

    history = _read_json(history_path)
    manifest = _read_json(manifest_path)

    if history.get("run_id") != manifest.get("run_id"):
        raise ValueError("Run ID pada kedua arsip tidak cocok.")

    if result.get("status") != history.get("status"):
        raise ValueError("Status pilot dan history tidak cocok.")

    if manifest.get("status") != history.get("status"):
        raise ValueError("Status run manifest tidak cocok.")

    attempts = history.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise ValueError("History tidak memiliki percobaan.")
    
    if manifest.get("revision_count") != history.get("revision_count"):
        raise ValueError("Jumlah revisi pada arsip tidak konsisten.")

    if manifest.get("stop_reason") != history.get("stop_reason"):
        raise ValueError("Alasan berhenti pada arsip tidak konsisten.")

    if result.get("revision_count") != history.get("revision_count"):
        raise ValueError("Jumlah revisi pilot tidak cocok dengan history.")

    if result.get("stop_reason") != history.get("stop_reason"):
        raise ValueError("Alasan berhenti pilot tidak cocok dengan history.")

    for index, attempt in enumerate(attempts):
        if attempt.get("iteration") != index:
            raise ValueError(
                f"Urutan iterasi tidak konsisten pada percobaan {index}."
            )

    code_hashes = [
        attempt["code_sha256"]
        for attempt in attempts
        if attempt.get("code_sha256")
    ]

    first = attempts[0]
    last = attempts[-1]

    durations = [
        attempt.get("elapsed_seconds")
        for attempt in attempts
    ]

    total_duration = (
        round(sum(durations), 6)
        if all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value >= 0
            for value in durations
        )
        else None
    )

    metadata = {
        "schema_version": "1.0",
        "collected_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),

        "job_id": result["job_id"],
        "run_id": history["run_id"],
        "kind": result["kind"],

        "configuration": {
            "model": manifest.get("model"),
            "temperature": (
                manifest.get("options") or {}
            ).get("temperature"),
            "seed": (
                manifest.get("options") or {}
            ).get("seed"),
            "max_revisions": manifest.get("max_revisions"),
            "config_sha256": result.get("config_sha256"),
        },

        "specification": {
            "spec_id": manifest.get("spec_id"),
            "source_file_sha256": result.get("spec_sha256"),
            "archived_spec_sha256": manifest.get("spec_sha256"),
        },

        "outcome": {
            "status": history["status"],
            "stop_reason": history.get("stop_reason"),
            "revision_count": history.get("revision_count"),
            "attempt_count": len(attempts),
        },

        "tests": {
            "initial": _test_summary(first),
            "final": _test_summary(last),
            "expected_internal_tests": manifest.get(
                "expected_internal_tests"
            ),
        },

        "code": {
            "initial_sha256": first.get("code_sha256"),
            "final_sha256": last.get("code_sha256"),
            "unique_hash_count": len(set(code_hashes)),
            "duplicate_hash_count": (
                len(code_hashes) - len(set(code_hashes))
            ),
            "identical_code_stop": (
                history.get("stop_reason") == "identical_code"
            ),
        },

        "execution": {
            "model_call_count": sum(
                attempt.get("model_called") is True
                for attempt in attempts
            ),
            "total_attempt_seconds": total_duration,
            "attempt_seconds": durations,
            "model_timeout_seconds": manifest.get(
                "model_timeout_seconds"
            ),
            "token_usage": None,
        },

        "environment": {
            "prototype_version": manifest.get(
                "prototype_version"
            ),
            "python": (
                manifest.get("environment") or {}
            ).get("python"),
            "platform": (
                manifest.get("environment") or {}
            ).get("platform"),
            "docker_image_id": manifest.get("image_id"),
        },

        "source_files": {
            "pilot_result": str(result_path),
            "history": str(history_path),
            "run_manifest": str(manifest_path),
        },
    }

    output = job_directory / "metadata.json"

    # Mode x mencegah penimpaan metadata yang sudah ada.
    with output.open("x", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)
        file.write("\n")

    return output