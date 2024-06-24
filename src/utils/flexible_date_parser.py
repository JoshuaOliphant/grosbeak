from datetime import date


def flexible_date_parser(value):
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        if value.lower() in ["not available", "n/a", ""]:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            # Try parsing just the year
            try:
                return date(int(value), 1, 1)
            except ValueError:
                return None
    return None
