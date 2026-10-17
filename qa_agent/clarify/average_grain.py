"""One real average-grain ambiguity should produce one clarification slot."""
from __future__ import annotations
from copy import deepcopy
import re


def with_unique_average_grain_request(requests,program_request):
    same=[];other=[]
    for item in requests:
        text=str(item.get('question') or '')+' '+str(item.get('reason') or '')
        equivalent=(item.get('field') in {'metric','average_grain'} and
            re.search(r'人均|平均|粒度',text) and re.search(r'客户|customer',text,re.I) and
            re.search(r'发票|账单|invoice',text,re.I))
        (same if equivalent else other).append(deepcopy(item))
    resolved=deepcopy(program_request)
    # Preserve descriptive material/options; option execution is still owned by
    # the existing trusted-card path, never newly enabled by a model request.
    for item in same:
        for key,value in item.items():
            if key not in resolved:resolved[key]=value
    return other+[resolved]
