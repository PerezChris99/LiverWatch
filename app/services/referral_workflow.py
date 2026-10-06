"""Referral lifecycle state machine.

The workflow is operational support only; it does not make a clinical diagnosis.
"""
from datetime import datetime,timezone
TRANSITIONS={"pending":{"sent","cancelled"},"sent":{"acknowledged","cancelled"},"acknowledged":{"completed","cancelled"},"completed":set(),"cancelled":set()}
URGENCIES={"routine","urgent","emergency"}
def transition(referral,new_status,when=None):
    if new_status not in TRANSITIONS.get(referral.status,set()): raise ValueError(f"Invalid referral transition: {referral.status} -> {new_status}")
    now=when or datetime.now(timezone.utc); referral.status=new_status
    if new_status=="sent": referral.sent_at=now
    elif new_status=="acknowledged": referral.acknowledged_at=now
    elif new_status=="completed": referral.completed_at=now
    return referral
def validate_urgency(value):
    if value not in URGENCIES: raise ValueError("Invalid referral urgency")
    return value
