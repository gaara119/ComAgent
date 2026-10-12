"""Apply only the hash-verified technical candidates after separate AI review."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"eval/artifacts/oct12/repairs-source-003"


def main():
    if OUT.exists():
        raise ValueError("Final repair application has already been recorded")
    for review in ["notes/oct12/staging/sql19/ai-review-v3-pass-2.md","notes/oct12/staging/ratio/ai-review-pass-2.md"]:
        if not (ROOT/review).is_file():
            raise ValueError("Independent review record is missing")
    records=[]
    specs=[("qa_agent/clarify/extractor.py","notes/oct12/staging/sql19/extractor_candidate-v3.py",
            "860129544ca50d37941e62e1c4743ead5f21066d473441469a028b394dad1326",
            "f203c3f39b6e74adbab8a2434c0983b9dcedb48451550f723d4175030358259d"),
           ("qa_agent/sql/ratio_guard.py","notes/oct12/staging/ratio/ratio_guard_candidate.py",
            "f27bc077049fcf3f4103c14e5137413c345a945d4944fbc399f473aa2e288fa8",
            "949a5306ccd57f20f716789a051b053dde9e6c1695e2c82d57207071bf66ca5c")]
    for name,candidate,expected_before,expected_after in specs:
        before=(ROOT/name).read_bytes();after=(ROOT/candidate).read_bytes()
        if sha256(before).hexdigest()!=expected_before or sha256(after).hexdigest()!=expected_after:
            raise ValueError("Reviewed source no longer matches: "+name)
        compile(after,str(ROOT/name),"exec")
        records.append({"file":name,"candidate":candidate,"before_sha256":expected_before,"after_sha256":expected_after})
    OUT.mkdir(parents=True)
    for record in records:
        target=ROOT/record["file"]
        (OUT/(target.name+".before.txt")).write_bytes(target.read_bytes())
        target.write_bytes((ROOT/record["candidate"]).read_bytes())
    # Configure a new evidence destination; preserve every credential verbatim.
    env=ROOT/".env"
    text=env.read_text(encoding="utf-8-sig")
    replacement="LLM_CAPTURE_DIR=eval/artifacts/oct12/provider-captures/live-003"
    if re.search(r"(?m)^LLM_CAPTURE_DIR=",text):
        text=re.sub(r"(?m)^LLM_CAPTURE_DIR=.*$",replacement,text)
    else:
        text=text.rstrip()+"\n"+replacement+"\n"
    env.write_text(text,encoding="utf-8")
    record={"created_at_utc":datetime.now(timezone.utc).isoformat(),"authorization":"User Oct12 execution request + actual DEV regression repairs; no new business default",
            "scope":"Explicit customer attribute lookup classification, exact midnight date proof only",
            "changes":records,"gold_or_label_changes":0,"human_records_changed":0,"held_predictions":0,
            "independent_review_files":["notes/oct12/staging/sql19/ai-review-v3-pass-2.md","notes/oct12/staging/ratio/ai-review-pass-2.md"],
            "provider_capture_directory":"eval/artifacts/oct12/provider-captures/live-003","credentials_printed":False}
    (OUT/"application.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"source_files_applied":len(records),"gold_changes":0,"credentials_printed":False}))


if __name__=="__main__":
    main()
