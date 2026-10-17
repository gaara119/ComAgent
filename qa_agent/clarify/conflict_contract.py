"""Input proposals and program decisions are deliberately different types."""
from __future__ import annotations
from typing import Any,Literal
from pydantic import BaseModel,ConfigDict,Field,StrictInt,model_validator

ConflictField=Literal['time_scope.current','time_scope.base','metric','filters','region_scope','numerator','denominator','rank_object','top_n','order','grouping']

class ConflictSourceRef(BaseModel):
    model_config=ConfigDict(extra='forbid')
    # IDs are supplied by the program registry; the model never computes hashes.
    source_id:str=Field(min_length=1,max_length=240)
    quote:str=Field(min_length=1,max_length=2400)
    source_version:str|StrictInt|None=None
    content_sha256:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    char_start:StrictInt|None=Field(default=None,ge=0)
    char_end:StrictInt|None=Field(default=None,ge=0)

class ConflictAlternative(BaseModel):
    model_config=ConfigDict(extra='forbid')
    source_ref:ConflictSourceRef

    @model_validator(mode='before')
    @classmethod
    def reference_only(cls,value):
        # Source dates are program-derived. A model value is neither another
        # user condition nor a reason to ask the user to resolve a model error.
        if isinstance(value,dict)and'value'in value:
            if value['value']is not None:
                raise ValueError('冲突备选项只能提供source_ref；不得填写value或猜测日期，日期由真实来源逐字核验后派生。')
            value={key:item for key,item in value.items()if key!='value'}
        return value

class ConflictProposal(BaseModel):
    model_config=ConfigDict(extra='forbid')
    id:str=Field(min_length=1,max_length=100)
    field:ConflictField
    alternatives:list[ConflictAlternative]=Field(min_length=2,max_length=8)

class ConflictRecord(BaseModel):
    model_config=ConfigDict(extra='forbid')
    # A content-derived program key, never the model's potentially duplicated ID.
    record_id:str
    proposal_ids:list[str]=Field(default_factory=list)
    field:ConflictField|None=None
    status:Literal['unknown','active','resolved_by_priority','resolved_by_patch','retired']
    evaluated_intent_version:int=0
    depends_on:list[str]=Field(default_factory=list)
    verified_alternatives:list[dict[str,Any]]=Field(default_factory=list)
    reason_code:str
    not_authoritative:bool=False
    resolution:dict[str,Any]|None=None
    review_hint:dict[str,Any]=Field(default_factory=dict)
