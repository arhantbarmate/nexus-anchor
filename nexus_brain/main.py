import rfc8785
import json
from decimal import Decimal, ROUND_HALF_EVEN


def to_fixed(value):
    """
    FIX 1: Enforce absolute determinism using Decimal.
    Ensures identical string output regardless of platform or locale.
    """
    if value is None:
        return "0.0000"
    return str(
        Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
    )


def run_aura_gold_logic(h4_high, h4_low, current_bid, rsi_val):
    """
    FIX 2: Perform all math in Decimal space to prevent binary float drift.
    """
    # Convert inputs to Decimal immediately
    bid = Decimal(str(current_bid))
    high = Decimal(str(h4_high))
    low = Decimal(str(h4_low))
    rsi = Decimal(str(rsi_val))
    one_point_five = Decimal("1.5")

    # Logic Implementation
    if bid > high and rsi > Decimal("50"):
        action = "BUY"
        sl = low
        tp = bid + (bid - low) * one_point_five
    elif bid < low and rsi < Decimal("50"):
        action = "SELL"
        sl = high
        tp = bid - (high - bid) * one_point_five
    else:
        action = "HOLD"
        sl = Decimal("0")
        tp = Decimal("0")

    # HARDENING: Enforce Action Enum
    assert action in {"BUY", "SELL", "HOLD"}, f"Invalid action generated: {action}"

    return action, sl, tp


def generate_ver():
    # TEST DATA
    symbol = "XAUUSD"
    h4_high = 2045.50
    h4_low = 2030.10
    current_bid = 2046.20
    rsi_val = 72.50

    # 1. Execute deterministic logic
    action, sl, tp = run_aura_gold_logic(h4_high, h4_low, current_bid, rsi_val)

    # 2. Build Schema (Strict adherence to VER v1.0)
    ver = {
        "version": "1.0",
        "context": {"engine": "nexus-v1", "logic_hash": "6a8e...f3"},
        "input": {
            "symbol": str(symbol),
            "h4_high": to_fixed(h4_high),
            "h4_low": to_fixed(h4_low),
            "current_bid": to_fixed(current_bid),
            "rsi_val": to_fixed(rsi_val),
        },
        "output": {"action": action, "sl": to_fixed(sl), "tp": to_fixed(tp)},
    }

    # 3. Canonicalize (RFC 8785)
    return rfc8785.dumps(ver).decode("utf-8")


if __name__ == "__main__":
    # Emit the deterministic VER
    print(generate_ver())
