from dataclasses import dataclass


@dataclass
class RiskAssessment:
    probability: float
    level: str


class RiskService:
    def assess(self, risk_probability: float, repeated_crisis_keywords: bool) -> RiskAssessment:
        if risk_probability >= 0.80:
            level = "HIGH"
        elif risk_probability >= 0.55:
            level = "MODERATE"
        else:
            level = "LOW"

        if repeated_crisis_keywords and level == "MODERATE":
            level = "HIGH"
        elif repeated_crisis_keywords and level == "LOW":
            level = "MODERATE"

        return RiskAssessment(probability=risk_probability, level=level)
