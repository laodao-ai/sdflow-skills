import json,sys,glob,os
SB="/private/tmp/claude-501/-Users-cheneyzhao-Documents-04-sdflow-skills/49e41057-82a1-4963-9640-8a1b18500424/scratchpad/ab"
def show(p, full=True):
    d=json.load(open(p))
    print("### %s"%p.split("logs/")[-1])
    if full: print(d.get("result",""))
    print("META rc sid=%s cost=%.4f dur_ms=%s turns=%s err=%s denials=%s"%(
        d.get("session_id"),d.get("total_cost_usd",0),d.get("duration_ms"),d.get("num_turns"),d.get("is_error"),d.get("permission_denials")))
    for m,v in d.get("modelUsage",{}).items():
        print("  %s in=%s out=%s cacheRead=%s cacheCreate=%s cost=%.4f"%(m,v.get("inputTokens"),v.get("outputTokens"),v.get("cacheReadInputTokens"),v.get("cacheCreationInputTokens"),v.get("costUSD",0)))
    print()
if len(sys.argv)>1 and sys.argv[1]=="--sum":
    for lane in ("legacy","thin","subagent"):
        tot=0.0; dur=0; ti=to=cr=cc=0; per={}
        for p in sorted(glob.glob(os.path.join(SB,"logs",lane,"turn*.json"))):
            d=json.load(open(p)); tot+=d.get("total_cost_usd",0) or 0; dur+=d.get("duration_ms",0) or 0
            for m,v in d.get("modelUsage",{}).items():
                a=per.setdefault(m,[0,0,0,0,0.0])
                a[0]+=v.get("inputTokens",0);a[1]+=v.get("outputTokens",0)
                a[2]+=v.get("cacheReadInputTokens",0);a[3]+=v.get("cacheCreationInputTokens",0);a[4]+=v.get("costUSD",0)
        n=len(glob.glob(os.path.join(SB,"logs",lane,"turn*.json")))
        print("%-9s turns=%-3d cost=$%.4f  model_wallclock=%.1fs"%(lane,n,tot,dur/1000))
        for m,a in sorted(per.items()):
            print("            %-28s in=%-7d out=%-7d cacheRead=%-9d cacheCreate=%-8d $%.4f"%(m,a[0],a[1],a[2],a[3],a[4]))
else:
    for p in sys.argv[1:]:
        show(p)
