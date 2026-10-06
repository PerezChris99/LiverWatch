from types import SimpleNamespace
from app.services.population import risk_distribution,district_summary
def test_small_population_is_suppressed():
 assert risk_distribution([SimpleNamespace(risk_level="low")],10)["suppressed"]
def test_distribution_after_threshold():
 rows=[SimpleNamespace(risk_level="low") for _ in range(10)]
 assert risk_distribution(rows,10)["distribution"]["low"]==10
def test_district_summary_excludes_small_groups():
 rows=[SimpleNamespace(district="A",risk_level="low") for _ in range(9)]+[SimpleNamespace(district="B",risk_level="high") for _ in range(10)]
 assert "A" not in district_summary(rows,10) and "B" in district_summary(rows,10)
