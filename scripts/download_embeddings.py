"""Download the pinned BGE-M3 QInt8 ONNX conversion, with content verification."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qa_agent.config import PROJECT_ROOT, get_settings

REPO = "Xenova/bge-m3"
REVISION = "4de13258303883538bd53b696b452bf8099f0858"
FILES = {
    "onnx/model_quantized.onnx": (569694530, "0826f8c1ab9edf1801db86c61919d4d108e8bfc0b809ec823ad366882ff0b77d"),
    "tokenizer.json": (17082821, "6710678b12670bc442b99edc952c4d996ae309a7020c1fa0096dd245c2faf790"),
    "tokenizer_config.json": (1173, None), "config.json": (770, None), "quantize_config.json": (834, None),
}


def digest(path: Path) -> str:
    result = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def download(client: httpx.Client, relative: str, root: Path) -> dict:
    size, expected_hash = FILES[relative]
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.stat().st_size == size and (not expected_hash or digest(target) == expected_hash):
        return {"path": relative, "size": size, "sha256": digest(target)}
    if target.exists():
        raise RuntimeError(f"Existing {relative} is inconsistent; preserve it and inspect before replacing")
    partial = target.with_suffix(target.suffix + ".part")
    url = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{relative}"
    for attempt in range(4):
        position = partial.stat().st_size if partial.exists() else 0
        try:
            with client.stream("GET", url, headers={"Range": f"bytes={position}-"} if position else {}) as response:
                response.raise_for_status()
                if position and response.status_code != 206:
                    position = 0
                mode = "ab" if position else "wb"
                last_report = time.monotonic()
                with partial.open(mode) as stream:
                    for block in response.iter_bytes(1024 * 1024):
                        stream.write(block)
                        position += len(block)
                        if position > size:
                            raise RuntimeError("Downloaded payload exceeds pinned size")
                        if time.monotonic() - last_report > 10:
                            print(f"{relative}: {position / 1e6:.1f}/{size / 1e6:.1f} MB", flush=True)
                            last_report = time.monotonic()
            if partial.stat().st_size != size:
                raise RuntimeError("Downloaded payload is incomplete")
            actual_hash = digest(partial)
            if expected_hash and actual_hash != expected_hash:
                raise RuntimeError("Downloaded model content SHA256 does not match")
            partial.replace(target)
            print(f"Verified {relative} ({size} bytes)", flush=True)
            return {"path": relative, "size": size, "sha256": actual_hash}
        except (httpx.HTTPError, RuntimeError):
            if attempt == 3:
                raise
            time.sleep(1 + attempt)
    raise RuntimeError("Download failed")


def main() -> int:
    destination = get_settings().bge_model_path
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = PROJECT_ROOT / "data/model_manifest/bge-m3.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=httpx.Timeout(45, read=60)) as client:
        files = [download(client, name, destination) for name in FILES]
    manifest = {
        "model": "BAAI/bge-m3", "conversion_repo": REPO, "revision": REVISION,
        "source": f"https://huggingface.co/{REPO}/tree/{REVISION}", "license": "MIT",
        "runtime": "onnxruntime", "device": "cpu", "weight_type": "QInt8",
        "pooling": "CLS", "normalization": "L2", "dimensions": 1024,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(), "files": files,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (destination / "download_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"BGE-M3 download verified; manifest: {manifest_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (httpx.HTTPError, RuntimeError, OSError) as exc:
        print(f"Embedding preparation failed: {type(exc).__name__}. Partial download retained; rerun to resume.", file=sys.stderr)
        raise SystemExit(2)
