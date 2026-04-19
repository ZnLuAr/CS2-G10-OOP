# 数据系统设计

> 本文档定义**全部持久化数据实体**的完整设计：字段、关系、生命周期与业务规则。
> **请在新增字段 / 编写模型类 / 修改 JSON 结构前先阅读本文档。**
>
> 涵盖实体：Player（玩家）/ Inventory（背包）/ Listing（挂单）/ Transaction（交易记录）/ Catalog（分类树）/ Item（物品）。

---

## 1. 设计目标

游戏装备交易系统围绕"玩家持有物品、挂单交易"展开，需兼顾：

- **OOP 多态**：用抽象基类 + 子类反映物品大类的差异
- **数据结构演示**：双向链表（背包）/ BST（按价格查挂单）/ HashMap（按 ID 查询）/ Tree（分类）/ Stack（撤销）/ Queue（批量结算）都有合理落点
- **可扩展性**：新增物品类型 / 字段时不破坏既有逻辑
- **数据契约稳定**：JSON 字段命名一旦发布，不轻易破坏向后兼容

---

## 2. 实体关系总览

```
Player ───持有───▶ Inventory ───包含───▶ Item
   │                                       │
   │                                       │
   └──挂单────▶ Listing ──引用──────────────┘
                    │
                    ↓
                Transaction ──引用──▶ Item / Player(buyer/seller)
```

- **Player → Inventory**：组合关系，Inventory 是 Player 的一部分
- **Inventory → Item**：通过 `item_id` 引用 `items.json` 中的元数据，避免重复存储
- **Listing → Item**：同上
- **Transaction → Item / Player**：冗余存储 `item_id` / `buyer_id` / `seller_id`，使历史记录独立可查
- **Catalog**：与 `Item.category` 的点号路径一一对应

---

## 3. Player 玩家

### 3.1 字段表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `player_id` | `str` | ✅ | 形如 `p_001` |
| `name` | `str` | ✅ | 昵称，长度 1–20，允许重名（以 ID 为准） |
| `gold` | `int` | ✅ | 当前金币（≥ 0） |
| `level` | `int` | ✅ | 玩家等级（≥ 1，初始 1） |
| `class` | `str` | ✅ | 职业（详见 §3.3） |
| `inventory` | `list[InventorySlot]` | ✅ | 背包，详见 §4 |
| `created_at` | `str` | ✅ | ISO 8601 时间戳 |

### 3.2 业务规则

- 删除玩家前必须：背包为空、无活跃挂单
- 金币只能通过交易 / 调试指令变动；任何变动都需走 `Player.add_gold / spend_gold` 方法
- `level` 当前不消耗经验自动升级，仅为门槛字段；可通过调试指令调整

### 3.3 职业取值（待会议确认）

> 暂定 5 个，最终列表见 §11 待讨论项：`warrior` / `archer` / `mage` / `summon` / `none`（无职业 / 通用）

### 3.4 JSON 示例

```json
{
  "players": [
    {
      "player_id": "p_001",
      "name": "Arthur",
      "gold": 1500,
      "level": 12,
      "class": "warrior",
      "inventory": [
        { "item_id": "i_001", "count": 1 },
        { "item_id": "i_031", "count": 5 }
      ],
      "created_at": "2026-04-19T10:00:00Z"
    }
  ]
}
```

---

## 4. Inventory 背包

### 4.1 设计要点

- **存储结构**：内存中以**自实现的双向链表**保存背包条目（节点顺序即拾取顺序）
- **JSON 表示**：序列化时落为 `Player.inventory` 数组，每个元素是 `InventorySlot`
- **容量上限**：每个玩家 `INVENTORY_CAPACITY = 50`（格数，而非物品总数）

### 4.2 InventorySlot 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `item_id` | `str` | ✅ | 引用 `items.json` 中的物品元数据 |
| `count` | `int` | ✅ | 当前数量；不可堆叠物品恒为 1 |
| `instance_state` | `object` | ⭕ | 实例化状态（如当前耐久 / 是否穿戴），仅可变属性才写入 |

> **元数据 vs 实例状态**：`items.json` 存的是"物品定义"（不变），`instance_state` 存的是"这件物品在该玩家手上的当前状态"（耐久衰减、穿戴标志等）。可堆叠物品天然无 `instance_state`。

### 4.3 业务规则

- 入库流程：可堆叠物品先尝试合入既有格，未填满则填到 `stack_size_max`；溢出部分新建一格；新建会占用一格容量
- 容量满且无法继续合堆叠时**拒绝**入库并抛 `InventoryFullError`
- 删除 / 移除遵循双向链表 O(1) 删除（已知节点引用）

---

## 5. Listing 挂单

### 5.1 字段表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `listing_id` | `str` | ✅ | 形如 `l_001` |
| `seller_id` | `str` | ✅ | 卖家 `player_id` |
| `item_id` | `str` | ✅ | 物品元数据 ID |
| `count` | `int` | ✅ | 出售数量（不可堆叠物品恒为 1） |
| `price` | `int` | ✅ | 单价（≥ 1） |
| `instance_state` | `object` | ⭕ | 上架瞬间的实例状态快照（耐久等） |
| `status` | `str` | ✅ | `active` / `sold` / `cancelled` |
| `created_at` | `str` | ✅ | 上架时间 |
| `closed_at` | `str` | ⭕ | 成交 / 撤销时间 |

### 5.2 业务规则

- 创建挂单时：物品从背包**移出**（不再占格），进入 `market.json`
- 状态机：`active → sold` / `active → cancelled`，**不可逆**
- 同一物品实例**不能重复挂单**（已挂单的就不在背包里）
- 撤销 / 未成交时退回卖家背包；若届时背包已满，挂单**保持 active 状态**并提示用户先腾位

### 5.3 与数据结构的对应

- **BST**：`market` 中维护以 `price` 为键的二叉搜索树，支持范围查询
- **HashMap**：以 `listing_id` 为键支持 O(1) 查询
- **Tree**：按 `Catalog` 树筛选时用到树遍历

---

## 6. Transaction 交易记录

### 6.1 字段表

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `transaction_id` | `str` | ✅ | 形如 `t_001` |
| `listing_id` | `str` | ✅ | 来源挂单 ID（追溯用） |
| `buyer_id` | `str` | ✅ | 买家 `player_id` |
| `seller_id` | `str` | ✅ | 卖家 `player_id` |
| `item_id` | `str` | ✅ | 物品元数据 ID |
| `count` | `int` | ✅ | 成交数量 |
| `price` | `int` | ✅ | 成交单价 |
| `total` | `int` | ✅ | 成交总金额 = `count * price` |
| `completed_at` | `str` | ✅ | 成交时间 |

### 6.2 设计取舍

- **冗余存储 buyer/seller/item 信息**：交易记录是历史档案，需独立可读，即使原始挂单 / 玩家被删也不丢失；牺牲少量空间换可追溯性
- **只追加、不修改**：`transactions.json` 是 append-only，不允许覆盖既有记录
- **入队结算**：管理员模式批量结算挂单时使用自实现的 Queue（FIFO），演示队列结构

---

## 7. Catalog 物品分类树

### 7.1 数据形态

`catalog.json` 是一棵**根→大类→子类**的两层树，与 `Item.category` 的点号路径一一对应。

```json
{
  "root": {
    "key": "root",
    "label": "全部",
    "children": [
      {
        "key": "weapon",
        "label": "武器",
        "children": [
          { "key": "sword", "label": "剑", "children": [] },
          { "key": "bow", "label": "弓弩", "children": [] }
        ]
      },
      {
        "key": "misc",
        "label": "杂项",
        "children": []
      }
    ]
  }
}
```

### 7.2 设计要点

- 用**自实现的 Tree** 加载到内存
- 浏览菜单通过**递归遍历**渲染（OOP 作业必考点之一）
- `Item.category` 形如 `"weapon.sword"`，路径与树节点的 `key` 链对齐
- 分类结构相对稳定，运行时一般不修改；新增大类 / 子类需同步更新 `catalog.json` 与 §8.1

---

## 8. Item 物品（核心实体）

> Item 是字段最多、子类最丰富的实体，单独占一节展开。

### 8.1 分类体系

#### 8.1.1 五大类

| 大类 | 英文键 | 子分类 |
|------|--------|--------|
| 武器 | `weapon` | 剑 `sword`、弓弩 `bow`、长矛 `spear`、重锤 `hammer`、长戟 `halberd` |
| 工具 | `tool` | 斧 `axe`、镐 `pickaxe`、锹 `shovel`、锄 `hoe` |
| 装备 | `armor` | 头盔 `helmet`、胸甲 `chestplate`、护胫 `greaves`、靴子 `boots`、盾牌 `shield` |
| 消耗品 | `consumable` | 药水 `potion`、食物 `food`、魔法物品 `magic`、材料 `material` |
| 杂项 | `misc` | （无子分类） |

#### 8.1.2 `category` 字段格式

- 形如 `"weapon.sword"` / `"armor.helmet"` / `"misc"`
- 与 `catalog.json` 树的根→叶路径一一对应（详见 §7）

### 8.2 类层次结构（OOP 设计）

```
Item (abstract)
├── Weapon
│   ├── Sword
│   ├── Bow
│   ├── Spear
│   ├── Hammer
│   └── Halberd
├── Tool
│   ├── Axe
│   ├── Pickaxe
│   ├── Shovel
│   └── Hoe
├── Armor
│   ├── Helmet
│   ├── Chestplate
│   ├── Greaves
│   ├── Boots
│   └── Shield
├── Consumable
│   ├── Potion
│   ├── Food
│   ├── Magic
│   └── Material
└── Misc
```

#### 8.2.1 抽象基类 `Item`

| 成员 | 类型 | 说明 |
|------|------|------|
| `item_id` | `str` | 唯一 ID |
| `name` | `str` | 名称 |
| `category` | `str` | 分类路径 |
| `rarity` | `str` | 稀有度 |
| `base_value` | `int` | 基础价值 |
| `to_dict()` | `dict` | 序列化为 JSON 可存储格式 |
| `from_dict()` | `Item` | （类方法 / 工厂）按 `category` 反序列化为正确子类 |
| `describe()` | `str` | 人类可读的描述（被各子类多态实现） |

#### 8.2.2 中间基类（按业务规则归并）

| 基类 | 引入字段 / 行为 | 子类 |
|------|----------------|------|
| `Durable` mixin | 耐久度（`durability` / `durability_max`） | Weapon、Tool、Armor |
| `Equippable` mixin | 穿戴状态（`equipped`、`slot`） | Weapon、Armor |
| `Stackable` mixin | 堆叠（`count`、`stack_size_max`） | Consumable、Misc |

> **设计取舍**：用组合（mixin / 接口）而非深层继承，避免菱形继承。
> 详见 `docs/dev-materials-for-report/design-decisions.md` 中相应条目（待补充）。

### 8.3 通用字段约定

#### 8.3.1 顶层字段（所有物品都有）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `item_id` | `str` | ✅ | 形如 `i_001` |
| `name` | `str` | ✅ | 长度 1–32 |
| `category` | `str` | ✅ | 详见 §8.1 |
| `rarity` | `str` | ✅ | `common` / `uncommon` / `rare` / `epic` / `legendary` |
| `base_value` | `int` | ✅ | 系统基础价值（≥ 0） |
| `description` | `str` | ⭕ | 物品说明文字，长度 0–200；缺省时 `describe()` 仅返回名称与基础信息 |
| `stats` | `object` | ✅ | 因子类不同而异，详见 §8.4 |

#### 8.3.2 `stats` 中的横切字段

- **耐久度** `durability` / `durability_max`
  - 适用：武器 / 工具 / 装备
  - 创建时 `durability == durability_max`
  - 耐久 = 0 的物品**不能挂单**，可以保留在背包中
  - 后续可扩展"修理"功能

- **堆叠** `count` / `stack_size_max`
  - 适用：消耗品 / 杂项
  - 同一 `item_id` 的可堆叠物品在背包中合并为一格节点
  - 当一格达到 `stack_size_max` 上限后，超出部分**自动新建一格**（同 `item_id` 可在背包中占多格）
  - 若背包已满（达容量上限）且无可堆叠的余位，则**拒绝**入库并提示
  - 挂单时按 `count` 拆分（出售 N 个，背包剩 `total - N`）

- **穿戴** `equipped`（默认 `false`）+ `slot`
  - 适用：武器 / 装备
  - 已穿戴的物品**不能挂单 / 不能丢弃**，需先脱下
  - 同一穿戴位互斥（同时只能穿一个头盔、一把武器等）

- **使用门槛** `level_req` / `class_req`
  - 适用：武器 / 工具 / 装备（可选，缺省视为无限制）
  - `level_req: int`，玩家等级低于该值时**不能穿戴 / 不能使用**，但仍可持有与交易
  - `class_req: list[str]`，限定职业；空列表或缺省视为全职业可用

### 8.4 各分类 `stats` 字段表

#### 8.4.1 武器 `weapon.*`

| 字段 | 类型 | 说明 |
|------|------|------|
| `attack` | `int` | 基础攻击力 |
| `attack_speed` | `float` | 攻击速度（每秒次数，参考值） |
| `durability` | `int` | 当前耐久 |
| `durability_max` | `int` | 满耐久 |
| `equipped` | `bool` | 是否已穿戴 |
| `slot` | `str` | 固定为 `"weapon"`（预留主副手扩展） |

##### 子类微调建议（不强制写入 stats，仅为生成种子数据时参考）

| 子类 | 攻击范围 | 备注 |
|------|----------|------|
| `sword` | 中 | 攻速较快，单体伤害适中 |
| `bow` | 远 | 攻速中等，可远程 |
| `spear` | 中长 | 攻速慢，刺穿伤害 |
| `hammer` | 短 | 攻速最慢，单击伤害最高 |
| `halberd` | 长 | 攻速慢，可范围 |

#### 8.4.2 工具 `tool.*`

| 字段 | 类型 | 说明 |
|------|------|------|
| `efficiency` | `float` | 工作效率（采集 / 砍伐倍率） |
| `tier` | `int` | 适用等级（1=木 / 2=石 / 3=铁 / 4=金 / 5=钻石） |
| `durability` | `int` | 当前耐久 |
| `durability_max` | `int` | 满耐久 |

> 工具无 `equipped`，使用时按需取出。

#### 8.4.3 装备 `armor.*`

| 字段 | 类型 | 说明 |
|------|------|------|
| `defense` | `int` | 物理防御 |
| `magic_resist` | `int` | 魔法抗性 |
| `slot` | `str` | 穿戴位（与子类一一对应：`helmet`/`chestplate`/`greaves`/`boots`/`shield`） |
| `durability` | `int` | 当前耐久 |
| `durability_max` | `int` | 满耐久 |
| `equipped` | `bool` | 是否已穿戴 |

#### 8.4.4 消耗品 `consumable.*`

| 字段 | 类型 | 说明 |
|------|------|------|
| `effect` | `str` | 效果类型（如 `heal` / `mana` / `buff_attack` / `restore_durability`） |
| `power` | `int` | 效果数值（恢复量 / 增益值） |
| `duration` | `int` | 持续时间（秒；瞬时填 0） |
| `stack_size_max` | `int` | 单格最大堆叠 |
| `count` | `int` | 当前数量 |

##### 子类专属字段

| 子类 | 额外字段 | 说明 |
|------|----------|------|
| `potion` | — | 通常瞬时生效，`duration = 0` |
| `food` | `nutrition: int` | 饱食度恢复值 |
| `magic` | `mana_cost: int` | 使用消耗的法力值 |
| `material` | — | 通常仅用于交易 / 制作，`effect` 可为 `none` |

#### 8.4.5 杂项 `misc`

| 字段 | 类型 | 说明 |
|------|------|------|
| `stack_size_max` | `int` | 单格最大堆叠 |
| `count` | `int` | 当前数量 |

> 杂项物品无功能性属性，仅用于剧情 / 收藏 / 交易。说明文字使用顶层 `description` 字段（详见 §8.3.1）。

### 8.5 完整 JSON 示例

```json
{
  "items": [
    {
      "item_id": "i_001",
      "name": "物理学圣剑",
      "category": "weapon.sword",
      "rarity": "legend",
      "base_value": 1200,
      "stats": {
        "attack": 85,
        "attack_speed": 1.4,
        "durability": 100,
        "durability_max": 100,
        "equipped": false,
        "slot": "weapon"
      }
    },
    {
      "item_id": "i_011",
      "name": "恋人を射ち堕とす",
      "category": "weapon.bow",
      "rarity": "epic",
      "base_value": 0,
      "description": "愛する人を失った世界には、どんな色の花が咲くだろう？",
      "stats": {
        "attack": 514,
        "durability": 1,
        "durability_max": 1,
        "stack_size_max": 1,
        "slot": "weapon"
      }
    },
    {
      "item_id": "i_021",
      "name": "铁镐",
      "category": "tool.pickaxe",
      "rarity": "common",
      "base_value": 80,
      "stats": {
        "efficiency": 1.5,
        "tier": 3,
        "durability": 200,
        "durability_max": 200
      }
    },
    {
      "item_id": "i_031",
      "name": "神圣水桶",
      "category": "armor.helmet",
      "rarity": "epic",
      "base_value": 120,
      "stats": {
        "defense": 1,
        "magic_resist": 1,
        "slot": "helmet",
        "durability": 800,
        "durability_max": 800,
        "equipped": false
      }
    },
    {
      "item_id": "i_041",
      "name": "生命药水(小)",
      "category": "consumable.potion",
      "rarity": "common",
      "base_value": 50,
      "stats": {
        "effect": "heal",
        "power": 100,
        "duration": 0,
        "stack_size_max": 16,
        "count": 5
      }
    },
    {
      "item_id": "i_051",
      "name": "唢呐",
      "category": "misc",
      "rarity": "legend",
      "base_value": 10,
      "description": "把尼曼愉悦送走",
      "stats": {
        "stack_size_max": 1,
        "count": 1
      }
    }
  ]
}
```

### 8.6 物品的生命周期

```
   [生成]
     │  种子数据 / 管理员创建
     ↓
   [入库] → items.json 注册元数据
     │
     ↓
   [被持有] → 进入某玩家的 Inventory
     │
     ├──→ [穿戴] ⇄ [脱下]    （仅武器 / 装备）
     │
     ├──→ [使用] → 消耗 1（消耗品）/ 损耗耐久（武器 / 工具 / 装备）
     │
     ├──→ [挂单] → 离开背包，进入 market.json
     │      │
     │      ├──→ [撤销] → 退回背包
     │      └──→ [成交] → 转入买家背包，写入 transactions.json
     │
     └──→ [丢弃 / 销毁] → 从背包移除（可选功能）
```

### 8.7 业务规则交叉表

| 操作 | 武器 | 工具 | 装备 | 消耗品 | 杂项 |
|------|:----:|:----:|:----:|:------:|:----:|
| 可堆叠 | ❌ | ❌ | ❌ | ✅ | ✅ |
| 有耐久 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 可穿戴 | ✅ | ❌ | ✅ | ❌ | ❌ |
| 耐久=0 是否能挂单 | ❌ | ❌ | ❌ | — | — |
| 已穿戴是否能挂单 | ❌ | — | ❌ | — | — |
| 已穿戴是否能丢弃 | ❌ | — | ❌ | — | — |

---

## 9. 命名与 ID 规则（全实体）

| 实体 | ID 前缀 | 示例 | 上限 |
|------|---------|------|------|
| Player | `p_` | `p_001` | `p_9999` |
| Item | `i_` | `i_001` | `i_9999` |
| Listing | `l_` | `l_001` | `l_9999` |
| Transaction | `t_` | `t_001` | `t_99999` |

- ID 由 `services/persistence.py` 在加载时维护自增计数器，新增实体时分配
- 时间戳一律使用 ISO 8601 UTC 格式（`2026-04-19T10:00:00Z`）
- 字符串枚举值（`rarity` / `class` / `status` / `slot` 等）一律小写
- JSON 中字段名一律 `snake_case`
- Python 子类类名与英文键 PascalCase 化（`sword` → `Sword`）

---

## 10. 字段变更流程

新增 / 修改字段时：

1. 先在本文档对应章节写入字段定义
2. 同步更新对应模型类的 `to_dict / from_dict`
3. 在 `docs/dev-materials-for-report/design-decisions.md` 写一条决策记录（变更原因）
4. 写一条 `docs/dev-materials-for-report/development-log.md` 条目
5. 如改动破坏既有 JSON 结构，需同步更新种子数据脚本

---

## 11. 待讨论项

### 已确定（2026-04-19）

- ✅ **消耗品堆叠到上限后**：超出部分新建一格；若背包已满则拒绝入库
- ✅ **物品使用门槛**：引入 `level_req`（等级要求）与 `class_req`（职业要求）字段，详见 §8.3.2

### 待讨论

- [ ] 穿戴位是否区分主手 / 副手 / 双手武器？（影响 `slot` 取值与穿戴互斥规则）
- [ ] 是否引入"附魔 / 词条"系统（可变长属性 list，附加于已有装备 / 武器之上）？
- [ ] 玩家职业取值集合（暂列 `warrior` / `archer` / `mage` / `rogue` / `none`，需最终敲定）
- [ ] `level` 是否需要经验值字段（`exp`）支撑升级，还是仅作为门槛字段手动调整？

> 讨论结果请同步到 `docs/dev-materials-for-report/design-decisions.md`，并回填到本文档。
