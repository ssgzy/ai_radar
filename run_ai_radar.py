"""统一运行 AI Radar 的命令入口。"""

from src.cli import run_cli


if __name__ == "__main__":
    run_cli(default_mode="standard")
