#!/bin/bash
# Submit one E20 batch to the shared cluster.
# submit_cluster.sh <run-name> <task-package-dir> <id-list-file> <jobs>
set -euo pipefail
CLIENT=/Users/zhangyingying/CUA/mac-cua-v2
OUT="$(cd "$(dirname "$0")" && pwd)"
name="$1"; dir="$2"; ids="$3"; jobs="$4"
args=()
while read -r t; do [ -n "$t" ] && args+=(--id "$t"); done < "$ids"
cd "$CLIENT"
uv run --no-dev mac-cua --cluster office run --task-dir "$dir" "${args[@]}" \
  --model-config config.client.toml --environment main --jobs "$jobs" --name "$name" > "$OUT/submit_$name.json" 2>&1
python3 - "$OUT/submit_$name.json" "$name" <<'EOF'
import json, sys
s = open(sys.argv[1]).read(); i = s.find('{')
try:
    d = json.loads(s[i:])
    print(sys.argv[2], d.get('id'), d.get('state'), d.get('url'))
except Exception:
    print(sys.argv[2], 'SUBMIT FAILED:', s[-500:])
EOF
