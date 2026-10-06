from app.services.monitoring import dedupe_key

def test_alert_dedupe_key_is_stable(): assert dedupe_key("trend",1,2,"2026-10-06")==dedupe_key("trend",1,2,"2026-10-06")
