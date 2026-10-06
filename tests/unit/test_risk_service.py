from datetime import datetime, timezone
from types import SimpleNamespace
from app.services.risk_service import fingerprint_input, summarise_trends

def test_risk_input_fingerprint_is_deterministic():
    assert fingerprint_input({"b":2,"a":1})==fingerprint_input({"a":1,"b":2})

def test_trend_summary_ignores_unusable_and_describes_direction():
    rows=[SimpleNamespace(code="ALT",value=30,observed_at=datetime(2026,1,1,tzinfo=timezone.utc),is_usable=True),SimpleNamespace(code="ALT",value=45,observed_at=datetime(2026,2,1,tzinfo=timezone.utc),is_usable=True),SimpleNamespace(code="AST",value=20,observed_at=datetime(2026,2,1,tzinfo=timezone.utc),is_usable=False)]
    result=summarise_trends(rows)
    assert result[0].code=="ALT" and result[0].direction=="rising" and result[0].delta==15
