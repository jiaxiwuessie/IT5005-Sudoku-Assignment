# IT5005 Sudoku Assignment

用命题逻辑表示数独规则，再通过前向／后向推理求解和解释。A/B/C 的共享求解器与 Q1–Q5 已整合；D 提供英文 Streamlit 界面、单格查询、可读证明和部署配置。

**已部署并通过线上功能验收：[Sudoku Logic Lab](https://it5005-sudoku-logic-lab.streamlit.app/)。** 小组名：`IT5005_Sudoku`；真实网址已写入 Notebook。

## 项目做了什么

1. 从 `puzzles.json` 读取 5 道 9×9 数独，已知数字分别为 30、33、36、39、42 个。
2. A 将规则编码成一般命题知识库和确定子句知识库。
3. C 在一般知识库上尝试归结、真值表检查，并在 Horn 知识库上完成共享闭包前向求解。
4. B 用结论索引、递归证明、循环检测和缓存实现后向推理及全盘求解。
5. Notebook 对完整棋盘、正确／错误候选、真实证明和两种算法的耗时进行验证，再回答 Q1–Q5。
6. D 将同一份核心代码接入 Streamlit：选择题目、选择算法、显示棋盘与时间、查询单格，以及阅读真实推理过程。

本项目是符号人工智能，没有训练模型。求解只使用 `givens`；题库中的 `solution` 仅用于离线核对结果。Horn 编码采用消元和最后候选规则，能完成所给题目，但并不保证解决所有可能的数独。

## 文件与分工

| 成员 | 编程任务 | 理论题 |
| --- | --- | --- |
| A | `build_general_kb`、`build_definite_kb` | Q1、Q4 |
| B | `pl_bc_entails`、`solve_full_grid_bc` | Q3 |
| C | `solve_full_grid_fc`、归结／模型检查实验、FC/BC 计时、Notebook 整合 | Q2、Q5 |
| D | Streamlit 界面、查询、可读证明、部署与交付 | 应用说明和部署网址 |

| 文件 | 用途 |
| --- | --- |
| `sudoku_solver.py` | 核心函数的唯一实现位置，并提供真实证明记录 |
| `Sudoku_Assignment.ipynb` | 实验、验证、Q1–Q5、应用说明和部署网址 |
| `sudoku_app.py` | 调用共享核心的英文交互应用 |
| `logic_.py`、`utils.py` | 老师提供的支持库，保持不变 |
| `puzzles.json` | 题目与仅供验证的参考解 |
| `requirements.txt` | 应用运行依赖 |
| `requirements-dev.txt` | 在运行依赖之外增加 Notebook 开发环境 |
| `tests/` | 开发验证，不放进三文件作业提交包 |
| 两份 PDF | 原始作业说明和部署指南 |

## 本地安装与运行

在项目根目录创建 Python 3.11 虚拟环境。macOS/Linux：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m streamlit run sudoku_app.py
```

仅运行应用时可以安装 `requirements.txt`。Windows 可用 `py -3.11 -m venv .venv`，PowerShell 激活命令为 `.venv\Scripts\Activate.ps1`。启动后，在浏览器打开终端显示的本地地址。

Notebook 可以在 VS Code（Python 和 Jupyter 扩展）中打开，选择该虚拟环境作为 Kernel；也可在项目目录执行 `python -m notebook`。核心函数修改后，应从顶部导入单元开始重新运行 Notebook。Notebook 中的归结和真值表实验各有 30 秒推理预算，整个 Run All 因此需要至少约一分钟。

## 应用怎么演示

1. 选择 30 个 givens 的题目，观察初始棋盘。
2. 选择 FC，求解并查看完整棋盘和实测时间。
3. 对同一题选择 BC，再次求解并比较实测时间。每次整盘求解包含新建 KB、索引、推理和棋盘重建，不包含界面绘制。
4. 输入行 1、列 1、候选 1，运行单格查询；此题结果应为 `True`。
5. 打开推理解释，阅读已知事实、行／列／宫排除和最后候选规则如何支持该结论。
6. 将同一格的候选改为 2，查询应为 `False`；然后切换题目，确认旧棋盘与查询结果已清除。

单格布尔结果来自 B 的 `pl_bc_entails`。Tutor mode 通过 C 的 `trace_fc_query` 提供**真实的 FC 支持证明**，不是 BC 递归搜索日志。证明包含实际前提、结论及所使用规则；界面将这些内容翻译成英文。`False` 表示当前 KB 未证明该查询，不能仅凭这个返回值声称已经证明否定；如展示 `Not` 的证明，需要单独推导并明确标注。

## 实验与验证

在项目根目录执行：

```bash
python -m unittest discover -s tests -v
```

Notebook 为每道题检查全部 729 个 BC 候选查询，共 3,645 个；比较两种全盘结果与参考解，并分别执行三次全新 FC/BC 求解，交替先后顺序，记录原始时间、中位数、范围和比值。Q2/Q5 引用 Notebook 本次实际输出，不能预设某种算法永远更快。

归结与模型检查在独立进程中运行，超时仅表示未在预算内完成，不能当作 `False`。真实证明会检查所有前提在结论前已经成立。开发测试另覆盖支持库 FC 对照、矩形宫格、推导停滞、矛盾 givens 等边界情况。

## 部署

按 `StreamlitDeploymentGuide.pdf` 使用 Streamlit Community Cloud：连接本 GitHub 仓库，选择包含完成代码的分支，入口文件设为 `sudoku_app.py`，使用与本地一致的 Python 3.11 环境。应用运行不需要 API key。

部署仓库必须保留 `sudoku_app.py`、`sudoku_solver.py`、`puzzles.json`、`logic_.py`、`utils.py`、`requirements.txt` 以及应用配置。上线后在公网网址重做题目选择、两种算法求解、True/False 查询及证明展示验收；确认成功后把真实地址填到 Notebook 的 **Deployed Streamlit app URL** 一节。

本次部署使用个人 Fork `jiaxiwuessie/IT5005-Sudoku-Assignment` 的 `member-d-app-delivery` 分支、Python 3.11。原仓库账号具有写入权限但缺少 Streamlit 要求的管理员权限，因此使用同源 Fork 托管。原仓库 D 改动见 [PR #5](https://github.com/Uncle416/IT5005-Sudoku-Assignment/pull/5)。

## 最终提交与呈现形式

创建名为 **IT5005_Sudoku** 的文件夹，只放入以下三个文件，然后压缩提交：

- `Sudoku_Assignment.ipynb`：必需单元已运行、输出可见、Q1–Q5 完整、含已验证的公开部署网址。
- `sudoku_solver.py`：共享核心实现。
- `sudoku_app.py`：Streamlit 应用。

最终有三种主要呈现形式：**Notebook 展示理论与实验；在线 Streamlit 应用展示交互与推理；三文件 ZIP 用于提交。** 完整 GitHub 仓库用于运行和部署，解释报告与截图用于阅读和交接；它们不额外放进老师要求的三文件 ZIP。

不要提交虚拟环境、缓存、密码或 token。修改 Notebook 后保留真实输出，避免用旧版本文件覆盖组员已合并的内容。

## D 交付记录

应用用法、12 项测试覆盖、计时口径、部署参数及最终三文件清单见 [D_HANDOFF.md](D_HANDOFF.md)。中文项目说明报告另作学习和演示材料。
