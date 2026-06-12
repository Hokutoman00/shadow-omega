"""
Foundry IQ grounding layer for Shadow-Omega convergence certificates.

Connects certificate findings to a Foundry IQ knowledge base (Azure AI Search
agentic retrieval, GA api-version 2026-04-01) holding a curated CWE/OWASP
corpus, and returns citation objects whose ref_id / docKey / corpus entry are
three-point matched. Every grounding result carries an explicit provenance
label so a live retrieval can never be confused with the bundled snapshot:

  - "foundry_iq_live"   : retrieved from the knowledge base over HTTPS
  - "bundled_snapshot"  : replayed from data/foundry_iq_snapshot.json

The fallback path exists so judges can run the full pipeline with zero Azure
credentials; it is never silent because the provenance label is fixed at the
entry point of each path and no code path rewrites it afterwards.

Uses Python stdlib (urllib.request) only, matching mcp_server.py conventions.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CORPUS_PATH = os.path.join(_DATA_DIR, "security_knowledge_corpus.json")
SNAPSHOT_PATH = os.path.join(_DATA_DIR, "foundry_iq_snapshot.json")

KNOWLEDGE_BASE_NAME = "shadow-omega-kb"
KNOWLEDGE_SOURCE_NAME = "shadow-omega-security-ks"
API_VERSION = "2026-04-01"

# G1: static intent table. Query strings are decided without any LLM so the
# zero-cost minimal retrieval path (keyword/hybrid search) stays sufficient.
FINDING_INTENTS = {
    "non_atomic_value_transfer": (
        "race condition non-atomic balance update check-then-act "
        "mitigation mutex compare-and-swap"
    ),
    "invalid_amount_transfer": (
        "improper input validation negative amount quantity bounds guard"
    ),
    "direct_authority_mutation": (
        "broken access control privilege escalation direct role mutation guarded API"
    ),
    "no_convergence": "secure design review residual risk defense in depth",
}


class GroundingUnavailable(Exception):
    """Live Foundry IQ path cannot be used; caller should take the snapshot path."""


def load_corpus() -> list[dict[str, Any]]:
    with open(CORPUS_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def corpus_by_id() -> dict[str, dict[str, Any]]:
    return {doc["id"]: doc for doc in load_corpus()}


def _credentials() -> tuple[str, str]:
    endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT", "").rstrip("/")
    key = os.environ.get("AZURE_SEARCH_ADMIN_KEY", "")
    if not endpoint or not key:
        raise GroundingUnavailable(
            "AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_ADMIN_KEY are not configured"
        )
    return endpoint, key


def retrieve_grounding(finding: str) -> dict[str, Any]:
    """
    G2: POST /knowledgebases/{kb}/retrieve against the live knowledge base.

    Raises GroundingUnavailable when credentials are missing, and lets
    urllib.error.URLError / TimeoutError propagate to the fallback in
    ground_finding().
    """
    endpoint, key = _credentials()
    url = (
        f"{endpoint}/knowledgebases/{KNOWLEDGE_BASE_NAME}/retrieve"
        f"?api-version={API_VERSION}"
    )
    body = {
        "intents": [{"type": "semantic", "search": FINDING_INTENTS[finding]}],
        "knowledgeSourceParams": [
            {"knowledgeSourceName": KNOWLEDGE_SOURCE_NAME, "kind": "searchIndex"}
        ],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "api-key": key},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def unpack_response(raw: dict[str, Any]) -> tuple[list[dict], list[dict], list[dict]]:
    """
    G3: unpack the double-encoded GA retrieve response.

    raw["response"][0]["content"][0]["text"] is itself a JSON string holding
    the chunk list; references and activity ride alongside as plain arrays.
    KeyError / IndexError / json.JSONDecodeError propagate to the fallback.
    """
    chunks = json.loads(raw["response"][0]["content"][0]["text"])
    references = raw.get("references", [])
    activity = raw.get("activity", [])
    return chunks, references, activity


def build_citations(
    chunks: list[dict[str, Any]],
    references: list[dict[str, Any]],
    corpus_index: dict[str, dict[str, Any]],
    provenance: str,
) -> list[dict[str, Any]]:
    """
    G4: three-point matching. chunk.ref_id <-> references[].id recovers the
    docKey, and docKey <-> corpus id recovers CWE/OWASP metadata. provenance
    is supplied by the caller (G5 passes "foundry_iq_live", G6 passes
    "bundled_snapshot") and is never decided here.
    """
    ref_by_id = {str(ref["id"]): ref for ref in references}
    citations = []
    for chunk in chunks:
        ref = ref_by_id.get(str(chunk.get("ref_id")))
        if ref is None:
            continue
        doc = corpus_index.get(ref.get("docKey"))
        if doc is None:
            continue
        citations.append(
            {
                "ref_id": str(chunk["ref_id"]),
                "doc_key": doc["id"],
                "title": doc["title"],
                "cwe_id": doc["cwe_id"],
                "owasp_id": doc["owasp_id"],
                "source_url": doc["source_url"],
                "excerpt": chunk.get("content", "")[:280],
                "provenance": provenance,
            }
        )
    return citations


def _activity_summary(activity: list[dict[str, Any]]) -> dict[str, Any]:
    for entry in activity:
        if entry.get("type") == "searchIndex":
            return {
                "knowledgeSourceName": entry.get("knowledgeSourceName"),
                "count": entry.get("count"),
                "elapsedMs": entry.get("elapsedMs"),
            }
    return {}


def load_snapshot_grounding(finding: str) -> dict[str, Any]:
    """
    G6: replay the bundled snapshot (recorded raw retrieve responses) through
    the same unpack/citation pipeline as the live path. provenance is fixed
    to "bundled_snapshot" at this entry point.
    """
    with open(SNAPSHOT_PATH, encoding="utf-8") as fh:
        snapshot = json.load(fh)
    raw = snapshot["responses"][finding]
    chunks, references, activity = unpack_response(raw)
    citations = build_citations(chunks, references, corpus_by_id(), "bundled_snapshot")
    return {
        "provenance": "bundled_snapshot",
        "knowledge_base": snapshot.get("knowledge_base", KNOWLEDGE_BASE_NAME),
        "api_version": snapshot.get("api_version", API_VERSION),
        "finding": finding,
        "captured_at": snapshot.get("captured_at"),
        "citations": citations,
        "retrieval_activity": _activity_summary(activity),
    }


def ground_finding(finding: str) -> dict[str, Any]:
    """
    G5: public API. Tries the live Foundry IQ path, falling back to the
    bundled snapshot on exactly three conditions: missing credentials,
    network/timeout failure, or a malformed retrieve response.
    """
    if finding not in FINDING_INTENTS:
        return {
            "error": f"unknown finding: {finding}",
            "known_findings": sorted(FINDING_INTENTS),
        }
    try:
        raw = retrieve_grounding(finding)
        chunks, references, activity = unpack_response(raw)
        citations = build_citations(
            chunks, references, corpus_by_id(), "foundry_iq_live"
        )
        return {
            "provenance": "foundry_iq_live",
            "knowledge_base": KNOWLEDGE_BASE_NAME,
            "api_version": API_VERSION,
            "finding": finding,
            "citations": citations,
            "retrieval_activity": _activity_summary(activity),
        }
    except (
        GroundingUnavailable,
        urllib.error.URLError,
        TimeoutError,
        KeyError,
        IndexError,
        json.JSONDecodeError,
    ):
        return load_snapshot_grounding(finding)


def provenance_status() -> dict[str, Any]:
    """
    Report which grounding path is active. Returns env-var presence as
    booleans only; credential values are never included.
    """
    endpoint_set = bool(os.environ.get("AZURE_SEARCH_ENDPOINT"))
    key_set = bool(os.environ.get("AZURE_SEARCH_ADMIN_KEY"))
    return {
        "active_path": "foundry_iq_live" if (endpoint_set and key_set) else "bundled_snapshot",
        "azure_search_endpoint_configured": endpoint_set,
        "azure_search_admin_key_configured": key_set,
        "knowledge_base": KNOWLEDGE_BASE_NAME,
        "knowledge_source": KNOWLEDGE_SOURCE_NAME,
        "api_version": API_VERSION,
        "corpus_documents": len(load_corpus()),
        "note": (
            "bundled_snapshot replays recorded retrieve responses through the "
            "same citation pipeline; provenance labels make the two paths "
            "distinguishable in every certificate."
        ),
    }
