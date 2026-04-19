# data/

本目录用于存放程序运行时生成的数据文件。

## 文件总览

| 文件 | 内容 |
|------|------|
| `players.json` | 所有玩家及其背包、金币 |
| `market.json` | 当前市场上的挂单 |
| `transactions.json` | 历史成交记录 |
| `catalog.json` | 物品分类树（如为静态可移到 `src/`） |

## 注意

- 本目录中除 `.gitkeep` 和本 README 外，**所有文件都不会被提交**（已在 `.gitignore` 中配置）。
- 程序首次运行时会自动生成初始数据集；后续运行加载并更新已有数据。
- 如需重置数据，删除本目录下的 `*.json` 文件即可，下次运行会重新生成。

---

## 数据字段约定

> 以下为初版字段设计，开发过程中如有调整请同步更新本文档。
> 字段命名统一使用 `snake_case`，时间戳使用 Unix 时间（整数秒）。

### 通用约定

| 字段 | 类型 | 说明 |
|------|------|------|
| `*_id` | `str` | 唯一标识，建议使用前缀 + 数字（如 `p_001`、`i_042`、`l_007`） |
| `created_at` | `int` | Unix 时间戳（秒） |
| `updated_at` | `int` | Unix 时间戳（秒） |

---

### 1. `players.json` — 玩家

```json
{
  "players": [
    {
      "player_id": "p_001",
      "name": "Koishi",
      "gold": 514,
      "inventory": ["i_001", "i_005", "i_023"],
      "created_at": 1740000000
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `player_id` | `str` | 玩家唯一 ID |
| `name` | `str` | 玩家昵称 |
| `gold` | `int` | 持有金币数量 |
| `inventory` | `list[str]` | 背包中物品 ID 列表（顺序即背包顺序） |
| `created_at` | `int` | 创建时间 |

> **关系**：`inventory` 中的 ID 引用 `items.json` 中的物品。

---

### 2. `items.json` — 物品

> 所有物品的"元数据库"。挂单和背包仅引用 `item_id`，避免重复存储。

```json
{
  "items": [
    {
      "item_id": "i_001",
      "name": "物理学圣剑",
      "category": "weapon.sword",
      "rarity": "legend",
      "base_value": 1200,
      "stats": { "attack": 85, "durability": 100 }
    },
    {
      "item_id": "i_010",
      "name": "皮甲",
      "category": "armor.light",
      "rarity": "common",
      "base_value": 200,
      "stats": { "defense": 30 }
    },
    {
      "item_id": "i_020",
      "name": "生命药水(小)",
      "category": "consumable.potion",
      "rarity": "common",
      "base_value": 50,
      "stats": { "heal": 100, "stack_size": 10 }
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `item_id` | `str` | 物品唯一 ID |
| `name` | `str` | 物品名称 |
| `category` | `str` | 分类路径（点号分隔，对应 `catalog.json` 中的树结构） |
| `rarity` | `str` | `common` / `uncommon` / `rare` / `epic` / `legendary` |
| `base_value` | `int` | 系统基础价值（参考价） |
| `stats` | `object` | 物品属性，因子类不同而异（武器有 `attack`，防具有 `defense`） |

> **多态体现**：`stats` 字段的内容由 `category` 决定，对应不同 `Item` 子类的反序列化逻辑。

---

### 3. `market.json` — 挂单

```json
{
  "listings": [
    {
      "listing_id": "l_001",
      "seller_id": "p_002",
      "item_id": "i_001",
      "price": 1500,
      "status": "active",
      "created_at": 1740000100
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `listing_id` | `str` | 挂单唯一 ID |
| `seller_id` | `str` | 卖家玩家 ID |
| `item_id` | `str` | 出售的物品 ID |
| `price` | `int` | 售价（金币） |
| `status` | `str` | `active` / `sold` / `cancelled` |
| `created_at` | `int` | 挂单时间 |

> **关系**：`seller_id` → `players.json`；`item_id` → `items.json`。
> 已成交或撤销的挂单可保留供历史查询，也可定期清理（待定）。

---

### 4. `transactions.json` — 成交记录

```json
{
  "transactions": [
    {
      "transaction_id": "t_001",
      "listing_id": "l_001",
      "buyer_id": "p_003",
      "seller_id": "p_002",
      "item_id": "i_001",
      "price": 1500,
      "completed_at": 1740000200
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `transaction_id` | `str` | 成交记录唯一 ID |
| `listing_id` | `str` | 来源挂单 ID |
| `buyer_id` | `str` | 买家玩家 ID |
| `seller_id` | `str` | 卖家玩家 ID（冗余存储，便于历史查询时不依赖挂单） |
| `item_id` | `str` | 成交物品 ID |
| `price` | `int` | 实际成交价 |
| `completed_at` | `int` | 成交时间 |

> **关系**：`listing_id` → `market.json`；`buyer_id` / `seller_id` → `players.json`；`item_id` → `items.json`。
> 此文件**只追加不修改**，是价格走势分析的数据源。

---

### 5. `catalog.json` — 物品分类树

> 用于演示**树结构 + 递归遍历**。如果分类是静态的（不会运行时变化），也可以放在 `src/` 内作为代码常量。

```json
{
  "root": {
    "name": "All Items",
    "children": [
      {
        "name": "Weapon",
        "children": [
          { "name": "Sword", "children": [] },
          { "name": "Axe", "children": [] },
          { "name": "Bow", "children": [] }
        ]
      },
      {
        "name": "Armor",
        "children": [
          { "name": "Light", "children": [] },
          { "name": "Heavy", "children": [] }
        ]
      },
      {
        "name": "Consumable",
        "children": [
          { "name": "Potion", "children": [] },
          { "name": "Food", "children": [] }
        ]
      }
    ]
  }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 节点名称 |
| `children` | `list[object]` | 子节点列表（叶子节点为空数组） |

> 物品的 `category` 字段（如 `weapon.sword`）即为根到叶的路径，可由树递归生成或反查。

---

## 字段调整流程

1. 修改本文档，明确"加了什么字段、为什么、影响哪些模块"
2. 在 `docs/design-decisions.md` 中追加一条决策记录
3. 同步修改对应模型类的 `to_dict()` / `from_dict()`
4. 在 `from_dict()` 中为新字段提供默认值，保证旧数据文件能加载（向后兼容）
