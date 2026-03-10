"""调度配置生成测试。"""

from pathlib import Path

from src.schedulers import build_cron_entry, build_launchd_plist


def test_build_cron_entry_contains_scheduler_script():
    """验证 cron 配置引用调度脚本。"""

    entry = build_cron_entry(project_root=Path("/tmp/ai_radar"), hour=7, minute=15)

    assert "15 7 * * *" in entry
    assert "run_scheduler_once.sh" in entry


def test_build_launchd_plist_contains_scheduler_mode():
    """验证 launchd 配置调用 scheduler 模式。"""

    plist = build_launchd_plist(
        label="local.ai_radar.scheduler",
        project_root=Path("/tmp/ai_radar"),
        python_executable="/usr/bin/python3",
        hour=8,
        minute=30,
    )

    assert "<string>scheduler</string>" in plist
    assert "<string>/tmp/ai_radar/run_ai_radar.py</string>" in plist
