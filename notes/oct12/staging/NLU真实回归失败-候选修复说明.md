本目录只保存候选补丁和隔离测试。**生产 `qa_agent/nlu/linker.py` 尚未修改**，当前正在运行的旧版本回归继续保持原版本。已有真实失败记录不覆盖，也没有将候选模块通过写成真实 API 修复成功。

| 真实问题 | 证据与原因 | 候选修复 |
| --- | --- | --- |
| `sp01-22`：Gudian 这个流派的曲目有多少首 | 原始回答 `nlu.mentions=[]`，SQL 查询 `genre.name='Gudian'` 得 0；只读参考 SQL 得 Classical 74。新别名表的“古典→Classical”已经 approved，来源关系无需新增。现实体提取正则只允许“的”连接，不接受“这个/这种”，所以拼音阶段根本未启动。 | 实体与流派/乐队/媒体格式之间允许“这个、这种、这一种、该、的”。提取到原文 Gudian 后，使用既有已批准古典别名的拼音索引得到 Classical。 |
| `oct12-join-13`：名字叫Jane、姓氏为Peacock的员工负责几位客户 | 原始回答把 Peacock 改写为 Leacock，并绑定 `customer.last_name`；SQL 仍按员工姓名查询，被来源守卫正确拒绝。`field_scope` 同时出现员工与客户时固定客户优先，把被计数客户误当姓名所有者。实际值索引已经包含 `employee.first_name`、`employee.last_name`。 | 对明确“名字/姓氏……的员工”或“员工的名字/姓氏”优先限制既有 employee 字段。如果该索引没有员工姓名列，返回空范围、保留原词，让 SQL 根据真实目录查询；不回退到相似客户姓名，不新建员工值或别名。 |

隔离候选测试 **9 通过、0 失败，1.10 秒**，覆盖两条真实完整题面、已有索引、缺员工姓名列时跳过，以及姓名属于客户的反例。此结果是模块隔离核验，尚无修改后 API 实测成绩。

候选源代码为 [linker_candidate.py](linker_candidate.py)，差异为 [nlu-candidate.patch](nlu-candidate.patch)，测试为 [test_staged_linker.py](test_staged_linker.py)，实际测试输出为 [test-staged-linker-results.txt](test-staged-linker-results.txt)。[staging-preflight.json](staging-preflight.json)记录了生产源码摘要未变化，以及既有批准别名、既有字段来源。

等主任务确认旧版回归结束后，才能应用这个候选补丁，接入正式测试目录并运行模块回归，再重启服务进行下一版本的真实目标题重测。当前不修改业务源码、实际别名、索引或人工记录。
