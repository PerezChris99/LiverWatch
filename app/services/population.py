"""Privacy-aware population health aggregation helpers."""
from collections import Counter
def risk_distribution(rows,min_group_size=10):
    rows=list(rows)
    if len(rows)<min_group_size: return {"suppressed":True,"total":len(rows)}
    counts=Counter(str(getattr(r,"risk_level","unknown")) for r in rows)
    return {"suppressed":False,"total":len(rows),"distribution":dict(counts)}
def district_summary(rows,min_group_size=10):
    groups={}
    for r in rows: groups.setdefault(str(getattr(r,"district","unknown")),[]).append(r)
    return {d:risk_distribution(items,min_group_size) for d,items in groups.items() if len(items)>=min_group_size}
