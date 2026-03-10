"""launchd 配置生成。"""

from __future__ import annotations

from pathlib import Path


def build_launchd_plist(
    label: str,
    project_root: Path,
    python_executable: str,
    hour: int = 9,
    minute: int = 0,
) -> str:
    """生成 launchd plist 内容。"""

    script_path = project_root / "scripts" / "run_scheduler_once.sh"
    stdout_path = project_root / "logs" / "launchd.stdout.log"
    stderr_path = project_root / "logs" / "launchd.stderr.log"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>{label}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_executable}</string>
    <string>{project_root / "run_ai_radar.py"}</string>
    <string>--mode</string>
    <string>scheduler</string>
  </array>
  <key>WorkingDirectory</key>
  <string>{project_root}</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>{hour}</integer>
    <key>Minute</key>
    <integer>{minute}</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>{stdout_path}</string>
  <key>StandardErrorPath</key>
  <string>{stderr_path}</string>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PYTHONPATH</key>
    <string>{project_root}</string>
  </dict>
</dict>
</plist>
"""
