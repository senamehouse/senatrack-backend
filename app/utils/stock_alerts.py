"""Shared interpretation of a company's stock alert setting."""


def stock_alert_threshold(settings: object) -> int:
    if not isinstance(settings, dict):
        return 10
    value = settings.get("stockAlertThreshold", settings.get("stock_alert_threshold", 10))
    return value if type(value) is int and value >= 0 else 10
