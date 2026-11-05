
import hashlib
import itertools
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from .spec import load_spec


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_pilot_manifest(
    specs,
    seeds,
    temperatures,
    output,
    model="qwen2.5:7b-instruct",
    max_revisions=3,
):
    output = Path(output)

    if not specs or not seeds or not temperatures:
        raise ValueError("Spec, seed, dan temperature wajib tersedia.")

    if not model.strip():
        raise ValueError("Nama model tidak boleh kosong.")

    if not 0 <= max_revisions <= 3:
        raise ValueError("Maksimal revisi harus antara 0 dan 3.")

    if any(seed < 0 for seed in seeds):
        raise ValueError("Seed tidak boleh negatif.")

    if any(not math.isfinite(t) or t < 0 or t > 2 for t in temperatures):
        raise ValueError("Temperature harus berada antara 0 dan 2.")

    if len(set(seeds)) != len(seeds):
        raise ValueError("Terdapat seed duplikat.")

    if len(set(temperatures)) != len(temperatures):
        raise ValueError("Terdapat temperature duplikat.")

    validated_specs = []

    for item in specs:
        path = Path(item).resolve()

        if not path.is_file():
            raise ValueError(f"Spec tidak ditemukan: {path}")

        # Validasi menggunakan parser spesifikasi proyek.
        load_spec(path)

        validated_specs.append({
            "path": str(path),
            "sha256": sha256_file(path),
        })

    paths = [item["path"] for item in validated_specs]

    if len(set(paths)) != len(paths):
        raise ValueError("Terdapat path spesifikasi duplikat.")

    jobs = []

    for index, (spec, temperature, seed) in enumerate(
        itertools.product(validated_specs, temperatures, seeds),
        start=1,
    ):
        config = {
            "spec_sha256": spec["sha256"],
            "model": model,
            "temperature": temperature,
            "seed": seed,
            "max_revisions": max_revisions,
        }

        config_hash = hashlib.sha256(
            json.dumps(config, sort_keys=True).encode("utf-8")
        ).hexdigest()

        jobs.append({
            "job_id": f"pilot-{index:04d}",
            "config_sha256": config_hash,
            "spec": spec["path"],
            "spec_sha256": spec["sha256"],
            "model": model,
            "temperature": temperature,
            "seed": seed,
            "max_revisions": max_revisions,
            "status": "PLANNED",
        })

    manifest = {
        "schema_version": "1.0",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "specifications": validated_specs,
        "seeds": list(seeds),
        "temperatures": list(temperatures),
        "max_revisions": max_revisions,
        "total_jobs": len(jobs),
        "estimated_max_model_calls_before_retry": (
            len(jobs) * (1 + max_revisions)
        ),
        "jobs": jobs,
    }

    # Tidak menimpa manifest yang sudah ada.
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("x", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)

    return {
        "status": "PLANNED",
        "manifest": str(output.resolve()),
        "total_jobs": len(jobs),
        "estimated_max_model_calls_before_retry": (
            len(jobs) * (1 + max_revisions)
        ),
    }
