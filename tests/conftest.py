"""pytest 适配器：@pytest.mark.fn -> suite 契约的 .state/trace.json。"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


def _bootstrap_env_test() -> None:
    """pytest-django 触碰 settings 前，把 .env.test（已入库测试夹具，fastapi 先例）
    灌进 os.environ——settings fail-fast 无兜底（suite-hard-rules §1），
    已设键不覆盖（显式 env 优先）。与 scripts/mypy-django.py 同款逻辑。"""
    env_file = Path(__file__).resolve().parent.parent / ".env.test"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_bootstrap_env_test()


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """DB-First：family schema 归 drizzle SSOT，django 侧全 managed=False 消费。
    不建 test 库、不跑 migrate/create——pytest-django 默认 setup_databases 会
    run_syncdb 把 django 自带 managed 表建进 saas_test（禁常驻第 4 类库）。
    只验连通；事务回滚由 django_db 的 atomic 包装承担。"""
    from django.db import connection

    with django_db_blocker.unblock():
        connection.ensure_connection()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "fn(id, ...): 该测试验证的功能子项 ID，如 @pytest.mark.fn('M01.F01.I14')"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("TRACE_MAP") != "1":
        return
    entries = []
    for item in items:
        fns: list[str] = []
        for marker in item.iter_markers(name="fn"):
            fns.extend(str(a) for a in marker.args)
        inert = any(item.get_closest_marker(n) is not None for n in ("skip", "skipif", "xfail"))
        entries.append(
            {"test": item.nodeid, "fns": [] if inert else sorted(set(fns)), "inert": inert}
        )
    out = Path(str(config.rootpath)) / ".state" / "trace.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps({"schema": 1, "tests": entries}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
