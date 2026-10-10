# D1 OHR 资料与溯源

`manifest.csv` 是系统运行时的文档允许清单，含 6 篇官方 OHR-Bench PDF，finance / law / textbook / manual / news / academic 各一篇。路径相对 `system`；`content_hash` 是原 PDF 的 SHA256。原 PDF 在 `data/docs/raw/`，大型原始文件与索引应忽略 Git，以固定 revision、下载脚本和清单复现。

原文件共 261 个物理页，原生文本抽取可用 255 页，6 个空白/图片页保持页码且不生成文本 chunk。未将官方 OCR ground truth 或 gold QA 加入运行时索引。

来源：官方 [OHR-Bench GitHub](https://github.com/opendatalab/OHR-Bench)、[Hugging Face 数据集](https://huggingface.co/datasets/opendatalab/OHR-Bench)。PDF 固定 HF revision `7f833e3eda9a571a9ea545a8f6d476fa1685033d`；QA 固定 GitHub revision `1f421eb428f9f5b8ac0bc8064d6ad1f13fab7af7`。每个文件的 ZIP entry、CRC32、SHA256、原下载 URL 保存在 `source_manifest.json`。

HF 数据集卡标注 CC-BY-4.0；上游 GitHub 的 PDF 版权说明另外注明数据集用于研究、非商业，并保留原文档权利。这里按研究比赛用途使用，不把原 PDF 的所有内容声明为团队原创或无限制授权。

新电脑从项目根目录执行：

```powershell
.\.venv\Scripts\python.exe scripts/prepare_rag_data.py --selected-d1
.\.venv\Scripts\python.exe -m eval.rag_build_gold
```

下载脚本通过 ZIP 中央目录和严格校验的 HTTP Range 定向提取六个文件，仅需约 14.1 MB 网络传输，无需下载 1.52 GB 全包。若已有文件 SHA256 一致，则跳过重新下载。脚本不执行从网上下载的代码。

第二条命令仅生成资料清单、gold 及审核表，不调用模型。它会机器核对每条官方 QA 的原 evidence_source=text、原始 page index，并将原 PDF 对应连续文字作为引用。物理页以 1 起；官方 evidence_page_no 为 0 起，因此转换为 `index + 1`。若重建前已有人工接受且内容哈希一致，保留该接受记录；若内容变化，则重新等待人工审核。

本项目 title 是便于显示的资料标签，不声称官方 ZIP 提供独立书目信息；MacBook/新闻资料为存档版本，回答应根据所选文件，不视为当前设备或当前行业情况。

题库与运行时隔离：`eval/datasets/rag_ohr.jsonl` 只供评测/审核读取，RAG 运行仅加载 `manifest.csv`、原 PDF 生成的 chunks 及索引。
