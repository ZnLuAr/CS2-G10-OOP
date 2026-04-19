# docs: 添加文档目录说明及 PR 流程示例

---

# PR Body

## 概述

为项目搭建基础工程化配置，统一多人协作环境，并建立协作规范文档。

本 PR 主要完成两件事：

- **协作规范**：在 `README.md` 中编写 PR 引导，然后好像就没什么事了（

- 同时作为一个 **Pull Request 流程示例**

---

## 变更文件

```
docs/README.md   新增  文档目录说明 + PR 流程演示载体
docs/README.md   新增  文档目录说明 + PR 流程演示载体
docs/README.md   新增  为什么会有这么多 docs/README.md 😡
```

### 文件变更统计

```
1 files changed, 34 insertions(+)
```

---

## 详细说明

### 1. `docs/README.md` — 文档目录

作为 `docs/` 目录的占位说明文件，后续用于存放报告素材、设计文档等。

在本次 PR 中同时承担**流程演示**的角色——让组员通过实际的 PR 页面了解 GitHub 协作流程。

### 2. `docs/README.md` — 文档目录

作为 `docs/` 目录的占位说明文件，再占个位

### 3. `docs/README.md` — 文档目录

作为 `docs/` 目录的占位说明文件，再蹲个坑

---

## 附：PR 流程简要说明

> 以下内容简要解释本次操作对应的流程。

```
① 从目标分支创建新分支
   main ──→ feat/pull-request-example-by-zn

② 在新分支上完成修改，commit 并 push
   git add → git commit → git push

③ 在 GitHub 上创建 Pull Request，填写变更说明（就是你现在看到的这个页面）

④ 组员 Review：查看改了什么，有没有问题

⑤ 确认无误后，合并到目标分支
   feat/pull-request-example-by-zn ──→ main
```

> 对于我们这个项目，日常开发直接在 `dev` 上推送即可，不必每次都走 PR。
> PR 更适合用在**较大的改动**或**需要大家确认的内容**上。

---

## Checklist

- [x] `.gitignore` 覆盖 Python 缓存、虚拟环境、IDE 配置、运行时数据
- [x] `.gitattributes` 配置换行符自动处理与二进制文件标记
- [x] `.editorconfig` 统一缩进、编码、换行设置
- [x] `docs/README.md` 目录说明已创建
- [x] `README.md` 协作规范已编写（先前提交）
- [x] 未提交任何不应纳入版本控制的文件
