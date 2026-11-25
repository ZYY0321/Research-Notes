#!/bin/bash
# Production Mac, night of 11-09: download finished shared-cluster runs and extract all finished batches.
# Outputs: ~/mac-cua/results/<name>/ (full cluster downloads), ~/overnight_raw/<name>/*.json (compact records), log ~/overnight_collect.log
H="$HOME"; LOG="$H/overnight_collect.log"; RAW="$H/overnight_raw"; CLIENT="$H/mac-cua-v2-latest"
export PATH="$H/.local/bin:$PATH"
mkdir -p "$RAW"
log() { echo "$(date '+%m-%d %H:%M:%S') $*" >> "$LOG"; }
CLUSTER_RUNS="E20A-ds-sky-wps-jy-1109=run-857978fa7245426cb2e2fb68e4fcea14 E20B-ds-sky-e14-1109=run-7e68e48a31b34cfab7073fb33530148f E20C-ds-sky-e12paired-1109=run-8a9b4764741b4d4ba583c09f37027a19"
deadline=$(( $(date +%s) + 16*3600 ))

state_of() { (cd "$CLIENT" && uv run --no-dev mac-cua --cluster office status "$1" 2>/dev/null) | python3 -c "
import sys,json; s=sys.stdin.read(); i=s.find('{')
try: print(json.loads(s[i:]).get('state'))
except Exception: print('unknown')"; }

extract() {  # extract <name> <run_dir>...
  local name="$1"; shift
  rm -rf "$RAW/$name.tmp"; EXTRACT_SKIP_FRESH=0 python3 "$H/e16_extract.py" "$RAW/$name.tmp" "$@" >> "$LOG" 2>&1 && rm -rf "$RAW/$name" && mv "$RAW/$name.tmp" "$RAW/$name" && touch "$RAW/$name/.done"
  log "extracted $name: $(ls "$RAW/$name" 2>/dev/null | grep -c json) records"
}

log "start"
while [ "$(date +%s)" -lt "$deadline" ]; do
  pending=0
  for pair in $CLUSTER_RUNS; do
    name="${pair%%=*}"; run="${pair#*=}"
    [ -e "$RAW/$name/.done" ] && continue
    st=$(state_of "$run")
    if [ "$st" = "finished" ] || [ "$st" = "cancelled" ] || [ "$st" = "failed" ]; then
      log "$name $run state=$st; downloading"
      for try in 1 2 3; do
        rm -rf "$H/mac-cua/results/$name"
        (cd "$CLIENT" && uv run --no-dev mac-cua --cluster office download "$run" --output "$H/mac-cua/results/$name") >> "$LOG" 2>&1
        [ -f "$H/mac-cua/results/$name/run.json" ] && break
        log "$name download attempt $try failed"; sleep 30
      done
      extract "$name" "$H/mac-cua/results/$name"
    else
      pending=1
    fi
  done
  if [ ! -e "$RAW/e19/.done" ]; then
    if grep -q "e19 chain done" "$H/e19_chain.log" 2>/dev/null; then
      extract e19 "$H/mac-cua/results"/e19-ds-sky-p3-smoke-1109/*/ "$H/mac-cua/results"/e19-ds-sky-p3-1109/*/ "$H/mac-cua/results"/e19-ds-sky-p3-e14-1109/*/
    else pending=1; fi
  fi
  if [ ! -e "$RAW/e20-mb/.done" ]; then
    if grep -q "e20 prod mb done" "$H/e20_prod.log" 2>/dev/null; then
      extract e20-mb "$H/mac-cua/results"/e20-ds-sky-mb-1109/*/
    else pending=1; fi
  fi
  [ "$pending" = 0 ] && { log "all collected"; exit 0; }
  sleep 600
done
log "deadline reached"
