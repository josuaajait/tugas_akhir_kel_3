import hashlib
import json
import re
from pathlib import Path

from .spec import load_spec
from .ollama import OllamaClient
from .orchestrator import run_products, run_resource
from .resources import ResourceDockerRunner, resource_contract
from .sandbox import DockerRunner, validate_products_contract

def validate_pilot_manifest(manifest_path):
    """Baca dan validasi manifest sebelum eksperimen dijalankan."""
    manifest_path = Path(manifest_path).resolve()

    if not manifest_path.is_file():
        raise ValueError(
            f"Manifest pilot tidak ditemukan: {manifest_path}"
        )

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    if manifest.get("schema_version") != "1.0":
        raise ValueError("Versi manifest pilot tidak didukung.")

    jobs = manifest.get("jobs")

    if not isinstance(jobs, list) or not jobs:
        raise ValueError("Manifest pilot tidak memiliki jobs.")

    if manifest.get("total_jobs") != len(jobs):
        raise ValueError("Jumlah jobs tidak sesuai manifest.")


    seen_ids = set()

    for job in jobs:
        job_id = job["job_id"]

        if not isinstance(job_id, str) or not re.fullmatch(
            r"pilot-[0-9]{4,}", job_id
        ):
            raise ValueError(f"Job ID tidak valid: {job_id}")

        if job_id in seen_ids:
            raise ValueError(f"Job ID duplikat: {job_id}")

        seen_ids.add(job_id)

        spec_path = Path(job["spec"])

        if not spec_path.is_file():
            raise ValueError(
                f"Spesifikasi tidak ditemukan: {spec_path}"
            )

        actual_hash = hashlib.sha256(
            spec_path.read_bytes()
        ).hexdigest()

        if actual_hash != job["spec_sha256"]:
            raise ValueError(
                f"Hash spesifikasi tidak cocok: {job_id}"
            )

        # Pastikan spesifikasi dapat diproses sistem.
        load_spec(spec_path)

        config = {
            "spec_sha256": job["spec_sha256"],
            "model": job["model"],
            "temperature": job["temperature"],
            "seed": job["seed"],
            "max_revisions": job["max_revisions"],
        }

        config_hash = hashlib.sha256(
            json.dumps(config, sort_keys=True).encode("utf-8")
        ).hexdigest()

        if config_hash != job["config_sha256"]:
            raise ValueError(
                f"Hash konfigurasi tidak cocok: {job_id}"
            )

        if job.get("status") != "PLANNED":
            raise ValueError(
                f"Status job tidak sesuai: {job_id}"
            )

    return manifest

def run_pilot(
    manifest_path,
    *,
    limit=1,
    kind="products",
    image=None,
    model_timeout=300,
    test_timeout=120,
):
    """Jalankan job pilot secara bertahap dan simpan hasilnya."""

    if type(limit) is not int or limit < 1:
        raise ValueError("Limit harus bilangan bulat positif.")

    if kind not in ("products", "resource"):
        raise ValueError("Jenis runner tidak valid.")

    if model_timeout <= 0 or test_timeout <= 0:
        raise ValueError("Timeout harus positif.")

    manifest_path = Path(manifest_path).resolve()

    # Seluruh konfigurasi diverifikasi sebelum eksekusi.
    manifest = validate_pilot_manifest(manifest_path)

    output_root = manifest_path.parent / "executions"
    completed = []
    skipped = 0

    for job in manifest["jobs"]:
        if len(completed) >= limit:
            break

        job_id = job["job_id"]
        job_folder = output_root / job_id

        # Jangan mengulang atau menimpa job yang sudah dimulai.
        if job_folder.exists():
            skipped += 1
            continue


        # Validasi jenis resource sebelum membuat folder.
        spec = load_spec(Path(job["spec"]))

        if kind == "products":
            validate_products_contract(spec)
        else:
            resource_contract(spec)

        # Buat folder baru secara eksklusif.
        # Folder tetap dipertahankan jika proses terputus.
        job_folder.mkdir(parents=True, exist_ok=False)
        started_path = job_folder / "started.json"

        with started_path.open("x", encoding="utf-8") as file:
            json.dump(
                {
                    "job_id": job_id,
                    "config_sha256": job["config_sha256"],
                    "status": "STARTED",
                },
                file,
                ensure_ascii=False,
                indent=2,
            )

        result = {
            "job_id": job_id,
            "config_sha256": job["config_sha256"],
            "spec_sha256": job["spec_sha256"],
            "kind": kind,
            "status": "ERROR",
            "run_directory": None,
        }

        try:
            client = OllamaClient(
                model=job["model"],
                temperature=job["temperature"],
                seed=job["seed"],
                timeout=model_timeout,
            )

            if kind == "products":
                runner = DockerRunner(
                    image=image or "critic-laravel:dev",
                    output_root=job_folder / "harness",
                    timeout=test_timeout,
                )
                execute = run_products
            else:
                runner = ResourceDockerRunner(
                    spec,
                    image=image,
                    output_root=job_folder / "harness",
                    timeout=test_timeout,
                )
                execute = run_resource

            run_folder = execute(
                spec,
                job_folder / "runs",
                client,
                runner,
                max_revisions=job["max_revisions"],
            )

            history = json.loads(
                (run_folder / "history.json").read_text(
                    encoding="utf-8"
                )
            )

            result.update(
                status=history["status"],
                stop_reason=history["stop_reason"],
                revision_count=history["revision_count"],
                run_directory=str(run_folder.resolve()),
            )

        except Exception as exc:
            result["error"] = (
                f"{type(exc).__name__}: {exc}"
            )

        # Simpan hasil baru tanpa menimpa hasil sebelumnya.
        result_path = job_folder / "pilot_result.json"

        with result_path.open("x", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=2)
            file.write("\n")

        completed.append(result)

    return {
        "status": (
            "ERROR"
            if any(item["status"] == "ERROR" for item in completed)
            else "COMPLETE"
        ),
        "manifest": str(manifest_path),
        "executed_jobs": len(completed),
        "skipped_existing": skipped,
        "results": completed,
    }
