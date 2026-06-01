"""
Test script for LiverWatch Google ADK Agents
=============================================

Run this after fixing the email-validator dependency to test the agents.

Usage:
    python test_agents.py
"""

import os
import sys

def test_imports():
    """Test if all agent imports work."""
    print("=" * 60)
    print("Testing Agent Imports...")
    print("=" * 60)
    
    try:
        from google.adk import Agent, Runner
        print("✅ google.adk imports successful")
        print(f"   - Agent: {Agent}")
        print(f"   - Runner: {Runner}")
    except ImportError as e:
        print(f"❌ Failed to import google.adk: {e}")
        return False
    
    try:
        from liverwatch_agents import root_agent
        print("✅ Root agent import successful")
        print(f"   - Agent name: {root_agent.name}")
        print(f"   - Model: {root_agent.model}")
    except ImportError as e:
        print(f"❌ Failed to import root_agent: {e}")
        return False
    
    try:
        from liverwatch_agents.sub_agents import (
            symptom_checker_agent,
            diet_advisor_agent,
            lab_interpreter_agent,
            health_educator_agent,
            healthcare_finder_agent
        )
        print("✅ All sub-agents imported successfully")
        print(f"   - Symptom Checker: {symptom_checker_agent.name}")
        print(f"   - Diet Advisor: {diet_advisor_agent.name}")
        print(f"   - Lab Interpreter: {lab_interpreter_agent.name}")
        print(f"   - Health Educator: {health_educator_agent.name}")
        print(f"   - Healthcare Finder: {healthcare_finder_agent.name}")
    except ImportError as e:
        print(f"❌ Failed to import sub-agents: {e}")
        return False
    
    print("\n✅ All imports successful!\n")
    return True


def test_api_key():
    """Check if Google API key is configured."""
    print("=" * 60)
    print("Checking API Key Configuration...")
    print("=" * 60)
    
    api_key = os.environ.get('GOOGLE_API_KEY')
    if api_key:
        print(f"✅ GOOGLE_API_KEY is set (length: {len(api_key)} chars)")
    else:
        print("⚠️  GOOGLE_API_KEY is not set")
        print("   Set it in .env file or environment:")
        print("   GOOGLE_API_KEY=your_key_here")
        return False
    
    print()
    return True


def test_tools():
    """Test if tools are working."""
    print("=" * 60)
    print("Testing Agent Tools...")
    print("=" * 60)
    
    try:
        from liverwatch_agents.tools import (
            assess_symptoms,
            get_diet_recommendations,
            interpret_lab_result
        )
        
        print("✅ Tool imports successful")
        
        # Test symptom assessment
        print("\n📊 Testing assess_symptoms...")
        result = assess_symptoms(
            symptoms=["fatigue", "yellow eyes"],
            duration_days=5
        )
        print(f"   Urgency: {result['urgency']}")
        print(f"   Conditions found: {len(result['possible_conditions'])}")
        
        # Test diet recommendations
        print("\n🥗 Testing get_diet_recommendations...")
        diet_result = get_diet_recommendations(
            condition="fatty_liver"
        )
        print(f"   Recommendations provided: {len(diet_result.get('foods_to_eat', []))} foods")
        
        # Test lab interpretation
        print("\n🔬 Testing interpret_lab_result...")
        lab_result = interpret_lab_result(
            test_name="ALT",
            value=150
        )
        print(f"   Interpretation: {lab_result.get('interpretation', 'N/A')}")
        
        print("\n✅ All tool tests passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_flask_import():
    """Test if Flask app can be imported."""
    print("=" * 60)
    print("Testing Flask Application...")
    print("=" * 60)
    
    try:
        from app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
        print(f"   - App name: {app.name}")
        print(f"   - Debug mode: {app.debug}")
        
        # Check if agent blueprint is registered
        blueprints = list(app.blueprints.keys())
        if 'agents' in blueprints:
            print("✅ Agents blueprint registered")
        else:
            print("⚠️  Agents blueprint not found")
        
        print(f"   - Registered blueprints: {', '.join(blueprints)}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + " " * 10 + "LiverWatch Agent System Test" + " " * 20 + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("API Key", test_api_key()))
    results.append(("Tools", test_tools()))
    results.append(("Flask App", test_flask_import()))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Your agent system is ready to use.\n")
        print("Next steps:")
        print("1. Run the Flask app: python run.py")
        print("2. Test the API endpoint: POST to /api/agents/chat")
        print("3. Check AGENTS_DOCUMENTATION.md for more info")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.\n")
        print("Common fixes:")
        print("1. Install email-validator>=2.0: pip install -U email-validator")
        print("2. Set GOOGLE_API_KEY in .env file")
        print("3. Check AGENTS_DOCUMENTATION.md for troubleshooting")
        return 1


if __name__ == "__main__":
    sys.exit(main())
