from app.services.readiness import check_configuration
def test_readiness_flags_missing_secrets():
 r=check_configuration({})
 assert not r["ready"] and "SECRET_KEY" in r["missing"]
