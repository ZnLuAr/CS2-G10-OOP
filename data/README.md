# data/

本目录用于存放程序运行时**自动生成**的数据文件。

> 📌 **数据契约的完整定义请看 [`../docs/data-design.md`](../docs/data-design.md)**——所有字段、关系、业务规则都在那里。本文档只负责"目录用途"与"如何处理这些文件"。

## 文件总览

| 文件 | 内容 |
|------|------|
| `players.json` | 所有玩家及其背包、金币 |
| `items.json` | 物品元数据库 |
| `market.json` | 当前市场上的挂单 |
| `transactions.json` | 历史成交记录 |
| `catalog.json` | 物品分类树 |

> 完整字段定义见 [`../docs/data-design.md`](../docs/data-design.md)。

## 注意

- 本目录中除 `.gitkeep` 和本 README 外，**所有文件都不会被提交**（已在 `.gitignore` 中配置）。
- 程序首次运行时会自动生成初始数据集；后续运行加载并更新已有数据。
- 如需重置数据，删除本目录下的 `*.json` 文件即可，下次运行会重新生成。
