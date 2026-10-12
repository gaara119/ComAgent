"""Refresh only the current README summary from completed acceptance evidence."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    report=json.loads((ROOT/'eval/reports/oct12/acceptance/10月12日任务逐项验收与证据.json').read_text(encoding='utf-8'))
    path=ROOT/'README.md'
    old=path.read_text(encoding='utf-8')
    marker='<!-- oct12-current-end -->'
    if marker in old:
        old=old.split(marker,1)[1].lstrip('\n')
    text=f'''## 10月12日当前交付

12号任务的五项已授权口径、JOIN及修复筛选保护、候选阈值与日期解析、同比澄清、RAG未核实降级、页面与方案EX均已接入原系统。沿用Python3.12和已验证模型，没有重建数据库或追改历史成绩。

本轮新增JOIN真实第二轮15/15；17项定向第二轮14/17，两个网络失败独立补测2/2后，按各题最新记录为16/17，属于跨运行摘要。最后的SQL整轮35题为34/35；发现sql-22日期“之前”被误成单月后窄修复，单题真实补测1/1且程序开放上界正确，不能称为新的整轮35/35。最终模块实际{report['module_passed']}通过。页面5个真实场景、33项检查及截图视觉检查通过，具体源码阶段和证据见报告。

- [10月12日任务逐项验收与证据](eval/reports/oct12/acceptance/10月12日任务逐项验收与证据.html)。
- [全部待人工审核统一入口](eval/reports/oct12/manual-review/全部待人工审核统一入口.html)：去重、题面清洗、标签和每次实际回答分别审核；保存及导出只生成草稿，不自动应用。
- [sql-38、robust-23定稿提案](notes/oct12/gold-38-23-proposal.md)及[参考答案与计分争议](notes/oct12/参考答案与计分争议提案.md)。
- [ZIP使用及增量源码说明](README-10月12日交付说明.md)。

老美两条关系依用户明确授权改为直接使用；当前值索引为data/indexes/values-oct12-approved。剩余两条别名、两gold、新JOIN标签、AW目录和实际回答语义仍等待人工确认。保留集预测0；本开发会话未开展保留题内容审核，隔离边界及早期检索事件如实留档。以下均为此前阶段历史记录。

{marker}

'''
    path.write_text(text+old,encoding='utf-8')
    print('Updated README current summary; historical body preserved.')

if __name__=='__main__':
    main()
