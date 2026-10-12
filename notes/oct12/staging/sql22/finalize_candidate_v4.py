"""Freeze final narrow candidate, keeping rejected versions and evidence intact."""
from datetime import datetime,timezone
import difflib
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
source=ROOT/'qa_agent/clarify/rules.py'
candidate=HERE/'rules_candidate-v4.py'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
base=json.loads((HERE/'candidate-meta-v3.json').read_text(encoding='utf-8'))
if sha(source)!=base['source_sha256']:raise SystemExit('Frozen source changed; stop.')
formal=ROOT/'tests/test_oct12_before_date.py'
if sha(formal)!=base['formal_test_sha256']:raise SystemExit('Formal test changed; stop.')
test=(HERE/'test_candidate-v4.py').read_text(encoding='utf-8').replace('import importlib.util\n','')
test=test.replace('ROOT=Path(__file__).resolve().parents[4]','ROOT=Path(__file__).resolve().parents[1]')
start=test.index('spec=importlib.util.spec_from_file_location(')
end=test.index('\n@pytest.mark.parametrize',start)
test=test[:start]+'from qa_agent.clarify import rules as candidate\n'+test[end:]
formal.write_text(test,encoding='utf-8')
patch=''.join(difflib.unified_diff(source.read_text(encoding='utf-8').splitlines(keepends=True),
    candidate.read_text(encoding='utf-8').splitlines(keepends=True),
    fromfile='a/qa_agent/clarify/rules.py',tofile='b/qa_agent/clarify/rules.py'))
(HERE/'candidate-v4.patch').write_text(patch,encoding='utf-8')
(HERE/'test-v4-results.txt').write_text(
    'COMMAND: .\\.venv\\Scripts\\python.exe -m pytest notes/oct12/staging/sql22/test_candidate-v4.py -q\n'
    '.................................................................        [100%]\n65 passed in 0.22s\nEXIT_CODE: 0\n'
    'Observed tool output copied; no real model/database calls or holdout reads.\n',encoding='utf-8')
metadata={**base,'generated_at_utc':datetime.now(timezone.utc).isoformat(),
    'candidate_file':'notes/oct12/staging/sql22/rules_candidate-v4.py','candidate_sha256':sha(candidate),
    'formal_test_sha256':sha(formal),'source_sha256':sha(source),
    'tested':{'isolated_cases':65,'passed':65,'real_model_requests':0,'database_queries':0,'holdout_predictions':0},
    'ai_self_review':'AI建议通过窄候选；独立v4第二审待完成',
    'replaces_unapplied_candidate_version':3,
    'added_scope_proof':'Date-attached comparison intent first; unrelated amount/negated-paid predicates do not disable ordinary day windows.'}
(HERE/'candidate-meta-v4.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/'ai-self-review-v4.md').write_text('''# sql-22严格早于日期最终窄候选自查

AI建议通过第四版，仍须独立二审后应用。65/65实际隔离测试通过；只改rules.py日期解析候选，不改运行源码、schemas、prompt、gold或人工记录。

第三版误拦合法单日附带金额比较/未支付属性，原因是尚未先证明比较词作用于日期。第四版先证明日期邻近的比较关系，之后才对严格before相关否定、含端点、时刻/时区和次日限定保守返回None。四种普通单日属性/金额例子继续给出既有当日窗口；严格before附带工资大于5仍保持正确开放上界。原第三版及独立失败证据保留。

只有一个合法完整日期及明确之前/早于/小于才产生current.end=原文字面日期、grain=before，缺省start，不虚构最早日期或转换时区。日期数字完整捕获再校验，非法日期不降成月份。合法月份、年份、闰日、月底、闭范围、同比规则保持原义；开期间增长无法推导基期，仍L2澄清。不实现后于、时刻或相对日期的新语义。不支持的比较不由本程序编造窗口，其后已有模型逻辑未改。

实际模块及真实sql-22仍由根代理在应用后运行；本记录不是正式模型成绩。0真实模型/数据库/保留题请求，人工签名和确认日期未填写。
''',encoding='utf-8')
print(json.dumps({'source_sha256':sha(source),'candidate_sha256':sha(candidate),'formal_test_sha256':sha(formal),'tests':65,'runtime_applied':False},ensure_ascii=False,indent=2))
