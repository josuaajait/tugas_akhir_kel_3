"""Portable, bounded A/B archive helpers; no model or Docker access."""
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path,limit=32_000_000):
    path=Path(path)
    if path.stat().st_size>limit:raise ValueError('JSON archive too large: '+str(path))
    value=json.loads(path.read_bytes())
    if not isinstance(value,dict):raise ValueError('JSON archive must be an object: '+str(path))
    return value


def local_path(root,name):
    if not isinstance(name,str) or not name or '\\' in name or ':' in name:
        raise ValueError('Archive path must be a relative POSIX path.')
    rel=PurePosixPath(name)
    if rel.is_absolute() or '..' in rel.parts or rel.as_posix()!=name:
        raise ValueError('Unsafe archive path: '+name)
    root=Path(root).resolve();path=(root/Path(*rel.parts)).resolve()
    if not path.is_relative_to(root):raise ValueError('Archive path escapes root: '+name)
    return path


def relative(root,path):
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def engine_manifest():
    hashes={p.relative_to(ROOT).as_posix():sha(p) for p in sorted((ROOT/'critic_agent').glob('*.py'))}
    digest=hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return digest,hashes


def artifact_index(folder):
    root=Path(folder).resolve();result={}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():raise ValueError('Symlinks are not allowed in a pair archive.')
        if path.is_file() and path.name!='pair.json' and not path.name.endswith('.tmp'):
            result[path.relative_to(root).as_posix()]=sha(path)
    return result


def verify_artifacts(folder,expected):
    if not isinstance(expected,dict) or not expected:raise ValueError('Missing artifact hash index.')
    for name,digest in expected.items():
        path=local_path(folder,name)
        if not path.is_file() or sha(path)!=digest:raise ValueError('Artifact missing/changed: '+name)
    if artifact_index(folder)!=expected:raise ValueError('Artifact inventory changed.')
