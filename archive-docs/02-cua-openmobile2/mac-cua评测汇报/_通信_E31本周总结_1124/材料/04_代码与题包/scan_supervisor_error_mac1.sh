cd ~/mac-cua/results 2>/dev/null || cd /Users/user/mac-cua/results
tot=0; se=0; unc=0
for d in */tasks/*/attempt-*; do
  [ -f "$d/agent/status.json" ] || continue
  tot=$((tot+1))
  if grep -q supervisor_error "$d/agent/status.json"; then
    se=$((se+1)); 
    if grep -q 'could not be confirmed' "$d/agent/stop-confirmation.json" 2>/dev/null; then unc=$((unc+1)); echo "UNC $d"; else echo "SE-other $d"; fi
  fi
done
echo "total_with_status=$tot supervisor_error=$se agent_stop_unconfirmed=$unc"
