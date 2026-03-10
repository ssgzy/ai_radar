# 调度说明

当前版本已完成 V4 的调度骨架，已经具备：

- `run_ai_radar.py` 默认作为 `scheduler` 入口
- `.runtime/locks/` 与 `.runtime/pid/` 的运行锁和 PID 元信息
- `scripts/run_scheduler_once.sh`
- `scripts/generate_scheduler_assets.py`
- `cron` 与 `launchd` 示例配置生成
- 陈旧锁自动恢复（针对 PID 已失效场景）

## 推荐命令

```bash
python run_ai_radar.py --max-items 1
python scripts/generate_scheduler_assets.py --hour 9 --minute 0
```

## 生成结果

- `outputs/exports/markdown/scheduling/cron.example.txt`
- `outputs/exports/markdown/scheduling/ai_radar.launchd.plist`

## 现实限制

- 电脑休眠、关机或合盖时，自动任务会中断
- `cron / launchd` 只负责触发，不负责替你解决网络波动或模型服务不可用
- 当前版本会自动恢复 PID 已失效的陈旧锁
- 如果进程还活着但逻辑卡死，仍需要手动检查 `.runtime/`
