#!/bin/bash
# Local Mac, 11-10 evening: wait for the production 美图 batch (e20-ds-sky-mb-1109), extract it there, then run local case analysis + labels.
# The 11-09 overnight loops (overnight_collect.sh / overnight_analyze.sh) hit their deadlines before this batch finished.
set -u
P=~/.config/prod-mac/prod.sh
LOG=/Users/zhangyingying/CUA/评测集建设/实验/E20_DeepSeek集群批量覆盖/analysis/_overnight_log.txt
log() { echo "$(date '+%m-%d %H:%M:%S') [mb_finish] $*" >> "$LOG"; }
deadline=$(( $(date +%s) + 6*3600 ))
log "start"
until $P ssh 'grep -q "e20 prod mb done" ~/e20_prod.log' 2>/dev/null; do
  [ "$(date +%s)" -ge "$deadline" ] && { log "deadline reached before batch finished"; exit 1; }
  sleep 300
done
log "batch finished; extracting on prod"
$P ssh 'H=$HOME; RAW=$H/overnight_raw; rm -rf $RAW/e20-mb.tmp; EXTRACT_SKIP_FRESH=0 python3 $H/e16_extract.py $RAW/e20-mb.tmp $H/mac-cua/results/e20-ds-sky-mb-1109/*/ >> $H/overnight_collect.log 2>&1 && rm -rf $RAW/e20-mb && mv $RAW/e20-mb.tmp $RAW/e20-mb && touch $RAW/e20-mb/.done; ls $RAW/e20-mb | grep -c json' >> "$LOG" 2>&1
log "extract done; running overnight_analyze for e20-mb"
caffeinate -i bash /Users/zhangyingying/CUA/评测集建设/实验/E20_DeepSeek集群批量覆盖/scripts/overnight_analyze.sh
log "done"
