"""Read dev sql-22 and reproduce its date extraction fault without model/DB calls."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from qa_agent.clarify.extractor import extract_intent
from qa_agent.clarify.rules import SemanticIntent, explicit_period
from qa_agent.sql.catalog import load_catalog

OUT=ROOT/'eval/artifacts/oct12/sql22-diagnosis-004'
OUT.mkdir(parents=True,exist_ok=True)
if (OUT/'readonly-diagnosis.json').exists():
    raise SystemExit('Evidence exists; refuse to overwrite it.')
guarded=[ROOT/'qa_agent/clarify/rules.py',ROOT/'qa_agent/clarify/extractor.py',
         ROOT/'eval/artifacts/d2-final/review/sql-dev-v1.jsonl']
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
before={str(path.relative_to(ROOT)).replace('\\','/'):sha(path) for path in guarded}
def single_dev(path):
    found=[]
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            item=json.loads(line)
            if item.get('id')=='sql-22':found.append(item)
    if len(found)!=1 or found[0].get('split')!='dev':
        raise RuntimeError('Only the single specified dev sql-22 may be selected.')
    return found[0]
gold=single_dev(guarded[2])
histories=[]
for rel in ['eval/artifacts/oct12/d2-dev-live-001/sql/responses.jsonl',
            'eval/artifacts/oct12/d2-dev-live-002/sql/responses.jsonl',
            'eval/artifacts/oct12/sql-final-live-003/responses.jsonl']:
    item=single_dev(ROOT/rel)
    response=item['response']
    histories.append({'file':rel,'id':'sql-22','split':'dev','matched':item['matched'],
        'comparison':item.get('comparison'),'status':response['status'],
        'question':item['request']['message'],'intent':response['intent'],
        'sql':response['sql'],'actual_rows':response['table'],
        'columns':response['metadata']['result_columns'],
        'sql_generation_input':next(step for step in response['steps'] if step['name']=='sql_gen')['input_summary']['question']})
capture_rel='eval/artifacts/oct12/provider-captures/live-003/dbc5172fa9fa4be89b195cb828274119.json'
capture=json.loads((ROOT/capture_rel).read_text(encoding='utf-8'))
provider_semantic=json.loads(capture['response']['choices'][0]['message']['content'])
class FixtureModel:
    calls=0
    def complete_json(self,*args,**kwargs):
        self.calls+=1
        return SemanticIntent.model_validate(provider_semantic)
model=FixtureModel()
runtime_semantic=extract_intent(gold['question'],load_catalog(ROOT/'data/catalog/chinook.yaml'),model,bindings=[])
period_probes=[]
for text in [gold['question'],'2004年1月1日之前入职的员工。','2004-01-01之前入职的员工。',
             '2004 年 1 月入职的员工。','2003年12月1日至2004年1月1日入职的员工。']:
    period_probes.append({'question':text,'explicit_period_actual':explicit_period(text)})
after={str(path.relative_to(ROOT)).replace('\\','/'):sha(path) for path in guarded}
if before!=after:raise RuntimeError('Runtime/gold hashes changed during read-only diagnosis.')
payload={
    'id':'sql-22','split':'dev','generated_at_utc':datetime.now(timezone.utc).isoformat(),
    'state':'AI发现错误','error_kind':'deterministic_date_boundary_parse',
    'gold_question':gold['question'],'gold_sql':gold['gold_sql'],'gold_result':gold['gold_result'],
    'gold_review_record':gold['gold_review'],'question_projection':'first_name only, last_name explicitly excluded',
    'provider_capture_file':capture_rel,'actual_provider_semantic':provider_semantic,
    'runtime_extract_with_same_provider_fixture':runtime_semantic.model_dump(),
    'actual_period_probes':period_probes,'run_history':histories,
    'judgment':{'reference':'AI建议通过','actual_final_answer':'AI发现错误',
        'reason':'Complete date with spaces fails complete-date regex; month regex matches a prefix and overwrites an earlier-than boundary with a month range. Original provider extracted strict < correctly. Earlier two SQL outputs happened to obey original question despite the incorrect month contract.'},
    'suggested_next_step':'Keep source frozen for this diagnosis. If a narrowly reviewed later fix is authorized, avoid making any one-sided date comparison into a closed day/month/year window; do not invent an earliest date. Preserve explicit operator/date semantics and add spaced/nonspaced/ISO + valid month/range counterexamples.',
    'execution':{'command':'.\\.venv\\Scripts\\python.exe notes/oct12/sql22-readonly-diagnosis.py',
        'fixture_complete_json_calls':model.calls,'real_model_requests':0,'database_queries':0,'holdout_predictions':0,
        'runtime_code_modified':False,'gold_modified':False,'human_review_modified':False},
    'before_sha256':before,'after_sha256':after,
}
(OUT/'readonly-diagnosis.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
doc='''# sql-22 最终开发集失败只读诊断

结论：AI发现确定性时间边界解析错误；参考题和 gold 的 first_name 投影没有冲突，不能通过改名字口径、删除行数比较或重跑掩盖本次错误。

本轮题面明确“2004 年 1 月 1 日之前入职”，要求 hire_date < 2004-01-01，投影 employee_id、first_name、hire_date，按 employee_id 升序。已接受 DEV gold 为六行员工 1—6；最终实际投影同样是这三个字段，但 SQL 查询变为 [2004-01-01, 2004-02-01)，只返回员工 7 Robert。本次不是 full_name 或额外列问题。

实际 provider 原始语义响应已经抽到 employee.hire_date < 2004-01-01，及早于该日的期间。程序 rules.py 的完整日期正则不接受数字与“年/月/日”之间的空格，紧接着月份正则匹配了“2004 年 1 月”前缀。extractor.py 随后用这个程序月窗口覆盖 provider 边界，再用 verified bindings 的空列表替换 filters；实际 SQL 生成输入出现错误月窗口，最终 SQL 沿用了错误窗口。

前两轮该题均结果匹配，但其 intent 已有同样错误的月窗口。生成模型遵循原题“之前”而输出严格小于，第二轮解释还明确忽略错误的月份标签。前两轮通过不能证明时间解析正确，第三轮暴露了同一程序缺陷。

本次读取三轮同一个 DEV 编号、对应 provider 语义原响应与已经接受的 DEV gold；以同一 provider 响应作本地 fixture 实际调用运行提取器，并额外只读运行日期解析探针。没有真实模型请求，没有数据库查询，没有保留集预测；源码和 gold 的读前、读后哈希一致。原始响应、复现输出、命令、具体来源和哈希见 [readonly-diagnosis.json](../../eval/artifacts/oct12/sql22-diagnosis-004/readonly-diagnosis.json)。

建议另行授权窄修复：单边“之前/之后”比较不能成为完整日、月或年窗口；完整日期可识别空格，但仅修空格仍会把“之前”误当一天，须同时防止比较运算符被丢弃。不得添加虚构最早日期；保持明确比较运算及日期，不改变 gold。修复应先隔离两遍审核，覆盖中文有/无空格、ISO 日期、合法月份窗口和已有完整范围反例，再进行模块及该题独立真实回归。本诊断不应用任何修复，不扩展业务口径，不填写人工签字或日期。
'''
(ROOT/'notes/oct12/sql22-final-readonly-diagnosis.md').write_text(doc,encoding='utf-8')
print(json.dumps({'state':payload['state'],'provider_predicate':provider_semantic.get('filters'),
    'reproduced_period':runtime_semantic.time_scope,'final_columns':histories[-1]['columns'],
    'final_rows':len(histories[-1]['actual_rows']),'gold_rows':len(gold['gold_result']),
    'code_and_gold_unchanged':before==after,'real_model_requests':0,'evidence':str(OUT.relative_to(ROOT))},ensure_ascii=False,indent=2))
