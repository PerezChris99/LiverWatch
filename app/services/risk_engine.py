"""
Liver Risk Engine — v3.0
=========================

Uganda Liver Risk Intelligence Platform
Rule-based liver risk assessment engine.

KEY RULES:
  ❌ Never diagnose diseases
  ❌ Never prescribe medication
  ❌ Never replace doctors
  ✅ Identify elevated risk patterns
  ✅ Recommend screening
  ✅ Generate referrals for high/urgent risk
  ✅ Always include the mandatory disclaimer

Risk weights are based on Uganda-specific epidemiology:
  - Hepatitis B prevalence ~11% (WHO 2023)
  - Aflatoxin exposure from staple grain storage
  - High alcohol burden (WHO ranking)
  - Limited access to liver specialist care
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import enum


class RiskLevel(str, enum.Enum):
    """Liver risk levels. Re-exported here so tests/services can import without touching models."""
    MINIMAL  = 'minimal'
    LOW      = 'low'
    MODERATE = 'moderate'
    HIGH     = 'high'
    URGENT   = 'urgent'
    CRITICAL = 'critical'


MEDICAL_DISCLAIMER = (
    "This platform does not provide medical diagnosis. "
    "Risk scores are for screening guidance only. "
    "Please consult a licensed healthcare professional."
)

# ── Risk factor weights (must sum to 1.0) ─────────────────────────────────
RISK_WEIGHTS: Dict[str, float] = {
    'hepatitis_status': 0.25,
    'alcohol':          0.20,
    'symptoms':         0.20,
    'medication':       0.10,
    'environmental':    0.10,
    'family_history':   0.05,
    'nutrition':        0.05,
    'biomarkers':       0.05,
}

# Clinical measurements are intentionally separated from experimental wearable
# ranges. Reference intervals vary by laboratory, method, age, sex and context.
# LiverWatch stores/validates their provenance but does not hard-code diagnosis.
SUPPORTED_CLINICAL_BIOMARKERS = {'ALT', 'AST', 'ALP', 'GGT', 'bilirubin_total', 'albumin', 'INR'}

# ── Symptom severity lists ────────────────────────────────────────────────
EMERGENCY_SYMPTOMS: List[str] = [
    'vomiting_blood',
    'severe_confusion',
    'difficulty_breathing',
    'severe_abdominal_pain_with_fever',
    'rapid_onset_jaundice',
    'loss_of_consciousness',
    'severe_abdominal_swelling',
]

HIGH_RISK_SYMPTOMS: List[str] = [
    'jaundice',           # yellow eyes or skin
    'dark_urine',
    'pale_stools',
    'severe_fatigue',
    'swollen_abdomen',
    'blood_in_stool',
    'confusion',
    'bleeding_easily',
    'spider_veins',       # spider angiomata
]

MODERATE_SYMPTOMS: List[str] = [
    'nausea',
    'loss_of_appetite',
    'abdominal_pain',
    'itching',
    'mild_fatigue',
    'low_grade_fever',
    'joint_pain',
    'right_upper_pain',   # right upper quadrant pain
]


# ── Data classes ──────────────────────────────────────────────────────────

@dataclass
class RiskFactorResult:
    name:         str
    category:     str
    value:        Any
    unit:         str
    weight:       float
    contribution: float
    is_elevated:  bool
    explanation:  str


@dataclass
class AssessmentResult:
    risk_level:       str          # 'low' | 'moderate' | 'high' | 'urgent'
    overall_score:    float        # 0.0 – 1.0
    confidence_level: float        # 0.0 – 1.0  (more data = higher confidence)
    explanation:      str
    recommendations:  List[str]
    requires_referral: bool
    referral_urgency:  Optional[str]   # 'routine' | 'urgent' | 'emergency' | None
    factors:           List[RiskFactorResult] = field(default_factory=list)
    emergency_symptoms: List[str]    = field(default_factory=list)
    disclaimer:        str = MEDICAL_DISCLAIMER


# ── Sub-calculators ───────────────────────────────────────────────────────

def calculate_alcohol_risk(data: Dict) -> Tuple[float, str]:
    """
    WHO-aligned alcohol risk calculation.
    Returns (score 0-1, explanation).
    """
    drinks_per_day = float(data.get('drinks_per_day', 0))
    years          = float(data.get('years_drinking', 0))
    binge          = bool(data.get('binge_drinking', False))

    if drinks_per_day == 0:
        return 0.0, "No alcohol use reported."

    if drinks_per_day <= 1:
        score = 0.05
        msg   = "Low alcohol intake — within generally accepted limits."
    elif drinks_per_day <= 2:
        score = 0.25
        msg   = "Moderate alcohol intake reduces the liver's ability to process toxins."
    elif drinks_per_day <= 4:
        score = 0.55
        msg   = "High alcohol intake. Significant risk of alcoholic liver disease."
    else:
        score = 0.85
        msg   = "Very high alcohol intake. Severe risk of alcoholic hepatitis and cirrhosis."

    if years > 10:
        score = min(1.0, score * 1.35)
        msg  += f" {int(years)} years of regular drinking compounds cumulative liver damage significantly."
    elif years > 5:
        score = min(1.0, score * 1.15)
        msg  += f" {int(years)} years of regular drinking increases cumulative risk."

    if binge:
        score = min(1.0, score * 1.20)
        msg  += " Binge drinking pattern causes acute liver stress episodes."

    return round(score, 3), msg


def calculate_hepatitis_risk(data: Dict) -> Tuple[float, str]:
    """HBV/HCV exposure and vaccination status risk."""
    hbsag    = bool(data.get('hbsag_positive', False))
    hcv      = bool(data.get('hcv_positive',   False))
    vacc_hbv = bool(data.get('vaccinated_hbv', False))
    exposure = bool(data.get('exposure_risk',  False))
    family   = bool(data.get('family_history', False))

    if hbsag:
        return 0.92, "Active Hepatitis B infection detected. Requires immediate medical management."
    if hcv:
        return 0.92, "Active Hepatitis C infection detected. Requires immediate medical management."
    if not vacc_hbv and exposure:
        return 0.45, (
            "High HBV exposure risk without vaccination. "
            "Immediate testing and vaccination strongly recommended."
        )
    if not vacc_hbv and family:
        return 0.30, (
            "Family history of Hepatitis B without personal vaccination. "
            "Testing and vaccination recommended."
        )
    if not vacc_hbv:
        return 0.12, "No HBV vaccination recorded. Vaccination recommended — free at most Ugandan health centres."
    return 0.0, "Hepatitis B vaccination up to date. No known active infection."


def calculate_symptom_risk(symptoms: List[str]) -> Tuple[float, str, List[str]]:
    """
    Symptom-based risk scoring.
    Returns (score, explanation, emergency_symptoms_found).
    """
    emergency = [s for s in symptoms if s in EMERGENCY_SYMPTOMS]
    high      = [s for s in symptoms if s in HIGH_RISK_SYMPTOMS]
    moderate  = [s for s in symptoms if s in MODERATE_SYMPTOMS]

    if emergency:
        return 1.0, (
            f"EMERGENCY — critical symptoms present: "
            f"{', '.join(s.replace('_', ' ') for s in emergency)}. "
            "Seek immediate medical care."
        ), emergency

    score = 0.0
    if high:
        score += min(0.80, len(high) * 0.25)
    if moderate:
        score += min(0.40, len(moderate) * 0.10)
    score = min(1.0, score)

    if score > 0.65:
        msg = (f"Multiple high-risk liver symptoms reported: "
               f"{', '.join(s.replace('_',' ') for s in high)}. "
               "Clinical evaluation strongly recommended.")
    elif score > 0.25:
        msg = ("Concerning symptoms noted. Screening and monitoring recommended.")
    elif score > 0:
        msg = ("Mild symptoms reported. Monitor and seek care if symptoms worsen.")
    else:
        msg = "No significant liver-related symptoms reported."

    return round(score, 3), msg, []


def calculate_medication_risk(data: Dict) -> Tuple[float, str]:
    """Hepatotoxic medication use risk."""
    otc_pain  = bool(data.get('otc_painkillers', False))
    freq      = data.get('painkiller_frequency', 'rarely')   # 'rarely'|'weekly'|'daily'
    tb_drugs  = bool(data.get('tb_treatment',    False))
    herbal    = bool(data.get('herbal_remedies', False))
    multi_med = bool(data.get('multiple_medications', False))

    score = 0.0
    notes: List[str] = []

    if otc_pain:
        if freq == 'daily':
            score += 0.42
            notes.append(
                "Daily OTC painkiller use (especially paracetamol/acetaminophen) "
                "can cause cumulative liver damage."
            )
        elif freq == 'weekly':
            score += 0.20
            notes.append("Regular weekly painkiller use should be monitored by a clinician.")

    if tb_drugs:
        score += 0.32
        notes.append(
            "TB treatment (rifampicin/isoniazid) can cause hepatotoxicity. "
            "Regular liver function monitoring is required during treatment."
        )

    if herbal:
        score += 0.18
        notes.append(
            "Herbal/traditional remedies can be hepatotoxic. "
            "Discuss with your healthcare provider."
        )

    if multi_med:
        score += 0.10
        notes.append(
            "Multiple concurrent medications increase drug-drug interaction risk "
            "and overall liver burden."
        )

    score = min(1.0, score)
    explanation = " ".join(notes) if notes else "Low medication-related liver risk identified."
    return round(score, 3), explanation


def calculate_environmental_risk(data: Dict) -> Tuple[float, str]:
    """
    Environmental hepatotoxin exposure — aflatoxin is particularly relevant in Uganda
    due to climate conditions and grain storage practices.
    """
    aflatoxin = bool(data.get('aflatoxin_exposure',  False))
    chemicals = bool(data.get('chemical_exposure',   False))
    unsafe_water = bool(data.get('unsafe_water',     False))

    score = 0.0
    notes: List[str] = []

    if aflatoxin:
        score += 0.40
        notes.append(
            "Aflatoxin exposure (from poorly stored maize, groundnuts, cassava) "
            "is a leading liver cancer risk factor in Uganda and East Africa."
        )

    if chemicals:
        score += 0.28
        notes.append(
            "Regular exposure to agricultural pesticides or industrial solvents "
            "can progressively damage liver function."
        )

    if unsafe_water:
        score += 0.18
        notes.append(
            "Unsafe drinking water increases risk of Hepatitis A, E, and "
            "other liver-affecting infections."
        )

    score = min(1.0, score)
    explanation = " ".join(notes) if notes else (
        "No significant environmental liver risk factors identified based on reported information."
    )
    return round(score, 3), explanation


def calculate_nutrition_risk(data: Dict) -> Tuple[float, str]:
    """BMI, diet quality, and metabolic risk."""
    bmi      = data.get('bmi', None)
    high_fat = bool(data.get('high_fat_diet', False))
    low_water = bool(data.get('low_water_intake', False))
    diabetes = bool(data.get('diabetes', False))

    score = 0.0
    notes: List[str] = []

    if bmi is not None:
        bmi = float(bmi)
        if bmi >= 35:
            score += 0.45
            notes.append(
                "Severe obesity (BMI ≥35) is a major risk factor for non-alcoholic "
                "fatty liver disease (NAFLD) and cirrhosis."
            )
        elif bmi >= 30:
            score += 0.28
            notes.append("Obesity (BMI 30–35) significantly increases risk of fatty liver disease.")
        elif bmi >= 25:
            score += 0.12
            notes.append("Overweight (BMI 25–30) slightly increases fatty liver risk.")

    if high_fat:
        score += 0.18
        notes.append(
            "High-fat, high-processed food diet promotes fat accumulation in the liver."
        )

    if low_water:
        score += 0.06
        notes.append("Inadequate hydration reduces the liver's ability to filter toxins efficiently.")

    if diabetes:
        score += 0.28
        notes.append(
            "Diabetes and insulin resistance are strongly associated with non-alcoholic "
            "fatty liver disease. Regular liver function monitoring is recommended."
        )

    score = min(1.0, score)
    explanation = " ".join(notes) if notes else "Nutritional risk profile appears low."
    return round(score, 3), explanation


def calculate_family_history_risk(data: Dict) -> Tuple[float, str]:
    """Genetic / familial risk factors."""
    hcc_family    = bool(data.get('liver_cancer_family',   False))
    cirrhosis_fam = bool(data.get('cirrhosis_family',      False))
    hbv_family    = bool(data.get('hbv_family',            False))

    score = 0.0
    notes: List[str] = []

    if hcc_family:
        score += 0.45
        notes.append(
            "Family history of liver cancer (HCC) significantly increases personal risk. "
            "Regular ultrasound screening is recommended."
        )
    if cirrhosis_fam:
        score += 0.30
        notes.append("Family history of liver cirrhosis is a risk indicator.")
    if hbv_family:
        score += 0.25
        notes.append(
            "Family history of Hepatitis B — testing and vaccination are strongly recommended."
        )

    score = min(1.0, score)
    explanation = " ".join(notes) if notes else "No significant family history of liver disease reported."
    return round(score, 3), explanation


def _normalize_input(data: Dict) -> Dict:
    """Accept flat OR nested assessment data and always return nested form."""
    nested_keys = ('hepatitis', 'alcohol', 'medications', 'environmental', 'nutrition', 'family_history')
    if any(k in data for k in nested_keys):
        return data
    return {
        'hepatitis': {
            'hbsag_positive': data.get('hbsag_positive', False),
            'hcv_positive':   data.get('hcv_positive',   False),
            'vaccinated_hbv': data.get('vaccinated_hbv', False),
            'exposure_risk':  data.get('hbv_exposure_risk', data.get('exposure_risk', False)),
            'family_history': data.get('hbv_family_history', data.get('family_history_hbv', False)),
        },
        'alcohol': {
            'drinks_per_day':  data.get('drinks_per_day', 0.0),
            'years_drinking':  data.get('years_drinking', 0),
            'binge_drinking':  data.get('binge_drinking', False),
        },
        'symptoms': data.get('symptoms', []),
        'medications': {
            'otc_painkillers':    data.get('otc_painkillers', False),
            'painkiller_frequency': data.get('painkiller_frequency', 'rarely'),
            'tb_treatment':       data.get('tb_treatment', False),
            'herbal_remedies':    data.get('herbal_remedies', False),
            'multiple_medications': data.get('multiple_medications', False),
        },
        'environmental': {
            'aflatoxin_exposure': data.get('aflatoxin_exposure', False),
            'chemical_exposure':  data.get('chemical_exposure', False),
            'unsafe_water':       data.get('unsafe_water', False),
        },
        'family_history': {
            'liver_cancer_family': data.get('liver_cancer_family', False),
            'cirrhosis_family':    data.get('cirrhosis_family', False),
            'hbv_family':          data.get('hbv_family_history', False),
        },
        'nutrition': {
            'bmi':           data.get('bmi', None),
            'high_fat_diet': data.get('high_fat_diet', False),
            'low_water_intake': data.get('low_water_intake', False),
            'diabetes':      data.get('diabetes', False),
        },
        'biomarkers': data.get('biomarkers', {}),
    }


# ── Recommendation generator ──────────────────────────────────────────────

def _generate_recommendations(
    risk_level: str,
    factors: List[RiskFactorResult],
    emergency_symptoms: List[str],
) -> List[str]:
    recs: List[str] = []

    if risk_level in ('critical', 'urgent') or emergency_symptoms:
        recs.append(
            "🚨 SEEK EMERGENCY CARE IMMEDIATELY — go to the nearest hospital "
            "emergency department or call 999 / 112."
        )
        recs.append(MEDICAL_DISCLAIMER)
        return recs

    # Universal
    recs.append(MEDICAL_DISCLAIMER)

    if risk_level == 'high':
        recs.append(
            "Schedule a Liver Function Test (LFT) and hepatitis panel at a health facility. "
            "Early detection significantly improves outcomes."
        )
        recs.append("Do not delay seeking medical evaluation.")

    if risk_level in ('moderate', 'high'):
        recs.append(
            "Consider attending a community liver screening event in your district. "
            "Ask your nearest Health Centre IV about the Hepatitis B test."
        )

    # Factor-specific
    elevated = [f for f in factors if f.is_elevated]
    for f in elevated:
        if f.category == 'alcohol':
            recs.append(
                "Reduce or eliminate alcohol. Even a 50% reduction in intake "
                "significantly lowers liver stress within weeks."
            )
        if f.category == 'hepatitis':
            recs.append(
                "Get tested for Hepatitis B and C. Vaccination is free at Ugandan "
                "government health centres."
            )
        if f.category == 'medication':
            recs.append(
                "Discuss your full medication list (including herbal remedies) "
                "with a pharmacist or clinician."
            )
        if f.category == 'environmental':
            recs.append(
                "Store grains and groundnuts in dry, sealed containers to reduce "
                "aflatoxin exposure. Discard discoloured or mouldy food."
            )
        if f.category == 'nutrition':
            recs.append(
                "A 5–10% reduction in body weight through diet and exercise can "
                "significantly improve fatty liver disease."
            )
        if f.category == 'family_history':
            recs.append(
                "Given your family history, consider annual liver ultrasound screening "
                "even in the absence of symptoms."
            )

    # Universal lifestyle tips
    recs.append("Drink at least 2 litres of clean water daily.")
    recs.append("Eat vegetables, fruits, and whole grains. Limit fried and processed foods.")
    recs.append("Get vaccinated against Hepatitis B if not already vaccinated — it is free in Uganda.")
    recs.append("Avoid sharing sharp objects (needles, razors, blades).")

    return recs


# ── Main entry point ──────────────────────────────────────────────────────

def run_risk_assessment(assessment_data: Dict) -> AssessmentResult:
    """
    Execute the full risk assessment pipeline.

    Args:
        assessment_data: Dict with keys:
            'hepatitis'     → hepatitis data dict
            'alcohol'       → alcohol data dict
            'symptoms'      → list[str] of symptom identifiers
            'medications'   → medication data dict
            'environmental' → environmental data dict
            'nutrition'     → nutrition data dict
            'family_history'→ family history dict

    Returns:
        AssessmentResult dataclass — NEVER a diagnosis.

    IMPORTANT: disclaimer_acknowledged must be set to True on the stored
               RiskAssessment model record before persisting.
    """
    factors:              List[RiskFactorResult] = []
    total_weighted_score: float = 0.0
    data_points:          int   = 0

    # Normalise flat or nested input
    assessment_data = _normalize_input(assessment_data)

    def _add_factor(
        name: str, category: str, score: float, explanation: str,
        value: Any = 'see explanation', unit: str = '',
    ):
        nonlocal total_weighted_score, data_points
        weight       = RISK_WEIGHTS.get(category, 0.0)
        contribution = score * weight
        factors.append(RiskFactorResult(
            name=name, category=category,
            value=str(value), unit=unit,
            weight=weight, contribution=contribution,
            is_elevated=(contribution > weight * 0.35),
            explanation=explanation,
        ))
        total_weighted_score += contribution
        data_points += 1

    # 1. Hepatitis status (weight 0.25)
    h_score, h_exp = calculate_hepatitis_risk(assessment_data.get('hepatitis', {}))
    _add_factor('hepatitis_status', 'hepatitis_status', h_score, h_exp,
                value=assessment_data.get('hepatitis', {}).get('hbsag_positive', False))

    # 2. Alcohol use (weight 0.20)
    a_score, a_exp = calculate_alcohol_risk(assessment_data.get('alcohol', {}))
    _add_factor('alcohol', 'alcohol', a_score, a_exp,
                value=assessment_data.get('alcohol', {}).get('drinks_per_day', 0),
                unit='drinks/day')

    # 3. Symptoms (weight 0.20)
    symptoms_list = assessment_data.get('symptoms', [])
    s_score, s_exp, emergency_syms = calculate_symptom_risk(symptoms_list)
    _add_factor('symptoms', 'symptoms', s_score, s_exp,
                value=', '.join(symptoms_list) if symptoms_list else 'none')

    # 4. Medications (weight 0.10)
    m_score, m_exp = calculate_medication_risk(assessment_data.get('medications', {}))
    _add_factor('medication', 'medication', m_score, m_exp)

    # 5. Environmental (weight 0.10)
    e_score, e_exp = calculate_environmental_risk(assessment_data.get('environmental', {}))
    _add_factor('environmental', 'environmental', e_score, e_exp)

    # 6. Family history (weight 0.05)
    fh_score, fh_exp = calculate_family_history_risk(assessment_data.get('family_history', {}))
    _add_factor('family_history', 'family_history', fh_score, fh_exp)

    # 7. Nutrition (weight 0.05)
    n_score, n_exp = calculate_nutrition_risk(assessment_data.get('nutrition', {}))
    _add_factor('nutrition', 'nutrition', n_score, n_exp)

    # Biomarkers (weight 0.05) — populated from wearable data when available
    biomarker_data = assessment_data.get('biomarkers', {})
    bio_score = float(biomarker_data.get('anomaly_score', 0.0))
    bio_exp   = biomarker_data.get('explanation', 'No wearable biomarker data available.')
    _add_factor('biomarkers', 'biomarkers', bio_score, bio_exp)

    # ── Derive risk level ─────────────────────────────────────────────────
    overall = min(1.0, total_weighted_score)

    # Factor domination: a single very high-risk factor elevates overall level
    # regardless of what the weighted average produces.
    max_raw: Dict[str, float] = {}
    for f in factors:
        if f.weight > 0:
            max_raw[f.category] = f.contribution / f.weight

    critical_dominate = any(s >= 0.90 for s in max_raw.values())
    high_dominate     = any(s >= 0.70 for s in max_raw.values())

    if emergency_syms:
        risk_level = 'critical'
        overall    = 1.0
    elif critical_dominate:
        risk_level = 'critical'
        overall    = max(overall, 0.85)
    elif high_dominate:
        risk_level = 'high'
        overall    = max(overall, 0.55)
    elif overall < 0.10:
        risk_level = 'minimal'
    elif overall < 0.25:
        risk_level = 'low'
    elif overall < 0.55:
        risk_level = 'moderate'
    elif overall < 0.80:
        risk_level = 'high'
    else:
        risk_level = 'urgent'

    # ── Confidence ────────────────────────────────────────────────────────
    confidence = round(min(1.0, data_points / len(RISK_WEIGHTS)), 3)

    # ── Explanation ───────────────────────────────────────────────────────
    elevated_names = [f.name for f in factors if f.is_elevated]
    if risk_level in ('critical', 'urgent'):
        explanation = (
            "CRITICAL RISK DETECTED. Emergency symptoms or critical risk factors identified. "
            "Seek immediate medical evaluation — do not delay."
        )
    elif risk_level == 'high':
        explanation = (
            f"HIGH RISK: Elevated factors — {', '.join(elevated_names)}. "
            "Professional liver health evaluation is strongly recommended."
        )
    elif risk_level == 'moderate':
        explanation = (
            f"MODERATE RISK: Concerning patterns detected. "
            "Liver health screening and lifestyle changes are recommended."
        )
    elif risk_level == 'low':
        explanation = (
            "LOW RISK: No major liver risk factors identified based on the "
            "information provided. Continue healthy habits and consider routine screening."
        )
    else:  # minimal
        explanation = (
            "MINIMAL RISK: No significant liver risk factors identified. "
            "Continue healthy habits."
        )

    # ── Referral ──────────────────────────────────────────────────────────
    requires_referral = risk_level in ('high', 'urgent', 'critical')
    if risk_level in ('critical', 'urgent') or emergency_syms:
        referral_urgency = 'emergency'
    elif risk_level == 'high':
        referral_urgency = 'urgent'
    elif risk_level == 'moderate':
        referral_urgency = 'routine'
    else:
        referral_urgency = None

    recommendations = _generate_recommendations(risk_level, factors, emergency_syms)

    return AssessmentResult(
        risk_level=risk_level,
        overall_score=round(overall, 3),
        confidence_level=confidence,
        explanation=explanation,
        recommendations=recommendations,
        requires_referral=requires_referral,
        referral_urgency=referral_urgency,
        factors=factors,
        emergency_symptoms=emergency_syms,
        disclaimer=MEDICAL_DISCLAIMER,
    )
