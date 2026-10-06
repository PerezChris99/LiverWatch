from types import SimpleNamespace
import pytest
from app.services.referral_workflow import transition
def test_referral_transitions():
 r=SimpleNamespace(status="pending",sent_at=None,acknowledged_at=None,completed_at=None)
 for s in ("sent","acknowledged","completed"): transition(r,s)
 assert r.status=="completed" and r.completed_at is not None
def test_referral_cannot_skip_states():
 r=SimpleNamespace(status="pending")
 with pytest.raises(ValueError): transition(r,"completed")
