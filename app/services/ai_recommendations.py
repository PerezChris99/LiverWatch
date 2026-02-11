"""
AI-Powered Recommendations Engine
=================================

Provides personalized liver health recommendations based on user data.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any


class LiverHealthAI:
    """AI engine for personalized liver health recommendations"""
    
    def __init__(self):
        self.risk_factors = {
            'alcohol_intake': {'weight': 0.30, 'threshold': 2, 'direction': 'higher_bad'},
            'fatty_foods': {'weight': 0.25, 'threshold': 3, 'direction': 'higher_bad'},
            'sugar_intake': {'weight': 0.20, 'threshold': 50, 'direction': 'higher_bad'},
            'water_intake': {'weight': 0.15, 'threshold': 2, 'direction': 'lower_bad'},
            'exercise_level': {'weight': 0.10, 'threshold': 30, 'direction': 'lower_bad'}
        }
    
    def calculate_risk_score(self, user_id: int, days: int = 30) -> float:
        """
        Calculate liver health risk score based on recent health logs.
        
        Args:
            user_id: User ID to calculate score for
            days: Number of days to consider
            
        Returns:
            Risk score between 0 (low risk) and 1 (high risk)
        """
        from app.models import HealthLog
        
        recent_date = datetime.now() - timedelta(days=days)
        health_logs = HealthLog.query.filter(
            HealthLog.user_id == user_id,
            HealthLog.date >= recent_date
        ).all()
        
        if not health_logs:
            return 0.5  # Neutral score if no data
        
        total_score = 0
        log_count = 0
        
        for log in health_logs:
            daily_score = 0
            factors_counted = 0
            
            # Alcohol intake
            if log.alcohol_intake is not None:
                if log.alcohol_intake > self.risk_factors['alcohol_intake']['threshold']:
                    daily_score += self.risk_factors['alcohol_intake']['weight']
                factors_counted += 1
            
            # Fatty foods
            if log.fatty_foods is not None:
                if log.fatty_foods > self.risk_factors['fatty_foods']['threshold']:
                    daily_score += self.risk_factors['fatty_foods']['weight']
                factors_counted += 1
            
            # Sugar intake
            if log.sugar_intake is not None:
                if log.sugar_intake > self.risk_factors['sugar_intake']['threshold']:
                    daily_score += self.risk_factors['sugar_intake']['weight']
                factors_counted += 1
            
            # Water intake (lower is bad)
            if log.water_intake is not None:
                if log.water_intake < self.risk_factors['water_intake']['threshold']:
                    daily_score += self.risk_factors['water_intake']['weight']
                factors_counted += 1
            
            # Exercise level (lower is bad)
            if log.exercise_level is not None:
                if log.exercise_level < self.risk_factors['exercise_level']['threshold']:
                    daily_score += self.risk_factors['exercise_level']['weight']
                factors_counted += 1
            
            if factors_counted > 0:
                total_score += daily_score
                log_count += 1
        
        if log_count == 0:
            return 0.5
        
        # Normalize score (0-1 range)
        avg_score = total_score / log_count
        return min(max(avg_score, 0), 1)
    
    def get_personalized_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations based on user's health data.
        
        Args:
            user_id: User ID to get recommendations for
            
        Returns:
            List of recommendation dictionaries
        """
        from app.models import HealthLog, Recipe
        
        risk_score = self.calculate_risk_score(user_id)
        recommendations = []
        
        # Get recent health data
        recent_log = HealthLog.query.filter_by(user_id=user_id)\
                                    .order_by(HealthLog.date.desc())\
                                    .first()
        
        if not recent_log:
            return [{
                'type': 'general',
                'title': 'Start Tracking Your Health',
                'message': 'Begin logging your daily habits to get personalized recommendations tailored to your lifestyle.',
                'priority': 'high',
                'icon': 'clipboard-list'
            }]
        
        # High-risk recommendations
        if risk_score > 0.7:
            recommendations.append({
                'type': 'urgent',
                'title': 'Consult a Healthcare Professional',
                'message': 'Your recent health patterns indicate increased liver disease risk. Please consult a liver specialist for a professional assessment.',
                'priority': 'urgent',
                'icon': 'exclamation-triangle'
            })
        
        # Specific recommendations based on data
        if recent_log.alcohol_intake and recent_log.alcohol_intake > 2:
            recommendations.append({
                'type': 'lifestyle',
                'title': 'Reduce Alcohol Consumption',
                'message': f'Your alcohol intake ({recent_log.alcohol_intake} units) exceeds safe limits. The liver can only process about 1 unit per hour. Consider reducing to 1-2 units per week.',
                'priority': 'high',
                'icon': 'wine-glass-alt'
            })
        
        if recent_log.water_intake and recent_log.water_intake < 2:
            recommendations.append({
                'type': 'nutrition',
                'title': 'Increase Water Intake',
                'message': f'You logged {recent_log.water_intake}L of water. Aim for at least 2-3 liters daily to help your liver flush out toxins effectively.',
                'priority': 'medium',
                'icon': 'tint'
            })
        
        if recent_log.exercise_level and recent_log.exercise_level < 30:
            recommendations.append({
                'type': 'fitness',
                'title': 'Increase Physical Activity',
                'message': f'You logged {recent_log.exercise_level} minutes of exercise. Aim for at least 30 minutes of moderate exercise daily to reduce liver fat and improve function.',
                'priority': 'medium',
                'icon': 'running'
            })
        
        if recent_log.fatty_foods and recent_log.fatty_foods > 3:
            recommendations.append({
                'type': 'nutrition',
                'title': 'Reduce Fatty Food Intake',
                'message': 'High consumption of fatty foods can lead to non-alcoholic fatty liver disease. Try incorporating more vegetables and lean proteins.',
                'priority': 'medium',
                'icon': 'utensils'
            })
        
        if recent_log.sugar_intake and recent_log.sugar_intake > 50:
            recommendations.append({
                'type': 'nutrition',
                'title': 'Cut Down on Sugar',
                'message': f'Your sugar intake ({recent_log.sugar_intake}g) is above recommended levels. Excess sugar is converted to fat in the liver.',
                'priority': 'medium',
                'icon': 'candy-cane'
            })
        
        # Add recipe recommendations if healthy eating needed
        if recent_log.fatty_foods and recent_log.fatty_foods > 2:
            liver_friendly_recipes = Recipe.query.limit(3).all()
            if liver_friendly_recipes:
                recommendations.append({
                    'type': 'nutrition',
                    'title': 'Try These Liver-Friendly Recipes',
                    'message': 'Based on your health data, these recipes can support your liver health while being delicious.',
                    'recipes': [{'title': r.title, 'id': r.id} for r in liver_friendly_recipes],
                    'priority': 'low',
                    'icon': 'book-open'
                })
        
        # Add positive reinforcement if doing well
        if risk_score < 0.3:
            recommendations.append({
                'type': 'positive',
                'title': 'Great Job!',
                'message': "Your health habits are excellent! Keep maintaining this healthy lifestyle to protect your liver.",
                'priority': 'low',
                'icon': 'star'
            })
        
        return recommendations
    
    def get_health_trends(self, user_id: int, days: int = 90) -> Dict[str, Any]:
        """
        Analyze health trends over time.
        
        Args:
            user_id: User ID to analyze
            days: Number of days to analyze
            
        Returns:
            Dictionary containing trend analysis
        """
        from app.models import HealthLog
        
        start_date = datetime.now() - timedelta(days=days)
        health_logs = HealthLog.query.filter(
            HealthLog.user_id == user_id,
            HealthLog.date >= start_date
        ).order_by(HealthLog.date).all()
        
        if len(health_logs) < 7:
            return {'status': 'insufficient_data', 'message': 'Log at least 7 days of data to see trends.'}
        
        trends = {}
        factors = ['alcohol_intake', 'fatty_foods', 'sugar_intake', 'water_intake', 'exercise_level']
        
        for factor in factors:
            values = [getattr(log, factor) for log in health_logs if getattr(log, factor) is not None]
            
            if len(values) < 7:
                continue
            
            # Calculate trend using recent vs overall average
            recent_count = min(7, len(values))
            recent_avg = sum(values[-recent_count:]) / recent_count
            overall_avg = sum(values) / len(values)
            
            # Determine trend direction
            change_pct = ((recent_avg - overall_avg) / overall_avg * 100) if overall_avg != 0 else 0
            
            # For water and exercise, higher is better
            if factor in ['water_intake', 'exercise_level']:
                if change_pct > 10:
                    trend = 'improving'
                elif change_pct < -10:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                # For alcohol, fatty foods, sugar - lower is better
                if change_pct < -10:
                    trend = 'improving'
                elif change_pct > 10:
                    trend = 'declining'
                else:
                    trend = 'stable'
            
            trends[factor] = {
                'trend': trend,
                'recent_avg': round(recent_avg, 2),
                'overall_avg': round(overall_avg, 2),
                'change_pct': round(change_pct, 1)
            }
        
        # Overall health trend
        improving_count = sum(1 for t in trends.values() if t['trend'] == 'improving')
        declining_count = sum(1 for t in trends.values() if t['trend'] == 'declining')
        
        if improving_count > declining_count:
            overall_trend = 'improving'
        elif declining_count > improving_count:
            overall_trend = 'declining'
        else:
            overall_trend = 'stable'
        
        return {
            'status': 'success',
            'overall_trend': overall_trend,
            'factors': trends,
            'data_points': len(health_logs)
        }
