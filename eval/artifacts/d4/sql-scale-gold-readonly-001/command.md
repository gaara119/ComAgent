本次实际从 system 目录运行，将本目录 command.py 中相同的 Python 内容作为标准输入传给：

```powershell
@'
# command.py 中保存的完整内容
'@ | .\.venv\Scripts\python.exe -B -
```

实际 stdout 为 report.json 中的同一 JSON：60 条参考查询执行、0 模型调用、0 系统预测、0 保留题。
这是随后保存的标准输入源码及命令说明，不声称当时运行了尚不存在的 command.py 文件。
证据目录已有内容，复现时需将源码的 out 换为新的目录，禁止覆盖本次结果。
