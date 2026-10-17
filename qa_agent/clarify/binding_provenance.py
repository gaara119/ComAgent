"""Retire a field-owner proof when an actual confirmed country scope changes."""
from copy import deepcopy

COUNTRY_COLUMNS={'invoice.billing_country','customer.country'}

def bind_initial_region(binding,target,question,*,explicit):
    """A region role can migrate a value, never its old column's index proof."""
    if binding.get('column')not in COUNTRY_COLUMNS or binding.get('column')==target:return dict(binding),None
    origin=deepcopy(binding);current=dict(binding)
    for key in ('field_owner_proof','evidence_ref','candidate_id','source_quote'):current.pop(key,None)
    source='program:explicit_initial_region_scope'if explicit else'program:approved_initial_region_scope'
    current.update(column=target,source='explicit_user_scope'if explicit else'approved_default_scope',
        method='program_initial_region_scope',value_index_revalidated=False,
        value_origin={'role':'value_only_not_current_field_authorization',**origin},
        field_owner_proof={'source':source,'column':target,'evidence':question,
            **({}if explicit else{'policy_id':'oct12.region.invoice_billing'if target=='invoice.billing_country'else'oct12.region.customer_residence'})},
        evidence_ref=source,scope_evidence=question if explicit else'oct12_approved_default')
    return current,{'old_column':origin['column'],'new_column':target,
        'old_proof':deepcopy(origin.get('field_owner_proof')),'value_origin':origin,'reason':source}

def migrate_region_bindings(bindings,target,user_message,intent_version,prior_bindings=None):
    migrated=[];retired=[]
    for binding in bindings:
        if binding.get('column') not in COUNTRY_COLUMNS:
            migrated.append(binding);continue
        previous=[p for p in (prior_bindings or [])if p.get('value')==binding.get('value')and p.get('operator')==binding.get('operator')and p.get('column')in COUNTRY_COLUMNS]
        origin=deepcopy(previous[0] if len(previous)==1 else binding)
        old=deepcopy(origin.get('field_owner_proof'))
        old_column=(old or{}).get('column')or origin['column']
        current=dict(binding)
        for key in ('field_owner_proof','evidence_ref','candidate_id','source_quote'):current.pop(key,None)
        current['column']=target
        current['value_origin']={'role':'value_only_not_current_field_authorization',
            **{k:deepcopy(origin[k])for k in ('column','value','source','method','evidence_ref','candidate_id','source_quote','scope_evidence','field_owner_proof')if k in origin}}
        current['source']='explicit_user_scope_change'if user_message.strip()else'program_unverified_scope_migration'
        current['method']='explicit_user_scope_change'if user_message.strip()else'unverified_scope_migration'
        current['value_index_revalidated']=False
        if old is not None:
            retired.append({'old_proof':old,'old_column':old_column,
                'new_column':target,'old_scope_evidence':origin.get('scope_evidence'),
                'value':deepcopy(binding.get('value')),'retired_at_version':intent_version})
        if user_message.strip():
            current['field_owner_proof']={'source':'program:confirmed_region_scope_change',
                'column':target,'evidence':user_message,'intent_version':intent_version}
            current['scope_evidence']=user_message
            current['source_quote']=user_message
            current['evidence_ref']=f'user_region_scope_change:v{intent_version}'
        migrated.append(current)
    return migrated,retired

def migrate_operand_bindings(current,previous,previous_region,target,user_message,intent_version):
    """Only mirrors of the prior region at the same typed filter path move."""
    if not isinstance(current,dict)or not isinstance(previous,dict):return current,[]
    result=deepcopy(current);retired=[]
    for name in ('numerator','denominator'):
        now=result.get(name);prior=previous.get(name)
        if not isinstance(now,dict)or not isinstance(prior,dict):continue
        filters=now.get('filters');old_filters=prior.get('filters')
        if not isinstance(filters,list)or not isinstance(old_filters,list):continue
        for index,binding in enumerate(filters):
            if not isinstance(binding,dict):continue
            prior=old_filters[index]if index<len(old_filters)else None
            if (not isinstance(prior,dict)or(prior.get('column')or prior.get('field'))!=previous_region
                    or prior.get('value')!=binding.get('value')or prior.get('operator')!=binding.get('operator')
                    or(binding.get('column')or binding.get('field'))not in{previous_region,target}
                    or binding.get('binding_scope')!=prior.get('binding_scope')):continue
            original=dict(prior);field_only='field'in binding and'column'not in binding
            normalized={**binding,'column':binding.get('column')or binding.get('field')}
            original['column']=original.get('column')or original.get('field')
            changed,events=migrate_region_bindings([normalized],target,user_message,intent_version,[original])
            migrated=changed[0]
            if field_only:migrated['field']=migrated.pop('column')
            elif 'field'in migrated:migrated['field']=target
            filters[index]=migrated
            retired.extend({**event,'operand':name,'filter_index':index}for event in events)
    return result,retired

def attach_region_choice(state,card,choice,patches):
    if not any(p.path=='region_scope'and p.op=='set'for p in patches):return
    choice_proof={'choice_id':choice['id'],'choice_label':choice['label'],
        'clarification_id':card['clarification_id'],'intent_version':state.intent.intent_version}
    for binding in state.bindings:
        proof=binding.get('field_owner_proof')or{}
        if binding.get('column')in COUNTRY_COLUMNS and proof.get('source')=='program:confirmed_region_scope_change'and proof.get('column')==state.analysis.region_scope and proof.get('intent_version')==state.intent.intent_version:
            binding['field_owner_proof']={**proof,**choice_proof,'source':'program:trusted_region_choice'}
            binding.update(source='explicit_user_choice',method='explicit_user_choice',
                evidence_ref=f"clarification:{card['clarification_id']}:{choice['id']}")
    for operand in ('numerator','denominator'):
        for binding in (state.analysis.query_scope.get(operand)or{}).get('filters',[]):
            proof=binding.get('field_owner_proof')or{}
            if proof.get('source')=='program:confirmed_region_scope_change'and proof.get('column')==state.analysis.region_scope and proof.get('intent_version')==state.intent.intent_version:
                binding['field_owner_proof']={**proof,**choice_proof,'source':'program:trusted_region_choice'}
                binding.update(source='explicit_user_choice',method='explicit_user_choice',
                    evidence_ref=f"clarification:{card['clarification_id']}:{choice['id']}")
    state.analysis.filters=state.bindings
    state.history.append({'event':'trusted_region_field_binding',**choice_proof,
        'target_column':state.analysis.region_scope})
