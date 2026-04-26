"""
最小日志服务

职责：
- 提供统一日志入口，避免各模块直接 print
- 控制台输出（INFO/DEBUG → stdout，WARN/ERROR → stderr）
- 同步 append 写入 data/operation.log（功能 ID 56）

文件写入失败时静默忽略，不影响业务流程。
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime

__all__ = ["Log", "log"]


_DEFAULT_LOG_FILE = os.path.join("data", "operation.log")


class Log:
    def __init__(self, log_file: str | None = _DEFAULT_LOG_FILE) -> None:
        self.log_file = log_file

    def _emit(self, level: str, module: str, event: str, **context) -> None:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
        context_str = " ".join(f"{k}={v!r}" for k, v in sorted(context.items()))
        line = f"[{timestamp}] [{level}] [{module}] {event}"
        if context_str:
            line += f" | {context_str}"

        stream = sys.stderr if level in {"ERROR", "WARN"} else sys.stdout
        print(line, file=stream)

        if self.log_file:
            self._write_to_file(line)

    def _write_to_file(self, line: str) -> None:
        # 对于高频的日志操作来说，每次 log.info() 都同步 open + append + close，
        # 会造成相当量的不必要的 I/O 开销。
        # 因为只是个框架，所以我只写这样一个最基础的方法

        # 更成熟的做法可以是，日志内容先进内存 buffer，然后再批量 flush
        # 等到程序退出时统一落盘
        # 或采用后台队列 / logging handler，但这些会引入 flush 时机、异常退出丢日志、测试隔离和并发安全等新的问题

        # 也可以采用 Gemini 在 PR #12 的 Code Review 中提到的办法，
        # 将目录创建逻辑移动到 __init__ 方法中，或者在类中使用一个布尔标记（例如 self._dir_checked）来确保目录仅在初始化或第一次写入时创建一次。
        # 就要等 YUXI 来实现和解决具体的方法和问题了 🙏

        try:
            directory = os.path.dirname(self.log_file) or "."
            os.makedirs(directory, exist_ok=True)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            # 此处捕获 OSError 以确保日志写入失败时不会中断主业务流程。
            # 这里使用 OS Error 而非我们在 error and log design 规定好的错误类型，
            # 是因为经过评估，认为常见的失败原因包括权限不足或磁盘空间不足。
            # OSError 应该是最能覆盖 “日志写入失败” 这一错误场景的。
            # 再者就是文档里没有合适的针对这种场景的错误💦
            # 接下来你也可以做好更合适的错误类型……              ——Zinc
            pass

    def debug(self, module: str, event: str, **context) -> None:
        self._emit("DEBUG", module, event, **context)

    def info(self, module: str, event: str, **context) -> None:
        self._emit("INFO", module, event, **context)

    def warn(self, module: str, event: str, **context) -> None:
        self._emit("WARN", module, event, **context)

    def error(self, module: str, event: str, **context) -> None:
        self._emit("ERROR", module, event, **context)


log = Log()
