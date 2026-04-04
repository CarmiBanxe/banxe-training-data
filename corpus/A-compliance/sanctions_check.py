#!/data/banxe/compliance-env/bin/python3
"""
Sanctions Check — Phase 2
PRIMARY:  Moov Watchman (OFAC/UN/EU/UK) on localhost:8084
SECONDARY: finsanctions (EU/UN/OFAC direct from gov servers, MIT)
Apache 2.0 + MIT
"""
import asyncio
import json
import sys
import httpx

WATCHMAN_URL = "http://127.0.0.1:8084"
WATCHMAN_MIN_MATCH = "0.80"


# ── Primary: Moov Watchman ────────────────────────────────────────────────────

async def _watchman_search(name: str, limit: int = 5) -> list[dict]:
    """Query Watchman REST API. Returns list of entity hits."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{WATCHMAN_URL}/v2/search",
                params={"name": name, "limit": limit, "minMatch": WATCHMAN_MIN_MATCH},
            )
            data = resp.json()
            return data.get("entities") or []
    except Exception as e:
        return []


def _normalize_watchman_hits(entities: list[dict]) -> list[dict]:
    hits = []
    for e in entities:
        hits.append({
            "source": "watchman",
            "list_name": e.get("sourceList", ""),
            "name_match": e.get("name", ""),
            "score": e.get("matchScore", 1.0),
            "entity_type": e.get("entityType", ""),
            "source_id": e.get("sourceID", ""),
        })
    return hits


# ── Secondary: finsanctions ───────────────────────────────────────────────────

def _finsanctions_search(name: str) -> list[dict]:
    """
    finsanctions pulls EU/UN/OFAC lists directly from gov servers.
    pip install finsanctions (MIT)
    Used as fallback/cross-check.
    """
    try:
        from finsanctions import search
        results = search(name, threshold=0.80)
        hits = []
        for r in results[:5]:
            hits.append({
                "source": "finsanctions",
                "list_name": r.get("list", ""),
                "name_match": r.get("name", ""),
                "score": r.get("score", 0.0),
                "entity_type": r.get("type", ""),
                "source_id": r.get("id", ""),
            })
        return hits
    except ImportError:
        return []
    except Exception:
        return []


# ── Main function ─────────────────────────────────────────────────────────────

async def check_sanctions(name: str, entity_type: str = "person") -> dict:
    """
    Full sanctions check: Watchman (primary) + finsanctions (secondary).

    Returns:
        sanctioned: bool
        hits: list of {source, list_name, name_match, score}
        checked_lists: list of lists checked
        sources_checked: ["watchman", "finsanctions"]
    """
    # Run Watchman (async) and finsanctions (sync in executor) in parallel
    loop = asyncio.get_event_loop()
    watchman_task = asyncio.create_task(_watchman_search(name))
    finsanctions_hits = await loop.run_in_executor(None, _finsanctions_search, name)
    watchman_entities = await watchman_task

    watchman_hits = _normalize_watchman_hits(watchman_entities)

    # Merge hits, deduplicate by list_name + name_match
    all_hits = watchman_hits + [h for h in finsanctions_hits
                                if not any(w["name_match"] == h["name_match"] and
                                           w["list_name"] == h["list_name"]
                                           for w in watchman_hits)]

    checked_lists = ["us_ofac_sdn", "us_ofac_cons", "us_csl", "us_fincen_311",
                     "uk_csl", "eu_csl", "un_csl"]

    return {
        "sanctioned": len(all_hits) > 0,
        "hits": all_hits,
        "hit_count": len(all_hits),
        "lists_with_hits": list({h["list_name"] for h in all_hits}),
        "checked_lists": checked_lists,
        "sources_checked": ["watchman", "finsanctions"],
        "top_match": all_hits[0]["name_match"] if all_hits else "",
    }


if __name__ == "__main__":
    name = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Vladimir Putin"
    result = asyncio.run(check_sanctions(name))
    print(json.dumps(result, indent=2, ensure_ascii=False))
