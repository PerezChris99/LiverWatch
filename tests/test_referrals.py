from types import SimpleNamespace
import pytest
from app.services.referrals import transition_referral
def test_referral_state_machine():
 r=SimpleNamespace(status="pending",sent_at=None,acknowledged_at=None,completed_at=None)
 transition_referral(r,"sent"); transition_referral(r,"acknowledged"); transition_referral(r,"completed")
 assert r.status=="completed" and r.completed_at is not None
def test_invalid_referral_transition():
 r=SimpleNamespace(status="pending")
 with pytest.raises(ValueError): transition_referral(r,"completed")
