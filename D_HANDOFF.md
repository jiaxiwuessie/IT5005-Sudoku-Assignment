# D 部分交付与验收

## 已完成

- `sudoku_app.py` 为英文应用 Sudoku Logic Lab，统一调用已有求解器，未改 A/B/C 核心和老师支持库。
- 五题选择、带行列编号与宫格边界的棋盘、FC/BC 整盘求解、真实单次计时。
- 每次整盘运行重新建库；计时包括建库、索引、推理和重建，不包括验证和界面渲染。
- BC 单格查询；用 `trace_fc_query` 独立核对 verdict 并展示 FC 支持证明，不声称展示 BC 搜索轨迹。
- 证明步骤滑块、当前结论/前提位置高亮、自然语言规则与前提、完整证明及文本下载。
- `False` 明确表示未推出，不当作已经证明否定；已知事实查询支持一步证明。
- 切换题目/重置清除旧结果；失败清除旧成功；算法不一致时不展示错误证明。
- 数据文件以应用文件位置定位，支持从其他工作目录启动。应用只保留 givens；参考答案仅用于离线测试。
- 整盘结果另按行、列、宫、givens 做结构校验。

## 验证证据

环境：Python 3.11.8 / macOS arm64；运行依赖固定在 requirements.txt。

```bash
python -m unittest discover -s tests -v
```

7 项求解器测试通过（原 C 的 4 项 + D 的 3 项）：五题双算法、3,645 个候选、5 题真实证明链、60 个随机 Horn 图共 960 查询与独立闭包一致，并覆盖矩形宫格、停滞、矛盾输入等。

5 项应用测试通过（`test_member_d_app.py`）：五题 FC/BC 界面流程；True/False/已知事实；滑块和清除状态；异常与推理不一致；结果合法性；实际证明文案和可访问棋盘结构。应用测试不需要运行 Web 服务器。

Notebook 的 7 个普通 Python 单元在同一虚拟环境和共享命名空间顺序实际执行，输出已保存。没有 IPython magic。此次采用普通 Python runner，未声称使用原生 Jupyter 内核运行。

| 界面题号 | givens | FC 中位秒 | BC 中位秒 | BC/FC |
| --- | --- | --- | --- | --- |
| 1 | 30 | 0.4889 | 2.1940 | 4.49 |
| 2 | 33 | 0.5027 | 2.2220 | 4.42 |
| 3 | 36 | 0.4880 | 2.1384 | 4.38 |
| 4 | 39 | 0.4791 | 2.1740 | 4.54 |
| 5 | 42 | 0.4895 | 2.1904 | 4.47 |

每种算法每题三次、交替顺序、全新知识库；归结和真值表分别约 30.14/30.01 秒预算超时，不等于 False。C_HANDOFF.md 保留先前环境的历史数据；本表和 Notebook 为此次结果。

## 本地运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m streamlit run sudoku_app.py
```

Windows PowerShell 激活：`.venv\Scripts\Activate.ps1`。

## 云端部署

已部署并进行浏览器功能验收：[Sudoku Logic Lab](https://it5005-sudoku-logic-lab.streamlit.app/)。

- Repository: `jiaxiwuessie/IT5005-Sudoku-Assignment`（同源 Fork；具有所需管理员权限）
- Branch: `member-d-app-delivery`（合并后可以改为 `main`）
- Main file: `sudoku_app.py`
- Python: `3.11`
- Secrets: 不需要。

线上验收：选任意题、分别运行 FC/BC、首题查 R1C1=1 得 True 并回放证明、查 R1C1=2 得 False、切换题目旧结果清空。构建成功和网址打开均不能代替这些功能验证。

公网检查通过 FC、BC、True/False 单格查询、299 步证明回放和切换题目。线上首题单次计时 FC 0.801 秒、BC 3.264 秒，仅作为部署验收记录；Notebook 的三次重复中位数仍使用其本地实验数据。真实 URL 已写入 Notebook。原仓库 PR #5 提供完整 D 改动，部署 Fork 保留相同运行源码。

## 最终交什么

课程正式提交只包含：

1. `Sudoku_Assignment.ipynb`
2. `sudoku_solver.py`
3. `sudoku_app.py`

放入名为 `IT5005_Sudoku` 的文件夹，再压缩上传课程系统。完整运行仓库另外保留支持库、JSON、requirements、配置和测试。中文说明报告和截图是组内学习/演示辅助材料，不加入只含三文件的课程压缩包。

## 能力边界

仅消元与最后候选；Q4 Naked Pairs 为理论编码，没有在求解器启用。不能保证任意数独可解。BC 的缓存要求 KB 在查询之间不做等量原地替换。应用只开放已验证题库，并对每次单格查询新建 KB。数学上的有限终止不消除 Python 递归深度对更大输入的限制。
