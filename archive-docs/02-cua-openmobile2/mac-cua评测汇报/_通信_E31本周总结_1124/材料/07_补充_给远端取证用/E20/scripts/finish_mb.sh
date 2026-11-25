#!/bin/bash
# Local Mac, 11-10 night: the overnight loops hit their deadlines before the 美图 batch finished.
# Wait for "e20 prod mb done" on prod -> extract there -> pull to raw/e20-mb -> narrate + label -> refresh 统计_E20.md.
set -u
EXP=/Users/zhangyingying/CUA/评测集建设/实验
D="$EXP/E20_DeepSeek集群批量覆盖"; S16="$EXP/E16_近期轨迹总报告/scripts"; P=~/.config/prod-mac/prod.sh
LOG="$D/analysis/_overnight_log.txt"
log() { echo "$(date '+%m-%d %H:%M:%S') [finish_mb] $*" | tee -a "$LOG"; }
set -a; . /Users/zhangyingying/CUA/.env; set +a
log "waiting for e20 prod mb done"
until $P ssh 'grep -q "e20 prod mb done" ~/e20_prod.log' 2>/dev/null; do sleep 120; done
log "prod batch done; extracting on prod"
$P ssh 'rm -rf ~/overnight_raw/e20-mb.tmp; EXTRACT_SKIP_FRESH=0 python3 ~/e16_extract.py ~/overnight_raw/e20-mb.tmp ~/mac-cua/results/e20-ds-sky-mb-1109/*/ >> ~/overnight_collect.log 2>&1 && rm -rf ~/overnight_raw/e20-mb && mv ~/overnight_raw/e20-mb.tmp ~/overnight_raw/e20-mb && touch ~/overnight_raw/e20-mb/.done; ls ~/overnight_raw/e20-mb | grep -c json'
rm -rf /tmp/ovr_e20-mb; $P get "~/overnight_raw/e20-mb" /tmp/ovr_e20-mb >/dev/null 2>&1
rm -rf "$D/raw/e20-mb"; mv /tmp/ovr_e20-mb "$D/raw/e20-mb"
log "pulled e20-mb: $(ls "$D/raw/e20-mb" | grep -c json) records"
mkdir -p "$D/raw/_all"; cp "$D/raw/e20-mb"/*.json "$D/raw/_all/" 2>/dev/null
python3 "$S16/narrate.py" "$D/raw/e20-mb" "$D/analysis/逐条" --workers 6 --skip-prefix "" >> "$LOG" 2>&1
python3 "$S16/label.py" "$D/raw/e20-mb" "$D/analysis/逐条" "$D/analysis/标签" --workers 6 >> "$LOG" 2>&1
touch "$D/analysis/.e20-mb.analyzed"
python3 "$D/scripts/e20_stats.py" >> "$LOG" 2>&1
log "FINISH_MB_DONE analyses=$(ls "$D/analysis/逐条" | grep -c '\.md$') labels=$(ls "$D/analysis/标签" | grep -c '\.json$')"
