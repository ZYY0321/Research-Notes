#!/bin/bash
# Local Mac, night of 11-09: pull compact records extracted on the production Mac and run case analysis + structured labels.
# E19 -> 实验/E19_DeepSeek_CLI优先提示/{raw/traj_1109,analysis/逐条,analysis/标签}; E20 batches -> 实验/E20_DeepSeek集群批量覆盖/... (same layout).
set -u
EXP=/Users/zhangyingying/CUA/评测集建设/实验
S16="$EXP/E16_近期轨迹总报告/scripts"
P=~/.config/prod-mac/prod.sh
LOG="$EXP/E20_DeepSeek集群批量覆盖/analysis/_overnight_log.txt"
mkdir -p "$EXP/E20_DeepSeek集群批量覆盖/analysis" "$EXP/E19_DeepSeek_CLI优先提示/analysis"
set -a; . /Users/zhangyingying/CUA/.env; set +a
log() { echo "$(date '+%m-%d %H:%M:%S') $*" >> "$LOG"; }
deadline=$(( $(date +%s) + 17*3600 ))
log "start"
while [ "$(date +%s)" -lt "$deadline" ]; do
  left=0
  for name in E20A-ds-sky-wps-jy-1109 E20B-ds-sky-e14-1109 E20C-ds-sky-e12paired-1109 e20-mb e19; do
    if [ "$name" = e19 ]; then D="$EXP/E19_DeepSeek_CLI优先提示"; else D="$EXP/E20_DeepSeek集群批量覆盖"; fi
    R="$D/raw/$name"
    [ -e "$D/analysis/.$name.analyzed" ] && continue
    if [ ! -e "$R/.done" ]; then
      if $P ssh "test -e ~/overnight_raw/$name/.done" 2>/dev/null; then
        rm -rf "/tmp/ovr_$name"; $P get "~/overnight_raw/$name" "/tmp/ovr_$name" >/dev/null 2>&1
        mkdir -p "$D/raw" && rm -rf "$R" && mv "/tmp/ovr_$name" "$R" && log "pulled $name ($(ls "$R" | grep -c json) records)"
      else left=1; continue; fi
    fi
    mkdir -p "$D/analysis/逐条" "$D/analysis/标签"
    python3 "$S16/narrate.py" "$R" "$D/analysis/逐条" --workers 6 --skip-prefix "" >> "$LOG" 2>&1
    python3 "$S16/label.py" "$R" "$D/analysis/逐条" "$D/analysis/标签" --workers 6 >> "$LOG" 2>&1
    n_md=$(ls "$D/analysis/逐条" | grep -c '\.md$'); n_lab=$(ls "$D/analysis/标签" | grep -c '\.json$')
    log "analyzed $name: analyses $n_md, labels $n_lab"
    touch "$D/analysis/.$name.analyzed"
  done
  [ "$left" = 0 ] && { log "all analyzed"; exit 0; }
  sleep 900
done
log "deadline reached"
