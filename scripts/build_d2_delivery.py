"""Build the original nine-item acceptance report and a portable evidence ZIP."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'eval/reports/d2-acceptance'


def read(path):
    return json.loads((ROOT/path).read_text(encoding='utf8'))


def rows(path):
    return [json.loads(line) for line in (ROOT/path).read_text(encoding='utf8').splitlines() if line]


def sha(content):
    return hashlib.sha256(content).hexdigest()


def link(path,label=None):
    relative=Path(os.path.relpath(ROOT/path,OUT)).as_posix()
    return f'[{label or path}]({relative})'


def command_record(name):
    files=sorted((ROOT/'eval/artifacts/d2/commands').glob('*-'+name+'.json'))
    if not files:
        raise RuntimeError('Missing actual command record: '+name)
    return files[-1].relative_to(ROOT).as_posix(),read(files[-1].relative_to(ROOT))


def generate():
    sql=read('eval/artifacts/d2/nl2sql/final/report.json')
    robust=read('eval/artifacts/d2/robust/final/report.json')
    rag=read('eval/artifacts/d2/rag/final/report.json')
    judge=read('eval/artifacts/d2/rag/final/ai-judge.json')
    exact=read('eval/artifacts/d2/rag/final/reanalysis.json')
    value=read('eval/artifacts/d2/index-audit.json')
    doc=read('eval/artifacts/d2/docs-audit-final.json')
    preflight=read('eval/artifacts/d2/preflight-final.json')
    engineering=read('eval/reports/d2-acceptance/engineering.json')
    ui=read('eval/artifacts/d2/e2e/browser/d2-live-final/report.json')
    live=read('eval/artifacts/d2/a-live/final/summary.json')
    unified=read('eval/reports/d2-acceptance/unified-review.json')
    module_path,module=command_record('all-modules-source-guard-final')
    module_text=(ROOT/module['output']).read_text(encoding='utf8')
    match=re.search(r'(\d+) passed.*?in ([\d.]+)s',module_text)
    if module['exit_code'] or not match or ui['status']!='PASSED' or engineering['status']!='PASS' or preflight['status']!='PASS':
        raise RuntimeError('Final engineering/module/UI/preservation verification has not passed')
    module_count,module_time=int(match[1]),float(match[2])
    ordinary={r['id']:r for r in rows('eval/artifacts/d2/nl2sql/final/responses.jsonl')}
    variants=rows('eval/artifacts/d2/robust/final/responses.jsonl')
    paired=sum(ordinary[r['base_id']]['matched'] for r in variants)/len(variants)
    drop=100*(paired-robust['exploratory_ex'])
    usage=Counter()
    model_calls=0
    for suite in ('nl2sql','robust','rag'):
        for row in rows(f'eval/artifacts/d2/{suite}/final/responses.jsonl'):
            for step in (row.get('response') or {}).get('steps',[]):
                if step['name']=='llm':
                    model_calls+=1
                    for field in ('prompt_tokens','completion_tokens','total_tokens'):
                        usage[field]+=step.get('output_summary',{}).get('usage',{}).get(field,0) or 0
    summary={'created_at_utc':datetime.now(timezone.utc).isoformat(),'title':'D2 原清单九项逐项验收与证据',
             'status':'ENGINEERING_PASS_HUMAN_REVIEW_PENDING','python':'3.12.10','model':'deepseek-flash',
             'sql':{'correct':sql['correct'],'count':sql['prediction_count'],'exploratory_ex':sql['exploratory_ex'],'segments':sql['segments']},
             'robust':{'correct':robust['correct'],'count':robust['prediction_count'],'exploratory_ex':robust['exploratory_ex'],'paired_original_ex':paired,'decline_percentage_points':drop},
             'rag':{'prediction_count':rag['prediction_count'],'hit_at_5':rag['hit_at_5'],'insufficient_handling':rag['insufficient_handling'],
                    'complete_gold_quote_hit_at_5':exact['complete_gold_quote_hit_at_5'],'auxiliary_judge_correct':judge['answer_correct'],'auxiliary_judge_supported':judge['all_claims_supported'],'auxiliary_judge_count':judge['denominator'],'human_review_count':0},
             'modules':{'passed':module_count,'seconds':module_time,'command_record':module_path},
             'engineering':{'passed':engineering['passed'],'total':engineering['total']},
             'ui':{'case_count':len(ui['cases']),'status':ui['status'],'browser_errors':ui['browser_errors']},
             'corpus':{'documents':doc['parsed_document_count'],'chunks':doc['chunk_count'],'vector_shape':[doc['chunk_count'],1024]},
             'review':unified['counts'],'holdout_prediction_count':0,'model_usage_final_benchmark_only':{'api_requests':77,'llm_steps':model_calls,**usage},
             'scope':'D2 only; formal EX and human semantic/faithfulness acceptance are pending; all holdout predictions reserved for D5'}
    lines=['# D2 原清单九项逐项验收与证据','',
           '**结论：九项工程功能已接入现有 D1 项目并完成实际测试；人工审核按用户要求集中留到末尾。正式成绩尚未发布。**', '',
           '执行日期：2026-10-10；原计划 D2 日期为 10/11。所有命令和原始日志保留真实 UTC 时间。沿用 Python 3.12.10、已验证的 DeepSeek `deepseek-flash`、原 Chinook PostgreSQL 与只读 `qa_reader`。', '',
           '| 实测项目 | 最终结果 | 成绩性质 |','|---|---|---|',
           f"| 单表 SQL 开发集 | {sql['correct']}/{sql['prediction_count']}，{sql['exploratory_ex']:.2%} | gold 待审的探索 EX；D1 同题21/21、新增14/14 |",
           f"| 鲁棒开发集 | {robust['correct']}/{robust['prediction_count']}，{robust['exploratory_ex']:.2%}；相对同源原题下降 {drop:.2f} 个百分点 | 六类扰动全部计入；gold 待审 |",
           f"| RAG 开发集 | {rag['prediction_count']} 次真实请求；可答题 Hit@5 {rag['hit_at_5']['passed']}/{rag['hit_at_5']['denominator']}；不足题 {rag['insufficient_handling']['passed']}/{rag['insufficient_handling']['denominator']} | PDF 金标页或非 PDF 金标片段命中；不足题不计命中率分母 |",
           f"| RAG 辅助模型复核 | 答案一致 {judge['answer_correct']}/{judge['denominator']}；断言支持 {judge['all_claims_supported']}/{judge['denominator']} | 同厂商模型辅助判分；人工正确性、忠实度仍待审核 |",
           f'| 模块与工程验收 | {module_count} passed，{module_time:.2f}秒；工程 {engineering["passed"]}/{engineering["total"]} | 真实命令及原始输出均保存 |',
           '| 页面联调 | 5个实际场景通过，0浏览器错误；步骤展开前后同会话API请求数不变 | Edge浏览器操作、真实trace与截图 |',
           '| 保留集 | SQL15＋鲁棒9＋RAG9，共33题，预测0 | D5冻结后运行 |','',
           'RAG 的更严格“完整 gold 引文位于 Top5 单片段”诊断为 '+f"{exact['complete_gold_quote_hit_at_5']['passed']}/{exact['complete_gold_quote_hit_at_5']['denominator']}，另行保存；它与原计划按证据页/片段定义的 Hit@5 区分，不能用页命中冒称完整引文或语义审核通过。", '',
           '开始开发时 Git HEAD 为 `be79386147942e068b36ce7eb53cc4f95e200422`。实际开发评测运行时工作区有 D2 增量，原报告明确记录 `working_tree_dirty=true`。77题最终跑批后，页面联调发现并修复显式未知表问题，另存受影响的真实正反例回归；没有把此前77题改称在修复后重新运行。', '',
           '## 原清单覆盖与 D1 复用','',
           'A4项、B5项与实施说明 D2-01至D2-09完整对应。'+link('notes/d2-execution-checklist.md','覆盖核对与差异处理')+'列明开发/保留划分、13份目标、来源范围纠正、协议页码和不提前实现D3的边界。'+link('notes/references/d2/方案.md','总计划')+'与'+link('notes/references/d2/D2-可执行技术方案.md','具体实施说明')+'原样保留。','',
           'D1 保留证据87份、原 SQL/RAG 题库、共享 `schemas.py` 均通过前后SHA核对；原BGE索引三个文件未改，数据库11张表内容哈希未变。此次只读查询和构建本机索引，没有重建或重复导入数据库。证据：'+link('eval/artifacts/d2/preflight-final.json')+'、'+link('eval/artifacts/d2/d1-index-preservation.json')+'。','']
    lines += ['题库中的exposure字段是创建时的历史快照；本轮当前实际预测次数另存 '+link('eval/artifacts/d2/exposure-ledger-final.json')+'，不得把初始 `d2_model_exposed=false` 误读为开发题从未实跑。已运行的全部题仍属开发集，33保留题预测0。','']
    sections=[
        ('D2-01 / A1','写 build_value_index.py：值索引、别名初稿（LLM生成后人工审核）、拼音、向量。',
         '已对全部34个低基数文本列建立5528条字段值记录、拼音索引及5528×1024真实BGE向量。81条别名保留模型草稿与建议审核取舍；已接受0、排除81，待审别名未进入运行索引。',
         ['scripts/build_value_index.py','qa_agent/nlu/value_index.py','data/aliases/aliases.csv'],
         '真实qa_reader DISTINCT取值＋真实BGE编码＋索引SHA/形状/有限值/归一化检查。所有列<5000 distinct，构建无失败列；一次编码耗时54.447秒。',
         ['eval/artifacts/d2/index-audit.json','eval/artifacts/d2/aliases-74-model-draft.csv','notes/d2-alias-review.md'],
         '工程完成；81条别名人工审核待完成。审核通过后按具体批准条目重新构建值索引，不能直接启用整份草稿。'),
        ('D2-02 / A2','写五级linker和补丁rewrite；值绑定作为硬约束传给SQL生成。',
         '精确→拼音→字符近似→向量Top5→受限LLM裁决已接入/api/chat。保留字符Top5和向量Top5各自的候选/分数来源，合法候选ID经枚举约束；补丁只改原始span并记录原题、改写题、方法与绑定。SQL生成接收绑定，执行前SQLGlot检查WHERE/HAVING及布尔/子查询绕过。原值不存在时保留，真实歧义发起最小澄清。显式未知表在模型/执行前拒绝，避免偷偷换表。',
         ['qa_agent/nlu/linker.py','qa_agent/nlu/rewrite.py','qa_agent/pipeline.py','qa_agent/sql/generator.py','qa_agent/sql/validator.py','qa_agent/sql/executor.py'],
         f"真实API边界 {live['api_passed']}/{live['api_count']}：精确Brazil、字符Brasil、真实标准值拼音u s a、语义ba xi/jia na da、职位错字、Narnia0与摇滚歧义；另有显式来源修复后的独立真实正反例。ON/OFF诊断6/6均正确，不能宣称本小样本证明EX提升。",
         ['eval/artifacts/d2/a-live/final/summary.json','eval/artifacts/d2/a-live/final/api-responses.jsonl','eval/artifacts/d2/a-live/final/ablation-responses.jsonl','eval/artifacts/d2/a-live/source-guard'],
         '工程完成。中文拼音ba xi/jia na da本轮走受限LLM，未冒称命中尚未审核的中文别名拼音索引。完整D3澄清状态机不在D2范围。'),
        ('D2-03 / A3','单表题扩到50道，写30道鲁棒变体。',
         '保留D1原始题库，新增D2题库版本。50道SQL覆盖COUNT、筛选、聚合、分组、TopN、日期、LIKE、NULL和不存在值；30变体按错字、别名、拼音、混合语言、口语、冗余词各5题。所有50条gold SQL真实只读执行并保存结果；变体保持同源标准结果和分组。',
         ['eval/build_d2_sql_datasets.py','eval/datasets/nl2sql_chinook_d2.jsonl','eval/datasets/robust.jsonl','eval/datasets/d2_sql.manifest.json'],
         '题库结构和同源关系检查PASS：SQL35dev/15holdout、鲁棒21dev/9holdout；原D1 21/9分组不改。gold执行与模型预测分开记录。',
         ['eval/artifacts/d2/input-audit-final.json','eval/datasets/review_d2/sql_gold_review.md'],
         '工程完成；50题gold与30变体语义保持逐题待审。保留题尚未预测。'),
        ('D2-04 / A4','按目录语义、值链接、SQL结构等错误修正；目标EX≥85%。',
         '实际开发集初跑、分类修复、回归已完成。鲁棒初轮18/21中的职位抽取和两道拼音候选问题修复为21/21；页面发现的未知表假空结果另存原始失败与回归。D1评测模型元数据兼容性回退已修复，原失败日志保留。',
         ['eval/run_eval.py','eval/metrics.py','eval/reanalyze_d2_rag.py','tests/test_d2_evaluation.py'],
         '单表最终35/35达到D2探索检查点，D1同题21/21、新题14/14；鲁棒最终21/21，相对同源原题下降0个百分点。正式入口真实返回READINESS_ONLY、预测0，因为gold未人工接受。',
         ['eval/artifacts/d2/nl2sql/final/report.json','eval/artifacts/d2/nl2sql/final/responses.jsonl','eval/artifacts/d2/robust/initial/report.json','eval/artifacts/d2/robust/final/report.json','eval/artifacts/d2/robust/final/responses.jsonl','eval/artifacts/d2/nl2sql/review-gate/report.json','eval/artifacts/d2/errors-and-fixes.json'],
         '工程及草稿开发探索通过；正式EX≥85%的人工验收状态待gold审核后再运行，未把探索成绩写成正式成绩。'),
        ('D2-05 / B1','trace接进界面：步骤时间线，每步可以展开。',
         '保持SQL结果、引用来源、处理步骤与耗时三个固定面板；每个真实Step可展开输入/输出摘要、状态和耗时。显示原题、补丁改写、引用原文及真实页/章节/图像；使用会话内响应重绘。',
         ['ui/app.py','api/main.py','scripts/capture_d2_demo.py','scripts/d2_capture_api.py'],
         '真实Edge五场景：普通SQL、纠错SQL、图片RAG、证据不足、显式失败。UI与API trace一致，展开前后同会话API请求数1→1，不额外调用LLM；固定三面板，0浏览器错误。记录器只为验收启用，复用原API handler。',
         ['eval/artifacts/d2/e2e/browser/d2-live-final/report.json',*ui['screenshots']],
         '工程完成。首次Streamlit交互式邮箱提示导致headless启动失败、首轮表格挂载断言过早的原日志均保留并修复。'),
        ('D2-06 / B2','混合检索RRF、引用ID核验、数字核验。',
         '先严格筛选指定doc_id，两路各Top20，RRF k=60从rank1起、稳定chunk_id打破同分，生成Top8。编号引用必须存在且实际文档一致；数值按对应引用片段核对数字、币种符号、负号、百分号和量级，失败至多重生成一次，仍不通过如实FAILED；不足返回EMPTY_RESULT且无伪造引用。',
         ['qa_agent/rag/retriever.py','qa_agent/rag/answer.py','qa_agent/rag/service.py','tests/test_d2_rag.py'],
         '真实开发21题：20可答有引用且来源/文字/page/section/bbox与当前哈希验证索引一致；1不足无引用。模块覆盖非法ID、数字串号/单位、重试与最终失败；这些fixture不冒称真实模型错误实跑。实际保留两路及融合完整排名，Hit@5只检查前5。',
         ['eval/artifacts/d2/rag/final/report.json','eval/artifacts/d2/rag/final/responses.jsonl','eval/artifacts/d2/rag/final/reanalysis.json','eval/artifacts/d2/e2e/evidence-authenticity-final.json'],
         '工程完成。数字字面检查不等于完整语义忠实度；实际答案人工正确性及忠实度留统一审核表。'),
        ('D2-07 / B3','补齐DOCX、HTML、MD、图片OCR解析器；知识库13份；manifest含来源/格式/许可。',
         '13独立资料：原生PDF6、另一来源扫描PDF1、Top4艺术家HTML2/DOCX1/PNG1、指标DOCX1、中文字典MD1；5种扩展格式、按原生/扫描区分6种资料形式。真实OCR保留bbox与置信度；DOCX/HTML/MD保持章节，PDF物理页从1计，非PDF page=null。500字符目标、80重叠，不跨页/章节。来源、许可、语言、派生关系、内容SHA和摄取状态有独立审计。',
         ['qa_agent/rag/parsers.py','qa_agent/rag/chunker.py','qa_agent/rag/index.py','scripts/ingest_docs.py','scripts/prepare_d2_documents.py','data/docs/manifest.csv'],
         '最终13/13入库，2193×1024真实BGE归一化向量；7英文/6中文。13原文件下载SHA、7PDF首末物理页预览、6非PDF伪物理页拒绝均实测通过。初建11/13因两DOCX在终版渲染中改动hash而失败，原失败索引/日志保留，终版用新目录重新构建。',
         ['eval/artifacts/d2/docs-audit-initial.json','eval/artifacts/d2/docs-audit-final.json','eval/artifacts/d2/source/corpus-preparation.json','eval/artifacts/d2/source/artist-source-audit.json','eval/artifacts/d2/source/ohr-scan-source.json','eval/reports/d2-acceptance/engineering.json'],
         '工程完成。扫描多栏顺序和562个不完整句子边界标志如实保留。艺人资料为署名中文改写；PNG为实际本地简介网页截图，未冒称维基原站截图。manifest的prepared表示源文件注册，实际ingested状态见最终索引审计。'),
        ('D2-08 / B4','2–3页DOCX业务指标口径手册，含销售额、客单价、复购、热门曲目及SQL。',
         '已生成3页指标手册，四项口径有A/B明确共同同意记录；金额单位不臆测，日期左闭右开，NULL/零分母/地区字段含义明确。机器定义同步保存，完整D3运行默认仍关闭。',
         ['data/docs/raw/d2/Chinook业务指标口径手册.docx','data/rules/metric_definitions.json','scripts/prepare_d2_metric_proposal.py','scripts/render_d2_docx.ps1'],
         '6段示例SQL真实只读执行。2024发票销售477.53，平均每张发票5.75，至少两张发票复购27人；整库发票额与明细额2328.60一致。Word实际导出3页PDF并渲染逐页检查；艺人DOCX为1页。',
         ['eval/artifacts/d2/source/metric-human-review.json','eval/artifacts/d2/source/metric-sql-checks.json','eval/artifacts/d2/source/docx-authoring-audit.json'],
         '四指标口径已确认，保留既有记录，不重复要求批准。文档版式由Codex检查，未将它当作题库gold或答案忠实度的人审。'),
        ('D2-09 / B5','RAG扩到30题＝OHR20＋自建文档10；跑第一轮评测。',
         '原20官方text QA保持问题、答案、物理页和14dev/6holdout；10自建文档题中含3不足，新增7dev/3holdout，最终21dev/9holdout。准备阶段将一OHR扫描题误算自建来源的问题在正式模型预测前纠正，原版本与独立OCR探针保留。',
         ['scripts/prepare_d2_rag_dataset.py','eval/datasets/rag_single.jsonl','eval/datasets/rag_single.manifest.json','eval/d2_rag_eval.py','eval/judge_d2_rag.py'],
         f"初轮及最终开发实跑各21请求；最终可答Hit@5 20/20、不足1/1；同源D1开发14题＋新增7题分别记录。最终辅助模型答案一致{judge['answer_correct']}/21、断言支持{judge['all_claims_supported']}/21，源响应/题库SHA和真实模型/调用trace齐全。",
         ['eval/artifacts/d2/rag/initial/report.json','eval/artifacts/d2/rag/final/report.json','eval/artifacts/d2/rag/final/ai-judge.json','eval/artifacts/d2/source/rag-source-scope-correction.json','eval/artifacts/d2/source/ocr-e2e-case.json','eval/reports/d2-acceptance/unified-review.html'],
         '工程、题集与实际基线完成；30题gold、实际开发答案正确性/忠实度仍待人工审核，不能发布正式RAG答案准确率或忠实度。9道保留题D5待测。')]
    for title,requirement,implementation,changed,method,evidence,remaining in sections:
        lines += ['## '+title,'','**要求：** '+requirement,'','**实现情况：** '+implementation,'',
                  '**改动文件：** '+ '、'.join(link(p) for p in changed)+'。','',
                  '**测试方法与实际结果：** '+method,'',
                  '**证据位置：** '+ '、'.join(link(p) for p in evidence)+'。','',
                  '**未完成事项 / 口径限制：** '+remaining,'']
    lines+=['## 实际命令、原始记录和后续审核','',
            '全部执行命令、exit code、UTC时间和脱敏输出见 '+link('eval/artifacts/d2/commands/commands.jsonl')+'。最终模块原始输出：'+link(module['output'])+'；测试含确定性fixture与真实独立probe，二者分别记录。依赖检查 '+link(command_record('dependency-check-final')[1]['output'])+'。', '',
            '开发评测实际使用以下命令（每次使用独立目录；原失败保留）：','',
            '```powershell',
            r'.\.venv\Scripts\python.exe eval\run_eval.py --suite nl2sql --split dev --draft-gold --run-id d2-nl2sql-final --output-dir eval/artifacts/d2/nl2sql/final',
            r'.\.venv\Scripts\python.exe eval\run_eval.py --suite robust --split dev --draft-gold --run-id d2-robust-final --output-dir eval/artifacts/d2/robust/final',
            r'.\.venv\Scripts\python.exe eval\run_eval.py --suite rag --split dev --draft-gold --run-id d2-rag-final --output-dir eval/artifacts/d2/rag/final',
            r'.\.venv\Scripts\python.exe -m pytest -q','```','',
            f"最后三套正式题集开发跑批合计77个API请求、{model_calls}个真实LLM步骤、{usage['total_tokens']} total_tokens。用量仅从这些最终响应的trace计算，不包括初轮、辅助评审、UI、额外probe与小样本消融；见本报告JSON。最终跑批并行运行，各均值为当时HTTP耗时，不冒称与D1串行延迟直接可比或已经做了D6效率压测。",'',
            '人工审核集中使用 '+link('eval/reports/d2-acceptance/unified-review.html','统一审核表 HTML')+' 或 '+link('eval/reports/d2-acceptance/unified-review.md','同内容 Markdown')+'，标准材料与真实回答已内嵌，无需为了解答逐个翻源码。191项待审＝81别名＋50SQLgold＋30鲁棒语义＋30RAG gold/回答；另4指标为既有共同批准记录。按题号填写A/B、日期、结论和意见；RAG同一项分别核对gold、答案正确性、引用忠实度。保留33题当前实际回答为空，D5前只审核题目与标准材料。', '',
            '审核后将具体通过/拒绝条目与改动告知或交回审核记录，先更新被批准的标注与哈希，再用新的run-id运行正式开发评测；若有gold修正，重新执行相应只读SQL并保存修订证据。当前没有替用户填写人工接受，也没有因为等待审核停止工程工作。', '',
            '## 打包与查看','',
            'ZIP内保留项目目录，根目录的同内容HTML报告可直接用浏览器打开；HTML的源码、日志、截图和原文附件均用相对路径。需先完整解压再打开。统一审核表在 `eval/reports/d2-acceptance/unified-review.html`，支持题号/词句搜索与dev/holdout筛选。', '',
            '附件包含对应源码、题集、标准结果、原始模型响应、日志、五场景截图、13份原资料及来源许可；不包含真实.env、数据库密码、虚拟环境、模型权重或PostgreSQL数据卷。附带索引供复核；新电脑运行须按README安装Python3.12依赖、准备本机模型/凭据并连接现有数据库。报告查看不需API key。', '',
            '当前本机页面：`http://127.0.0.1:8501/`；API：`http://127.0.0.1:8000/docs`。这两个地址供本机使用，附件中的证据不依赖这两个服务地址。','']
    OUT.mkdir(parents=True,exist_ok=True)
    content='\n'.join(lines)
    (OUT/'requested-d2-evidence.md').write_text(content,encoding='utf8')
    (OUT/'requested-d2-evidence.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    from markdown_it import MarkdownIt
    body=MarkdownIt('commonmark').enable('table').render(content)
    html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>D2 原清单九项逐项验收与证据</title><style>body{max-width:1100px;margin:32px auto;padding:0 20px;font:16px/1.75 system-ui,Microsoft YaHei,sans-serif;color:#202830}h1{font-size:30px}h2{font-size:23px;margin-top:36px}a{color:#075eb1;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse}th,td{padding:10px;border:1px solid #ccd3da;text-align:left;vertical-align:top}th{background:#f2f5f8}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f7;padding:16px}code{font-family:Consolas,monospace;font-size:14px}</style><body>'+body+'</body></html>'
    (OUT/'requested-d2-evidence.html').write_text(html,encoding='utf8')
    (ROOT/'eval/reports/d2.md').write_text(content,encoding='utf8')
    # Rebase this optional short location's links to preserve their actual targets.
    shorter=ROOT/'eval/reports/d2.md'
    shorter.write_text(re.sub(r'\]\(([^)]+)\)',lambda m:']('+rebase(m.group(1),OUT,shorter.parent)+')',content),encoding='utf8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


def rebase(target,source,destination):
    if urlsplit(target).scheme or target.startswith('#'):
        return target
    parts=target.split('#',1)
    path=(source/unquote(parts[0])).resolve()
    return Path(os.path.relpath(path,destination)).as_posix()+('#'+parts[1] if len(parts)>1 else '')


class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.targets=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('a','img'):
            self.targets.extend(v for k,v in attrs if k in ('href','src') and v)


def package(destination):
    from dotenv import dotenv_values
    contents={}
    candidates=subprocess.check_output(['git','-c','core.quotepath=false','ls-files','-z','--cached','--others','--exclude-standard'],cwd=ROOT).decode('utf8').split('\0')
    for name in filter(None,candidates):
        path=ROOT/name
        # Include source, all D2 evidence and necessary historical source data.
        if name.startswith(('output/','eval/reports/d1','eval/reports/rag-d1','notes/screenshots/D1')):
            continue
        if path.is_file() and name not in {'eval/reports/d2-acceptance/package-audit.json','eval/reports/d2-acceptance/bundle-file-manifest.json'}:
            contents[Path(name).as_posix()]=path.read_bytes()
    for directory in ('data/docs/raw','data/indexes/values','data/indexes/docs-final'):
        for path in (ROOT/directory).rglob('*'):
            if path.is_file(): contents[path.relative_to(ROOT).as_posix()]=path.read_bytes()
    # Follow all evidence links so the acceptance and review tables are portable.
    for docname in ('requested-d2-evidence.html','unified-review.html'):
        parser=Links();parser.feed((OUT/docname).read_text(encoding='utf8'))
        for target in parser.targets:
            if urlsplit(target).scheme or target.startswith('#'):continue
            path=(OUT/unquote(target.split('#',1)[0])).resolve()
            if not path.is_relative_to(ROOT) or not path.exists():
                raise ValueError('Missing/outside evidence link: '+target)
            if path.is_file():contents[path.relative_to(ROOT).as_posix()]=path.read_bytes()
            else:
                for item in path.rglob('*'):
                    if item.is_file():contents[item.relative_to(ROOT).as_posix()]=item.read_bytes()
    for name in ('requested-d2-evidence.html','requested-d2-evidence.md'):
        content=(OUT/name).read_text(encoding='utf8')
        if name.endswith('.html'):
            content=re.sub(r'href="([^"]+)"',lambda m:'href="'+rebase(m.group(1),OUT,ROOT)+'"',content)
        else:
            content=re.sub(r'\]\(([^)]+)\)',lambda m:']('+rebase(m.group(1),OUT,ROOT)+')',content)
        contents['D2 原清单九项逐项验收与证据'+Path(name).suffix]=content.encode('utf8')
    contents['先看这里.txt']=('请先完整解压本ZIP，再双击根目录“D2 原清单九项逐项验收与证据.html”。\n统一审核表：eval/reports/d2-acceptance/unified-review.html。\n原文附件保留项目目录结构，证据相对链接在解压后可打开。\n目录型链接请用文件管理器查看，源码可用文本编辑器打开。\n查看报告无需启动项目或配置API key；运行环境与模型权重不打包。\n').encode('utf8')
    secrets=[v.encode() for k,v in dotenv_values(ROOT/'.env').items() if v and (k.endswith('PASSWORD') or k.endswith('API_KEY') or k=='DB_URL' or k.endswith('_DB_URL'))]
    for name,content in contents.items():
        if any(secret in content for secret in secrets):raise ValueError('Configured credential found in attachment: '+name)
        if Path(name).name=='.env' or name.startswith(('.venv/','.git/','data/models/','models/','.runtime/')) or '..' in Path(name).parts:
            raise ValueError('Excluded/private path in attachment: '+name)
    missing=[];local_link_count=0
    for name in ('D2 原清单九项逐项验收与证据.html','eval/reports/d2-acceptance/unified-review.html'):
        parser=Links();parser.feed(contents[name].decode('utf8'))
        for target in parser.targets:
            if urlsplit(target).scheme or target.startswith('#'):continue
            resolved=(ROOT/Path(name).parent/unquote(target.split('#',1)[0])).resolve()
            relative=resolved.relative_to(ROOT).as_posix()
            local_link_count+=1
            if relative not in contents and not any(n.startswith(relative.rstrip('/')+'/') for n in contents):missing.append(relative)
    if missing:raise ValueError('Missing packaged evidence: '+','.join(missing))
    manifest={'created_at_utc':datetime.now(timezone.utc).isoformat(),'evidence_local_links_checked':local_link_count,'missing_links':missing,
              'configured_credential_matches':0,'file_count_excluding_this_manifest':len(contents),
              'files':[{'path':name,'size':len(content),'sha256':sha(content)} for name,content in sorted(contents.items())]}
    encoded=json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf8')
    (OUT/'bundle-file-manifest.json').write_bytes(encoded)
    contents['eval/reports/d2-acceptance/bundle-file-manifest.json']=encoded
    destination=destination.resolve();destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,content in sorted(contents.items()):archive.writestr(name,content)
    with zipfile.ZipFile(destination) as archive:
        corrupt=archive.testzip()
        if corrupt:raise ValueError('ZIP CRC failed: '+corrupt)
        for record in manifest['files']:
            if sha(archive.read(record['path']))!=record['sha256']:raise ValueError('ZIP file SHA mismatch')
    audit={'created_at_utc':datetime.now(timezone.utc).isoformat(),'zip':destination.name,'zip_sha256':sha(destination.read_bytes()),'bytes':destination.stat().st_size,
           'files':len(contents),'zip_crc':'PASS','all_attachment_sha256':'PASS','configured_credential_matches':0,'evidence_links':local_link_count,'missing_links':[],
           'excludes':['real .env and credentials','virtual environment','model weights','database volumes','Git metadata'],
           'note':'Package audit is stored outside the ZIP to avoid a self-referential ZIP hash; per-file manifest is inside the ZIP'}
    (OUT/'package-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(audit,ensure_ascii=False,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip',type=Path)
    args=parser.parse_args()
    generate()
    if args.zip:package(args.zip)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
