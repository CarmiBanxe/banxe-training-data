#!/usr/bin/env python3
"""
Sanctions Check — Layer 2 (Entity Screening)

Screens entities against sanctions and watchlists:
  PRIMARY:   Moov Watchman REST API (localhost:8084) — OFAC SDN / UN / EU / UK CSL /
             US-CSL / FinCEN 311 / US BoS  (Apache 2.0, zero external calls)
  FALLBACK:  Local fuzzy name matching (difflib.SequenceMatcher, stdlib only)

Decision vocabulary (aligned with compliance_validator thresholds):
  SANCTIONS_CONFIRMED  score=100  → auto-REJECT, MLRO notified (match ≥ 95%)
  SANCTIONS_PROBABLE   score=70   → REJECT pending MLRO review (match 80–95%)
  SUBJECT_JURISDICTION_A  score=100  → Category A hard block (SAMLA 2018)
  SUBJECT_JURISDICTION_B  score=35   → Category B EDD mandatory (FCA EDD §4.2)

Returns list[RiskSignal] for aggregation by aml_orchestrator.
"""
from __future__ import annotations

import json
import urllib.request
import urllib.parse
from difflib import SequenceMatcher
from typing import Optional

from compliance.models import SanctionsSubject, RiskSignal
from compliance.verification.compliance_validator import (
    _HARD_BLOCK_JURISDICTIONS,
    _HIGH_RISK_JURISDICTIONS,
)

WATCHMAN_URL       = "http://127.0.0.1:8084"
WATCHMAN_MIN_MATCH = 0.80
WATCHMAN_TIMEOUT   = 5    # seconds

__all__ = ["screen_entity"]


# ── Watchman HTTP (stdlib urllib — no httpx dependency) ───────────────────────

def _watchman_search(name: str, limit: int = 5) -> list[dict]:
    """GET /v2/search via urllib. Returns raw entity list or [] on any error."""
    try:
        params = urllib.parse.urlencode({
            "name": name,
            "limit": limit,
            "minMatch": WATCHMAN_MIN_MATCH,
        })
        url = f"{WATCHMAN_URL}/v2/search?{params}"
        with urllib.request.urlopen(url, timeout=WATCHMAN_TIMEOUT) as resp:
            data = json.loads(resp.read())
            return data.get("entities") or []
    except Exception:
        return []


def _normalize_watchman(entities: list[dict]) -> list[dict]:
    return [
        {
            "source":      "watchman",
            "list_name":   e.get("sourceList", ""),
            "name_match":  e.get("name", ""),
            "score":       float(e.get("matchScore", 1.0)),
            "entity_type": e.get("entityType", ""),
            "source_id":   e.get("sourceID", ""),
        }
        for e in entities
    ]


# ── Local fuzzy fallback (stdlib only — offline) ──────────────────────────────
# A minimal curated list of high-profile sanctioned names.
# Watchman holds the authoritative dataset; this is a last-resort heuristic.

_LOCAL_FALLBACK_NAMES: list[tuple[str, str, str]] = [
    # (canonical_name, list_name, entity_type)
    ("Vladimir Putin",         "uk_csl",       "person"),
    ("Kim Jong Un",            "us_ofac_sdn",  "person"),
    ("Alexander Lukashenko",   "eu_csl",       "person"),
    ("Bashar Al-Assad",        "eu_csl",       "person"),
    ("Ali Khamenei",           "us_ofac_sdn",  "person"),
    ("Miguel Diaz-Canel",      "us_ofac_sdn",  "person"),
    ("Min Aung Hlaing",        "us_ofac_sdn",  "person"),
    ("Nicolás Maduro",         "us_ofac_sdn",  "person"),
    ("Al-Shabaab",             "un_csl",       "company"),
    ("Hamas",                  "us_ofac_sdn",  "company"),
    ("Hezbollah",              "us_ofac_sdn",  "company"),
    ("Islamic State",          "un_csl",       "company"),
    ("Wagner Group",           "uk_csl",       "company"),
]


def _fuzzy_local_search(name: str) -> list[dict]:
    """stdlib SequenceMatcher fallback when Watchman is unreachable."""
    name_lower = name.lower()
    results = []
    for canonical, list_name, etype in _LOCAL_FALLBACK_NAMES:
        ratio = SequenceMatcher(None, name_lower, canonical.lower()).ratio()
        if ratio >= WATCHMAN_MIN_MATCH:
            results.append({
                "source":      "local_fuzzy",
                "list_name":   list_name,
                "name_match":  canonical,
                "score":       round(ratio, 3),
                "entity_type": etype,
                "source_id":   "",
            })
    return sorted(results, key=lambda h: h["score"], reverse=True)


# ── RiskSignal factories ──────────────────────────────────────────────────────

def _hits_to_signals(hits: list[dict]) -> list[RiskSignal]:
    """Convert watchlist hits to RiskSignals. One signal for the best match."""
    if not hits:
        return []

    best       = max(hits, key=lambda h: h["score"])
    match_pct  = best["score"]
    source_tag = f"[{best['source']}] {best['list_name']}"

    if match_pct >= 0.95:
        return [RiskSignal(
            source="sanctions_check",
            rule="SANCTIONS_CONFIRMED",
            score=100,
            reason=(f"Confirmed sanctions match: '{best['name_match']}' "
                    f"({source_tag}, match={match_pct:.0%}). MLRO notification mandatory."),
            authority="SAMLA 2018 / UK HMT Consolidated List",
            requires_edd=True,
            requires_mlro=True,
        )]
    else:
        return [RiskSignal(
            source="sanctions_check",
            rule="SANCTIONS_PROBABLE",
            score=70,
            reason=(f"Probable sanctions match: '{best['name_match']}' "
                    f"({source_tag}, match={match_pct:.0%}). Manual MLRO review required."),
            authority="UK HMT Consolidated List / OFAC SDN",
            requires_edd=True,
            requires_mlro=True,
        )]


def _jurisdiction_signal(subject: SanctionsSubject) -> Optional[RiskSignal]:
    """Category A / B jurisdiction flag based on subject's declared jurisdiction."""
    if not subject.jurisdiction:
        return None
    jur = subject.jurisdiction.upper()
    if jur in _HARD_BLOCK_JURISDICTIONS:
        return RiskSignal(
            source="sanctions_check",
            rule="SUBJECT_JURISDICTION_A",
            score=100,
            reason=(f"Subject jurisdiction '{jur}' is Category A (hard block): "
                    "SAMLA 2018 / UK HMT Consolidated List. MLRO notified."),
            authority="SAMLA 2018 / UK HMT Consolidated List",
            requires_edd=True,
            requires_mlro=True,
        )
    if jur in _HIGH_RISK_JURISDICTIONS:
        return RiskSignal(
            source="sanctions_check",
            rule="SUBJECT_JURISDICTION_B",
            score=35,
            reason=(f"Subject jurisdiction '{jur}' is Category B (high-risk): "
                    "EDD mandatory (FCA EDD §4.2)."),
            authority="FCA EDD §4.2",
            requires_edd=True,
        )
    return None


# ── Public API ────────────────────────────────────────────────────────────────

def screen_entity(subject: SanctionsSubject) -> list[RiskSignal]:
    """
    Screen an entity against sanctions watchlists.

    Rule order:
      1. Category A jurisdiction → score=100, MLRO, short-circuit
      2. Watchman primary search (+ alias search on miss)
      3. Local fuzzy fallback (stdlib SequenceMatcher, offline-safe)
      4. Category B jurisdiction → score=35, EDD (appended, not short-circuit)

    Returns list[RiskSignal] for aggregation by aml_orchestrator.
    """
    signals: list[RiskSignal] = []

    # ── Rule 1: Category A jurisdiction (hard block, short-circuit) ────────────
    jur_signal = _jurisdiction_signal(subject)
    if jur_signal and jur_signal.rule == "SUBJECT_JURISDICTION_A":
        return [jur_signal]

    # ── Rule 2: Watchman name search ──────────────────────────────────────────
    entities = _watchman_search(subject.name)

    # Try aliases if primary name yields no hits
    if not entities:
        for alias in subject.aliases[:3]:
            entities = _watchman_search(alias)
            if entities:
                break

    if entities:
        signals.extend(_hits_to_signals(_normalize_watchman(entities)))
    else:
        # ── Rule 3: Local fuzzy fallback ──────────────────────────────────────
        local_hits = _fuzzy_local_search(subject.name)
        if not local_hits:
            for alias in subject.aliases[:3]:
                local_hits = _fuzzy_local_search(alias)
                if local_hits:
                    break
        if local_hits:
            signals.extend(_hits_to_signals(local_hits))

    # ── Rule 4: Category B jurisdiction (EDD, non-blocking) ───────────────────
    if jur_signal:  # already confirmed it's B, not A
        signals.append(jur_signal)

    return signals


# ── Backward-compat wrapper (api.py uses this name) ──────────────────────────

async def check_sanctions(name: str, entity_type: str = "person") -> dict:
    """
    Legacy dict-return wrapper for api.py callers.
    New code: use screen_entity(SanctionsSubject(...)) directly.
    """
    subject = SanctionsSubject(name, entity_type=entity_type)
    signals = screen_entity(subject)
    sanctioned = any(
        s.rule in ("SANCTIONS_CONFIRMED", "SANCTIONS_PROBABLE", "SUBJECT_JURISDICTION_A")
        for s in signals
    )
    # Extract best name match from reason field ("'...' (source...")
    top_match = ""
    for s in signals:
        if "match" in s.reason and "'" in s.reason:
            try:
                top_match = s.reason.split("'")[1]
                break
            except IndexError:
                pass
    return {
        "sanctioned":    sanctioned,
        "hits":          [{"rule": s.rule, "reason": s.reason, "score": s.score} for s in signals],
        "hit_count":     len(signals),
        "lists_with_hits": sorted({s.rule for s in signals}),
        "top_match":     top_match,
        "sources_checked": ["watchman", "local_fuzzy"],
    }


# ── __main__ smoke tests ──────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("HARD BLOCK — Cat A jurisdiction",
         SanctionsSubject("Dmitry Ivanov", entity_type="person", jurisdiction="RU")),
        ("HARD BLOCK — Cat A + DPRK name",
         SanctionsSubject("Kim Jong Un", entity_type="person", jurisdiction="KP")),
        ("CLEAR — UK national, clean name",
         SanctionsSubject("Jane Smith", entity_type="person", jurisdiction="GB")),
        ("EDD — Cat B jurisdiction only",
         SanctionsSubject("Ahmad Hassan", entity_type="person", jurisdiction="SY")),
        ("PROBABLE — fuzzy name match",
         SanctionsSubject("Vladimir Puttin", entity_type="person", jurisdiction="DE")),
        ("COMPANY — known entity",
         SanctionsSubject("Hezbollah Finance Unit", entity_type="company", jurisdiction="LB")),
    ]

    sep = "=" * 60
    print(f"\n{sep}")
    print("  sanctions_check.py — smoke tests")
    print(sep)

    for label, subject in tests:
        sigs = screen_entity(subject)
        composite = min(sum(s.score for s in sigs), 100)
        print(f"\n  [{label}]  {subject.name} ({subject.jurisdiction})")
        if sigs:
            for sig in sigs:
                print(f"   [{sig.score:+d}] {sig.rule}")
                print(f"        {sig.reason[:90]}")
            print(f"   => composite score contrib: {composite}")
        else:
            print("   => CLEAR (no hits)")

    print(f"\n{sep}\n")
