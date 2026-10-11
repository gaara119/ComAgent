"""Collect real source rectangles for development predictions, no heldout access."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from qa_agent.rag.parsers import load_documents


def compact(text):
    return re.sub(r"\s+", "", text)


def main():
    import pymupdf
    from PIL import Image, ImageDraw
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--responses",type=Path,default=ROOT/"eval/artifacts/d2-final/rag/regression/responses.jsonl")
    parser.add_argument("--index",type=Path,default=ROOT/"data/indexes/docs-d2-final-v4")
    parser.add_argument("--output",type=Path,default=ROOT/"eval/artifacts/d2-final/rag/location-check")
    args = parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    chunks = {row["chunk_id"]:row for line in (args.index/"chunks.jsonl").read_text(encoding="utf8").splitlines() if (row:=json.loads(line))}
    documents = {doc["doc_id"]:doc for doc in load_documents()}
    outputs = [json.loads(line) for line in args.responses.read_text(encoding="utf8").splitlines() if line.strip()]
    if any(row.get("split")!="dev" for row in outputs):
        raise ValueError("This audit script accepts development predictions only")
    results = []
    for row in outputs:
        response = row.get("response") or {}
        candidates = {c["evidence_id"]:c for c in response.get("metadata",{}).get("retrieved_pages",[])}
        entries = []
        for evidence in response.get("evidences",[]):
            source = chunks[candidates[evidence["evidence_id"]]["chunk_id"]]
            entry = {"evidence_id":evidence["evidence_id"],"chunk_id":source["chunk_id"],
                     "doc_id":source["doc_id"],"page":source["page"],"section_path":source["section_path"],
                     "text":source["text"],"bbox":source["bbox"],"parser":source["parser"],
                     "coordinate_system":source.get("coordinate_system"),
                     "section_location_status":source.get("section_location_status"),
                     "ocr_confidence_min":source.get("ocr_confidence_min"),
                     "index_membership":all(source.get(key)==evidence.get(key) for key in
                         ("doc_id","page","section_path","text","bbox")),
                     "visual_review":"pending_ai_visual_review"}
            if source["page"] is not None:
                document = pymupdf.open(documents[source["doc_id"]]["resolved_path"])
                physical = document[source["page"]-1]
                physical.set_rotation(0)
                pixmap = physical.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5),alpha=False)
                image = Image.frombytes("RGB",(pixmap.width,pixmap.height),pixmap.samples)
                if source.get("bbox"):
                    bbox = source["bbox"]
                    draw = ImageDraw.Draw(image)
                    draw.rectangle([v*1.5 for v in bbox],outline="#d62728",width=3)
                    # Coordinates are rounded to 0.01pt at ingestion. Use a
                    # disclosed 0.1pt tolerance only for text-engine clipping;
                    # the rendered rectangle remains the original bbox.
                    clip_rect = pymupdf.Rect(bbox)+(-.1,-.1,.1,.1)
                    clip = physical.get_text(clip=clip_rect,sort=True)
                    entry["native_clip_text"] = clip
                    entry["native_clip_exact_text_support"] = compact(source["text"]) in compact(clip) if source["parser"]!="RapidOCR" else None
                    entry["bbox_within_visible_cropbox"] = bool(pymupdf.Rect(bbox) in physical.rect)
                filename = f"{row['id']}-{evidence['evidence_id']}-p{source['page']}.png"
                image.save(args.output/filename)
                entry["rendered_source"] = str((args.output/filename).resolve().relative_to(ROOT)).replace("\\","/")
                document.close()
            else:
                entry["visual_review"] = "non_pdf_source_read_required"
            entries.append(entry)
        results.append({"id":row["id"],"split":"dev","question":row["request"]["message"],
                        "reference_answer":row.get("reference_answer"),"answer":response.get("answer"),
                        "status":response.get("status"),"citations":entries,
                        "answer_ai_review":"pending","human_review":"pending_human_review"})
    (args.output/"citation-location-check.json").write_text(json.dumps({"reviewed_development_count":len(results),
            "holdout_prediction_count":0,"rows":results},ensure_ascii=False,indent=2),encoding="utf8")
    print(json.dumps({"dev":len(results),"cited":sum(len(r["citations"]) for r in results),"path":str(args.output)},ensure_ascii=False))


if __name__ == "__main__":
    main()
