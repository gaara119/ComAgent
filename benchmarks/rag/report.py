"""Transparent aggregates, paired transitions and small dependency-free SVG plots."""
from collections import Counter, defaultdict
import csv
from html import escape
import json
from pathlib import Path
from statistics import mean

from benchmarks.rag.metrics import percentiles


def aggregate(rows):
    groups = defaultdict(list)
    for row in rows: groups[row['strategy']].append(row)
    result = {}
    for strategy, values in groups.items():
        eligible = [r for r in values if r['answerable'] and not r.get('retrieval',{}).get('diagnostic_fixed_evidence')]
        generated = [r for r in values if 'generation' in r]
        def answerable_condition(r):
            return r['answerable'] if r.get('evidence_condition_answerable') is None else r['evidence_condition_answerable']
        unknown = [r for r in generated if not answerable_condition(r)]
        answerable = [r for r in generated if answerable_condition(r)]
        usage = [r['generation']['usage'] for r in generated]
        complete = all(u.get('usage_complete',False) for u in usage)
        result[strategy] = {
            'logical_questions':len(values),'unique_questions':len({r['id'] for r in values}),
            'answerable_metric_denominator':len(eligible),'failures':sum(bool(r['error']) for r in values),
            **{key: mean(r.get('retrieval',{}).get(key,0) or 0 for r in eligible) if eligible else None
               for key in ['hit@5','recall@5','mrr@5','ndcg@5','precision@5','evidence_coverage@5']},
            'end_to_end_ms':percentiles([r['latency_ms'] for r in values]),
            'retrieval_ms':percentiles([r['retrieval_trace']['retrieval_timing_ms']['total'] for r in values
                                      if 'retrieval_timing_ms' in r.get('retrieval_trace',{})]),
            'generation_ms':percentiles([r['generation']['latency_ms'] for r in generated]),
            'physical_calls':sum(u.get('physical_calls',0) for u in usage),
            'input_tokens':sum(u.get('input_tokens',0) or 0 for u in usage) if complete else None,
            'output_tokens':sum(u.get('output_tokens',0) or 0 for u in usage) if complete else None,
            'cache_hit_input_tokens':sum(u.get('cache_hit_input_tokens',0) or 0 for u in usage) if all(u.get('cache_usage_complete',False) for u in usage) else None,
            'cache_miss_input_tokens':sum(u.get('cache_miss_input_tokens',0) or 0 for u in usage) if all(u.get('cache_usage_complete',False) for u in usage) else None,
            'missing_usage_attempts':sum(u.get('missing_usage_attempts',0) for u in usage),
            'usage_complete':complete,'money_usd':None,'money_status':'not_verified; no price assumed',
            'unanswerable_refusal_recall':sum(r['generation']['status']=='EMPTY_RESULT' for r in unknown)/len(unknown) if unknown else None,
            'answerable_false_refusal_rate':sum(r['generation']['status']=='EMPTY_RESULT' for r in answerable)/len(answerable) if answerable else None,
            'semantic_answer_correctness':None,'semantic_faithfulness':None,'semantic_citation_support':None,
            'semantic_reviewed_count':0,'error_categories':dict(Counter(x for r in values for x in r['error_categories']))}
    return result


def paired(rows, baseline='bm25'):
    groups = defaultdict(dict)
    for row in rows:
        key=(row['id'],row['repeat'])
        if key in groups[row['strategy']]: raise ValueError('Duplicate question/repeat key')
        groups[row['strategy']][key]=row
    if baseline not in groups: return {}
    result={}
    for strategy, candidates in groups.items():
        if strategy==baseline: continue
        if candidates.keys()!=groups[baseline].keys(): raise ValueError('Unpaired strategy cases')
        transitions=Counter(); deltas=[]
        for key,row in candidates.items():
            before=groups[baseline][key]
            for field in ('question','retrieval_question','allowed_doc_ids','answerable'):
                if before.get(field)!=row.get(field):raise ValueError('Changed paired question/scope: '+row['id'])
            if row.get('retrieval',{}).get('diagnostic_fixed_evidence') or before.get('retrieval',{}).get('diagnostic_fixed_evidence'):
                continue
            if not row['answerable']:continue
            a=before.get('retrieval',{}).get('recall@5',0)==1 and not before['error']
            b=row.get('retrieval',{}).get('recall@5',0)==1 and not row['error']
            transitions[('pass' if a else 'fail')+'_to_'+('pass' if b else 'fail')]+=1
            deltas.append((row.get('retrieval',{}).get('recall@5',0) or 0)-(before.get('retrieval',{}).get('recall@5',0) or 0))
        result[strategy]={'baseline':baseline,'criterion':'all required source evidence at top5; not answer correctness',
            'pairs':len(deltas),'recall_at_5_delta':mean(deltas) if deltas else None,
            **{key:transitions[key] for key in ['fail_to_pass','pass_to_fail','pass_to_pass','fail_to_fail']}}
    return result


def bars(path,title,entries,unit=''):
    entries=list(entries)
    height=95+38*max(len(entries),1)
    largest=max([abs(v) for _,v in entries]+[1e-9])
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="850" height="{height}" viewBox="0 0 850 {height}">',
           '<rect width="100%" height="100%" fill="#fff"/>',
           f'<text x="24" y="32" font-family="sans-serif" font-size="19" fill="#24204d">{escape(title)}</text>']
    for i,(name,value) in enumerate(entries):
        y=58+i*38
        width=450*abs(value)/largest
        parts.extend([f'<text x="24" y="{y+19}" font-family="sans-serif" font-size="13">{escape(name)}</text>',
                      f'<rect x="240" y="{y}" width="{width:.2f}" height="25" rx="4" fill="#8060bb"/>',
                      f'<text x="{245+width:.2f}" y="{y+18}" font-family="sans-serif" font-size="12">{value:.3f}{escape(unit)}</text>'])
    parts.append('</svg>');path.write_text('\n'.join(parts),encoding='utf-8')


def write_report(directory,rows,manifest):
    directory=Path(directory)
    summary={'groups':aggregate(rows),'paired':paired(rows),'interpretation':'source-labelled mechanical retrieval diagnostics; semantic scores unverified'}
    (directory/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    fields=['id','strategy','repeat','category','answerable','hit@5','recall@5','mrr@5','ndcg@5','latency_ms','error_categories','prediction_sha256']
    with (directory/'results.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for r in rows:
            writer.writerow({**{k:r.get(k) for k in fields},**{k:r.get('retrieval',{}).get(k) for k in ['hit@5','recall@5','mrr@5','ndcg@5']},
                             'error_categories':';'.join(r['error_categories'])})
    reviews=[{'id':r['id'],'strategy':r['strategy'],'repeat':r['repeat'],'prediction_sha256':r['prediction_sha256'],
              'reviewer_kind':None,'reviewer':None,'answer_correctness':None,'faithfulness':None,
              'citation_support':None,'fact_completeness':None,'notes':'','review_status':'pending_human_review'}
             for r in rows if 'generation' in r]
    (directory/'review-template.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2),encoding='utf-8')
    failures=[r for r in rows if r['error_categories']]
    (directory/'failure-cases.json').write_text(json.dumps(failures[:10],ensure_ascii=False,indent=2),encoding='utf-8')
    bars(directory/'quality.svg','Required source evidence Recall@5 (not answer accuracy)',[(s,v['recall@5'] or 0) for s,v in summary['groups'].items()])
    counts=Counter(x for r in rows for x in r['error_categories'])
    bars(directory/'errors.svg','Diagnostic error categories (may overlap)',counts.items())
    bars(directory/'transitions.svg','Paired retrieval transitions; all evidence at top5',
         [(s+' '+k,v[k]) for s,v in summary['paired'].items() for k in ['fail_to_pass','pass_to_fail']])
    def pct(v):return 'not_verified' if v is None else f'{v*100:.2f}%'
    lines=['# RAG评测与优化报告','',
        '## 1. 结论边界','',
        '本报告由真实工具调用记录生成。使用原创合成开发语料验证评测链路；标签仍待人工审核。它不是公开基准成绩，也不能证明真实用户场景泛化能力。',
        '检索使用原文位置与规范化文本证据标签；关键词/数字/引用ID检查属于机械诊断。答案正确性、忠实性和引用语义支持分别保留为 not_verified。',
        f"本次模式：`{manifest['mode']}`；生成方式：`{manifest['answer_mode']}`；缓存：`{manifest['cache_protocol']}`。",
        '','## 2. 数据与隔离','',
        f"数据集版本 `{manifest['dataset_version']}`，SHA256 `{manifest['dataset_sha256']}`。只运行 dev，未读取或预测旧保留集。原200题继续属于Agent综合评测。",
        '来源标签固定到文档哈希、页码/章节和原文引句，不绑定某次切片的chunk_id。同家族、同会话不得跨开发/测试集泄漏。当前未建立独立最终测试集。',
        '多轮题提供显式有效检索问题；这里只测试有效问题下的检索，不把它当成多轮重写成功率。',
        '','## 3. 实验控制','',
        f"共用 {manifest['index']['chunk_count']} 个片段、同一来源哈希、相同切片、Top-{manifest['top_k']} 和每通道候选预算 {manifest['candidate_k_per_channel']}。",
        '混合检索可以融合两路候选，因此总候选量不一定与单通道相同；这里控制每通道预算，不宣称相同总计算量。当前重排为词项/短语覆盖率与RRF分数的轻量重排，不是Cross-Encoder。',
        'cold逐请求清空应用检索缓存；warm先执行同一查询预热再计时。操作系统页缓存和ONNX会话不清空，故不是机器冷启动。索引构建耗时单独记录。',
        '','## 4. 检索指标与真实结果','',
        'Recall@5：前5片段覆盖的唯一必要原文证据比例。MRR@5：第一条命中证据的倒数排名。nDCG@5：在允许范围的完整冻结语料上建立chunk-ID二元相关性标签，依据全体相关片段计算理想DCG；命中任一正确来源引句则相关。',
        '一块覆盖多个证据时Recall可同时计入，标准nDCG按该块的binary qrel计分。不同重叠片段是不同qrel，同一chunkID重复不加分；额外novelty_ndcg只作去重新证据诊断，不与标准nDCG混用。无答案题不进入正证据Recall分母；执行失败在可回答题分母中计0。',
        '', '|策略|可回答题次|Hit@5|Recall@5|MRR@5|nDCG@5|失败|','|---|---:|---:|---:|---:|---:|---:|']
    for s,v in summary['groups'].items():
        lines.append(f"|{s}|{v['answerable_metric_denominator']}|{pct(v['hit@5'])}|{pct(v['recall@5'])}|{v['mrr@5'] or 0:.4f}|{v['ndcg@5'] or 0:.4f}|{v['failures']}|")
    lines.extend(['','![检索覆盖](quality.svg)','','## 5. 质量与时延','',
        '|策略|检索P50/P90(ms)|端到端P50/P90(ms)|物理调用|输入/输出token|', '|---|---:|---:|---:|---:|'])
    for s,v in summary['groups'].items():
        t=v['retrieval_ms'];e=v['end_to_end_ms']
        lines.append(f"|{s}|{t.get('p50')} / {t.get('p90')}|{e.get('p50')} / {e.get('p90')}|{v['physical_calls']}|{v['input_tokens']} / {v['output_tokens']}|")
    lines.extend(['','每次真实请求和重试都保留。缺失usage不按零token处理。未提供可靠单价，金额保持未核验。检索-only和extractive运行没有付费模型调用，不能据此报告DeepSeek生成质量。',
        '','## 6. 配对增减','',json.dumps(summary['paired'],ensure_ascii=False,indent=2),
        '','![配对迁移](transitions.svg)','','按相同题ID和重复编号配对；正、负和零收益全部保留。重复测量用于时延，不增加独立样本数，不作统计显著性宣称。',
        '','## 7. 错误定位','', '![错误分类](errors.svg)',
        '错误类别可以重叠；这里只标记执行失败、证据缺失、排序靠后、拒答状态和引用结构问题。生成失真、引用语义不支持需单独审核，不从字符串猜测。',
        '最多10个代表记录见 failure-cases.json，所有失败仍完整保存在 predictions.jsonl。',
        '','## 8. 固定证据诊断','',
        'generation入口支持reference、reference_noise、missing_key。reference提供标签中的充分证据，reference_noise增加允许范围内的干扰片段，missing_key移除最后一项必要证据。标签未经人工确认时仍按“参考证据”称呼。',
        '固定证据使用标签，只属于诊断条件，不计入正常检索或端到端成绩。extractive只复述输入，不能用来证明模型抗噪声或拒绝幻觉能力。',
        '','## 9. 答案、忠实性和引用','',
        '逐题结果保留实际生成输入、回答、引用、验证警告和trace。review-template.json用于逐项语义审核。compare/review工具校验prediction_sha256，防止把旧回答的审核应用到新回答。',
        '默认三个语义指标均为空，AI审核与人工审核单独统计；不填写人工签名，不自动批准标签。拒答指标依据真实EMPTY_RESULT状态，独立于答案正确性。',
        '','## 10. 可复现证据','',
        '- manifest.json：命令、源码文件哈希、Git版本、环境、语料与切片、模型身份、缓存和预算。',
        '- predictions.jsonl：所有题次的检索排名、证据、实际回答与错误。results.csv为扁平摘要。',
        '- summary.json：分母、分组均值、调用/token、错误分类和配对增减。',
        '- 索引保存在独立工作目录，不替换用户知识库。输出目录已存在时拒绝覆盖。',
        '','## 11. 限制与后续','',
        '当前只提供合成开发集，不冒充200道独立RAG题、人工已审标签或最终测试成绩。未运行的神经重排、LLM语义裁判、真实生成式抗噪声和公网并发均保持未验证。',
        '下一步应人工审核证据与答案要点，按来源/家族划分独立测试集，再在明确预算下运行生成式评测。不要根据本开发集反复选择最好的一次结果。',
        '','## 12. 方法参考','',
        '- [BEIR官方评测实现](https://github.com/beir-cellar/beir/blob/main/beir/retrieval/evaluation.py)：排序指标和分母设计。',
        '- [RAGChecker官方实现](https://github.com/amazon-science/RAGChecker)：检索与生成拆解、细粒度错误诊断。',
        '- [Ragas官方指标](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)：正确性、忠实性、相关性分开评价。',
        '这里只借鉴评测原则，未声称已完整接入这些框架或复现其论文结果。'])
    (directory/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
