from __future__ import annotations

from pathlib import Path

from src.services.logger import Log


def test_log_writes_to_file(tmp_path, capsys):
    log_file = tmp_path / "operation.log"
    logger = Log(log_file=str(log_file))

    logger.info("test", "created", player_id="p_001")

    out = capsys.readouterr().out
    assert "[INFO]" in out
    assert log_file.exists()
    assert "player_id='p_001'" in log_file.read_text(encoding="utf-8")


def test_log_appends_instead_of_overwrite(tmp_path):
    log_file = tmp_path / "operation.log"
    logger = Log(log_file=str(log_file))

    logger.info("test", "first")
    logger.warn("test", "second")

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "[INFO]" in lines[0]
    assert "[WARN]" in lines[1]


def test_log_creates_parent_directory(tmp_path):
    log_file = tmp_path / "nested" / "logs" / "operation.log"
    logger = Log(log_file=str(log_file))

    logger.info("test", "mkdir")

    assert log_file.exists()


def test_log_ignores_oserror(tmp_path):
    blocker = tmp_path / "blocked"
    blocker.write_text("not a directory", encoding="utf-8")
    log_file = blocker / "operation.log"
    logger = Log(log_file=str(log_file))

    logger.info("test", "oserror")

    assert blocker.read_text(encoding="utf-8") == "not a directory"


def test_warn_and_error_go_to_stderr(tmp_path, capsys):
    log_file = tmp_path / "operation.log"
    logger = Log(log_file=str(log_file))

    logger.warn("test", "warn_event")
    logger.error("test", "error_event")

    captured = capsys.readouterr()
    assert "[WARN]" in captured.err
    assert "[ERROR]" in captured.err


def test_debug_and_info_go_to_stdout(tmp_path, capsys):
    log_file = tmp_path / "operation.log"
    logger = Log(log_file=str(log_file))

    logger.debug("test", "debug_event")
    logger.info("test", "info_event")

    captured = capsys.readouterr()
    assert "[DEBUG]" in captured.out
    assert "[INFO]" in captured.out


def test_context_keys_are_sorted_in_output(tmp_path):
    log_file = tmp_path / "operation.log"
    logger = Log(log_file=str(log_file))

    logger.info("test", "sorted_context", z=3, a=1, m=2)

    line = log_file.read_text(encoding="utf-8").splitlines()[0]
    assert line.index("a=1") < line.index("m=2") < line.index("z=3")
