"""
最小日志服务

当前阶段先提供统一日志入口，避免各模块直接 print。
后续若需要写入 data/operation.log，可在此扩展。
"""

from __future__ import annotations

from datetime import datetime
import sys

__all__ = ["Log", "log"]




class Log:
    def _emit(self, level: str, module: str, event: str, **context) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        context_str = " ".join(f"{k}={v!r}" for k, v in sorted(context.items()))
        line = f"[{timestamp}] [{level}] [{module}] {event}"
        if context_str:
            line += f" | {context_str}"

        stream = sys.stderr if level in {"ERROR", "WARN"} else sys.stdout
        print(line, file=stream)

    def debug(self, module: str, event: str, **context) -> None:
        self._emit("DEBUG", module, event, **context)

    def info(self, module: str, event: str, **context) -> None:
        self._emit("INFO", module, event, **context)

    def warn(self, module: str, event: str, **context) -> None:
        self._emit("WARN", module, event, **context)

    def error(self, module: str, event: str, **context) -> None:
        self._emit("ERROR", module, event, **context)


log = Log()
