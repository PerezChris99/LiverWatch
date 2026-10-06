"""
Risk Engine Tests
=================

Tests for the rule-based liver risk assessment engine.
All scenarios must NEVER produce diagnostic language.
"""

import pytest
from app.services.risk_engine import (
    run_risk_assessment,
    AssessmentResult,
    RiskLevel,
    EMERGENCY_SYMPTOMS,
)


# ── Helper ────────────────────────────────────────────────────────────────

def base_data(**overrides):
    """Minimal safe input with overrides."""
    data = {
        'hbsag_positive': False,
        'hcv_positive': False,
        'vaccinated_hbv': True,
        'hbv_exposure_risk': False,
        'hbv_family_history': False,
        'drinks_per_day': 0.0,
        'years_drinking': 0,
        'binge_drinking': False,
        'symptoms': [],
        'otc_painkillers': False,
        'painkiller_frequency': 'rarely',
        'tb_treatment': False,
        'herbal_remedies': False,
        'multiple_medications': False,
        'aflatoxin_exposure': False,
        'chemical_exposure': False,
        'unsafe_water': False,
        'liver_cancer_family': False,
        'cirrhosis_family': False,
        'bmi': 22.0,
        'high_fat_diet': False,
        'low_water_intake': False,
        'diabetes': False,
        'disclaimer_acknowledged': True,
    }
    data.update(overrides)
    return data


# ── Low risk ──────────────────────────────────────────────────────────────

class TestLowRisk:
    def test_healthy_person(self):
        result = run_risk_assessment(base_data())
        assert isinstance(result, AssessmentResult)
        assert result.risk_level in (RiskLevel.LOW, RiskLevel.MINIMAL)
        assert result.requires_referral is False

    def test_disclaimer_always_present(self):
        result = run_risk_assessment(base_data())
        assert result.disclaimer
        assert 'medical diagnosis' in result.disclaimer.lower() or \
               'healthcare professional' in result.disclaimer.lower()

    def test_recommendations_list(self):
        result = run_risk_assessment(base_data())
        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0

    def test_no_diagnosis_language(self):
        result = run_risk_assessment(base_data())
        forbidden = ['you have', 'you are diagnosed', 'diagnosis is', 'you definitely']
        full_text = result.explanation.lower() + ' ' + ' '.join(result.recommendations).lower()
        for phrase in forbidden:
            assert phrase not in full_text, f"Diagnostic phrase found: '{phrase}'"


# ── High alcohol ──────────────────────────────────────────────────────────

class TestHighAlcohol:
    def test_heavy_drinker_is_high_risk(self):
        result = run_risk_assessment(base_data(
            drinks_per_day=8.0,
            years_drinking=15,
            binge_drinking=True,
        ))
        assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        assert result.overall_score > 0.5

    def test_moderate_drinker(self):
        result = run_risk_assessment(base_data(
            drinks_per_day=2.0,
            years_drinking=5,
        ))
        assert result.overall_score < 0.6

    def test_alcohol_factor_captured(self):
        result = run_risk_assessment(base_data(drinks_per_day=6.0, years_drinking=10))
        factor_categories = [f.category for f in result.factors]
        assert 'alcohol' in factor_categories


# ── Hepatitis ─────────────────────────────────────────────────────────────

class TestHepatitis:
    def test_hbsag_positive_high_risk(self):
        result = run_risk_assessment(base_data(hbsag_positive=True))
        assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        assert result.requires_referral is True

    def test_hcv_positive_high_risk(self):
        result = run_risk_assessment(base_data(hcv_positive=True))
        assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_both_hepatitis_very_high(self):
        result = run_risk_assessment(base_data(
            hbsag_positive=True,
            hcv_positive=True,
        ))
        assert result.overall_score > 0.6

    def test_vaccinated_lower_risk(self):
        vaccinated = run_risk_assessment(base_data(
            vaccinated_hbv=True, hbv_exposure_risk=False,
        ))
        unvaccinated = run_risk_assessment(base_data(
            vaccinated_hbv=False, hbv_exposure_risk=True,
        ))
        assert vaccinated.overall_score <= unvaccinated.overall_score


# ── Emergency symptoms ────────────────────────────────────────────────────

class TestEmergencySymptoms:
    def test_vomiting_blood_is_critical(self):
        result = run_risk_assessment(base_data(
            symptoms=['vomiting_blood'],
        ))
        assert result.risk_level == RiskLevel.CRITICAL
        assert result.requires_referral is True
        assert result.referral_urgency == 'emergency'

    def test_severe_confusion_is_emergency(self):
        result = run_risk_assessment(base_data(
            symptoms=['severe_confusion'],
        ))
        assert result.risk_level == RiskLevel.CRITICAL

    def test_multiple_high_risk_symptoms(self):
        result = run_risk_assessment(base_data(
            symptoms=['jaundice', 'dark_urine', 'pale_stools', 'swollen_abdomen'],
        ))
        assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        assert result.requires_referral is True

    def test_emergency_notice_in_recommendations(self):
        result = run_risk_assessment(base_data(
            symptoms=['vomiting_blood'],
        ))
        all_text = ' '.join(result.recommendations).lower()
        assert 'emergency' in all_text or 'immediately' in all_text


# ── Compound risk ─────────────────────────────────────────────────────────

class TestCompoundRisk:
    def test_hepatitis_plus_alcohol_plus_symptoms(self):
        result = run_risk_assessment(base_data(
            hbsag_positive=True,
            drinks_per_day=5.0,
            years_drinking=10,
            symptoms=['jaundice', 'dark_urine'],
        ))
        assert result.risk_level == RiskLevel.CRITICAL
        assert result.overall_score > 0.7

    def test_all_factors_low(self):
        result = run_risk_assessment(base_data(
            vaccinated_hbv=True,
            drinks_per_day=0.5,
            bmi=21.0,
        ))
        assert result.risk_level in (RiskLevel.MINIMAL, RiskLevel.LOW)


# ── Score bounds ──────────────────────────────────────────────────────────

class TestScoreBounds:
    def test_score_between_0_and_1(self):
        for scenario in [
            base_data(),
            base_data(hbsag_positive=True, drinks_per_day=10, symptoms=['vomiting_blood']),
            base_data(vaccinated_hbv=True, bmi=20.0),
        ]:
            result = run_risk_assessment(scenario)
            assert 0.0 <= result.overall_score <= 1.0, \
                f'Score out of bounds: {result.overall_score}'

    def test_confidence_between_0_and_1(self):
        result = run_risk_assessment(base_data())
        assert 0.0 <= result.confidence_level <= 1.0
