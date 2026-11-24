cd /Users/user/mac-cua/results
n=0; ok=0
for d in e31*/tasks/*/attempt-*; do
  ls $d/agent/rollout-trace/trace-*/trace.jsonl >/dev/null 2>&1 || continue
  n=$((n+1))
  if grep -q '"score": 1' "$d/grading/score.json" 2>/dev/null; then ok=$((ok+1)); echo "S1 $d"; fi
done
echo "e31 attempts_with_trace=$n with_score1=$ok"
