"""
LiverWatch - Agent Tools
========================

Tools that agents can use to perform actions and retrieve information.
Following Google ADK patterns for tool definitions.
"""

from typing import Optional
from .shared import (
    LIVER_CONDITIONS,
    LIVER_FRIENDLY_FOODS,
    LAB_REFERENCE_RANGES,
    UGANDA_HOSPITALS,
    normalize_symptom,
    get_urgency_level,
    get_current_timestamp
)


# ============================================================================
# SYMPTOM ASSESSMENT TOOLS
# ============================================================================

def assess_symptoms(symptoms: list[str], duration_days: int = 0) -> dict:
    """
    Assess a list of symptoms and provide initial guidance.
    
    Args:
        symptoms: List of symptoms the user is experiencing
        duration_days: How many days symptoms have persisted
        
    Returns:
        Assessment with urgency level and recommendations
    """
    normalized_symptoms = [normalize_symptom(s) for s in symptoms]
    urgency = get_urgency_level(symptoms)
    
    # Find matching conditions
    possible_conditions = []
    for condition_id, condition in LIVER_CONDITIONS.items():
        matches = set(normalized_symptoms) & set(condition["symptoms"])
        if matches:
            match_score = len(matches) / len(condition["symptoms"])
            possible_conditions.append({
                "condition": condition["name"],
                "match_score": round(match_score * 100),
                "matching_symptoms": list(matches),
                "urgency": condition["urgency"]
            })
    
    # Sort by match score
    possible_conditions.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Duration factor
    duration_warning = None
    if duration_days > 14:
        duration_warning = "Symptoms lasting more than 2 weeks should be evaluated by a doctor."
    elif duration_days > 7:
        duration_warning = "A week of symptoms warrants medical attention."
    
    return {
        "timestamp": get_current_timestamp(),
        "symptoms_reported": symptoms,
        "symptoms_normalized": normalized_symptoms,
        "urgency": urgency,
        "possible_conditions": possible_conditions[:3],  # Top 3
        "duration_warning": duration_warning,
        "disclaimer": "This is not a diagnosis. Please consult a healthcare provider."
    }


def get_symptom_info(symptom: str) -> dict:
    """
    Get detailed information about a specific symptom.
    
    Args:
        symptom: The symptom to look up
        
    Returns:
        Information about the symptom and related conditions
    """
    normalized = normalize_symptom(symptom)
    
    related_conditions = []
    for condition_id, condition in LIVER_CONDITIONS.items():
        if normalized in condition["symptoms"]:
            related_conditions.append({
                "name": condition["name"],
                "description": condition["description"],
                "urgency": condition["urgency"]
            })
    
    return {
        "symptom": symptom,
        "normalized_name": normalized,
        "related_liver_conditions": related_conditions,
        "general_advice": "Track when this symptom occurs and what makes it better or worse."
    }


# ============================================================================
# LAB RESULTS INTERPRETATION TOOLS
# ============================================================================

def interpret_lab_result(test_name: str, value: float) -> dict:
    """
    Interpret a single lab test result.
    
    Args:
        test_name: Name of the test (ALT, AST, bilirubin, etc.)
        value: The numeric result value
        
    Returns:
        Interpretation of the result
    """
    test_key = test_name.upper().replace(" ", "_")
    
    # Map common names
    name_mapping = {
        "ALT": "ALT",
        "SGPT": "ALT",
        "AST": "AST", 
        "SGOT": "AST",
        "BILIRUBIN": "bilirubin_total",
        "TOTAL_BILIRUBIN": "bilirubin_total",
        "ALBUMIN": "albumin",
        "PLATELETS": "platelets",
        "PLT": "platelets"
    }
    
    test_key = name_mapping.get(test_key, test_key.lower())
    
    if test_key not in LAB_REFERENCE_RANGES:
        return {
            "test": test_name,
            "value": value,
            "status": "unknown",
            "message": f"Test '{test_name}' not in our database. Please consult your doctor."
        }
    
    ref = LAB_REFERENCE_RANGES[test_key]
    
    # Determine status
    if test_key in ["albumin", "platelets"]:
        # These are concerning when LOW
        if value >= ref["normal_range"][0] and value <= ref["normal_range"][1]:
            status = "normal"
        elif test_key == "albumin":
            status = "low" if value >= ref.get("very_low", (0, 0))[1] else "very_low"
        else:
            status = "low" if value >= ref.get("very_low", (0, 0))[1] else "very_low"
    else:
        # These are concerning when HIGH
        if value >= ref["normal_range"][0] and value <= ref["normal_range"][1]:
            status = "normal"
        elif value <= ref.get("mild_elevation", (0, 0))[1]:
            status = "mild"
        elif value <= ref.get("moderate_elevation", (0, 0))[1]:
            status = "moderate"
        else:
            status = "severe"
    
    return {
        "test": ref["name"],
        "value": value,
        "unit": ref["unit"],
        "normal_range": f"{ref['normal_range'][0]}-{ref['normal_range'][1]} {ref['unit']}",
        "status": status,
        "interpretation": ref["interpretation"].get(status, "Consult your doctor"),
        "disclaimer": "Lab interpretation requires clinical context. Always discuss results with your healthcare provider."
    }


def interpret_liver_panel(results: dict) -> dict:
    """
    Interpret a complete liver function panel.
    
    Args:
        results: Dictionary with test names as keys and values as values
                Example: {"ALT": 85, "AST": 45, "bilirubin": 1.5}
                
    Returns:
        Complete interpretation with overall assessment
    """
    interpretations = []
    concerns = []
    
    for test_name, value in results.items():
        result = interpret_lab_result(test_name, value)
        interpretations.append(result)
        
        if result.get("status") not in ["normal", "unknown"]:
            concerns.append({
                "test": result.get("test", test_name),
                "status": result.get("status"),
                "interpretation": result.get("interpretation")
            })
    
    # Overall assessment
    if not concerns:
        overall = "All tested values appear within normal limits."
        urgency = "low"
    elif any(c["status"] in ["severe", "very_low"] for c in concerns):
        overall = "Some values are significantly abnormal. Medical evaluation is strongly recommended."
        urgency = "high"
    else:
        overall = "Some values are outside normal range. Follow up with your healthcare provider."
        urgency = "moderate"
    
    return {
        "timestamp": get_current_timestamp(),
        "individual_results": interpretations,
        "concerns": concerns,
        "overall_assessment": overall,
        "urgency": urgency,
        "next_steps": [
            "Discuss these results with your doctor",
            "Keep a copy of your lab results for future reference",
            "Ask about any necessary follow-up tests"
        ],
        "disclaimer": "This is an educational interpretation only. Your doctor should provide the official interpretation."
    }


# ============================================================================
# DIET AND NUTRITION TOOLS
# ============================================================================

def get_diet_recommendations(condition: Optional[str] = None) -> dict:
    """
    Get liver-friendly diet recommendations.
    
    Args:
        condition: Specific liver condition (optional)
        
    Returns:
        Diet recommendations
    """
    recommendations = {
        "foods_to_eat": LIVER_FRIENDLY_FOODS["highly_recommended"],
        "foods_to_avoid": LIVER_FRIENDLY_FOODS["foods_to_limit"],
        "general_tips": [
            "Eat small, frequent meals instead of large ones",
            "Stay well hydrated with clean water",
            "Limit salt intake to reduce fluid retention",
            "Choose lean proteins over fatty meats",
            "Include colorful vegetables in every meal"
        ]
    }
    
    # Condition-specific advice
    if condition:
        condition_lower = condition.lower()
        if "fatty" in condition_lower or "nafld" in condition_lower:
            recommendations["condition_specific"] = [
                "Weight loss (even 5-10%) can significantly improve fatty liver",
                "Avoid all added sugars and sweetened beverages",
                "Increase fiber intake through whole grains and vegetables",
                "Exercise at least 150 minutes per week"
            ]
        elif "hepatitis" in condition_lower:
            recommendations["condition_specific"] = [
                "Absolutely no alcohol - even small amounts can worsen liver damage",
                "Eat adequate protein to help liver repair",
                "Avoid raw or undercooked shellfish",
                "Take medications exactly as prescribed"
            ]
        elif "cirrhosis" in condition_lower:
            recommendations["condition_specific"] = [
                "Strict sodium restriction (usually under 2g/day)",
                "May need protein restriction if experiencing confusion",
                "Small, frequent meals are easier on the liver",
                "Avoid alcohol completely - critical for survival"
            ]
    
    return {
        "timestamp": get_current_timestamp(),
        **recommendations,
        "disclaimer": "These are general guidelines. Work with a dietitian for a personalized plan."
    }


def get_recipe_suggestion(meal_type: str = "any", restrictions: list[str] = None) -> dict:
    """
    Get a liver-friendly recipe suggestion.
    
    Args:
        meal_type: breakfast, lunch, dinner, snack, or any
        restrictions: dietary restrictions (vegetarian, no_fish, etc.)
        
    Returns:
        Recipe suggestion
    """
    recipes = {
        "breakfast": [
            {
                "name": "Millet Porridge (Obushera)",
                "ingredients": ["1 cup millet flour", "4 cups water", "lemon juice", "optional honey"],
                "instructions": "Mix flour with cold water, add to boiling water, stir 10 mins, add lemon",
                "liver_benefits": "Whole grain, B vitamins, gentle on digestion"
            },
            {
                "name": "Fruit and Groundnut Bowl",
                "ingredients": ["Papaya cubes", "Banana slices", "Crushed groundnuts", "Honey drizzle"],
                "instructions": "Combine fruits, top with groundnuts and honey",
                "liver_benefits": "Antioxidants, healthy fats, natural energy"
            }
        ],
        "lunch": [
            {
                "name": "Steamed Fish with Vegetables",
                "ingredients": ["Tilapia fillet", "Tomatoes", "Onions", "Dodo (amaranth)", "Lemon, ginger"],
                "instructions": "Season fish, layer vegetables in pot, steam 20-25 minutes",
                "liver_benefits": "Lean protein, omega-3s, low fat"
            },
            {
                "name": "Bean and Matooke Katogo",
                "ingredients": ["Beans", "Green bananas", "Tomatoes", "Onion", "Olive oil"],
                "instructions": "Cook beans, sauté vegetables, add matooke, simmer until tender",
                "liver_benefits": "Plant protein, fiber, turmeric anti-inflammatory"
            }
        ],
        "dinner": [
            {
                "name": "Grilled Chicken with Greens",
                "ingredients": ["Chicken breast", "Nakati or sukuma wiki", "Garlic", "Lemon"],
                "instructions": "Grill chicken, steam greens with garlic, serve with lemon",
                "liver_benefits": "Lean protein, antioxidant greens"
            }
        ],
        "snack": [
            {
                "name": "Fresh Fruit with Groundnuts",
                "ingredients": ["Mango slices", "Roasted groundnuts (unsalted)"],
                "liver_benefits": "Vitamins, healthy fats, no added sugar"
            }
        ]
    }
    
    if meal_type.lower() == "any":
        import random
        meal_type = random.choice(list(recipes.keys()))
    
    meal_recipes = recipes.get(meal_type.lower(), recipes["lunch"])
    
    # Filter by restrictions if provided
    if restrictions:
        restrictions_lower = [r.lower() for r in restrictions]
        if "vegetarian" in restrictions_lower or "no_meat" in restrictions_lower:
            meal_recipes = [r for r in meal_recipes if "chicken" not in r["name"].lower() and "fish" not in r["name"].lower()]
        if "no_fish" in restrictions_lower:
            meal_recipes = [r for r in meal_recipes if "fish" not in r["name"].lower()]
    
    if not meal_recipes:
        meal_recipes = recipes["snack"]  # Fallback
    
    import random
    selected = random.choice(meal_recipes) if meal_recipes else meal_recipes[0]
    
    return {
        "meal_type": meal_type,
        "recipe": selected,
        "tip": "Cooking at home lets you control ingredients and avoid excess salt and oil."
    }


# ============================================================================
# HEALTHCARE FACILITY TOOLS
# ============================================================================

def find_healthcare_facilities(
    location: str = "Kampala",
    specialty: Optional[str] = None
) -> dict:
    """
    Find healthcare facilities in Uganda.
    
    Args:
        location: City or region
        specialty: Specific specialty needed
        
    Returns:
        List of matching facilities
    """
    results = []
    
    for hospital in UGANDA_HOSPITALS:
        # Location match
        if location.lower() in hospital["location"].lower():
            # Specialty match
            if specialty:
                if any(specialty.lower() in s.lower() for s in hospital["specialties"]):
                    results.append(hospital)
            else:
                results.append(hospital)
    
    # If no exact location match, return all
    if not results:
        results = UGANDA_HOSPITALS
    
    return {
        "search_location": location,
        "search_specialty": specialty,
        "facilities_found": len(results),
        "facilities": results,
        "emergency_numbers": {
            "general_emergency": "999 or 112",
            "ambulance": "911"
        },
        "tip": "Call ahead to confirm services and schedule appointments."
    }


# ============================================================================
# HEALTH TRACKING TOOLS  
# ============================================================================

def create_health_log_entry(
    user_message: str,
    symptoms: list[str] = None,
    mood: str = None,
    notes: str = None
) -> dict:
    """
    Create a health log entry from user input.
    
    Args:
        user_message: The user's original message
        symptoms: Any symptoms mentioned
        mood: User's reported mood
        notes: Additional notes
        
    Returns:
        Structured health log entry
    """
    return {
        "timestamp": get_current_timestamp(),
        "user_input": user_message,
        "symptoms": symptoms or [],
        "mood": mood,
        "notes": notes,
        "followup_suggested": len(symptoms or []) >= 2,
        "message": "Health log entry created. Remember to share this with your healthcare provider."
    }


def get_health_education(topic: str) -> dict:
    """
    Get educational information about liver health topics.
    
    Args:
        topic: The topic to learn about
        
    Returns:
        Educational content
    """
    topics = {
        "hepatitis_b": {
            "title": "Understanding Hepatitis B",
            "overview": "Hepatitis B is a viral infection that attacks the liver. It can be acute (short-term) or chronic (long-term).",
            "transmission": ["Unprotected sex", "Sharing needles", "Mother to baby at birth", "Blood contact"],
            "prevention": ["Get vaccinated (3 doses)", "Use protection", "Don't share personal items like razors"],
            "treatment": "Antiviral medications can suppress the virus. Regular monitoring is important.",
            "uganda_context": "Uganda has high Hepatitis B prevalence (4.3%). Vaccination is now part of childhood immunization."
        },
        "fatty_liver": {
            "title": "Understanding Fatty Liver Disease",
            "overview": "Fatty liver occurs when too much fat accumulates in liver cells. It's increasingly common.",
            "causes": ["Obesity", "Type 2 diabetes", "High cholesterol", "Sedentary lifestyle"],
            "prevention": ["Maintain healthy weight", "Exercise regularly", "Limit sugar and processed foods"],
            "treatment": "Lifestyle changes are the main treatment. Weight loss of 5-10% can significantly improve the condition.",
            "uganda_context": "Rising obesity rates in urban Uganda are increasing fatty liver cases."
        },
        "liver_function": {
            "title": "What Your Liver Does",
            "overview": "The liver is your body's largest internal organ and performs over 500 functions.",
            "functions": [
                "Filters blood from the digestive tract",
                "Produces bile for digestion",
                "Processes medications",
                "Stores vitamins and energy",
                "Makes proteins for blood clotting",
                "Removes toxins from the body"
            ],
            "why_it_matters": "A healthy liver is essential for life. Many liver conditions are preventable or treatable when caught early."
        }
    }
    
    topic_key = topic.lower().replace(" ", "_")
    
    if topic_key in topics:
        return {
            "topic": topic,
            "content": topics[topic_key],
            "related_topics": [k for k in topics.keys() if k != topic_key][:3]
        }
    else:
        return {
            "topic": topic,
            "message": f"I don't have detailed information on '{topic}'. Try asking about: hepatitis, fatty liver, or liver function.",
            "available_topics": list(topics.keys())
        }
