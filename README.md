# IT5005 Sudoku Assignment

数独知识表示与命题逻辑推理小组作业。A/B/C 的核心求解函数及 Q1–Q5 已整合；Notebook 包含真实运行输出。D 的 Streamlit 界面、推理展示与部署已完成，网址已填入 Notebook。

## 文件与分工

| 成员 | 编程任务 | 理论题 |
| --- | --- | --- |
| A | `build_general_kb`、`build_definite_kb` | Q1、Q4 |
| B | `pl_bc_entails`、`solve_full_grid_bc` | Q3 |
| C | `solve_full_grid_fc`、归结/模型检查实验、FC/BC 计时、Notebook 整合 | Q2、Q5 |
| D | Streamlit 界面、推理展示、部署 | 应用验收与部署网址 |

- `sudoku_solver.py`：核心函数的唯一实现位置。
- `Sudoku_Assignment.ipynb`：导入、实验、理论题和最终输出。
- `sudoku_app.py`：调用核心函数的应用。
- `logic_.py`、`utils.py`：老师提供的支持库，不修改。
- `puzzles.json`：输入数据；`solution` 仅用于验证，不用于求解。
- 两份 PDF：作业要求和部署说明。

D 的推理记录由 A 提供规则说明、B/C 协助记录实际推理步骤。Notebook 的各题由负责人撰写，C 负责最终整合。

## C 部分：实现、实验与交接

- `solve_full_grid_fc` 建立一次 Horn KB，调用老师的 `pl_fc_entails` 完成一次共享推导，再还原全盘；不会读取 `solution`。无法推出唯一值时抛出 `ValueError`，不猜测答案。
- `_ObservedFCKB` 为规则前提建立索引并观察已处理事实，支持库及 A/B 的函数保持原样。标记查询 `FCClosureComplete` 不在 Sudoku KB 中，因此库函数会耗尽议程。
- Notebook 对归结与真值表检查分别设置 30 秒推理预算；超时不是逻辑上的 `False`。实验使用独立子进程，不需要手动中断内核。
- 对五个题目分别运行三次 FC/BC，交替执行顺序，每次重新建库，输出原始时间、中位数、范围及比值；验证覆盖五个全盘解和 3,645 个 BC 候选查询。Q2/Q5 与这些输出对应。
- 测试命令：`python -m unittest discover -s tests -v`。额外覆盖原库 FC 对照、矩形宫格、推导停滞、矛盾 givens 和实际证明记录。

D 可额外导入 `trace_fc_query(kb, query)`，获得 `(entailed, steps)`。每条记录有 `premises`、`conclusion`、`rule`；均为逻辑表达式，给定事实的 `rule` 为 `None`。成功时只返回目标证明所需步骤，按推导顺序排列。失败返回 `(False, [])`，表示未证明，不表示证明了否定。界面应按 A 提供的规则含义将记录转成自然语言；单格查询的要求仍是调用 `pl_bc_entails`，可以用 FC 证明辅助展示并核对两者结果。

B 请核对 Q5 对现有 BC 索引、缓存和循环处理的描述及性能解释。D 完成后，将真实部署网址填入 Notebook 最后一节，并进行最终应用验收。开发用测试和支持文件保留在仓库，最终交作业仍只打包要求的三个文件。

## 安装本地环境

先安装 Python 3，在项目目录创建虚拟环境。macOS/Linux 示例：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Windows 可用 `py -m venv .venv`，PowerShell 激活命令为 `.venv\Scripts\Activate.ps1`。
依赖文件根据 starter 的导入整理，尚未固定版本或进行跨平台环境验证。

## 使用 VS Code

1. 使用 Open Folder 打开整个项目文件夹。
2. 安装 Microsoft 的 Python 和 Jupyter 扩展。
3. 编辑 `sudoku_solver.py` 中分配给自己的函数。
4. 打开 `Sudoku_Assignment.ipynb`，在右上角 Select Kernel 选择 `.venv` 对应的 Python。
5. 先运行顶部导入单元，再运行加载题目的单元。修改并保存求解器后，重新运行含 `importlib.reload(sudoku_solver)` 的导入单元。
6. 在 Part B 的对应 `Your answer:` Markdown 单元填写理论题。

## 使用浏览器版 Jupyter Notebook

激活同一个项目环境后，在项目根目录运行：

```bash
jupyter notebook
```

在浏览器文件列表中打开 `Sudoku_Assignment.ipynb`。使用 Jupyter 的文本编辑器或其他编辑器修改 `.py` 文件，保存后重新运行 Notebook 的导入单元。

VS Code 和 Jupyter 使用相同的 `.ipynb`/`.py` 文件，无需转换；各自的 Python 环境和运行变量不会通过 GitHub 同步。

## GitHub 协作

私有仓库需要仓库所有者先在 Settings > Collaborators 中邀请组员。组员接受邀请后，克隆仓库：

```bash
git clone https://github.com/Uncle416/IT5005-Sudoku-Assignment.git
cd IT5005-Sudoku-Assignment
```

建议每个任务使用独立分支。以 A 开始任务为例，在工作区没有未提交修改时运行：

```bash
git switch main
git pull --ff-only
git switch -c member-a-kb
```

编辑完成后，在 VS Code 的 Source Control 中查看并暂存自己修改的文件，Commit，然后 Publish Branch/Push，在 GitHub 建立 Pull Request 供组员检查和合并。

- A/B/C 编辑同一个 Python 文件中的不同函数，不要用整个旧文件覆盖新版本。
- Notebook 容易产生合并冲突：错开修改时间或通过各自分支由 C 逐项整合。
- GitHub 同步文件内容和提交历史，不同步实时光标或运行状态。
- 不提交虚拟环境、缓存、密码或 token。

## 运行应用

核心实现完成后，在项目根目录执行：

```bash
streamlit run sudoku_app.py
```

D 的在线应用：[Sudoku Logic Lab](https://it5005-sudoku-logic-lab.streamlit.app/)。支持五题选择、FC/BC 求解与计时、BC 单格查询及 FC 支持证明回放。

## 最终提交

开发仓库包含运行所需支持文件；交作业时另建以小组名命名的文件夹，仅放入以下三个文件并压缩：

- `Sudoku_Assignment.ipynb`（必需单元已运行、输出可见、Q1–Q5 完整、已填部署网址）
- `sudoku_solver.py`
- `sudoku_app.py`

## 工具参考

- [VS Code 中使用 Jupyter Notebook](https://code.visualstudio.com/docs/datascience/jupyter-notebooks)
- [Jupyter Notebook 官方说明](https://jupyter-notebook.readthedocs.io/en/stable/notebook.html)
