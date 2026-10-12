"""Hash protected evidence and verify portable proof links, without label reads."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets=[]
    def handle_starttag(self, tag, attrs):
        if tag in {"a","img"}:
            self.targets += [value for key,value in attrs if key in {"href","src"} and value]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--extracted",type=Path)
    args=parser.parse_args()
    out=(ROOT/args.output).resolve()
    if not out.is_relative_to(ROOT/"eval/reports/oct12") or out.exists():
        raise ValueError("Use a fresh Oct12 verification path")
    protected=json.loads((ROOT/"eval/artifacts/d2-final/protected-originals-before.json").read_text(encoding="utf-8"))["files"]
    changed=[name for name,digest in protected.items() if not (ROOT/name).is_file() or sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
    base=args.extracted.resolve() if args.extracted else ROOT
    entries=[base/"eval/reports/oct12/acceptance/10月12日任务逐项验收与证据.html", base/"eval/reports/oct12/manual-review/全部待人工审核统一入口.html", base/"notes/oct12/gold-38-23-proposal.md", base/"notes/oct12/参考答案与计分争议提案.md"]
    links=[]
    for file in entries:
        if not file.is_file():
            raise ValueError("Missing report: "+str(file.relative_to(base)))
        content=file.read_text(encoding="utf-8")
        if file.suffix==".html":
            parsed=Links();parsed.feed(content);targets=parsed.targets
        else:
            targets=re.findall(r"\]\(([^)]+)\)",content)
        for target in sorted(set(targets)):
            target=target.strip("<>")
            url=urlsplit(target)
            if url.scheme or url.netloc or target.startswith("#"):
                continue
            path=(file.parent/unquote(url.path)).resolve()
            links.append({"report":file.relative_to(base).as_posix(),"target":target,
                          "relative":not target.startswith(("/","\\")),"inside_package":path.is_relative_to(base),"exists":path.exists()})
    snapshot=json.loads((ROOT/"eval/artifacts/oct12/runtime-snapshot-004/manifest.json").read_text(encoding="utf-8"))
    snapshot_hashes=snapshot.get("source_sha256") or snapshot.get("sha256") or {}
    if not snapshot_hashes:
        snapshot_hashes={item["path"]:item["sha256"] for item in snapshot.get("files",[]) if isinstance(item,dict)}
    current=[name for name,digest in snapshot_hashes.items() if not (ROOT/name).is_file() or sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
    result={"created_at_utc":datetime.now(timezone.utc).isoformat(),"scope":"Protected old files hashed only, no held content audit or prediction; safe report links verified after full extraction" if args.extracted else "Protected old files hashed only and safe relative links; no held content audit/prediction",
            "protected_old_file_count":len(protected),"changed_old_files":changed,"protected_old_status":"PASS" if not changed else "FAIL",
            "relative_links_checked":len(links),"missing_or_absolute_links":[item for item in links if not all(item[key] for key in ["relative","inside_package","exists"])],
            "runtime_snapshot_files":len(snapshot_hashes),"runtime_changed_after_final_snapshot":current,"held_predictions":0,"human_decisions_applied":0}
    result["passed"]=not changed and not result["missing_or_absolute_links"] and not current and bool(snapshot_hashes)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__=="__main__":
    raise SystemExit(main())
