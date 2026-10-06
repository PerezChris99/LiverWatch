"""Versioned, explainable risk orchestration.

This layer adds reproducibility and longitudinal context around the existing
rule engine. It deliberately does not introduce diagnostic thresholds.
"""
from __future__ import annotations
import hashlib, json
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Iterable
from app.services.risk_engine import run_risk_assessment, AssessmentResult

ENGINE_VERSION="3.1.0"

@dataclass(frozen=True)
class TrendSignal:
    code:str
    count:int
    first_value:float
    latest_value:float
    delta:float
    direction:str

@dataclass(frozen=True)
class LongitudinalRiskResult:
    assessment:AssessmentResult
    trends:tuple[TrendSignal,...]
    data_quality:float
    engine_version:str=ENGINE_VERSION

def fingerprint_input(data:dict)->str:
    payload=json.dumps(data,sort_keys=True,separators=(",",":"),default=str)
    return hashlib.sha256(payload.encode()).hexdigest()

def summarise_trends(observations:Iterable[Any])->tuple[TrendSignal,...]:
    grouped={}
    for obs in observations:
        if not getattr(obs,"is_usable",False): continue
        grouped.setdefault(obs.code,[]).append(obs)
    out=[]
    for code,items in grouped.items():
        items=sorted(items,key=lambda x:x.observed_at)
        if len(items)<2: continue
        first=float(items[0].value); latest=float(items[-1].value); delta=latest-first
        direction="rising" if delta>0 else "falling" if delta<0 else "stable"
        out.append(TrendSignal(code,len(items),first,latest,delta,direction))
    return tuple(out)

def assess_with_history(data:dict, observations:Iterable[Any]=())->LongitudinalRiskResult:
    assessment=run_risk_assessment(data)
    trends=summarise_trends(observations)
    # Confidence is based on supplied assessment dimensions; observation quality
    # is a separate signal so missing/poor measurements never silently become normal.
    usable=sum(1 for o in observations if getattr(o,"is_usable",False))
    total=sum(1 for _ in observations)
    quality=1.0 if total==0 else round(usable/total,3)
    return LongitudinalRiskResult(assessment,trends,quality)
