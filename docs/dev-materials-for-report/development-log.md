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

### [2026-04-20] 完成系统启动 5 项功能（功能 ID 1-5）

- **变更内容**：
  - 新建领域模型（方案 C：字段固定的实体先 dataclass，多态层留给 owner）
    - [`src/models/player.py`](../../src/models/player.py)
    - [`src/models/listing.py`](../../src/models/listing.py)
    - [`src/models/transaction.py`](../../src/models/transaction.py)
    - [`src/models/__init__.py`](../../src/models/__init__.py) 统一导出
  - 持久化与种子
    - [`src/services/seed.py`](../../src/services/seed.py)：完整 Catalog + 50 物品 + 12 玩家 + 25 挂单
    - [`src/services/persistence.py`](../../src/services/persistence.py)：`Persistence` 类（load_all / save_* / seed_if_empty / next_*_id / 完整性校验 / 备份 / reset）
    - `Repository` 数据载体：Player/Listing/Transaction 已用模型类，Item/Catalog 仍为 dict（待 JIAFENG / XINGZHOU）
  - 应用生命周期
    - [`src/app.py`](../../src/app.py)：`App` 类承载 bootstrap → banner → ui_runner → shutdown，含进程级兜底（KeyboardInterrupt / TradingSystemError / 任意 Exception 三档退出码）
  - 入口收口
    - [`main.py`](../../main.py) 缩减为 ~10 行，只调 `App().run()`
  - 测试
    - [`tests/services/test_persistence.py`](../../tests/services/test_persistence.py) 19 用例
    - [`tests/test_app.py`](../../tests/test_app.py) 10 用例
  - 全套 73 个测试通过
- **关键设计决策**（详见 design-decisions.md，待补）：
  - **`Repository` 字段类型**：放弃"全 dict"方案，对字段固定无子类的实体（Player/Listing/Transaction）直接用 dataclass，避免后续 `repo.players[pid]['gold']` → `.gold` 大重构
  - **`App` 放在 `src/app.py`**：与 `src/services/` 等同层，根目录只留 `main.py` 作为薄入口
  - **完整性校验分级**：背包 / 挂单引用错误硬抛 `DataIntegrityError`；交易引用挂单缺失仅 print 警告（历史允许挂单被清理）
- **遗留问题**：
  - `Item` 多态层（5 子类 + mixin）等 JIAFENG 实现，届时 Persistence 切换 `dict` → `Item`
  - `CatalogTree` 等 XINGZHOU 实现自实现 Tree 后包装
  - 完整性校验中"软警告"目前 print，等 logger 落地后改 `log.warn`

### [2026-04-21] 制定主菜单系统实现计划（功能 ID 6-9）

- **变更内容**：
  - 制定 [`feat/main-menu`](../../../..) 分支开发计划，见 [Claude Code 计划文件](../../../.claude/plans/snuggly-cuddling-petal.md)
  - 确定架构：单一文件 `src/ui/cli.py` 承载 CLI 交互，通过 `run_cli(app)` 注入 App 实例
  - 明确菜单层级：主菜单 6 个顶级入口 → 各子菜单 → 统一返回键 "b"
  - 设计操作撤销栈（功能 ID 9）：自实现 `OperationStack`（max_size=20），支持撤销挂单、删除物品等可逆操作
  - 规定异常处理策略：CLI 层捕获全部异常，用户可见消息从 `e.message` 取，服务层只抛不译
  - 更新测试思路：用 `monkeypatch` 模拟输入序列，验证菜单导航与异常分支
- **原因**：
  - 功能 ID 1-5（系统启动）已完成，UI 层是下一个阻塞点——没有菜单，后续玩家/物品/市场功能无法交互验证
  - 需要在服务层（PlayerService / MarketService 等）由其他组员实现前，先把 CLI 外壳和菜单导航打通
- **关键设计决策**：
  - 保留 `_default_ui_runner` 作为测试注入点，但默认改为导入 `from src.ui.cli import run_cli`
  - 撤销栈独立实现（不混用 `src/structures/stack.py`），避免操作元数据与通用 Stack 耦合
  - 非法输入统一抛 `InvalidInputError`（已在 errors/validation.py 定义），CLI 捕获后翻译为用户提示
- **遗留问题**：
  - 各子菜单的具体功能依赖下游服务：`PlayerService`（WEIJIE ZHOU）、`ItemService`（JIAFENG YE）、`Inventory`（XINGZHOU PENG）、`MarketService`（MINGJIN LI）
  - 计划先实现菜单外壳 + 已有数据的只读展示（如玩家列表、物品列表），写操作待服务层对接

### [2026-04-21] 实现主菜单系统（功能 ID 6-9）

- **变更内容**：
  - 新建 [`src/ui/cli.py`](../../src/ui/cli.py)：
    - `TradingCLI` 类承载全部交互逻辑
    - 6 个顶级菜单入口（玩家 / 物品 / 背包 / 市场 / 报表 / 退出）
    - 5 个子菜单层级，统一 "b" 键返回
    - `InvalidInputError` 捕获并重新显示菜单（功能 ID 8）
    - 自实现 `OperationStack`（max_size=20，FIFO 淘汰），支持撤销挂单（功能 ID 9）
  - 修改 [`src/app.py`](../../src/app.py)：`run_cli` 延迟导入，替代占位 UI runner
  - 已实现的可交互功能：玩家列表/详情/搜索、物品列表/详情/搜索、市场挂单浏览/撤销/价格查询/排序、富豪榜、系统快照、金币充值（调试）
  - 标记功能 ID 6-9 为已完成
  - 全部 73 个测试通过
- **关键设计决策**：
  - CLI 内部循环捕获全部异常，符合 "服务层只抛、UI 层翻译" 的分层原则
  - 撤销栈独立实现（不混用 structures/stack.py），避免操作元数据与通用栈耦合
  - 写操作（创建玩家、挂单上架、购买等）留待各服务层负责人实现，当前以占位提示替代
- **CLI 占位提示清单**（`src/ui/cli.py` 中以 `"[XXX] 功能待 YYY 实现"` 形式提示用户）：
  - 玩家管理：创建玩家、修改玩家名、删除玩家 → 待 `PlayerService`（WEIJIE ZHOU）
  - 物品管理：按分类浏览 → 待 `CatalogTree`（XINGZHOU PENG）
  - 背包管理：按稀有度排序、移除物品、添加物品、容量信息 → 待 `Inventory`（XINGZHOU PENG）
  - 交易市场：挂单上架、按分类筛选、购买物品 → 待 `MarketService`（MINGJIN LI）
  - 历史与报表：物品成交历史、价格统计、交易额榜 → 待 `TransactionService`（MINGJIN LI）
- **测试**：新增 [`tests/ui/test_cli.py`](../../tests/ui/test_cli.py) 28 个用例
  - `OperationStack` 数据结构测试（LIFO、FIFO 淘汰、空栈边界）
  - 主菜单导航与子菜单返回测试
  - 非法输入处理测试（功能 ID 8）
  - 查询功能测试（玩家/物品/挂单按 ID、名字搜索）
  - 数据展示测试（快照、富豪榜、成交历史）
  - 使用 monkeypatch 模拟输入序列，避免真实交互
- **遗留问题**：
  - 上述 14 个菜单项待各服务层负责人对接后，从 print 占位提示改为实际业务调用
  - 撤销栈目前仅演示于 "撤销挂单"，后续可扩展至删除物品等可逆操作
  - CLI 层异常路径测试（模拟 KeyboardInterrupt）因 mock 复杂度暂缓

### [2026-04-21] 补服务层代码骨架（service framework Phase 1）

- **变更内容**：
  - 新增 6 个服务模块：
    - [`src/services/logger.py`](../../src/services/logger.py)
    - [`src/services/player_service.py`](../../src/services/player_service.py)
    - [`src/services/transaction.py`](../../src/services/transaction.py)
    - [`src/services/item_service.py`](../../src/services/item_service.py)
    - [`src/services/market.py`](../../src/services/market.py)
    - [`src/services/inventory.py`](../../src/services/inventory.py)
  - 修改 [`src/services/__init__.py`](../../src/services/__init__.py)，统一导出 service 层边界
  - 修改 [`src/app.py`](../../src/app.py)：bootstrap 后初始化 `player_service` / `item_service` / `transaction_service` / `market_service`
  - 修改 [`src/ui/cli.py`](../../src/ui/cli.py)：
    - 玩家列表 / 按 ID 查询 / 名字搜索 / 金币充值改走 `PlayerService`
    - 物品列表 / 按 ID 查询改走 `ItemService`
    - 活跃挂单 / 区间查询 / 排序 / 撤销挂单改走 `MarketService`
    - 玩家成交历史 / 富豪榜 / 系统快照改走 `TransactionService`
  - 新增 4 份服务层测试：
    - [`tests/services/test_player_service.py`](../../tests/services/test_player_service.py)
    - [`tests/services/test_transaction_service.py`](../../tests/services/test_transaction_service.py)
    - [`tests/services/test_item_service.py`](../../tests/services/test_item_service.py)
    - [`tests/services/test_market_service.py`](../../tests/services/test_market_service.py)
- **原因**：
  - 之前只有文档接口，没有代码层可 import 的 service 边界，导致 CLI 只能直接操作 `repo`
  - 为了推进“历史与报表”功能，必须先补 `TransactionService` 等最小可依赖骨架
- **关键设计决策**：
  - 这一轮只实现当前数据模型下安全可落地的方法：查询、报表、轻量写操作（如加金币、取消挂单）
  - 明确保留 `NotImplementedError` 的接口：`ItemService.create_item/delete_item`、`MarketService.create_listing/buy/settle_pending`、`Inventory` 全部真实操作
  - `Inventory` 只保留骨架，不提前固化过渡实现，避免影响后续双向链表版本
- **测试**：
  - 新增服务层测试 35 个
  - 全量测试通过：**140 passed**
- **遗留问题**：
  - `Item` 多态层、`CatalogTree`、`Inventory` 双向链表、市场事务回滚仍待各负责人继续实现
  - 当前 service framework 先解决“可依赖开发”，不是最终完整业务层

### [2026-04-22] 性能遗留项 TODO（来自 PR #8 review）

> 这一项不是 bug，是为了避免“PR 回复随时间丢失”，把 reviewer 提出的性能改进点
> 统一记录下来，便于后续负责人接手时直接找到上下文。
> 对应代码处已以 `# TODO(perf): ...` 形式就地标注，并回指向本条。

- **现状**：当前 service 层多处使用 O(N) 全量扫描 repo 集合，在 seed 级数据量下没有性能问题，但数据量大时会退化
- **背景**：service framework Phase 1 刻意不在 `Repository` 中引入二级索引与缓存，避免提前固化数据结构，并保持 repo 单一信号源
- **具体点位**：
  1. [`src/services/transaction.py`](../../src/services/transaction.py)::`by_player` —— 每次按玩家查交易全量扫描 `repo.transactions`
     - 优化方向：`Repository` 维护 `player_id -> [transaction_ref]` 索引，append 时更新
  2. [`src/services/transaction.py`](../../src/services/transaction.py)::`top_by_volume` —— 每次查交易额榜全量聚合
     - 优化方向：`TransactionService.append` 时增量更新玩家累计成交额缓存（仿 `snapshot` 思路）
  3. [`src/services/player_service.py`](../../src/services/player_service.py)::`delete` —— 删除玩家时全量扫描 `repo.listings` 判断活跃挂单
     - 优化方向：`Repository` 维护 `seller_id -> active_listing_ids` 索引；或在 `MarketService` 中暴露 `has_active_listings(player_id)` 封装点
- **处理建议**：
  - 本条**不在 Phase 1 修**，以免把 `Repository` 过早复杂化
  - 等到 `MarketService.buy / create_listing / settle_pending` 真正落地时统一设计索引
  - 届时建议同时更新 [`docs/services-interface.md`](../services-interface.md) §4 `Repository` 字段说明

### [2026-04-22] 完成历史与报表功能（Phase 1.5）

- **变更内容**：
  - 扩展 [`src/services/transaction.py`](../../src/services/transaction.py)：
    - 新增 `by_category(category_prefix)`
    - 新增 `price_stats_by_category(category_prefix)`
  - 修改 [`src/ui/cli.py`](../../src/ui/cli.py)：
    - 报表菜单 2 / 3 / 5 不再是占位提示
    - 物品成交历史支持 **按 `item_id` / 按类型分类** 两种口径
    - 价格统计支持 **按 `item_id` / 按类型分类** 两种口径
    - 新增交易额榜展示
    - 完善玩家成交历史输出（时间 / 角色 / 对手 / 数量 / 金额）
  - 更新 [`tests/services/test_transaction_service.py`](../../tests/services/test_transaction_service.py)：新增 category 聚合与空结果测试
  - 更新 [`tests/ui/test_cli.py`](../../tests/ui/test_cli.py)：新增报表 2 / 3 / 5 的 CLI 测试（含空数据场景）
- **原因**：
  - `docs/功能列表.csv` 与 `docs/data-design.md` 都明确要求“物品成交历史 / 价格统计”支持按 `item_id` 与按类型/分类查询
  - 当前 `TransactionService` 已具备 item 维度统计能力，只需小幅扩展即可让 CLI 侧完整对齐文档口径
- **关键设计决策**：
  - 这轮采用 `Item.category.startswith(category_prefix)` 作为“按类型/分类”查询语义，直接复用现有 category 路径体系（如 `weapon` / `weapon.sword` / `misc`）
  - 不引入 Repository 新索引，不修改 Persistence，不触碰 Market.buy，保持 Phase 1.5 范围可控
  - 交易驱动的报表在空数据集下统一给出友好提示，而不是把“无成交记录”当异常泄漏给最终用户
- **测试**：
  - 针对 `TransactionService` 与 `CLI` 的历史/报表测试通过
  - 当前相关测试通过：**44 passed**
- **遗留问题**：
  - 当前“价格走势”仍是时间倒序明细展示，不是可视化趋势图
  - 交易额榜与玩家历史目前仍基于线性扫描 / 聚合，性能优化已单列到上方“性能遗留项 TODO”

### [2026-04-22] 完成操作日志落盘（功能 ID 56）

- **变更内容**：
  - 扩展 [`src/services/logger.py`](../../src/services/logger.py)：
    - 保留控制台输出
    - 追加写入 `data/operation.log`
    - 文件写入失败时吞 `OSError`，不影响业务流程
  - 修改 [`src/services/persistence.py`](../../src/services/persistence.py)：
    - `_validate_integrity()` 中“交易引用缺失挂单”的软警告不再 `print`
    - 改为 `log.warn("persistence", "txn_references_missing_listing", ...)`
  - 新增 [`tests/services/test_logger.py`](../../tests/services/test_logger.py)
  - 更新 [`tests/services/test_persistence.py`](../../tests/services/test_persistence.py)：补“软警告只告警不抛异常”测试
  - 更新 [`docs/services-interface.md`](../services-interface.md)：logger 小节补充实际落盘行为
- **原因**：
  - `docs/error-and-log-design.md` 与功能列表都要求关键操作写入 `data/operation.log`
  - 之前 logger 只有统一入口，没有真正落盘；Persistence 软警告也还停留在 `print`
- **关键设计决策**：
  - logger 文件写入失败只吞 `OSError`，不吞更宽泛的 `Exception`，避免静默掩盖真实代码 bug
  - 保持 logger 对外接口不变：`log.info/warn/error/debug(module, event, **context)`
  - 软警告行为不变：仍然只告警、不抛异常，只是输出介质从 `print` 改为 `log.warn`
- **测试**：
  - `tests/services/test_logger.py` + `tests/services/test_persistence.py` 相关测试通过：**24 passed**
- **遗留问题**：
  - 当前只完成了日志落盘，不包含 CLI 菜单上的“手动保存 / 数据重置”入口（留到下一轮）

<!-- 在此添加新条目 -->
