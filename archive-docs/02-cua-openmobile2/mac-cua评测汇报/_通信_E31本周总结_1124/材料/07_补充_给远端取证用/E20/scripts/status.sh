#!/bin/bash
# One-shot status of the 11-09 overnight work (cluster E20A/B/C, prod E19/E20-mb, collection and analysis loops).
cd /Users/zhangyingying/CUA/mac-cua-v2 || exit 1
echo "== $(date '+%m-%d %H:%M')"
for pair in E20A=run-857978fa7245426cb2e2fb68e4fcea14 E20B=run-7e68e48a31b34cfab7073fb33530148f E20C=run-8a9b4764741b4d4ba583c09f37027a19; do
  uv run --no-dev mac-cua --cluster office status "${pair#*=}" 2>/dev/null > /tmp/e20_status.json
  python3 - "${pair%%=*}" <<'PY'
import sys, json, collections
s = open('/tmp/e20_status.json').read(); i = s.find('{')
try:
    d = json.loads(s[i:]); c = collections.Counter(t.get('state') for t in d.get('tasks', []))
    print(sys.argv[1], d.get('state'), dict(c))
except Exception as e:
    print(sys.argv[1], 'status unavailable', e)
PY
done
~/.config/prod-mac/prod.sh ssh 'echo "-- prod"; for f in ~/e19-ds-sky-p3-1109.log ~/e19-ds-sky-p3-e14-1109.log ~/e20-ds-sky-mb-1109.log; do [ -f $f ] && echo "$(basename $f): $(grep -c " end " $f) done, last: $(tail -1 $f | cut -c1-90)"; done; echo "collect: $(tail -1 ~/overnight_collect.log)"' 2>/dev/null
echo "analyze: $(tail -1 /Users/zhangyingying/CUA/评测集建设/实验/E20_DeepSeek集群批量覆盖/analysis/_overnight_log.txt)"
