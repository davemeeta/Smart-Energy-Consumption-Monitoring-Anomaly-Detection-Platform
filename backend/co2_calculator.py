CO2_FACTOR    = 0.380   # kg CO2/kWh (Germany 2024)
PRICE_PER_KWH = 0.32    # EUR/kWh
BASELINE_KWH  = 0.03    # normal per-minute consumption (UCI dataset baseline)

def calculate(kwh: float, hours: float = 1.0) -> dict:
    total_kwh = kwh * hours
    co2_kg    = round(total_kwh * CO2_FACTOR, 6)
    cost_eur  = round(total_kwh * PRICE_PER_KWH, 6)
    saving_kwh = max(0.0, total_kwh - BASELINE_KWH * hours)
    return {
        "total_kwh":              round(total_kwh, 6),
        "co2_kg":                 co2_kg,
        "cost_eur":               cost_eur,
        "potential_saving_eur":   round(saving_kwh * PRICE_PER_KWH, 6),
        "potential_saving_co2_kg": round(saving_kwh * CO2_FACTOR, 6),
    }