"""
AI-Based Behavioral Analysis Module
This module analyzes gaming behavior and classifies addiction levels
using rule-based AI logic suitable for BCA academic projects.
"""

class GameAddictionAnalyzer:
    """
    Analyzes gaming behavior patterns to detect potential addiction.
    Uses threshold-based classification (rule-based AI approach).
    """
    
    def __init__(self):
        # Define thresholds for addiction classification
        # These are based on WHO gaming disorder research guidelines
        self.NORMAL_HOURS = 2          # Up to 2 hours/day is normal
        self.RISK_HOURS = 4            # 2-4 hours shows risk
        self.NORMAL_SESSIONS = 2       # Up to 2 sessions/day is normal
        self.RISK_SESSIONS = 3         # 3+ sessions shows concern
    
    def analyze_behavior(self, hours_per_day, sessions_per_day, plays_at_night):
        """
        Main analysis function that classifies addiction level.
        
        Parameters:
        - hours_per_day: float (total gaming hours per day)
        - sessions_per_day: int (number of gaming sessions)
        - plays_at_night: str ('yes' or 'no')
        
        Returns:
        - dict with classification, risk_score, and advice
        """
        
        # Initialize risk score (0-100 scale)
        risk_score = 0
        risk_factors = []
        
        # Factor 1: Analyze daily gaming hours
        if hours_per_day <= self.NORMAL_HOURS:
            risk_score += 10
        elif hours_per_day <= self.RISK_HOURS:
            risk_score += 40
            risk_factors.append("Moderate gaming duration")
        else:
            risk_score += 60
            risk_factors.append("Excessive gaming duration")
        
        # Factor 2: Analyze gaming sessions frequency
        if sessions_per_day <= self.NORMAL_SESSIONS:
            risk_score += 5
        elif sessions_per_day <= self.RISK_SESSIONS:
            risk_score += 20
            risk_factors.append("Frequent gaming sessions")
        else:
            risk_score += 30
            risk_factors.append("Very frequent gaming sessions")
        
        # Factor 3: Analyze night gaming behavior
        # Night gaming indicates poor sleep patterns
        if plays_at_night.lower() == 'yes':
            risk_score += 15
            risk_factors.append("Gaming during night hours")
        
        # Classify based on total risk score
        classification = self._classify_risk(risk_score)
        advice = self._generate_advice(classification, risk_factors)
        
        return {
            'classification': classification,
            'risk_score': min(risk_score, 100),  # Cap at 100
            'risk_factors': risk_factors,
            'advice': advice,
            'status_color': self._get_status_color(classification)
        }
    
    def _classify_risk(self, risk_score):
        """
        Classifies user into addiction categories based on risk score.
        
        Risk Score Ranges:
        - 0-30: Normal (healthy gaming habits)
        - 31-60: At Risk (warning signs present)
        - 61-100: Addicted (intervention needed)
        """
        if risk_score <= 30:
            return "Normal"
        elif risk_score <= 60:
            return "At Risk"
        else:
            return "Addicted"
    
    def _get_status_color(self, classification):
        """Returns color code for visual representation."""
        colors = {
            'Normal': 'green',
            'At Risk': 'yellow',
            'Addicted': 'red'
        }
        return colors.get(classification, 'gray')
    
    def _generate_advice(self, classification, risk_factors):
        """
        Generates personalized advice based on classification.
        Provides actionable recommendations for each category.
        """
        advice_map = {
            'Normal': {
                'message': 'Great job! Your gaming habits are healthy.',
                'tips': [
                    'Continue maintaining a balanced schedule',
                    'Keep gaming as a recreational activity',
                    'Ensure you have time for other hobbies and social activities'
                ]
            },
            'At Risk': {
                'message': 'Warning! You are showing signs of problematic gaming behavior.',
                'tips': [
                    'Try to reduce gaming time by 30 minutes each day',
                    'Set specific time limits before you start playing',
                    'Take 10-minute breaks every hour',
                    'Avoid gaming 2 hours before bedtime',
                    'Engage in physical activities or outdoor hobbies'
                ]
            },
            'Addicted': {
                'message': 'Alert! Your gaming behavior indicates addiction. Immediate action needed.',
                'tips': [
                    'Seek professional help from a counselor or psychologist',
                    'Inform family members about your gaming habits',
                    'Create a strict gaming schedule (max 1 hour/day)',
                    'Remove gaming apps from your phone',
                    'Replace gaming time with sports, reading, or creative activities',
                    'Join support groups for gaming addiction'
                ]
            }
        }
        
        return advice_map.get(classification, advice_map['Normal'])


# Example usage and testing
if __name__ == "__main__":
    # Create analyzer instance
    analyzer = GameAddictionAnalyzer()
    
    # Test cases
    print("Test Case 1: Normal User")
    result1 = analyzer.analyze_behavior(1.5, 1, 'no')
    print(f"Classification: {result1['classification']}")
    print(f"Risk Score: {result1['risk_score']}\n")
    
    print("Test Case 2: At Risk User")
    result2 = analyzer.analyze_behavior(3.5, 3, 'yes')
    print(f"Classification: {result2['classification']}")
    print(f"Risk Score: {result2['risk_score']}\n")
    
    print("Test Case 3: Addicted User")
    result3 = analyzer.analyze_behavior(8, 5, 'yes')
    print(f"Classification: {result3['classification']}")
    print(f"Risk Score: {result3['risk_score']}")