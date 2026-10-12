"""Relocate only newly untracked unit probes out of a historical capture path."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PREFIX="eval/experiments/after_d2_01_03/regression/final/provider-captures/V1-final-001/"
OUT=ROOT/"eval/artifacts/oct12/mock-provider-captures/early-modules"

def main():
    if OUT.exists():
        raise ValueError("Archive already exists")
    names=subprocess.check_output(["git","ls-files","--others","--exclude-standard","--",PREFIX],cwd=ROOT,text=True).splitlines()
    records=[]
    for name in names:
        source=(ROOT/name).resolve();target=(OUT/source.name).resolve()
        if not source.is_relative_to((ROOT/PREFIX).resolve()) or not target.is_relative_to(OUT.resolve()) or target.exists():
            raise ValueError("Unexpected relocation path")
        raw=source.read_bytes();data=json.loads(raw)
        messages=data.get("request",{}).get("messages") or []
        response_id=(data.get("response") or {}).get("id")
        probe=(len(messages)>=2 and messages[0].get("role")=="system" and messages[0].get("content","").startswith("prompt\n") and
               any(m.get("role")=="user" and m.get("content")=="question" for m in messages) and
               all(m.get("role")!="user" or m.get("content")=="question" or m.get("content","").startswith("上次结果") for m in messages))
        if not probe or response_id not in {None,"chatcmpl-test"}:
            raise ValueError("Not a recognized unit probe: "+name)
        records.append({"original":name,"archive":target.relative_to(ROOT).as_posix(),"sha256":sha256(raw).hexdigest(),"response_id":response_id})
    OUT.mkdir(parents=True)
    for record in records:
        source=(ROOT/record["original"]).resolve();target=(ROOT/record["archive"]).resolve()
        source.rename(target)
        if sha256(target.read_bytes()).hexdigest()!=record["sha256"]:
            raise ValueError("Relocation hash mismatch")
    (OUT/"relocation-manifest.json").write_text(json.dumps({"created_at_utc":datetime.now(timezone.utc).isoformat(),"kind":"HTTP mock unit-test probes, not actual provider measurements","scope":"Only newly untracked recognized probe files; tracked historical files untouched","count":len(records),"hashes_preserved":True,"files":records},ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"unit_probe_files_archived":len(records),"historical_tracked_files_changed":0}))

if __name__=="__main__":
    main()
