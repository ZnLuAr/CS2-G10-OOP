# 开发日志

> 时间线式记录关键变更：什么时候改了什么、为什么改。
> 用于报告的"开发与测试"章节，证明系统是迭代演进的。

---

## 模板

### [YYYY-MM-DD] 简短标题

- **变更内容**：做了什么
- **原因**：为什么要做
- **遗留问题**：（可选）有没有引入新问题或待办

---

## 日志

### [2026-03-10 ~ 2026-03-11] 项目初始化

- **变更内容**：
  - 创建 GitHub 仓库 `CS2-G10-OOP`
  - 编写根目录 `README.md`：项目简介、核心要求速览、小组成员、协作规范（分支管理、commit 格式、冲突处理 FAQ）
  - 添加 `.gitignore`、`.gitattributes`、`.editorconfig`，统一开发环境
- **原因**：让组员（多数为 Git 新手）有清晰的协作流程与起手指引
- **遗留问题**：无

---

### [2026-03-11] 创建文档体系与 PR 流程演示

- **变更内容**：
  - 新建 `docs/` 目录
  - 添加 `docs/README.md`、`docs/PR-draft-for-reference.md`，演示 Pull Request 流程
- **原因**：让不熟悉 GitHub 的组员通过实际的 PR 看到流程，而不是只看文字
- **遗留问题**：无

---

### [2026-04-19] 确定应用场景与项目骨架

- **变更内容**：
  - 经组员讨论，选定 **游戏装备交易系统** 作为应用场景
  - 创建 `src/` 完整目录骨架（`models/` `structures/` `services/` `ui/` `errors/`），每个子包 `__init__.py` 中写明预期模块清单
  - 创建 `tests/` 目录及 `tests/structures/` `tests/models/` `tests/services/` 的 README 占位
  - `main.py` 写入入口骨架
- **原因**：让组员认领模块时知道该建什么文件、放在哪
- **遗留问题**：各模块的认领分工待定

---

### [2026-04-19] 数据字段约定与持久化方案

- **变更内容**：
  - 创建 `data/README.md`，定义 5 个 JSON 文件的字段、关系与示例
  - 配套修改 `.gitignore`：忽略 `data/` 下数据文件，但保留目录结构（`.gitkeep` + README）
  - 创建 `data/stats-design.md`，详细定义各物品分类的 `stats` 字段
  - 在 `data/README.md` 显眼处加入指引，链接到 `stats-design.md`
- **原因**：先把数据契约定下来，避免后续多人开发时字段命名 / 结构产生分歧
- **遗留问题**：
  - `stats-design.md` 中的 5 个待讨论项需在下次会议中确认
  - 各分类 stats 数值范围 / 倍率与 rarity 的关系待定

---

### [2026-04-19] 编写功能列表

- **变更内容**：
  - 创建 `docs/功能列表.csv`，按"模块 / 功能名称 / 描述 / 优先级 / 标签"细粒度列出 61 项功能
  - 每个核心数据结构都有明确功能挂钩（HashMap → ID 查询，BST → 价格区间查询等）
- **原因**：让组员能按模块认领任务，同时保证课程要求的所有数据结构都有合理使用场景
- **遗留问题**：负责人列待填

### [2026-04-19] 数据设计待讨论项部分确认

- **变更内容**：
  - 在 `docs/data-design.md` 中确认两项设计：
    1. 消耗品堆叠超上限：自动新建一格；背包满则拒绝入库
    2. 引入 `level_req` / `class_req` 字段，作为武器 / 工具 / 装备的使用门槛
  - 待讨论项保留：主副手 / 双手武器、附魔 / 词条系统
- **原因**：先把无争议的字段约定下来，避免阻塞 Item 子类与 Inventory 的开发
- **遗留问题**：上述 2 项需下次会议讨论；`class_req` 取值集合（职业列表）尚未定义

### [2026-04-19] 数据设计文档补全非物品实体

- **变更内容**：
  - `docs/data-design.md` 补充 §10 Player / §11 Inventory / §12 Listing / §13 Transaction / §14 Catalog 五节
  - 新增 §15 全实体命名与 ID 规则汇总（前缀 / 上限 / 时间戳格式 / 字段命名约定）
  - 文档标题由"Item 物品系统设计"改为"数据系统设计"
  - 待讨论项追加 2 项：玩家职业取值集合、是否引入经验值字段
- **原因**：之前的版本只覆盖了物品，遗漏了其它 4 类实体；统一在一份文档里，避免后续多人开发字段对不上
- **遗留问题**：4 项待会议确认（主副手 / 附魔 / 职业列表 / 经验值）

### [2026-04-20] description 字段提升至 Item 顶层

- **变更内容**：
  - `description` 从 `Misc.stats` 移到 §8.3.1 顶层字段（可选，长度 0–200）
  - 所有物品都可写说明文字；`describe()` 多态方法可基于此返回统一格式描述
  - 同步更新 §8.5 JSON 示例
- **原因**：说明文字是跨子类的元数据，放顶层避免重复定义
- **遗留问题**：无

### [2026-04-20] 制定异常与日志接口规范

- **变更内容**：
  - 新建 [`docs/error-and-log-design.md`](../error-and-log-design.md)
  - 定义三层异常树（`TradingSystemError` → `Data/Validation/Trade` → 16 个具体类）
  - 给出每个异常的字段、默认消息、抛出 / 捕获 / 日志的决策表
  - 规定操作日志格式（统一走 `src/services/logger.py` 包装）
  - 文末附"给负责人 YUXI ZHU 的实施路径"
- **原因**：
  - 异常名称已被功能列表里的多个模块（市场 / 背包 / 交易）引用，再不定下来下游会各自捏一套
  - 负责人是新手，规范化的接口比让其自由摸索更可控
- **遗留问题**：`src/errors/__init__.py` 与 `src/services/logger.py` 待实现

### [2026-04-20] docs/ 目录拆分：分离"项目文档"与"开发素材"

- **变更内容**：
  - 新建 [`docs/dev-materials-for-report/`](./) 子目录，移入 `design-decisions.md` / `development-log.md` / `testing-notes.md`
  - 项目级稳定文档（`data-design.md` / `error-and-log-design.md` / `功能列表.csv` / `project-introduction.md` / `reflection.md`）保留在 `docs/` 根
  - 子目录内新增 [`README.md`](./README.md) 说明用途与分工
  - 同步更新 [`docs/README.md`](../README.md) 文档总览（按"项目文档"与"开发素材"两段呈现）
  - 修正 `data-design.md` 与本日志中受路径变化影响的链接
- **原因**：
  - "项目文档"是其他模块要查阅的接口规范，结构稳定；"开发素材"是面向报告的过程性记录，按时间累积
  - 分目录后两类文档不会互相干扰，组员一眼就知道在哪儿写什么
- **遗留问题**：无

### [2026-04-20] 制定服务层接口规范

- **变更内容**：
  - 新建 [`docs/services-interface.md`](../services-interface.md)
  - 列出 `src/services/` 下 7 个模块（persistence / logger / player_service / item_service / inventory / market / transaction）的全部公开方法签名、参数、返回值、抛出异常与副作用标注
  - 引入 `Repository` 数据载体，避免在服务间到处传 6 个参数
  - 给出调用关系图，禁止反向依赖（`Persistence` 不依赖业务服务，`PlayerService` 不依赖 `MarketService`）
  - 文末附"给各模块负责人的提示"
  - 同步更新 [`docs/README.md`](../README.md) 文档总览
- **原因**：
  - `MarketService.buy` 这类事务方法横跨 4 个模块，再不把签名钉死下游会各自实现
  - 接口规范优先于实现：负责人可先写假实现（`raise NotImplementedError`）让别人能 import 跑通
- **遗留问题**：`Repository` 字段定型后若需新增字段，需同步更新所有 `Persistence.save_*` 与种子脚本

### [2026-04-20] 实现自定义异常体系（基础部分）

- **变更内容**：
  - 按 [`error-and-log-design.md §2-§4`](../error-and-log-design.md) 实现 `src/errors/` 全部 16 个异常类 + 3 层基类
  - 拆分为 4 个文件：[`base.py`](../../src/errors/base.py) / [`data.py`](../../src/errors/data.py) / [`validation.py`](../../src/errors/validation.py) / [`trade.py`](../../src/errors/trade.py)
  - [`__init__.py`](../../src/errors/__init__.py) 仅做统一 re-export 与 `__all__`，保证调用方写法不变（`from src.errors import InsufficientGoldError`）
  - 新增 [`tests/services/test_errors.py`](../../tests/services/test_errors.py)：4 组共 44 个用例，覆盖异常树结构、基类行为、每个具体异常的字段与消息、捕获契约（基类抓子类）
  - 同步更新 [`error-and-log-design.md §7`](../error-and-log-design.md) 的目录约定（从单文件改为按大类分文件）
- **原因**：
  - 系统启动 / 持久化等模块的异常（`PersistenceError` / `DataIntegrityError` / `SerializationError`）已经被本人接下来的工作直接依赖，先把这部分稳定下来下游才能写
  - 单文件方案（300 行）已临近可读性临界，按异常大类拆分更便于多人扩展
- **遗留问题**：
  - `src/services/logger.py` 仍未实现，待 YUXI ZHU 接手
  - 异常路径测试（功能 ID 60）的"完整端到端"用例需等服务层落地后再补

<!-- 在此添加新条目 -->
