#!/usr/bin/env bash
# HIGHLAND CAPITAL - 每日盘前资讯管线启动脚本
# 可由 Mac launchd 在 05:00 或 07:00 自动触发

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXEC="/Users/qiaoquanming/Downloads/03_投资/etf_quant/.venv/bin/python"

if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="python3"
fi

mkdir -p "$DIR/logs"
echo "=== HIGHLAND CAPITAL 盘前晨报生成 [$(date '+%Y-%m-%d %H:%M:%S')] ===" >> "$DIR/logs/morning_pipeline.log"
"$PYTHON_EXEC" "$DIR/src/pipeline.py" >> "$DIR/logs/morning_pipeline.log" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "=== 运行成功 [$(date '+%Y-%m-%d %H:%M:%S')] ===" >> "$DIR/logs/morning_pipeline.log"
else
    echo "=== 运行失败 (退出码: $EXIT_CODE) [$(date '+%Y-%m-%d %H:%M:%S')] ===" >> "$DIR/logs/morning_pipeline.log"
fi
exit $EXIT_CODE
