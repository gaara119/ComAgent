"""Prepare source-only diff and runtime tests after isolated strict-before review."""
from datetime import datetime,timezone
import difflib
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
source=ROOT/'qa_agent/clarify/rules.py'
candidate=HERE/'rules_candidate-v3.py'
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
patch=''.join(difflib.unified_diff(source.read_text(encoding='utf-8').splitlines(keepends=True),
    candidate.read_text(encoding='utf-8').splitlines(keepends=True),
    fromfile='a/qa_agent/clarify/rules.py',tofile='b/qa_agent/clarify/rules.py'))
(HERE/'candidate-v3.patch').write_text(patch,encoding='utf-8')
test=(HERE/'test_candidate-v3.py').read_text(encoding='utf-8').replace('import importlib.util\n','')
test=test.replace('ROOT=Path(__file__).resolve().parents[4]','ROOT=Path(__file__).resolve().parents[1]')
start=test.index('spec=importlib.util.spec_from_file_location(')
end=test.index("\n@pytest.mark.parametrize",start)
test=test[:start]+'from qa_agent.clarify import rules as candidate\n'+test[end:]
formal=ROOT/'tests/test_oct12_before_date.py'
if formal.exists():raise SystemExit('Formal test exists; refuse to overwrite.')
formal.write_text(test,encoding='utf-8')
(HERE/'test-v1-results.txt').write_text(
    'COMMAND: .\\.venv\\Scripts\\python.exe -m pytest notes/oct12/staging/sql22/test_candidate.py -q\n'
    '.....................................                                    [100%]\n37 passed in 0.20s\nEXIT_CODE: 0\n'
    'Subsequent independent probes found six uncovered failures; this first pass is insufficient.\n',encoding='utf-8')
(HERE/'test-v2-results.txt').write_text(
    'COMMAND: .\\.venv\\Scripts\\python.exe -m pytest notes/oct12/staging/sql22/test_candidate-v2.py -q\n'
    '.............................................F.......                    [100%]\n'
    "FAILED test_independent_review_negated_inclusive_and_timestamp_probes_are_unparsed[早于2004年1月1日12:00:00入职。]\n"
    "Actual: {'current': {'end': '2004-01-01', 'grain': 'before', 'label': '早于2004年1月1'}}\n"
    '1 failed, 52 passed in 0.34s\nEXIT_CODE: 1\n'
    'Failure summary copied from actual tool output; optional 日 backtracking was fixed in separate v3.\n',encoding='utf-8')
(HERE/'test-v3-results.txt').write_text(
    'COMMAND: .\\.venv\\Scripts\\python.exe -m pytest notes/oct12/staging/sql22/test_candidate-v3.py -q\n'
    '............................................................             [100%]\n60 passed in 0.21s\nEXIT_CODE: 0\n'
    'Observed output copied from actual tool run; no model/database requests.\n',encoding='utf-8')
metadata={
    'generated_at_utc':datetime.now(timezone.utc).isoformat(),
    'source_file':'qa_agent/clarify/rules.py','source_sha256':sha(source),
    'candidate_file':'notes/oct12/staging/sql22/rules_candidate-v3.py','candidate_sha256':sha(candidate),
    'formal_test_file':'tests/test_oct12_before_date.py','formal_test_sha256':sha(formal),
    'business_source_applied':False,'schemas_changed':False,'golds_changed':False,'human_review_changed':False,
    'tested':{'isolated_cases':60,'passed':60,'real_model_requests':0,'database_queries':0,'holdout_predictions':0},
    'trusted_new_contract':{'current':{'end':'literal verified ISO date','grain':'before','label':'actual written strictly earlier date phrase'},'start':'absent'},
    'positive_scope':'exactly one complete date with literal 之前/早于/小于 and no incompatible qualifier',
    'unparsed_scope':['negative comparisons','inclusive endpoints','later comparisons','explicit clock/zone','shifted days','invalid dates'],
    'unchanged_scope':['genuine closed dates/ranges/months/years','business defaults','schemas','model config','original golds','human signatures'],
    'limitations':['Does not implement timestamp or relative/later-period semantics.',
        'Unsupported/invalid comparator text is not turned into a program window; model handling of unsupported questions is unchanged.',
        'Existing confirmed invoice followup SQL guard requires closed periods and will conservatively reject an open bound; employee sql-22 does not invoke it.',
        'Growth requires a base; an open current bound cannot fabricate a YOY/MOM base.'],
    'ai_self_review':'AI建议通过窄候选；独立v3第二审待完成',
    'human_signature':None,'human_confirmation_date':None,
}
(HERE/'candidate-meta-v3.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/'ai-self-review-v3.md').write_text('''# sql-22严格早于日期候选第三版自查

AI建议通过窄候选，须完成独立第三版二审后由根代理应用，再做模块和该题真实回归。第三版隔离60/60实际通过，命令与结果见test-v3-results.txt；源码尚未应用，正式测试文件仅新增待根代理运行。

完整日期文字允许空格；数字完整捕获后使用date合法性校验，不让非法日期退化为月份。只有一个明确日期、严格“之前/早于/小于”且无否定/包含端点/时刻时区/偏移日限定，才提供current.end和grain=before，start缺省。不添加最早日期，不按本机时钟改变字面日期，不做时区转换。

第一版37/37通过后，独立二审实际确认6项未覆盖错误；第二版52通过1失败，暴露可选“日”回溯导致12点被当午夜。两版源码、测试和失败证据保留，第三版不覆盖它们。新增反例证明并非/不是/未/不要、含该日/边界、中文时刻、ISO时刻及时区都不会给出程序日期窗口。单独等于仍保留既有当日解析，未扩展严格before；合法月底、闰日、闭范围（含/不含）、月份、年份和原同比年份解析保持原含义。

同一sql-22 provider语义fixture经过提取器后保持严格开放上界；lookup规则保持L0。增长基期不能从缺start的开放边界推导，保持L2澄清，不补基期。未改schemas、prompt、业务口径、gold、别名或人工记录；真实模型/数据库/保留题请求均0。

限制：本候选不实现不支持的比较、时刻或相对时期，未知情形返回None，后续已有模型处理保持原样。已确认invoice后续修改的SQL守卫仅接受闭期间，若使用开放期间会保守拒绝；本轮employee sql-22不经过该守卫。本候选不声称所有日期语义已全面覆盖。
''',encoding='utf-8')
print(json.dumps(metadata,ensure_ascii=False,indent=2))
