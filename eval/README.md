# A 的 D1 SQL 题库与评测

题库来自当前导入的 Chinook 真实数据库，30 道题覆盖计数、筛选、聚合、分组、Top-N、日期、LIKE、NULL 和无匹配。单题只访问一张业务表。21 道开发题和 9 道保留题的划分已经写入每条记录；同源问法使用相同 family_id 并保持同一划分。

## 先复核 gold

```powershell
.\.venv\Scripts\python.exe -m eval.build_gold
.\.venv\Scripts\python.exe scripts/review_gold.py
```

第一条只执行已写好的 30 条标准 SQL，用于建立标注，**不会调用模型，也不会运行保留题系统预测**。日期题使用实际导入的年份。第二条导出 `eval/datasets/review/gold_review.md` 和可在 Excel 查看的一份 UTF-8 CSV。默认全部状态为 `needs_human_review`，A 需要对照问题、SQL 和结果核对筛选、单位、日期边界、排序和并列处理。

确认部分题后，显式记录审核：

```powershell
.\.venv\Scripts\python.exe scripts/review_gold.py --accept sql-01,sql-02 --reviewer A
```

接受时保存内容哈希，修改问题、SQL、标准结果或划分会使旧接受记录失效。Codex 的生成和数据库可执行检查不能代替人工认可。

## 开发集评测

先启动 FastAPI 并在本地 `.env` 中配置可用的模型凭据，再运行：

```powershell
.\.venv\Scripts\python.exe -m eval.run_eval
```

默认仅调用 21 道开发题，接口为 `/api/chat`。未配置 key、人工审核未完成或 API 未就绪时，输出 `READINESS_ONLY` 报告，实际预测数为 0，**不填写 EX**。人工审核完成后，报告给出正确数/21、EX、真实失败分类与耗时。模型调用失败、超时、错误状态和不正确结果均计入分母。

如果 A 尚未完成逐题审核，确实需要先探索模型输出，可使用：

```powershell
.\.venv\Scripts\python.exe -m eval.run_eval --draft-gold
```

该模式只允许开发集，成绩名称为 `exploratory_ex`，报告明确注明草稿状态。不能将其当成已人工核验的正式基线。评测不会读取 gold SQL 作为模型提示，HTTP 请求只包含问题和来源范围。

## 结果比较口径

- 忽略列别名和列排列，但对所有行使用同一个列映射。
- 有序题逐行比较；无序题按多重集合比较，保留重复行。
- 空表、NULL、0、空字符串、布尔值分别处理。
- 数字使用 Decimal 比较；JSON 中的金额字符串仅在声明为数值的列转换。
- 仅 monetary_columns 标出的金额列按两位小数比较；时长、编号等不做金额舍入。
- 日期按 ISO 表达统一；Top-N 题已规定确定性的并列排序。

报告保存题库/导入 SQL 的 SHA256、Git commit、配置模型和响应模型、实际请求/响应、SQL、步骤、每题判断及分母。报告的 `responses.jsonl` 只在真的发起预测后产生。

## 保留集纪律

D1 禁止对 9 道保留题运行系统预测。到 D5 计划冻结后，需要干净的 Git 工作目录、指向当前 HEAD 的真实冻结 tag、人工已接受的 gold，以及显式参数：

```powershell
# 仅在后续正式冻结评测时执行，D1 不执行。
.\.venv\Scripts\python.exe -m eval.run_eval --split holdout --allow-holdout --frozen-tag d5-frozen
```

无法仅凭 `--split holdout` 或 `--draft-gold` 绕过保护。开发代码与业务目录不应读取 `eval/datasets`；gold 的读取仅发生在标注和评测工具中。
