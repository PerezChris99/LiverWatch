"""Monitoring alert orchestration with deduplication and explicit escalation language."""
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from app import db
from app.models import MonitoringAlert

def dedupe_key(*parts): return hashlib.sha256("|".join(str(x) for x in parts).encode()).hexdigest()

def create_alert(*,alert_type,severity,title,message,evidence=None,user_id=None,patient_id=None,source_observation_id=None,window_key=None):
    if severity not in {"info","warning","urgent","critical"}: raise ValueError("Invalid alert severity")
    if user_id is None and patient_id is None: raise ValueError("Alert must belong to a user or patient")
    key=dedupe_key(alert_type,user_id,patient_id,window_key or datetime.now(timezone.utc).date())
    existing=MonitoringAlert.query.filter_by(dedupe_key=key,status="open").first()
    if existing: return existing,False
    alert=MonitoringAlert(user_id=user_id,patient_id=patient_id,alert_type=alert_type,severity=severity,title=title,message=message,source_observation_id=source_observation_id,dedupe_key=key)
    if evidence: alert.set_evidence(evidence)
    db.session.add(alert); db.session.flush(); return alert,True

def acknowledge_alert(alert, when=None):
    alert.status="acknowledged"; alert.acknowledged_at=when or datetime.now(timezone.utc); return alert

def resolve_alert(alert, when=None):
    alert.status="resolved"; alert.resolved_at=when or datetime.now(timezone.utc); return alert
