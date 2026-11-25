#!/bin/bash
# Production Mac: fetch E20A task by task (no recordings), extract, then hand over to the overnight pipeline.
N=E20A-ds-sky-wps-jy-1109
python3 ~/fetch_run_tasks.py ~/mac-cua-v2-latest run-857978fa7245426cb2e2fb68e4fcea14 ~/mac-cua/local-tasks/zyy-basic ~/mac-cua/results/$N > ~/fetch_e20a.log 2>&1
rm -rf ~/overnight_raw/$N.tmp
EXTRACT_SKIP_FRESH=0 python3 ~/e16_extract.py ~/overnight_raw/$N.tmp ~/mac-cua/results/$N >> ~/fetch_e20a.log 2>&1
n=$(ls ~/overnight_raw/$N.tmp 2>/dev/null | grep -c json)
if [ "$n" -gt 0 ]; then rm -rf ~/overnight_raw/$N && mv ~/overnight_raw/$N.tmp ~/overnight_raw/$N && touch ~/overnight_raw/$N/.done; fi
echo "$(date '+%m-%d %H:%M:%S') fetched+extracted $N: $n records" >> ~/overnight_collect.log
cd ~ && nohup ~/overnight_collect.sh > ~/overnight_collect.out 2>&1 &
