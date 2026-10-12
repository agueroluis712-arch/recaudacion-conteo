import hashlib
import math
from decimal import Decimal


def _controlled_random_fraction(load, elapsed_seconds, duration_seconds):
    multiplier = {"SECONDS": 1, "MINUTES": 60, "HOURS": 3600}[load.interval_unit_snapshot]
    interval_seconds = max(1, load.interval_value_snapshot * multiplier)
    total_intervals = max(1, math.ceil(duration_seconds / interval_seconds))
    completed = min(total_intervals, max(0, math.floor(elapsed_seconds / interval_seconds)))
    if completed >= total_intervals:
        return Decimal("1")
    variation = float(load.max_variation_snapshot / Decimal("100"))
    intensity = float(load.randomness_intensity_snapshot / Decimal("100"))
    raw = []
    for index in range(total_intervals):
        digest = hashlib.sha256(f"{load.id}:{index}".encode()).digest()
        unit = int.from_bytes(digest[:8], "big") / ((1 << 64) - 1)
        raw.append(1 + (unit * 2 - 1) * variation * intensity)
    window = max(1, load.smoothing_intervals_snapshot)
    weights = [sum(raw[max(0, i-window+1):i+1]) / len(raw[max(0, i-window+1):i+1]) for i in range(total_intervals)]
    return Decimal(str(sum(weights[:completed]) / sum(weights)))


def progression_fraction(load, now, start, cutoff):
    if now < start:
        return Decimal("0")
    if now >= cutoff or cutoff <= start:
        return Decimal("1")
    elapsed = (now - start).total_seconds()
    duration = (cutoff - start).total_seconds()
    ratio = Decimal(str(max(0.0, min(1.0, elapsed / duration))))
    if load.algorithm_snapshot == "INMEDIATO":
        return Decimal("1")
    if load.algorithm_snapshot == "ACELERADO_AL_FINAL":
        return Decimal(str(float(ratio) ** float(load.gamma_snapshot)))
    if load.algorithm_snapshot == "LINEAL_ALEATORIO_CONTROLADO":
        return _controlled_random_fraction(load, elapsed, duration)
    return ratio
