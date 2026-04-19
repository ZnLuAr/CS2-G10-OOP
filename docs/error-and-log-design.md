# 异常与日志接口规范

> 本文档定义系统中**所有自定义异常**与**操作日志**的接口规范。
> **所有模块在抛出 / 捕获异常、写日志前都必须遵循本文档。**
> 主要负责人：YUXI ZHU；其它模块的开发者按本文档调用即可。

---

## 1. 设计目标

- **统一**：全系统只有一棵异常树，避免每个模块各捏一套
- **可读**：异常消息对最终用户友好，日志对开发者可定位
- **可测试**：每个异常都能被精确捕获（`except InsufficientGoldError`），不靠字符串匹配
- **新手友好**：本文档照着填空就能写出代码

---

## 2. 异常类层次

```
Exception
└── TradingSystemError              # 项目所有自定义异常的基类
    ├── DataError                   # 数据 / 持久化相关
    │   ├── DataIntegrityError      # 外键 / 引用完整性破坏
    │   ├── PersistenceError        # 文件读写失败
    │   └── SerializationError      # JSON 序列化 / 反序列化失败
    │
    ├── ValidationError             # 输入 / 状态校验失败
    │   ├── InvalidInputError       # 用户输入非法（菜单选项、字段长度等）
    │   ├── NotFoundError           # 按 ID 查找不到目标
    │   │   ├── PlayerNotFoundError
    │   │   ├── ItemNotFoundError
    │   │   └── ListingNotFoundError
    │   └── BusinessRuleError       # 违反业务规则
    │       ├── InventoryFullError
    │       ├── InventoryNotEmptyError      # 删玩家时背包非空
    │       ├── ItemNotEquippableError      # 不可穿戴 / 已穿戴 / 已损坏
    │       ├── ItemBrokenError             # 耐久 = 0
    │       └── LevelOrClassRequirementError
    │
    └── TradeError                  # 交易领域错误
        ├── InsufficientGoldError
        ├── SelfPurchaseError
        ├── ListingNotActiveError
        └── DuplicateListingError   # 同一物品实例重复上架
```

> **设计取舍**：三层够用——基类 → 大类（数据 / 校验 / 交易）→ 具体异常。再深没必要。

---

## 3. 基类定义

### 3.1 `TradingSystemError`

```python
class TradingSystemError(Exception):
    """项目所有自定义异常的根基类。

    Attributes:
        message: 面向用户的友好消息（中文，可直接打印给最终用户）
        context: 面向开发者的上下文 dict（写日志用，不展示给用户）
    """

    default_message: str = "系统出现异常"

    def __init__(self, message: str | None = None, **context):
        self.message = message or self.default_message
        self.context = context
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message
```

### 3.2 子类示例

每个具体异常**至少**重写 `default_message`，并在 `__init__` 里把关键字段塞进 `context`：

```python
class InsufficientGoldError(TradeError):
    default_message = "金币不足，无法完成交易"

    def __init__(self, required: int, available: int, **context):
        super().__init__(
            message=f"金币不足：需要 {required}，当前 {available}",
            required=required,
            available=available,
            **context,
        )


class PlayerNotFoundError(NotFoundError):
    default_message = "玩家不存在"

    def __init__(self, player_id: str, **context):
        super().__init__(
            message=f"未找到玩家：{player_id}",
            player_id=player_id,
            **context,
        )


class InventoryFullError(BusinessRuleError):
    default_message = "背包已满"

    def __init__(self, player_id: str, capacity: int, **context):
        super().__init__(
            message=f"背包已满（{capacity} 格），无法继续放入物品",
            player_id=player_id,
            capacity=capacity,
            **context,
        )
```

---

## 4. 全部异常清单（速查表）

| 类名 | 父类 | 必填参数 | 默认消息（中文） |
|------|------|----------|-----------------|
| `DataIntegrityError` | `DataError` | `entity, ref_id` | 数据完整性错误 |
| `PersistenceError` | `DataError` | `path, op` | 数据文件读写失败 |
| `SerializationError` | `DataError` | `entity, raw` | 数据序列化失败 |
| `InvalidInputError` | `ValidationError` | `field, value` | 输入非法 |
| `PlayerNotFoundError` | `NotFoundError` | `player_id` | 玩家不存在 |
| `ItemNotFoundError` | `NotFoundError` | `item_id` | 物品不存在 |
| `ListingNotFoundError` | `NotFoundError` | `listing_id` | 挂单不存在 |
| `InventoryFullError` | `BusinessRuleError` | `player_id, capacity` | 背包已满 |
| `InventoryNotEmptyError` | `BusinessRuleError` | `player_id` | 背包非空，无法删除玩家 |
| `ItemNotEquippableError` | `BusinessRuleError` | `item_id, reason` | 物品不可穿戴 |
| `ItemBrokenError` | `BusinessRuleError` | `item_id` | 物品已损坏 |
| `LevelOrClassRequirementError` | `BusinessRuleError` | `item_id, level_req, class_req` | 玩家等级 / 职业不满足要求 |
| `InsufficientGoldError` | `TradeError` | `required, available` | 金币不足 |
| `SelfPurchaseError` | `TradeError` | `player_id` | 不能购买自己的挂单 |
| `ListingNotActiveError` | `TradeError` | `listing_id, status` | 挂单已失效 |
| `DuplicateListingError` | `TradeError` | `item_id` | 同一物品已在挂单中 |

> **新增异常的流程**：先在本表追加一行，再到 [src/errors/__init__.py](../src/errors/__init__.py) 实现，最后到 [`dev-materials-for-report/development-log.md`](./dev-materials-for-report/development-log.md) 记一笔。

---

## 5. 抛出 / 捕获 / 日志的决策表

| 场景 | 谁抛 | 谁捕获 | 是否写日志 |
|------|------|--------|-----------|
| 用户输入非法 | UI / 服务层 | UI 主循环 | INFO（关键操作） |
| 业务规则违反（背包满 / 已穿戴等） | 服务层 | UI 调用处 | INFO |
| 找不到 ID | 服务层 | UI 调用处 | INFO |
| 交易类错误 | `services/market.py` | UI 调用处 | WARNING |
| 数据完整性 / 序列化失败 | `services/persistence.py` | 主循环外层 | ERROR + 堆栈 |
| 文件 I/O 失败 | `services/persistence.py` | 主循环外层 | ERROR + 堆栈 |
| 未预期异常（任何 `Exception`） | — | 主循环最外层 `try/except` | ERROR + 堆栈，程序继续 |

**核心原则**：

1. **服务层只抛、不捕获**——服务层不知道前端是 CLI 还是别的，由调用者决定怎么向用户呈现
2. **UI 层负责"翻译"异常**——`except TradingSystemError as e: print(e.message)` 即可
3. **主循环外层兜底**——任何漏网的 `Exception` 都不能让程序崩溃

---

## 6. 日志规范

### 6.1 文件位置

- 操作日志：`data/operation.log`（追加写��
- 程序不应把日志写到 stdout（保持 CLI 输出干净）

### 6.2 日志格式

固定格式（使用 Python `logging` 模块）：

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] [module] message | context_key1=value1 context_key2=value2
```

示例：

```
[2026-04-20 14:32:11] [INFO]  [market]      listing_created | listing_id=l_017 seller_id=p_003 item_id=i_011 price=1500
[2026-04-20 14:33:02] [WARN]  [market]      buy_rejected    | reason=insufficient_gold buyer_id=p_005 required=1500 available=800
[2026-04-20 14:35:00] [ERROR] [persistence] save_failed     | path=data/players.json error=PermissionError
```

### 6.3 日志级别

| 级别 | 使用场景 |
|------|----------|
| `DEBUG` | 开发期辅助（仅在 `--debug` 模式下输出） |
| `INFO` | 关键操作成功（创建 / 更新 / 删除 / 交易完成） |
| `WARNING` | 业务规则拦截（金币不足、自购等可预期错误） |
| `ERROR` | 数据完整性 / 文件 I/O 失败 / 未预期异常 |

### 6.4 调用约定

封装在 [src/services/logger.py](../src/services/logger.py)（待建）中暴露统一接口：

```python
from src.services.logger import log

log.info("market", "listing_created", listing_id="l_017", seller_id="p_003", price=1500)
log.warn("market", "buy_rejected", reason="insufficient_gold", buyer_id="p_005")
log.error("persistence", "save_failed", path="data/players.json", error=str(e))
```

> **不要直接用 `print` / `logging.info`**——一律走 `log.*`，便于后续统一改写格式 / 接入文件轮转。

---

## 7. 实现路径与目录约定

```
src/
├── errors/
│   └── __init__.py        # 全部异常类（按 §2 层次实现）
└── services/
    └── logger.py          # log.info / log.warn / log.error 包装
```

- 所有异常**集中在 `src/errors/__init__.py`**，便于 `from src.errors import InsufficientGoldError` 一行导入
- 不要散落在各业务模块里

---

## 8. 测试要求

异常路径测试（功能列表 ID 60）必须覆盖以下分支，每个用例独立：

- 金币不足 → `InsufficientGoldError` 被抛出且字段正确
- 自购 → `SelfPurchaseError`
- 挂单失效 → `ListingNotActiveError`
- 找不到玩家 / 物品 / 挂单 → 各自对应的 `NotFoundError` 子类
- 背包满 → `InventoryFullError`
- 输入非法 → `InvalidInputError`
- 数据完整性破坏（比如手改 JSON 把 `item_id` 改成不存在的）→ `DataIntegrityError`

测试模板：

```python
def test_buy_raises_when_buyer_lacks_gold():
    market = make_market_with_listing(price=1000)
    poor_buyer = make_player(gold=500)
    with pytest.raises(InsufficientGoldError) as exc_info:
        market.buy(listing_id="l_001", buyer=poor_buyer)
    assert exc_info.value.context["required"] == 1000
    assert exc_info.value.context["available"] == 500
```

---

## 9. 给负责人（YUXI ZHU）的实施建议

按以下顺序推进，每步完成都可独立提 PR：

1. **[一天]** 在 `src/errors/__init__.py` 实现 §3 的基类 + §4 表中所有子类，每个类带 docstring
2. **[一天]** 在 `src/services/logger.py` 实现 §6.4 的 `log.info / warn / error` 包装
3. **[半天]** 在 `tests/services/test_errors.py` 写"每个异常能被实例化、消息正确、context 正确"的基础单测
4. **[配合开发]** 协助其他模块在抛异常时**用对类**——别人 PR review 时帮忙看一眼

> **遇到拿不准的地方**：直接在群里问，或开 issue 讨论，不要默默自己改设计。
> 接口一旦发布，改起来要协调全组，所以宁可多问一句。
