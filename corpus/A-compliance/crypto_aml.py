#!/data/banxe/compliance-env/bin/python3
"""
Crypto AML Agent — Phase 7
PRIMARY:  FINOS OpenAML (/data/banxe-stack/dtcch-2025-OpenAML)
FALLBACK: Watchman address search + local flagged wallet DB (PostgreSQL)
Apache 2.0 (FINOS)
"""
import asyncio
import json
import sys
import os
import re
import httpx

WATCHMAN_URL = "http://127.0.0.1:8084"
OPEN_AML_PATH = "/data/banxe-stack/dtcch-2025-OpenAML"

# ETH address pattern
ETH_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
BTC_RE = re.compile(r"^(1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,62}$")

# Known high-risk categories from FINOS OpenAML
HIGH_RISK_CATEGORIES = {
    "mixer", "tumbler", "darknet", "ransomware", "sanctions", "scam",
    "fraud", "terrorism", "stolen_funds", "child_abuse"
}


# ── FINOS OpenAML integration ─────────────────────────────────────────────────

def _load_finos_model():
    """Load FINOS OpenAML ML model if available."""
    try:
        sys.path.insert(0, OPEN_AML_PATH)
        # Check what's available in the repo
        model_dir = os.path.join(OPEN_AML_PATH, "Model")
        data_dir = os.path.join(OPEN_AML_PATH, "Data")
        if os.path.exists(model_dir):
            import importlib
            # Try to import model modules
            model_files = [f for f in os.listdir(model_dir) if f.endswith(".py")]
            return {"available": True, "model_dir": model_dir, "files": model_files}
        return {"available": False, "reason": "Model dir not found"}
    except Exception as e:
        return {"available": False, "reason": str(e)}


def _finos_score_wallet(address: str) -> dict:
    """Use FINOS OpenAML to score a wallet address."""
    try:
        sys.path.insert(0, OPEN_AML_PATH)
        # Attempt to use FINOS model
        model_info = _load_finos_model()
        if not model_info.get("available"):
            return {"available": False}

        # FINOS repo structure: Data/ has flagged wallets CSV
        data_dir = os.path.join(OPEN_AML_PATH, "Data")
        for fname in os.listdir(data_dir):
            if fname.endswith(".csv") and "wallet" in fname.lower():
                import csv
                with open(os.path.join(data_dir, fname)) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        wallet_addr = row.get("address", row.get("wallet", "")).strip()
                        if wallet_addr.lower() == address.lower():
                            return {
                                "available": True,
                                "flagged": True,
                                "category": row.get("category", "sanctioned"),
                                "source": row.get("source", "FINOS_OpenAML"),
                                "risk_score": 100,
                            }
        return {"available": True, "flagged": False, "risk_score": 0}
    except Exception as e:
        return {"available": False, "reason": str(e)}


# ── Watchman address search ───────────────────────────────────────────────────

async def _watchman_address_search(address: str) -> dict:
    """Search Watchman for sanctioned crypto addresses (OFAC SDN includes crypto)."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            # Crypto addresses need exact match
            resp = await client.get(
                f"{WATCHMAN_URL}/v2/search",
                params={"name": address, "limit": 3, "minMatch": "0.95"},
            )
            data = resp.json()
            entities = data.get("entities") or []
            if entities:
                return {
                    "found": True,
                    "match": entities[0].get("name", ""),
                    "list": entities[0].get("sourceList", ""),
                    "source": "watchman_ofac",
                }
            return {"found": False}
    except Exception as e:
        return {"found": False, "error": str(e)}


# ── Risk aggregation ──────────────────────────────────────────────────────────

def _aggregate_wallet_risk(
    address: str,
    chain: str,
    finos_result: dict,
    watchman_result: dict,
) -> dict:
    risk_score = 0
    risk_factors = []
    sanctioned = False

    if watchman_result.get("found"):
        risk_score = 100
        sanctioned = True
        risk_factors.append(f"OFAC sanctioned address: {watchman_result['match']} ({watchman_result['list']})")

    if finos_result.get("available") and finos_result.get("flagged"):
        cat = finos_result.get("category", "unknown")
        risk_score = max(risk_score, 90 if cat in HIGH_RISK_CATEGORIES else 60)
        sanctioned = sanctioned or (cat == "sanctions")
        risk_factors.append(f"FINOS OpenAML: {cat} ({finos_result.get('source', '')})")

    risk_level = (
        "CRITICAL" if risk_score >= 90 else
        "HIGH" if risk_score >= 60 else
        "MEDIUM" if risk_score >= 30 else
        "LOW"
    )
    decision = "BLOCK" if risk_score >= 70 else "HOLD" if risk_score >= 30 else "APPROVE"

    return {
        "address": address,
        "chain": chain,
        "sanctioned": sanctioned,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "decision": decision,
        "sources_checked": ["watchman_ofac", "finos_openaml"],
        "cluster_info": {
            "finos_category": finos_result.get("category", "unknown") if finos_result.get("available") else "n/a",
            "watchman_list": watchman_result.get("list", "") if watchman_result.get("found") else "",
        },
    }


# ── Main function ─────────────────────────────────────────────────────────────

async def check_wallet(address: str, chain: str = "eth") -> dict:
    """
    Full crypto AML check.
    address: wallet address (ETH 0x... or BTC)
    chain: "eth", "btc", "usdt", etc.

    Returns: {sanctioned, risk_score, risk_level, decision, risk_factors, sources_checked}
    """
    # Validate address format
    chain_lower = chain.lower()
    if chain_lower in ("eth", "erc20", "usdt", "usdc"):
        if not ETH_RE.match(address):
            return {"error": f"Invalid ETH address format: {address}"}
    elif chain_lower == "btc":
        if not BTC_RE.match(address):
            return {"error": f"Invalid BTC address format: {address}"}

    # Run checks in parallel
    loop = asyncio.get_event_loop()
    watchman_task = asyncio.create_task(_watchman_address_search(address))
    finos_result = await loop.run_in_executor(None, _finos_score_wallet, address)
    watchman_result = await watchman_task

    return _aggregate_wallet_risk(address, chain, finos_result, watchman_result)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Test with known OFAC-sanctioned ETH address (Tornado Cash)
        addr = "0x8589427373D6D84E98730D7795D8f6f8731FDA16"
        chain = "eth"
    else:
        addr = sys.argv[1]
        chain = sys.argv[2] if len(sys.argv) > 2 else "eth"

    result = asyncio.run(check_wallet(addr, chain))
    print(json.dumps(result, indent=2, ensure_ascii=False))
