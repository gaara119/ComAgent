"""Import explicit semantic assessments bound to immutable prediction hashes."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator


class Assessment(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    id:str
    strategy:str
    repeat:int=Field(ge=1)
    prediction_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    reviewer_kind:Literal['human','ai']|None=None
    reviewer:str|None=None
    answer_correctness:float|None=Field(default=None,ge=0,le=1)
    faithfulness:float|None=Field(default=None,ge=0,le=1)
    citation_support:float|None=Field(default=None,ge=0,le=1)
    fact_completeness:float|None=Field(default=None,ge=0,le=1)
    notes:str=''
    review_status:Literal['pending_human_review','assessed']='pending_human_review'

    @model_validator(mode='after')
    def attribution(self):
        if any(getattr(self,k) is not None for k in ('answer_correctness','faithfulness','citation_support','fact_completeness')):
            if not self.reviewer_kind or not self.reviewer or not self.notes.strip() or self.review_status!='assessed':
                raise ValueError('A score requires explicit reviewer kind, identity, rationale and assessed status')
        return self


def apply_assessments(predictions,assessments):
    rows={(r['id'],r['strategy'],r['repeat']):r for r in predictions}
    if len(rows)!=len(predictions):raise ValueError('Duplicate prediction key')
    for r in predictions:
        calculated=hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!='prediction_sha256'},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        if calculated!=r.get('prediction_sha256'):raise ValueError('Prediction contents do not match its hash')
    verified=[];seen=set()
    for raw in assessments:
        a=Assessment.model_validate(raw);key=(a.id,a.strategy,a.repeat)
        if key in seen:raise ValueError('Duplicate assessment key')
        seen.add(key)
        if key not in rows or rows[key]['prediction_sha256']!=a.prediction_sha256:
            raise ValueError('Assessment does not match exact prediction hash')
        if 'generation' not in rows[key]:raise ValueError('Cannot assess a retrieval-only record as an answer')
        verified.append(a)
    summary={}
    for kind in ('ai','human'):
        own=[a for a in verified if a.reviewer_kind==kind and a.review_status=='assessed']
        summary[kind]={'assessed_records':len(own),'total_predictions':len(rows)}
        for field in ('answer_correctness','faithfulness','citation_support','fact_completeness'):
            scores=[getattr(a,field) for a in own if getattr(a,field) is not None]
            summary[kind][field]={'mean':mean(scores) if scores else None,'denominator':len(scores)}
    return {'summary':summary,'assessments':[a.model_dump() for a in verified],
            'notice':'AI judgments and human assessments are separate; this does not approve dataset labels.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--predictions',type=Path,required=True);p.add_argument('--assessments',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    rows=[json.loads(s) for s in a.predictions.read_text('utf-8').splitlines() if s.strip()]
    result=apply_assessments(rows,json.loads(a.assessments.read_text('utf-8')))
    with a.output.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result['summary']))


if __name__=='__main__':main()
