# 测试与调试笔记

> 记录测试中发现的问题、定位过程、修复方式。
> 报告要求至少描述一个"重大问题的诊断与解决"，本文档是素材库。

---

## 测试思路与策略

> 本节记录我们写测试时的总体思路，便于后续成员（XINGZHOU / JIAFENG / KE / DI / RUNFENG）
> 在为自己模块补测试时保持一致的风格。

### 1. 组织方式：按"行为场景"而非"被测函数"分类

每个测试文件用若干 `class TestXxx:` 把用例分组，类名描述**一组场景**而不是一个方法。

例如 `tests/services/test_persistence.py`:

| 测试类                | 关心的问题                                |
|-----------------------|-------------------------------------------|
| `TestSeedIfEmpty`     | 首次运行能否生成数据、是否幂等            |
| `TestLoadAll`         | 加载后内存模型类型是否正确                |
| `TestRoundTrip`       | save → load 之后数据是否等价              |
| `TestIdCounters`      | ID 自增是否从最大值继续、是否独立         |
| `TestIntegrityCheck`  | 外键损坏是否抛 `DataIntegrityError`       |
| `TestErrorPaths`      | 坏 JSON / 缺字段是否抛 `SerializationError` |
| `TestBackupAndReset`  | 备份 / 重置是否生效                       |

`tests/test_app.py` 同理：`TestBootstrap` / `TestBanner` / `TestShutdown` / `TestRun`。

这种分组的好处：报告/答辩时可以直接按"场景"讲，"我针对 *持久化* 测了 7 个场景"
比"我测了 19 个函数"更有说服力。

### 2. 用 fixture 隔离副作用

所有涉及文件系统的测试都用 pytest 内置的 `tmp_path`，永远不动项目根目录的 `data/`：

```python
@pytest.fixture
def data_dir(tmp_path):
    return str(tmp_path / "data")

@pytest.fixture
def fresh_persistence(data_dir):
    p = Persistence(data_dir=data_dir)
    p.seed_if_empty()
    return p
```

每个测试拿到的都是一个**全新的**临时目录，互不影响。运行 `pytest` 时哪怕中途 Ctrl+C，
也不会污染真实数据。

### 3. 用依赖注入把"难以触发的场景"变成普通函数调用

`App.__init__` 接受一个 `ui_runner` 回调，默认是真正的 CLI；测试里直接塞一个假函数：

```python
def test_keyboard_interrupt_returns_zero(self, app):
    def interrupt(a):
        raise KeyboardInterrupt
    app.ui_runner = interrupt
    assert app.run() == 0
```

如果 UI 写死在 `App.run` 里，要测 `KeyboardInterrupt` 兜底就只能去模拟键盘事件——
依赖注入让它退化成一行 `raise`。同样的思路也用在测 `RuntimeError` / `DataIntegrityError`
两条异常分支上。

### 4. 抓输出用 `capsys`，不要 `print` 一通靠肉眼看

`show_banner()` / 错误信息 / 启动提示都通过 `capsys.readouterr()` 拿到再断言：

```python
def test_banner_includes_name_version_and_counts(self, app, capsys):
    app.bootstrap()
    app.show_banner()
    out = capsys.readouterr().out
    assert PROGRAM_NAME in out and VERSION in out
```

注意只断言**关键字段是否出现**，不断言完整字符串——后者会让以后改一个空格就挂一片测试。

### 5. 异常断言：抓类型 + context，不抓 message

服务层只抛、不翻译；UI 层才把异常翻译成给用户看的中文。所以测试里**只验证异常类型和
结构化字段**，不验证给人看的 message：

```python
with pytest.raises(DataIntegrityError) as exc:
    fresh_persistence.load_all()
assert exc.value.context["ref_id"] == "i_999999"
```

这样以后产品想换措辞，不用动一行测试代码。

### 6. 分层：单元 → 模块 → 端到端

| 层级       | 现状                      | 谁负责                       |
|------------|---------------------------|------------------------------|
| 单元测试   | `test_errors.py` (44 例)  | YUXI                         |
| 模块测试   | `test_persistence.py` (19 例) / `test_app.py` (10 例) | YUXI |
| 端到端测试 | 暂缓                      | 等 UI 落地后由 KE / DI 补    |

端到端测试要等到主菜单 (功能 ID 6-9) 写完才有意义，现在写只能 mock 一切，价值不大。

### 7. 故意"不测"的部分（要在报告里讲清楚）

- **种子数据的具体内容**：只测最少数量（>=10 玩家、>=50 物品、>=20 挂单），
  不测某玩家叫什么名字——这种测试每次改种子都要改测试，不值。
- **软警告 print**：`_validate_integrity` 里 transaction 引用过期 listing 只 print，
  没拦截。等 logger 落地后改成 `log.warn`，再加测试断言日志记录。
- **Item / Catalog 的领域行为**：`Persistence` 暂时把它们当 dict 处理，
  等 JIAFENG 的 Item 多态层和 XINGZHOU 的 CatalogTree 落地后，
  由各自负责人补测试，不在 YUXI 这里覆盖。

### 8. CLI 与 logger 测试补强经验

这一轮我们没有新增业务功能，而是专门把**已有功能的回归保护补扎实**。

#### 8.1 不再满足于 `len(out) > 0`

CLI 测试早期很多都只是断言“有输出”，这种写法能防止程序崩掉，但防不住：

- 表头字段丢失
- 菜单标题改错
- 输出列顺序变乱
- 报表进入了错误分支但仍然打印了一些东西

所以后续测试尽量改成**断言关键字段**，例如：

- 富豪榜：`排名 / 玩家 / 金币`
- 交易额榜：`排名 / 玩家 / 成交额`
- 系统快照：`总玩家数 / 总物品数`
- 物品成交历史：`买家= / 卖家=`

这样即使输出格式有轻微调整，也能较稳定地保护功能语义。

#### 8.2 大列表输出要测“显示上限”

CLI 不是网页，没有滚动容器；如果一口气把上百条成交记录全打出来，用户很难读。

因此我们在历史报表里约定：

- 最多显示前 20 条
- 若还有剩余，显示 `还有 N 条未显示`

对应测试要覆盖：

1. 注入 25+ 条样例交易
2. 断言输出里出现“还有 5 条未显示”
3. 确认不是直接全量打印

这种测试的价值在于，它保护的是**交互体验约束**，而不是纯粹的业务逻辑。

#### 8.3 日志测试要分三层验证

logger 不只是“能调一下方法”就算完成，至少要分别验证：

1. **stdout / stderr 分流**
   - `INFO/DEBUG -> stdout`
   - `WARN/ERROR -> stderr`
2. **文件落盘**
   - `data/operation.log` / 临时文件确实被 append 写入
3. **context 稳定性**
   - `context` key 排序稳定，避免日志顺序随机导致测试不稳

这也是为什么 `tests/services/test_logger.py` 里不只测“文件存在”，还测：

- append 而非 overwrite
- 自动建目录
- `OSError` 静默失败
- key 顺序稳定

### 9. 跑测试的命令

```bash
python -m pytest                       # 全量
python -m pytest tests/test_app.py     # 单文件
python -m pytest -k "Integrity"        # 按关键字筛
python -m pytest -v                    # 看每个用例名
```

CI 没接，靠提交前本地手跑。

---

## 模板

### [YYYY-MM-DD] 问题标题

- **现象**：观察到的错误行为（报错信息、错误输出截图等）
- **复现步骤**：怎么触发
- **定位过程**：怎么一步步找到原因（用了什么手段：print / debugger / 单元测试 / 代码审查）
- **根因**：真正的原因
- **修复**：怎么改的（指向 commit 或 PR）
- **回归测试**：增加了哪个测试用例防止再发

---

## 笔记

### [YYYY-MM-DD] 示例：背包删除物品时索引错位

- **现象**：删除背包中第 3 个物品后，后续插入的物品出现在错误位置
- **复现步骤**：连续添加 5 个物品 → 删除索引 2 → 再添加 1 个 → 打印背包
- **定位过程**：
  - 单元测试 `test_inventory.py::test_remove_then_insert` 失败
  - 在 `DoublyLinkedList.remove` 添加打印语句，发现 `prev/next` 指针未正确重连
- **根因**：删除尾节点时未更新 `tail` 引用
- **修复**：commit `abc1234`，在 `remove()` 末尾增加 `self.tail = node.prev` 分支
- **回归测试**：新增 `test_remove_tail_updates_tail`

<!-- 在此添加新条目 -->
