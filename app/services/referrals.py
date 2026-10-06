"""Referral workflow state machine."""
from datetime import datetime,timezone

TRANSITIONS={
 "pending":{"sent","cancelled"},
 "sent":{"acknowledged","cancelled"},
 "acknowledged":{"completed","cancelled"},
 "completed":set(),
 "cancelled":set(),
}
URGENCIES={"routine","urgent","emergency"}

def transition_referral(referral,new_status,when=None):
    current=referral.status
    if new_status not in TRANSITIONS.get(current,set()): raise ValueError(f"Invalid referral transition: {current} -> {new_status}")
    now=when or datetime.now(timezone.utc)
    referral.status=new_status
    if new_status=="sent": referral.sent_at=now
    elif new_status=="acknowledged": referral.acknowledged_at=now
    elif new_status=="completed": referral.completed_at=now
    return referral

def validate_referral_urgency(urgency):
    if urgency not in URGENCIES: raise ValueError("Invalid referral urgency")
    return urgency
