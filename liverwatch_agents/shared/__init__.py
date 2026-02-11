"""
LiverWatch - Shared Tools for All Agents
========================================

Common tools used across multiple agents.
"""

from datetime import datetime
from typing import Optional

# ============================================================================
# KNOWLEDGE BASE - Liver Health Information
# ============================================================================

LIVER_CONDITIONS = {
    "hepatitis_b": {
        "name": "Hepatitis B",
        "description": "Viral infection affecting the liver",
        "symptoms": ["fatigue", "jaundice", "dark_urine", "abdominal_pain", "nausea", "joint_pain"],
        "risk_factors": ["unvaccinated", "healthcare_worker", "multiple_partners", "iv_drug_use"],
        "urgency": "moderate",
        "treatable": True,
        "treatment": "Antiviral medications can manage the infection. Vaccination prevents it."
    },
    "hepatitis_c": {
        "name": "Hepatitis C", 
        "description": "Blood-borne viral infection",
        "symptoms": ["fatigue", "jaundice", "dark_urine", "abdominal_pain", "nausea"],
        "risk_factors": ["blood_transfusion_before_1992", "iv_drug_use", "tattoos_unsterile"],
        "urgency": "moderate",
        "treatable": True,
        "treatment": "Modern antivirals cure over 95% of cases within 8-12 weeks."
    },
    "fatty_liver": {
        "name": "Fatty Liver Disease (NAFLD/NASH)",
        "description": "Fat accumulation in liver cells",
        "symptoms": ["fatigue", "abdominal_discomfort", "enlarged_liver"],
        "risk_factors": ["obesity", "diabetes", "high_cholesterol", "sedentary_lifestyle"],
        "urgency": "low",
        "treatable": True,
        "treatment": "Lifestyle changes: weight loss, exercise, healthy diet. Often reversible."
    },
    "cirrhosis": {
        "name": "Cirrhosis",
        "description": "Severe scarring of the liver",
        "symptoms": ["jaundice", "fatigue", "easy_bruising", "swelling", "confusion", "weight_loss"],
        "risk_factors": ["chronic_hepatitis", "alcohol_abuse", "fatty_liver"],
        "urgency": "high",
        "treatable": False,
        "treatment": "Cannot be reversed but progression can be slowed. May need transplant."
    },
    "liver_cancer": {
        "name": "Hepatocellular Carcinoma",
        "description": "Primary liver cancer",
        "symptoms": ["weight_loss", "abdominal_pain", "jaundice", "fatigue", "loss_of_appetite"],
        "risk_factors": ["cirrhosis", "chronic_hepatitis_b", "chronic_hepatitis_c"],
        "urgency": "critical",
        "treatable": True,
        "treatment": "Surgery, transplant, ablation, or systemic therapy depending on stage."
    }
}

SYMPTOM_MAPPING = {
    "yellow_skin": "jaundice",
    "yellow_eyes": "jaundice", 
    "yellowing": "jaundice",
    "tired": "fatigue",
    "exhausted": "fatigue",
    "no_energy": "fatigue",
    "stomach_pain": "abdominal_pain",
    "belly_pain": "abdominal_pain",
    "right_side_pain": "abdominal_pain",
    "dark_pee": "dark_urine",
    "brown_urine": "dark_urine",
    "throwing_up": "nausea",
    "feel_sick": "nausea",
    "itchy": "itching",
    "itchy_skin": "itching",
    "swollen_belly": "swelling",
    "swollen_legs": "swelling",
    "confused": "confusion",
    "bruise_easily": "easy_bruising"
}

LIVER_FRIENDLY_FOODS = {
    "highly_recommended": [
        {"name": "Leafy greens", "examples": "Spinach, kale, dodo (amaranth), nakati", "benefit": "Rich in antioxidants"},
        {"name": "Cruciferous vegetables", "examples": "Cabbage, broccoli, cauliflower", "benefit": "Support detoxification"},
        {"name": "Fatty fish", "examples": "Tilapia, Nile perch", "benefit": "Omega-3 fatty acids reduce inflammation"},
        {"name": "Nuts", "examples": "Groundnuts, cashews (unsalted)", "benefit": "Healthy fats and vitamin E"},
        {"name": "Coffee", "examples": "Black coffee, 1-2 cups daily", "benefit": "May protect against liver disease"},
        {"name": "Whole grains", "examples": "Millet, sorghum, brown rice", "benefit": "Fiber and steady energy"},
        {"name": "Beans and legumes", "examples": "Kidney beans, cowpeas, lentils", "benefit": "Plant protein"},
        {"name": "Fruits", "examples": "Papaya, watermelon, citrus fruits", "benefit": "Antioxidants and hydration"}
    ],
    "foods_to_limit": [
        {"name": "Alcohol", "reason": "Direct liver toxin"},
        {"name": "Fried foods", "reason": "High in unhealthy fats"},
        {"name": "Added sugars", "reason": "Promotes fatty liver"},
        {"name": "Red meat", "reason": "Hard to metabolize"},
        {"name": "Salt", "reason": "Causes fluid retention"},
        {"name": "Processed foods", "reason": "High sodium and preservatives"}
    ]
}

UGANDA_HOSPITALS = [
    {
        "name": "Mulago National Referral Hospital",
        "location": "Kampala",
        "specialties": ["Gastroenterology", "Hepatology", "General Medicine"],
        "phone": "+256 414 541 884",
        "type": "Public"
    },
    {
        "name": "Nakasero Hospital",
        "location": "Kampala", 
        "specialties": ["Liver diagnostics", "Hepatology"],
        "phone": "+256 312 256 001",
        "type": "Private"
    },
    {
        "name": "Uganda Cancer Institute",
        "location": "Kampala",
        "specialties": ["Liver cancer", "Oncology"],
        "phone": "+256 414 540 410",
        "type": "Public"
    },
    {
        "name": "Mengo Hospital",
        "location": "Kampala",
        "specialties": ["General Medicine", "Liver screening"],
        "phone": "+256 414 270 222",
        "type": "Private"
    }
]

# ============================================================================
# LAB REFERENCE RANGES
# ============================================================================

LAB_REFERENCE_RANGES = {
    "ALT": {
        "name": "Alanine Aminotransferase",
        "unit": "U/L",
        "normal_range": (7, 56),
        "mild_elevation": (56, 150),
        "moderate_elevation": (150, 500),
        "severe_elevation": (500, float('inf')),
        "interpretation": {
            "normal": "Liver cells appear healthy",
            "mild": "Minor liver stress - may be temporary",
            "moderate": "Significant liver inflammation - needs evaluation",
            "severe": "Serious liver damage - urgent medical attention needed"
        }
    },
    "AST": {
        "name": "Aspartate Aminotransferase", 
        "unit": "U/L",
        "normal_range": (10, 40),
        "mild_elevation": (40, 120),
        "moderate_elevation": (120, 400),
        "severe_elevation": (400, float('inf')),
        "interpretation": {
            "normal": "No significant liver or muscle damage",
            "mild": "Minor elevation - could be liver or muscle",
            "moderate": "Liver inflammation likely",
            "severe": "Serious liver or heart damage"
        }
    },
    "bilirubin_total": {
        "name": "Total Bilirubin",
        "unit": "mg/dL",
        "normal_range": (0.1, 1.2),
        "mild_elevation": (1.2, 3.0),
        "moderate_elevation": (3.0, 10.0),
        "severe_elevation": (10.0, float('inf')),
        "interpretation": {
            "normal": "Liver processing bilirubin normally",
            "mild": "Slight increase - may cause mild jaundice",
            "moderate": "Visible jaundice - liver function impaired", 
            "severe": "Severe jaundice - liver failure risk"
        }
    },
    "albumin": {
        "name": "Albumin",
        "unit": "g/dL",
        "normal_range": (3.5, 5.0),
        "low": (2.5, 3.5),
        "very_low": (0, 2.5),
        "interpretation": {
            "normal": "Liver producing proteins normally",
            "low": "Reduced liver synthetic function",
            "very_low": "Liver failure - not producing enough protein"
        }
    },
    "platelets": {
        "name": "Platelet Count",
        "unit": "x10^9/L",
        "normal_range": (150, 400),
        "low": (100, 150),
        "very_low": (0, 100),
        "interpretation": {
            "normal": "Normal blood clotting capacity",
            "low": "May indicate liver fibrosis or cirrhosis",
            "very_low": "Advanced liver disease likely - bleeding risk"
        }
    }
}


def get_current_timestamp() -> str:
    """Get current timestamp for logging."""
    return datetime.now().isoformat()


def normalize_symptom(symptom: str) -> str:
    """Normalize symptom names to standard terms."""
    symptom_lower = symptom.lower().strip().replace(" ", "_")
    return SYMPTOM_MAPPING.get(symptom_lower, symptom_lower)


def get_urgency_level(symptoms: list[str]) -> dict:
    """Determine urgency based on symptoms."""
    normalized = [normalize_symptom(s) for s in symptoms]
    
    critical_symptoms = {"confusion", "severe_bleeding", "vomiting_blood"}
    high_symptoms = {"jaundice", "severe_abdominal_pain", "persistent_vomiting"}
    
    if any(s in critical_symptoms for s in normalized):
        return {
            "level": "critical",
            "message": "Seek emergency medical care immediately",
            "action": "Go to the nearest hospital or call 999/112"
        }
    elif any(s in high_symptoms for s in normalized):
        return {
            "level": "high", 
            "message": "See a doctor within 24-48 hours",
            "action": "Schedule an urgent appointment"
        }
    elif len(normalized) >= 3:
        return {
            "level": "moderate",
            "message": "Schedule an appointment this week",
            "action": "See your healthcare provider soon"
        }
    else:
        return {
            "level": "low",
            "message": "Monitor symptoms and maintain healthy habits",
            "action": "Track symptoms and seek care if they worsen"
        }
