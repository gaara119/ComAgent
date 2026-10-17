"""Stable identifiers for existing, user-approved Oct12 policy definitions.

IDs align with the supplied public material's policy_registry; the policy
meaning comes from notes/references/oct12/12号任务.md, never case gold.
"""
CUSTOMER_AMOUNT='oct12.customer.amount'
PERIOD_ALL_DATA='oct12.period.all_data'
POLICY_PATTERNS=[('账单国家统计（10月12日已确认默认口径）','oct12.region.invoice_billing'),
 ('客户所在地统计（10月12日已确认默认口径）','oct12.region.customer_residence'),
 ('热门曲目按购买数量统计','oct12.popular.quantity'),
 ('客户谁买得最多',CUSTOMER_AMOUNT),('客户“买得最多”的分子排名',CUSTOMER_AMOUNT),
 ('默认查询客户消费金额排名',CUSTOMER_AMOUNT),('未指定期间，按全部现有数据统计',PERIOD_ALL_DATA),
 ('销售额占比默认以同期全部发票金额','oct12.ratio.invoice_denominator'),
 ('未指定排名条数','plan.ranking.top_n_10')]

def default_policy_ids(analysis):
    return sorted({identity for text in analysis.default_assumptions
                   for pattern,identity in POLICY_PATTERNS if pattern in text})
