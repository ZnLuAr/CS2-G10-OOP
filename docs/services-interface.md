# 服务层接口规范

> 本文档定义 `src/services/` 下**所有服务类的对外接口**：方法签名、参数、返回值、抛出异常与副作用。
> **任何服务模块的开发者在动手写实现前都必须先在此对齐接口；调用方（UI 层 / 测试层）也以本文档为准。**
>
> 配套文档：
> - 实体字段定义见 [`data-design.md`](./data-design.md)
> - 异常类与日志接口见 [`error-and-log-design.md`](./error-and-log-design.md)
> - 模块负责人见 [`功能列表.csv`](./功能列表.csv)

---

## 1. 设计目标

- **统一边界**：服务层只暴露"做什么"，不暴露"怎么做"——UI 与测试都只依赖签名
- **职责清晰**：服务**只抛、不捕获**异常；UI 负责翻译异常为用户提示
- **可测试**：每个公开方法的输入输出都能在单测中独立断言
- **新手友好**：照着签名 + docstring 填空就能写出实现

---

## 2. 模块总览

```
src/services/
├── persistence.py    # 加载 / 保存全部 JSON、ID 自增、数据完整性校验
├── logger.py         # log.info / warn / error 统一日志入口
├── player_service.py # 玩家 CRUD + 查询
├── item_service.py   # 物品 CRUD + 分类树查询
├── inventory.py      # 单玩家背包操作（双向链表）
├── market.py         # 挂单、交易、价格 BST 查询
└── transaction.py    # 交易记录追加 + 历史查询 + 排行榜
```

| 模块 | 主要负责人 | 关键数据结构 |
|------|-----------|-------------|
| `persistence` | LVZHEN ZHOU | HashMap（ID→实体） |
| `logger` | YUXI ZHU | — |
| `player_service` | WEIJIE ZHOU | HashMap |
| `item_service` | JIAFENG YE | HashMap + Tree（Catalog） |
| `inventory` | XINGZHOU PENG | DoublyLinkedList |
| `market` | MINGJIN LI | BST（按价格）+ HashMap（按 ID）+ Queue（批量结算） |
| `transaction` | LVZHEN ZHOU | List（append-only） |

---

## 3. 通用约定

### 3.1 命名

- 模块文件名：`snake_case.py`
- 类名：`PascalCase`，服务类后缀统一为 `Service` 或表义名词（如 `Inventory` / `Market`）
- 公开方法：`snake_case`，动词开头（`create_player` / `buy` / `cancel_listing`）
- 私有辅助方法：以 `_` 开头

### 3.2 类型注解

- **所有公开方法必须带完整类型注解**（参数 + 返回值）
- 集合返回值优先使用 `list[T]` / `dict[K, V]`，避免暴露内部数据结构
- ID 一律 `str` 类型（如 `player_id: str`）

### 3.3 异常

- 服务方法**只抛、不捕获** `TradingSystemError` 子类（参见 [`error-and-log-design.md §2`](./error-and-log-design.md)）
- 不允许返回 `None` / `False` / 空串来表示"失败"——一律抛对应异常
- 文档中**必须列出**该方法可能抛出的所有自定义异常

### 3.4 副作用

每个公开方法在 docstring 中标注以下任一：

- `# pure` —— 仅读取，不改内存、不写盘
- `# mutates` —— 修改内存对象
- `# persists` —— 修改内存 **且**写盘（通过 `Persistence.save_*`）
- `# logs` —— 写 `data/operation.log`

> **保存策略**：所有"成功的写操作"自动落盘（功能 ID 50）。服务方法在变更后调用对应 `Persistence.save_*` 即可，不需要 UI 层额外触发。

### 3.5 日志

- 关键操作（创建 / 更新 / 删除 / 交易）在方法**末尾**调用 `log.info` / `log.warn`
- 异常路径由抛出方写日志（参见 `error-and-log-design.md §5` 决策表）

---

## 4. `persistence.py` 持久化

### 4.1 类 `Persistence`

加载 / 保存全部 JSON 数据，并维护 ID 自增计数器。**单例**风格使用（启动时构造一次）。

```python
class Persistence:
    def __init__(self, data_dir: str = "data") -> None: ...

    # ===== 加载 =====
    def load_all(self) -> "Repository":
        """从 data/*.json 加载全部数据，返回内存仓库对象。
        # mutates self （初始化 ID 计数器）

        Raises:
            PersistenceError: 文件读取失败
            SerializationError: JSON 反序列化失败
            DataIntegrityError: 外键完整性校验失败（仅警告级则不抛，由实现决定）
        """

    def seed_if_empty(self) -> bool:
        """若 data/ 下无业务文件则生成种子数据（玩家≥10/物品≥50/挂单≥20）。
        # persists
        Returns: 是否触发了种子生成
        """

    # ===== 保存 =====
    def save_players(self, players: list["Player"]) -> None: ...    # persists
    def save_items(self, items: list["Item"]) -> None: ...          # persists
    def save_market(self, listings: list["Listing"]) -> None: ...   # persists
    def save_transactions(self, txns: list["Transaction"]) -> None: ...  # persists
    def save_catalog(self, catalog: "CatalogTree") -> None: ...     # persists
    def save_all(self, repo: "Repository") -> None: ...             # persists

    # ===== ID 分配 =====
    def next_player_id(self) -> str: ...   # 返回 "p_001" 形式
    def next_item_id(self) -> str: ...
    def next_listing_id(self) -> str: ...
    def next_transaction_id(self) -> str: ...

    # ===== 备份 =====
    def backup_before_save(self, path: str) -> None:
        """保存前将旧文件备份为 data/backup/*.json.bak（功能 ID 51）。"""
```

### 4.2 数据载体 `Repository`

加载后所有内存数据通过单一 `Repository` 对象传递，避免到处传 6 个参数。

```python
@dataclass
class Repository:
    players: dict[str, "Player"]          # HashMap: player_id → Player
    items: dict[str, "Item"]              # HashMap: item_id → Item
    listings: dict[str, "Listing"]        # HashMap: listing_id → Listing
    transactions: list["Transaction"]     # append-only
    catalog: "CatalogTree"
```

---

## 5. `logger.py` 日志

详见 [`error-and-log-design.md §6`](./error-and-log-design.md)，此处仅列签名：

```python
class Log:
    def debug(self, module: str, event: str, **context) -> None: ...
    def info(self, module: str, event: str, **context) -> None: ...
    def warn(self, module: str, event: str, **context) -> None: ...
    def error(self, module: str, event: str, **context) -> None: ...

log: Log  # 模块级单例，使用方式：from src.services.logger import log
```

---

## 6. `player_service.py` 玩家服务

```python
class PlayerService:
    def __init__(self, repo: Repository, persistence: Persistence) -> None: ...

    # ===== 创建 =====
    def create_player(self, name: str, gold: int = 0,
                      level: int = 1, klass: str = "none") -> Player:
        """# persists # logs
        Raises:
            InvalidInputError: name 长度不在 1-20 / gold < 0 / level < 1 / klass 非法
        """

    # ===== 查询 =====
    def get_by_id(self, player_id: str) -> Player:
        """# pure  HashMap O(1) 查找
        Raises: PlayerNotFoundError
        """

    def search_by_name(self, keyword: str) -> list[Player]:
        """# pure  线性扫描 O(n)，包含匹配，用于与 HashMap 查询作复杂度对比"""

    def list_all(self, sort_by: str = "id", desc: bool = False) -> list[Player]:
        """# pure  sort_by ∈ {"id", "name", "gold"}"""

    # ===== 修改 =====
    def rename(self, player_id: str, new_name: str) -> None:
        """# persists # logs
        Raises: PlayerNotFoundError, InvalidInputError
        """

    def add_gold(self, player_id: str, amount: int) -> None:
        """充值（调试用）。# persists # logs
        Raises: PlayerNotFoundError, InvalidInputError (amount ≤ 0)
        """

    def spend_gold(self, player_id: str, amount: int) -> None:
        """扣金币（仅供 MarketService 内部调用）。# persists
        Raises: PlayerNotFoundError, InsufficientGoldError
        """

    # ===== 删除 =====
    def delete(self, player_id: str) -> None:
        """# persists # logs
        Raises:
            PlayerNotFoundError
            InventoryNotEmptyError: 背包非空
            BusinessRuleError: 存在活跃挂单
        """
```

---

## 7. `item_service.py` 物品服务

```python
class ItemService:
    def __init__(self, repo: Repository, persistence: Persistence) -> None: ...

    # ===== 查询 =====
    def get_by_id(self, item_id: str) -> Item:
        """# pure  HashMap O(1)
        Raises: ItemNotFoundError
        """

    def list_all(self, category_prefix: str | None = None) -> list[Item]:
        """# pure  按 category 前缀筛选（如 'weapon' 或 'weapon.sword'）"""

    def browse_catalog(self, node_key: str = "root") -> CatalogNode:
        """# pure  返回分类树节点，UI 递归向下浏览
        Raises: InvalidInputError (node_key 不存在)
        """

    def items_in_category(self, category: str) -> list[Item]:
        """# pure  返回某叶子分类下的所有物品（递归遍历）"""

    # ===== 创建 / 删除（管理员）=====
    def create_item(self, payload: dict) -> Item:
        """根据 payload['category'] 实例化对应 Item 子类。# persists # logs
        Raises:
            InvalidInputError: 字段缺失或非法
            SerializationError: 子类构造失败
        """

    def delete_item(self, item_id: str) -> None:
        """# persists # logs
        Raises:
            ItemNotFoundError
            BusinessRuleError: 仍有玩家持有 / 仍有活跃挂单
        """
```

---

## 8. `inventory.py` 背包

> **设计要点**：每个 `Player` 持有一个 `Inventory` 实例（组合关系）。`Inventory` 内部使用**自实现的双向链表**保存条目。

```python
class Inventory:
    CAPACITY: int = 50  # 格数上限

    def __init__(self, owner_id: str) -> None: ...

    # ===== 查询 =====
    def slots(self) -> list[InventorySlot]:
        """# pure  按链表顺序返回快照（拷贝，外部修改不影响内部）"""

    def find(self, item_id: str) -> InventorySlot | None:
        """# pure  线性扫描，O(n)"""

    def is_full(self) -> bool: ...                    # pure
    def used(self) -> int: ...                        # pure  当前格数

    def sorted_view(self, key: str = "rarity") -> list[InventorySlot]:
        """# pure  排序展示但不改变内部存储顺序（功能 ID 25）"""

    # ===== 增 =====
    def add(self, item: Item, count: int = 1,
            instance_state: dict | None = None) -> None:
        """入库：可堆叠物品先合堆，溢出自动新建格；不可堆叠新建格。# mutates
        Raises:
            InventoryFullError: 容量满且无法继续合堆叠
            InvalidInputError: count ≤ 0
        """

    # ===== 删 =====
    def remove(self, item_id: str, count: int = 1) -> None:
        """从背包移除指定物品（用于成交 / 丢弃 / 上架）。# mutates
        双向链表已知节点 O(1) 删除。
        Raises:
            ItemNotFoundError: 该物品不在背包内
            InvalidInputError: count ≤ 0 或 count 超出该物品持有数
            ItemNotEquippableError: 试图移除已穿戴物品
        """
```

> `Inventory` 不直接落盘——它是 `Player` 的一部分；调用 `PlayerService` / `MarketService` 完成业务操作后由其负责 `save_players`。

---

## 9. `market.py` 市场服务

```python
class MarketService:
    def __init__(self,
                 repo: Repository,
                 persistence: Persistence,
                 player_service: PlayerService,
                 transaction_service: "TransactionService") -> None: ...

    # ===== 挂单 =====
    def create_listing(self, seller_id: str, item_id: str,
                       count: int, price: int) -> Listing:
        """从背包移出物品并生成挂单。# persists # logs
        Raises:
            PlayerNotFoundError
            ItemNotFoundError: 卖家背包内无该物品
            InvalidInputError: price < 1 / count < 1
            DuplicateListingError: 同一不可堆叠物品已挂单
            ItemBrokenError: 耐久 = 0
            ItemNotEquippableError: 已穿戴
        """

    def cancel_listing(self, listing_id: str, requester_id: str) -> None:
        """卖家撤销自己的活跃挂单。# persists # logs
        Raises:
            ListingNotFoundError
            ListingNotActiveError
            BusinessRuleError: requester_id ≠ seller_id
            InventoryFullError: 背包满（挂单**保持 active**，并提示用户）
        """

    # ===== 浏览 / 查询 =====
    def list_active(self, sort_by: str = "created_at",
                    desc: bool = False) -> list[Listing]:
        """# pure  sort_by ∈ {"price", "created_at"}"""

    def query_by_price_range(self, min_price: int,
                             max_price: int) -> list[Listing]:
        """# pure  BST 范围查询，核心数据结构演示点（功能 ID 32）"""

    def query_by_category(self, category_prefix: str) -> list[Listing]: ...  # pure
    def query_by_seller(self, seller_id: str) -> list[Listing]: ...          # pure

    def get_listing(self, listing_id: str) -> Listing:
        """# pure  HashMap O(1)
        Raises: ListingNotFoundError
        """

    # ===== 交易 =====
    def buy(self, listing_id: str, buyer_id: str) -> Transaction:
        """事务式购买：校验 → 扣买家 → 加卖家 → 物品入买家背包 →
        挂单置 sold → 写交易记录。任一步失败回滚。# persists # logs
        Raises:
            ListingNotFoundError
            ListingNotActiveError
            PlayerNotFoundError
            SelfPurchaseError
            InsufficientGoldError
            InventoryFullError: 买家背包满
        """

    # ===== 批量结算（管理员）=====
    def settle_pending(self, listing_ids: list[str]) -> list[Transaction]:
        """使用自实现 Queue（FIFO）批量处理。单条失败不影响其余。# persists # logs"""
```

---

## 10. `transaction.py` 交易记录服务

```python
class TransactionService:
    def __init__(self, repo: Repository, persistence: Persistence) -> None: ...

    # ===== 写入（仅供 MarketService 内部调用）=====
    def append(self, txn: Transaction) -> None:
        """append-only，禁止覆盖既有记录。# persists"""

    # ===== 历史查询 =====
    def by_player(self, player_id: str,
                  role: str = "both") -> list[Transaction]:
        """# pure  role ∈ {"buyer", "seller", "both"}，按 completed_at 倒序"""

    def by_item(self, item_id: str) -> list[Transaction]: ...  # pure

    # ===== 统计 =====
    def price_stats(self, item_id: str) -> dict:
        """# pure
        Returns: {"min": int, "max": int, "avg": float, "count": int}
        Raises: InvalidInputError 若无成交记录
        """

    # ===== 排行榜 =====
    def top_by_gold(self, n: int = 10) -> list[Player]: ...        # pure
    def top_by_volume(self, n: int = 10) -> list[tuple[Player, int]]: ...  # pure

    # ===== 系统快照 =====
    def snapshot(self) -> dict:
        """# pure
        Returns: {"players": int, "items": int, "active_listings": int,
                  "total_volume": int}
        """
```

---

## 11. 调用关系图

```
UI (cli)
  │
  ├──▶ PlayerService ──▶ Persistence
  ├──▶ ItemService ────▶ Persistence
  ├──▶ MarketService ──┬──▶ PlayerService.spend_gold / add_gold
  │                    ├──▶ Inventory.add / remove
  │                    ├──▶ TransactionService.append
  │                    └──▶ Persistence
  └──▶ TransactionService ──▶ Persistence

所有模块 ──▶ logger.log
异常路径 ──▶ src/errors（统一异常）
```

**禁止反向依赖**：`Persistence` / `logger` / `errors` 不依赖任何业务服务；`PlayerService` 不依赖 `MarketService`。

---

## 12. 接口变更流程

修改 / 新增任何公开方法签名时：

1. 先在本文档对应章节修改签名 + docstring + 异常列表
2. 同步更新 [`error-and-log-design.md §4`](./error-and-log-design.md)（如新增异常）
3. 在 [`dev-materials-for-report/design-decisions.md`](./dev-materials-for-report/design-decisions.md) 写一条决策记录
4. 在 [`dev-materials-for-report/development-log.md`](./dev-materials-for-report/development-log.md) 写一条日志
5. 通知该模块的下游调用方（看调用关系图）

> **接口稳定**比"漂亮的实现"更重要。一个签名一旦发布，改起来要协调全组——拿不准就先在群里问。

---

## 13. 给负责人的提示

- **WEIJIE ZHOU（PlayerService）/ JIAFENG YE（ItemService）**：你们的方法是其他人的依赖入口，先把签名敲死、写好假实现（`raise NotImplementedError`），让别人能 import 跑通，再补实现
- **XINGZHOU PENG（Inventory）**：核心是双向链表的 add / remove；对外只暴露本文档列出的方法，链表节点不要泄漏
- **MINGJIN LI（Market）**：`buy` 是事务，强烈建议先写测试再写实现，每一步失败都要能回滚
- **LVZHEN ZHOU（Persistence / Transaction）**：`Repository` 是全系统的内存中枢，一旦定型就别频繁改字段
- **YUXI ZHU（Logger）**：先把 `log.info / warn / error` 三个最常用接口实现出来即可，DEBUG 与文件轮转可以延后
