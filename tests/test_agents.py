"""
Agent System Unit Tests
========================

Tests for the Google ADK agent system including:
- Agent initialization and configuration
- Tool functionality
- Agent routing and orchestration
"""

import pytest
from liverwatch_agents.tools import (
    assess_symptoms,
    get_symptom_info,
    interpret_lab_result,
    get_diet_recommendations,
    find_healthcare_facilities,
    get_health_education
)


class TestAgentImports:
    """Test that all agents import correctly."""
    
    def test_root_agent_import(self):
        """Test root agent can be imported."""
        from liverwatch_agents import root_agent
        assert root_agent is not None
        assert root_agent.name == "liverwatch_assistant"
        assert "gemini" in root_agent.model.lower()
    
    def test_sub_agents_import(self):
        """Test all sub-agents can be imported."""
        from liverwatch_agents.sub_agents import (
            symptom_checker_agent,
            diet_advisor_agent,
            lab_interpreter_agent,
            health_educator_agent,
            healthcare_finder_agent
        )
        
        agents = [
            symptom_checker_agent,
            diet_advisor_agent,
            lab_interpreter_agent,
            health_educator_agent,
            healthcare_finder_agent
        ]
        
        for agent in agents:
            assert agent is not None
            assert hasattr(agent, 'name')
            assert hasattr(agent, 'model')


class TestSymptomTools:
    """Test symptom assessment tools."""
    
    def test_assess_mild_symptoms(self, sample_symptoms):
        """Test assessment of mild symptoms."""
        result = assess_symptoms(sample_symptoms['mild'], duration_days=2)
        
        assert 'urgency' in result
        assert 'possible_conditions' in result
        assert 'symptoms_reported' in result
        assert result['urgency']['level'] in ['low', 'medium', 'high']
    
    def test_assess_severe_symptoms(self, sample_symptoms):
        """Test assessment of severe symptoms requiring urgent care."""
        result = assess_symptoms(sample_symptoms['severe'], duration_days=1)
        
        assert 'urgency' in result
        assert result['urgency']['level'] in ['high', 'critical']
        assert len(result['possible_conditions']) > 0
    
    def test_assess_symptoms_with_duration(self):
        """Test that duration affects assessment."""
        symptoms = ['fatigue', 'nausea']
        
        short_duration = assess_symptoms(symptoms, duration_days=2)
        long_duration = assess_symptoms(symptoms, duration_days=20)
        
        assert 'duration_warning' in long_duration
        assert long_duration['duration_warning'] is not None
    
    def test_get_symptom_info(self):
        """Test getting information about specific symptoms."""
        result = get_symptom_info('jaundice')
        
        assert 'symptom' in result
        assert 'normalized_name' in result
        assert 'related_liver_conditions' in result
        assert len(result['related_liver_conditions']) > 0
    
    def test_empty_symptoms_list(self):
        """Test handling of empty symptoms list."""
        result = assess_symptoms([], duration_days=0)
        
        assert 'symptoms_reported' in result
        assert len(result['symptoms_reported']) == 0


class TestLabTools:
    """Test lab result interpretation tools."""
    
    def test_interpret_normal_alt(self):
        """Test interpretation of normal ALT value."""
        result = interpret_lab_result('ALT', 25)
        
        assert 'status' in result
        assert result['status'] == 'normal'
        assert 'interpretation' in result
    
    def test_interpret_elevated_alt(self):
        """Test interpretation of elevated ALT value."""
        result = interpret_lab_result('ALT', 150)
        
        assert 'status' in result
        assert result['status'] in ['mild', 'moderate', 'severe']
        assert 'interpretation' in result
        assert 'normal_range' in result
    
    def test_interpret_critical_alt(self):
        """Test interpretation of critically high ALT value."""
        result = interpret_lab_result('ALT', 500)
        
        assert 'status' in result
        assert result['status'] in ['moderate', 'severe']  # Depends on thresholds
        assert 'interpretation' in result
    
    def test_interpret_ast(self):
        """Test interpretation of AST values."""
        result = interpret_lab_result('AST', 200)
        
        assert 'test' in result
        assert 'value' in result
        assert result['value'] == 200
        assert 'status' in result
    
    def test_interpret_bilirubin(self):
        """Test interpretation of bilirubin values."""
        result = interpret_lab_result('bilirubin', 3.0)
        
        assert 'test' in result
        assert 'status' in result
        assert 'unit' in result
    
    def test_unknown_test(self):
        """Test handling of unknown test names."""
        result = interpret_lab_result('UNKNOWN_TEST', 100)
        
        assert 'status' in result
        assert result['status'] == 'unknown'
        assert 'message' in result


class TestDietTools:
    """Test diet recommendation tools."""
    
    def test_general_diet_recommendations(self):
        """Test getting general diet recommendations."""
        result = get_diet_recommendations()
        
        assert 'foods_to_eat' in result
        assert 'foods_to_avoid' in result
        assert 'general_tips' in result
        assert len(result['foods_to_eat']) > 0
        assert len(result['general_tips']) > 0
    
    def test_fatty_liver_recommendations(self):
        """Test diet recommendations for fatty liver."""
        result = get_diet_recommendations(condition='fatty_liver')
        
        assert 'condition_specific' in result
        assert len(result['condition_specific']) > 0
        assert any('weight loss' in tip.lower() for tip in result['condition_specific'])
    
    def test_hepatitis_recommendations(self):
        """Test diet recommendations for hepatitis."""
        result = get_diet_recommendations(condition='hepatitis')
        
        assert 'condition_specific' in result
        assert any('alcohol' in tip.lower() for tip in result['condition_specific'])
    
    def test_cirrhosis_recommendations(self):
        """Test diet recommendations for cirrhosis."""
        result = get_diet_recommendations(condition='cirrhosis')
        
        assert 'condition_specific' in result
        assert any('sodium' in tip.lower() for tip in result['condition_specific'])


class TestHealthEducation:
    """Test health education information retrieval."""
    
    def test_get_health_education(self):
        """Test getting health education information."""
        result = get_health_education('fatty_liver')
        
        assert 'topic' in result
        assert 'information' in result or 'content' in result


class TestHealthcareFinder:
    """Test healthcare facility finding functionality."""
    
    def test_find_facilities_default(self):
        """Test finding healthcare facilities."""
        result = find_healthcare_facilities()
        
        assert 'facilities' in result or 'hospitals' in result
    
    def test_find_facilities_kampala(self):
        """Test finding facilities in Kampala."""
        result = find_healthcare_facilities(location='Kampala')
        
        assert 'facilities' in result or 'hospitals' in result
        
        # Check facility structure if list is not empty
        hospitals = result.get('facilities', result.get('hospitals', []))
        if hospitals:
            facility = hospitals[0]
            assert 'name' in facility
