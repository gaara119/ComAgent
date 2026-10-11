import csv
import json
from pathlib import Path
import pdfplumber
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[4]
ART=ROOT/'eval/artifacts/d2-ai-preaudit/rag'
dest=ART/'bbox-visual'
dest.mkdir(exist_ok=True)
manifest={r['doc_id']:r for r in csv.DictReader((ROOT/'data/docs/manifest.csv').open(encoding='utf-8-sig'))}
rows=json.loads((ART/'dev-compact-inputs.json').read_text(encoding='utf-8'))
out=[]
docs={}
for row in rows:
    for e in row['actual']['evidences']:
        if not e.get('bbox') or not e.get('page'):
            continue
        d=e['doc_id']
        if d not in docs:
            docs[d]=pdfplumber.open(ROOT/manifest[d]['path'])
        p=docs[d].pages[e['page']-1]
        cb=p.cropbox
        b=e['bbox']
        shifted=[b[0]+cb[0],b[1]+cb[1],b[2]+cb[0],b[3]+cb[1]]
        im=Image.open(ART/'raw-pages'/f"{d}-physical-p{e['page']}.png").convert('RGB')
        scale=[im.width/p.width,im.height/p.height]
        box=[round(shifted[k]*scale[k%2]) for k in range(4)]
        crop=dest/f"{row['id']}-{e['evidence_id']}-visible-crop.png"
        im.crop(tuple(box)).save(crop)
        draw=ImageDraw.Draw(im)
        draw.rectangle(box,outline='red',width=4)
        path=dest/f"{row['id']}-{e['evidence_id']}-cropbox-outline.png"
        im.save(path)
        out.append({'id':row['id'],'eid':e['evidence_id'],'page':e['page'],'coordinate_interpretation':'CropBox-local, translated to full rendered MediaBox','pixel_box':box,'outline_path':path.relative_to(ROOT).as_posix(),'visible_crop_path':crop.relative_to(ROOT).as_posix()})
(ART/'actual-bbox-visible-render.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(len(out))
