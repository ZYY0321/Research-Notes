#!/bin/bash
# E20 on the production Mac: after E19's chain, run the 95 unrun 美图 basic tasks with DeepSeek on Sky (default Sky prompt).
H="$HOME"
until grep -q "e19 chain done" "$H/e19_chain.log" 2>/dev/null || ! pgrep -f e19_chain.sh >/dev/null; do sleep 60; done
[ -e "$H/e20.stop" ] && exit 0
QUEUE_CODE="$H/mac-cua-sky-r2" SKY_QUEUE_CFG="$H/mac-cua-sky-deepseek/config.toml" QUEUE_TASKS="$H/mac-cua/local-tasks/zyy-basic" \
  python3 "$H/queue_cfg.py" e20-ds-sky-mb-1109 "$H/e20_ids_mb.txt"
echo "$(date '+%m-%d %H:%M:%S') e20 prod mb done" >> "$H/e20_prod.log"
