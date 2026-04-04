#!/data/banxe/compliance-env/bin/python3
"""
Transaction Monitor — Phase 11 (jube_lite)
6 detection rules + Redis velocity counters.
Jube TM (AGPLv3) handles the ML layer; this handles deterministic rules.
"""
import asyncio
import json
import sys
import os
import time
import hashlib
from datetime import datetime, timezone
from typing import Optional

# Redis for velocity counters
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

REDIS_URL = "redis://127.0.0.1:6379"

# High-risk jurisdictions (FATF + UK OFSI + EU sanctioned)
HIGH_RISK_JURISDICTIONS = {
    "RU", "BY", "IR", "KP", "CU", "MM", "AF", "VE",
    "SY", "IQ", "LB", "YE", "HT", "ML", "LY", "SO", "SS",
    "NI", "ZW", "SD", "CF", "BI",
}

# Structuring detection window
STRUCTURING_WINDOW_SEC  = 86400   # 24h
STRUCTURING_THRESHOLD   = 10_000  # GBP/EUR reporting threshold
STRUCTURING_MIN_TX      = 3       # minimum transactions to trigger
VELOCITY_WINDOW_SEC     = 86400   # 24h for velocity checks

# Rule thresholds
SINGLE_TX_FLAG  = 10_000   # GBP — MLR 2017 threshold
VELOCITY_24H    = 25_000   # GBP — cumulative 24h
ROUND_AMOUNT_MIN = 5_000   # flag round amounts above this


# ── Redis velocity helpers ────────────────────────────────────────────────────

async def _get_redis() -> Optional[object]:
    if not REDIS_AVAILABLE:
        return None
    try:
        r = aioredis.from_url(REDIS_URL, decode_responses=True)
        await r.ping()
        return r
    except Exception:
        return None


async def _add_velocity(r, account: str, amount: float, window: int) -> float:
    """Add transaction to Redis sorted set, return 24h total."""
    if not r:
        return amount
    now = time.time()
    key = f"banxe:velocity:{account}"
    tx_id = f"{now}:{amount}"
    try:
        pipe = r.pipeline()
        await pipe.zadd(key, {tx_id: now})
        await pipe.zremrangebyscore(key, 0, now - window)
        await pipe.execute()
        # Sum all amounts in window
        members = await r.zrange(key, 0, -1)
        total = sum(float(m.split(":")[1]) for m in members if ":" in m)
        await r.expire(key, window + 3600)
        return total
    except Exception:
        return amount


async def _get_recent_tx_count(r, account: str, window: int) -> int:
    """Count transactions in window."""
    if not r:
        return 1
    now = time.time()
    key = f"banxe:velocity:{account}"
    try:
        count = await r.zcount(key, now - window, now)
        return count
    except Exception:
        return 1


# ── Detection rules ───────────────────────────────────────────────────────────

async def check_transaction(tx: dict) -> dict:
    """
    Apply 6 AML detection rules to a transaction.

    tx: {
        from: str (account/name),
        to: str,
        amount: float,
        currency: str,
        tx_type: str,
        jurisdiction: str (ISO2, optional),
        from_account: str (optional),
        to_account: str (optional),
    }
    Returns: {flagged, rules_triggered, risk_score, recommended_action, details}
    """
    amount      = float(tx.get("amount", 0))
    currency    = tx.get("currency", "GBP").upper()
    sender      = tx.get("from", tx.get("from_account", "unknown"))
    recipient   = tx.get("to", tx.get("to_account", "unknown"))
    jurisdiction = (tx.get("jurisdiction", "") or "").upper()
    tx_type     = tx.get("tx_type", "wire")

    # Normalise to GBP (approximate)
    fx = {"EUR": 0.86, "USD": 0.79, "GBP": 1.0, "USDT": 0.79, "ETH": 2500.0}
    amount_gbp = amount * fx.get(currency, 1.0)

    rules_triggered = []
    risk_score = 0

    # ── Rule 1: Single transaction threshold (MLR 2017) ──────────────────────
    if amount_gbp >= SINGLE_TX_FLAG:
        rules_triggered.append({
            "rule": "SINGLE_TX_THRESHOLD",
            "detail": f"£{amount_gbp:,.0f} >= £{SINGLE_TX_FLAG:,} MLR threshold",
            "score": 30,
        })
        risk_score += 30

    # ── Rule 2: 24h velocity (cumulative) ────────────────────────────────────
    r = await _get_redis()
    velocity_total = await _add_velocity(r, sender, amount_gbp, VELOCITY_WINDOW_SEC)
    if velocity_total >= VELOCITY_24H:
        rules_triggered.append({
            "rule": "VELOCITY_24H",
            "detail": f"24h cumulative £{velocity_total:,.0f} >= £{VELOCITY_24H:,}",
            "score": 40,
        })
        risk_score += 40

    # ── Rule 3: Structuring (multiple txs just below threshold) ──────────────
    tx_count = await _get_recent_tx_count(r, sender, STRUCTURING_WINDOW_SEC)
    if (amount_gbp >= STRUCTURING_THRESHOLD * 0.80 and
            amount_gbp < STRUCTURING_THRESHOLD and
            tx_count >= STRUCTURING_MIN_TX):
        rules_triggered.append({
            "rule": "POTENTIAL_STRUCTURING",
            "detail": f"£{amount_gbp:,.0f} just below £{STRUCTURING_THRESHOLD:,} threshold, {tx_count} txs in 24h",
            "score": 60,
        })
        risk_score += 60

    # ── Rule 4: Round amount (smurfing indicator) ─────────────────────────────
    is_round = (amount_gbp >= ROUND_AMOUNT_MIN and
                amount_gbp == round(amount_gbp, -3))
    if is_round:
        rules_triggered.append({
            "rule": "ROUND_AMOUNT",
            "detail": f"Round amount £{amount_gbp:,.0f} may indicate structuring",
            "score": 15,
        })
        risk_score += 15

    # ── Rule 5: Rapid in-out (layering) ──────────────────────────────────────
    in_key  = f"banxe:last_credit:{sender}"
    out_key = f"banxe:last_debit:{sender}"
    if r:
        try:
            last_credit = await r.get(in_key)
            if last_credit:
                elapsed = time.time() - float(last_credit)
                if elapsed < 3600 and amount_gbp >= 1000:  # credited & debited within 1h
                    rules_triggered.append({
                        "rule": "RAPID_IN_OUT",
                        "detail": f"Funds received {elapsed:.0f}s ago then immediately sent (layering indicator)",
                        "score": 50,
                    })
                    risk_score += 50
            await r.setex(out_key, VELOCITY_WINDOW_SEC, str(time.time()))
        except Exception:
            pass

    # ── Rule 6: High-risk jurisdiction ───────────────────────────────────────
    if jurisdiction in HIGH_RISK_JURISDICTIONS:
        rules_triggered.append({
            "rule": "HIGH_RISK_JURISDICTION",
            "detail": f"Jurisdiction {jurisdiction} is high-risk (FATF/OFSI/EU)",
            "score": 35,
        })
        risk_score += 35

    if r:
        await r.aclose()

    # ── Aggregate ─────────────────────────────────────────────────────────────
    flagged = risk_score >= 30 or bool(rules_triggered)
    recommended_action = (
        "BLOCK_AND_SAR"  if risk_score >= 70 else
        "HOLD_AND_REVIEW" if risk_score >= 40 else
        "ENHANCED_MONITORING" if risk_score >= 30 else
        "PASS"
    )

    return {
        "flagged":   flagged,
        "rules_triggered": rules_triggered,
        "risk_score": risk_score,
        "recommended_action": recommended_action,
        "velocity_24h_gbp":  round(velocity_total, 2),
        "transaction_count_24h": tx_count,
        "details": {
            "amount_gbp":    round(amount_gbp, 2),
            "original":      f"{amount} {currency}",
            "sender":        sender,
            "recipient":     recipient,
            "jurisdiction":  jurisdiction,
        },
    }


if __name__ == "__main__":
    # Structuring test: 4 transactions of £8,500 in 24h
    async def test():
        tx = {
            "from": "TEST_ACCOUNT_001",
            "to": "RECIPIENT_UK",
            "amount": 8500.0,
            "currency": "GBP",
            "tx_type": "wire",
            "jurisdiction": "GB",
        }
        # Simulate 4 transactions
        for i in range(4):
            r = await check_transaction(tx)
            print(f"TX {i+1}: flagged={r['flagged']}, score={r['risk_score']}, action={r['recommended_action']}")
            print(f"  Rules: {[x['rule'] for x in r['rules_triggered']]}")
            print()

    asyncio.run(test())
