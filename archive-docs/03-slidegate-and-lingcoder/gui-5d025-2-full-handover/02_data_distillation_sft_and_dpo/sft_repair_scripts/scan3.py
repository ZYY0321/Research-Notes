#!/usr/bin/env python3
"""Characterize system-prompt variants at record level.
Buckets each record's system prompt by (has_cn_heading, has_en, has_tag) and length band."""
import json, sys
def main(path):
    buckets={}   # (cn,en,tag) -> {"n":..,"lmin":..,"lmax":..,"ex":cid}
    no_protocol_at_all=0   # none of the three markers
    total=0
    with open(path,encoding="utf-8") as fh:
        for line in fh:
            line=line.strip()
            if not line: continue
            try: rec=json.loads(line)
            except Exception: continue
            sysm=next((m for m in rec.get("messages",[]) if m.get("role")=="system"),None)
            if not sysm: continue
            total+=1
            c=sysm.get("content") or ""
            cn="文件操作预播报协议" in c
            en="File Action Protocol" in c
            tag="<file_action>" in c
            key=(cn,en,tag)
            b=buckets.setdefault(key,{"n":0,"lmin":10**9,"lmax":0,"ex":rec.get("case_id"),"agent":rec.get("agent")})
            b["n"]+=1; L=len(c); b["lmin"]=min(b["lmin"],L); b["lmax"]=max(b["lmax"],L)
            if not (cn or en or tag): no_protocol_at_all+=1
    out={"path":path,"total_sys":total,"no_protocol_at_all":no_protocol_at_all,
         "buckets":[{"cn":k[0],"en":k[1],"tag":k[2],**v} for k,v in sorted(buckets.items(),key=lambda kv:-kv[1]["n"])]}
    print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__": main(sys.argv[1])
