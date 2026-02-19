from src.application.services.risk_service import RiskService


def test_risk_thresholds() -> None:
    service = RiskService()
    assert service.assess(0.81, False).level == "HIGH"
    assert service.assess(0.60, False).level == "MODERATE"
    assert service.assess(0.20, False).level == "LOW"


def test_risk_keyword_escalation() -> None:
    service = RiskService()
    assert service.assess(0.60, True).level == "HIGH"
    assert service.assess(0.20, True).level == "MODERATE"
