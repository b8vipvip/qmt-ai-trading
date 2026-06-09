# -*- coding: utf-8 -*-
# qmt_daily_dryrun.py
# 从 config.json 读取配置
# 一键运行：生成信号 -> 生成计划 -> 安全预检
# 注意：全流程不下单，并自动保存日志

import os
import subprocess
from datetime import datetime
from qmt_config import load_config


LOG_FILE = None


def log_print(*args):
    text = " ".join([str(x) for x in args])
    print(text)

    if LOG_FILE:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def run_step(python_exe, script_path):
    log_print("\n" + "=" * 80)
    log_print("运行脚本:", script_path)
    log_print("=" * 80)

    result = subprocess.run(
        [python_exe, script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )

    log_print(result.stdout)

    if result.returncode != 0:
        log_print("[ERROR] 步骤失败，停止后续流程:", script_path)
        return False

    log_print("[OK] 步骤完成:", script_path)
    return True


def main():
    global LOG_FILE

    cfg = load_config()

    python_exe = cfg["qmt_python_exe"]
    scripts = cfg["daily_scripts"]

    logs_dir = cfg["paths"].get("logs_dir", r"D:\AI\qmt\logs")
    os.makedirs(logs_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    LOG_FILE = os.path.join(logs_dir, "daily_dryrun_{0}.log".format(ts))

    log_print("=== QMT Daily Dry-Run Pipeline ===")
    log_print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log_print("日志文件:", LOG_FILE)
    log_print("说明：本流程只生成信号、计划和安全预检，不执行任何实盘交易。")

    all_ok = True

    for script in scripts:
        ok = run_step(python_exe, script)
        if not ok:
            all_ok = False
            log_print("\n流程中止。")
            break

    log_print("\n" + "=" * 80)

    if all_ok:
        log_print("[OK] 今日 dry-run 流程全部完成。")
    else:
        log_print("[ERROR] 今日 dry-run 流程未完成。")

    log_print("没有执行任何实盘交易。")
    log_print("日志文件:", LOG_FILE)
    log_print("=" * 80)


if __name__ == "__main__":
    main()