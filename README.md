# JC1503 OOP Group Project — CS 2 Group 10


## Python 面向对象程序设计 · 期中小组作业

---

> OOP 不是 OP（肃然



## 项目简介

本项目是 JC1503 课程的期中小组作业，要求以 Python 面向对象的方式设计并实现一个**完整的个人软件系统**。系统需选定一个现实应用场景（如记录管理、预订系统、追踪系统等），围绕该场景提供一组有意义的 CRUD 操作，并具备数据持久化能力。

### 核心要求速览

| 类别 | 要点 |
|------|------|
| **OOP 设计** | 类与对象、封装、继承、多态、组合、抽象基类、自定义异常 |
| **数据结构** | 双向链表、栈、队列、树、二叉搜索树、哈希表（自行实现） |
| **算法** | 递归树遍历、搜索行为分析、复杂度考量 |
| **持久化** | 首次运行自动生成初始数据集并存储；后续运行加载并更新 |
| **测试** | 单元测试、模块测试、系统测试 |

## 小组成员（排名不分先后）

| 姓名 | 负责模块 | GitHub ID |
|------|----------|-----------|
| MINGJIN LI | | Matthew-0223 |
| XINGZHOU PENG | | xing-520 |
| JIAFENG YE | | Kelvinvoyage |
| WEIJIE ZHOU | | Q123422 |
| YUXI ZHU | | shaun070119 |
| LVZHEN ZHOU | | ZnLuAr |

## 项目结构

```

· 以下为预期目录结构，随开发推进逐步建立。

.
├── src/                # 源代码
│   ├── models/         # 领域模型 / 实体类
│   ├── structures/     # 自实现的数据结构
│   ├── services/       # 业务逻辑
│   └── ui/             # 用户界面 / CLI 交互
├── tests/              # 测试代码
├── data/               # 运行时数据文件（由程序自动生成，不提交）
├── docs/               # 文档 / 报告素材
├── main.py             # 程序入口
├── requirements.txt    # 依赖列表（如有）
└── README.md
```

## 如何运行

### 环境要求

- **Python 3.10 或以上**（项目可能用到较新的 type hints 语法 ~~，其实我还是推荐 Python 3.12 以上~~）
- 不依赖任何第三方库（`requirements.txt` 暂为空）

### 步骤

```bash
# 1. 克隆仓库
git clone <仓库地址>
cd <项目目录>

# 2. （可选）创建虚拟环境
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行程序
python main.py

# 5. 运行测试
python -m pytest tests/
```

---

## 小组协作规范

> 以下规范尽量简洁实用，即使不熟悉 Git 也能快速上手。

### 核心原则

**重要：不要直接在 `main` 分支上改代码。**

`main` 分支是稳定版本，只接受经过验证的代码。日常开发请在 `dev` 分支上进行。

---

### 分支管理

| 分支 | 用途 | 谁可以直接提交 |
|------|------|----------------|
| `main` | 稳定版本，用于最终提交 | 仅通过合并 `dev` 更新 |
| `dev` | 日常开发分支 | 所有人 |
| `feat/<功能名>` | 个人功能分支（可选） | 创建者 |

**建议工作方式：**
- 如果你不太熟悉 Git，直接在 `dev` 分支上工作即可
- 如果你习惯独立开发，可以创建自己的 `feat/xxx` 分支，完成后合入 `dev`

---

### 日常工作流（新手友好版）

#### 第一次克隆仓库

```bash
# 1. 克隆仓库到本地
git clone git@github.com:ZnLuAr/CS2-G10-OOP.git
cd CS2-G10-OOP

# 2. 切换到 dev 分支（日常开发分支）
git checkout dev

# 3. 确认当前分支
git branch
# 应该看到 * dev（星号表示当前分支）
```

#### 每次开始工作前

```bash
# 拉取最新代码（避免基于过时的代码修改）
git pull origin dev
```

**为什么要先 pull？**
- 其他组员可能已经推送了新代码
- 如果你基于旧代码修改，推送时会产生冲突
- 先 pull 可以提前发现冲突，更容易解决

#### 完成修改后提交

```bash
# 1. 查看你修改了哪些文件
git status

# 2. 添加修改的文件到暂存区
git add <文件名>              # 添加单个文件
git add .                     # 添加所有修改（小心，确认没有不该提交的文件）

# 3. 提交修改（附上说明信息）
git commit -m "feat: 添加了 XXX 功能"

# 4. 推送到远程仓库
git push origin dev
```

**常见问题：**

<details>
<summary><b>推送时提示 "rejected" 或 "non-fast-forward"</b></summary>

说明远程仓库有新的提交，你的本地代码不是最新的。

**解决方法：**
```bash
# 先拉取远程代码
git pull origin dev

# 如果有冲突，Git 会提示哪些文件冲突了
# 打开冲突文件，找到 <<<<<<< 和 >>>>>>> 标记
# 手动保留正确的代码，删除冲突标记

# 解决冲突后，重新提交
git add <冲突文件>
git commit -m "fix: 解决合并冲突"
git push origin dev
```

**不确定怎么解决？先找组员帮忙，不要用 `--force` 强制推送！**
</details>

<details>
<summary><b>不小心在 main 分支上改了代码怎么办？</b></summary>

**还没 commit：**
```bash
# 切换到 dev 分支，Git 会带着你的修改一起过去
git checkout dev
```

**已经 commit 但还没 push：**
```bash
# 切换到 dev 分支
git checkout dev

# 把 main 分支的最后一次提交应用到 dev
git cherry-pick main

# 回到 main 分支，撤销那次提交
git checkout main
git reset --hard HEAD~1
```

**已经 push 了：**
找熟悉 Git 的组员帮忙处理。
</details>

<details>
<summary><b>想撤销刚才的修改</b></summary>

**还没 add：**
```bash
git checkout -- <文件名>    # 撤销单个文件的修改
git checkout -- .           # 撤销所有修改
```

**已经 add 但还没 commit：**
```bash
git reset HEAD <文件名>     # 取消暂存
git checkout -- <文件名>    # 撤销修改
```

**已经 commit 但还没 push：**
```bash
git reset --soft HEAD~1     # 撤销 commit，保留修改
git reset --hard HEAD~1     # 撤销 commit，丢弃修改（危险！）
```
</details>

---

### 查看项目状态的常用命令

```bash
git status              # 查看当前修改了哪些文件
git log --oneline       # 查看提交历史（简洁版）
git diff                # 查看具体修改了什么内容
git branch              # 查看所有分支，* 表示当前分支
```

### Commit 信息格式

写清楚做了什么即可，建议格式：

```
<类型>: <简要描述>
```

常用类型：

| 类型 | 含义 |
|------|------|
| `feat` | 新增功能 |
| `fix` | 修复 bug |
| `docs` | 文档更新 |
| `test` | 添加或修改测试 |
| `refactor` | 重构（不改变功能） |
| `chore` | 杂项（依赖更新、配置修改等） |

示例：
- `feat: 添加学生记录的增删改查`
- `fix: 修复文件读取时的编码错误`
- `docs: 更新 README 成员信息`

### 文件管理

- **不要提交** `data/` 目录中的运行时数据文件（已在 `.gitignore` 中配置）。
- **不要提交** 虚拟环境目录（`venv/`、`__pycache__/` 等）。
- **不要提交** ~~自己的小秘密~~。
- 每个人修改文件前，确认自己在最新的代码基础上工作。

### 注

- 如果你要修改别人负责的模块，请**提前沟通**。
- 遇到合并冲突或不确定的操作，在群里问一声，避免覆盖他人的工作。
- 如果实在想不出或懒得写 commit，可以去看看 https://github.com/AptS-1547/gcop-rs

---

## .gitignore 建议

请确保仓库中包含以下 `.gitignore` 配置：

```
__pycache__/
*.pyc
venv/
.venv/
data/
*.egg-info/
.pytest_cache/
.idea/
.vscode/
```

---

## 许可

本项目仅用于 JC1503 课程作业，不对外发布。
