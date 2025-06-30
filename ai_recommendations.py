"""
AI-powered recommendation engine for personalized liver health suggestions
"""
import datetime
from models import HealthLog, User, Recipe
from typing import List, Dict, Any

class LiverHealthAI:
    """AI engine for personalized liver health recommendations"""
    
    def __init__(self):
        self.risk_factors = {
            'alcohol_intake': {'weight': 0.3, 'threshold': 2},
            'fatty_foods': {'weight': 0.25, 'threshold': 3},
            'sugar_intake': {'weight': 0.2, 'threshold': 50},
            'water_intake': {'weight': -0.15, 'threshold': 2},  # Negative weight - more water is better
            'exercise_level': {'weight': -0.1, 'threshold': 30}  # Negative weight - more exercise is better
        }
    
    def calculate_risk_score(self, user_id: int, days: int = 30) -> float:
        """Calculate liver health risk score based on recent health logs"""
        recent_date = datetime.datetime.now() - datetime.timedelta(days=days)
        health_logs = HealthLog.query.filter(
            HealthLog.user_id == user_id,
            HealthLog.date >= recent_date
        ).all()
        
        if not health_logs:
            return 0.5  # Neutral score if no data
        
        total_score = 0
        for log in health_logs:
            daily_score = 0
            
            # Calculate score based on each factor
            if log.alcohol_intake:
                if log.alcohol_intake > self.risk_factors['alcohol_intake']['threshold']:
                    daily_score += self.risk_factors['alcohol_intake']['weight']
            
            if log.fatty_foods:
                if log.fatty_foods > self.risk_factors['fatty_foods']['threshold']:
                    daily_score += self.risk_factors['fatty_foods']['weight']
            
            if log.sugar_intake:
                if log.sugar_intake > self.risk_factors['sugar_intake']['threshold']:
                    daily_score += self.risk_factors['sugar_intake']['weight']
            
            if log.water_intake:
                if log.water_intake < abs(self.risk_factors['water_intake']['threshold']):
                    daily_score += abs(self.risk_factors['water_intake']['weight'])
            
            if log.exercise_level:
                if log.exercise_level < abs(self.risk_factors['exercise_level']['threshold']):
                    daily_score += abs(self.risk_factors['exercise_level']['weight'])
            
            total_score += daily_score
        
        # Normalize score (0-1 range)
        avg_score = total_score / len(health_logs)
        return min(max(avg_score, 0), 1)
    
    def get_personalized_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Get personalized recommendations based on user's health data"""
        risk_score = self.calculate_risk_score(user_id)
        recommendations = []
        
        # Get recent health data
        recent_log = HealthLog.query.filter_by(user_id=user_id).order_by(HealthLog.date.desc()).first()
        
        if not recent_log:
            return [{
                'type': 'general',
                'title': 'Start Tracking Your Health',
                'message': 'Begin logging your daily habits to get personalized recommendations.',
                'priority': 'high'
            }]
        
        # High-risk recommendations
        if risk_score > 0.7:
            recommendations.append({
                'type': 'urgent',
                'title': 'Consult a Healthcare Professional',
                'message': 'Your recent health patterns indicate increased liver disease risk. Please consult a liver specialist.',
                'priority': 'urgent'
            })
        
        # Specific recommendations based on data
        if recent_log.alcohol_intake and recent_log.alcohol_intake > 2:
            recommendations.append({
                'type': 'lifestyle',
                'title': 'Reduce Alcohol Consumption',
                'message': f'Your alcohol intake ({recent_log.alcohol_intake} units) exceeds safe limits. Consider reducing to 1-2 units per week.',
                'priority': 'high'
            })
        
        if recent_log.water_intake and recent_log.water_intake < 2:
            recommendations.append({
                'type': 'nutrition',
                'title': 'Increase Water Intake',
                'message': 'Aim for at least 2-3 liters of water daily to support liver function.',
                'priority': 'medium'
            })
        
        if recent_log.exercise_level and recent_log.exercise_level < 30:
            recommendations.append({
                'type': 'fitness',
                'title': 'Increase Physical Activity',
                'message': 'Aim for at least 30 minutes of moderate exercise daily to improve liver health.',
                'priority': 'medium'
            })
        
        # Add recipe recommendations
        liver_friendly_recipes = Recipe.query.limit(3).all()
        if liver_friendly_recipes:
            recommendations.append({
                'type': 'nutrition',
                'title': 'Try These Liver-Friendly Recipes',
                'message': 'Based on your health data, these recipes can support your liver health.',
                'recipes': [{'title': r.title, 'id': r.id} for r in liver_friendly_recipes],
                'priority': 'low'
            })
        
        return recommendations
    
    def get_health_trends(self, user_id: int, days: int = 90) -> Dict[str, Any]:
        """Analyze health trends over time"""
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)
        health_logs = HealthLog.query.filter(
            HealthLog.user_id == user_id,
            HealthLog.date >= start_date
        ).order_by(HealthLog.date).all()
        
        if not health_logs:
            return {'status': 'insufficient_data'}
        
        # Calculate trends
        trends = {}
        factors = ['alcohol_intake', 'fatty_foods', 'sugar_intake', 'water_intake', 'exercise_level']
        
        for factor in factors:
            values = [getattr(log, factor) for log in health_logs if getattr(log, factor) is not None]
            if len(values) > 1:
                # Simple trend calculation (improving/worsening)
                recent_avg = sum(values[-7:]) / len(values[-7:]) if len(values) >= 7 else values[-1]
                overall_avg = sum(values) / len(values)
                
                if factor in ['water_intake', 'exercise_level']:
                    # For these factors, higher is better
                    trend = 'improving' if recent_avg > overall_avg else 'declining'
                else:
                    # For these factors, lower is better
                    trend = 'improving' if recent_avg < overall_avg else 'declining'
                
                trends[factor] = {
                    'trend': trend,
                    'recent_avg': round(recent_avg, 2),
                    'overall_avg': round(overall_avg, 2)
                }
        
        return {
            'status': 'success',
            'trends': trends,
            'overall_risk_trend': 'improving' if self.calculate_risk_score(user_id, 30) < self.calculate_risk_score(user_id, 90) else 'concerning'
        }
