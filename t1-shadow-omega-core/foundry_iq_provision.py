"""
One-shot provisioning CLI for the Shadow-Omega Foundry IQ knowledge base.

Creates (idempotently) on an Azure AI Search service, Free tier sufficient:
  1. search index  : shadow-omega-security-index (semantic config attached)
  2. documents     : data/security_knowledge_corpus.json via mergeOrUpload
  3. knowledge source : shadow-omega-security-ks (kind=searchIndex)
  4. knowledge base   : shadow-omega-kb (no models field = no LLM = zero cost)

Usage:
  python foundry_iq_provision.py --provision   # steps 1-4, safe to re-run
  python foundry_iq_provision.py --snapshot    # record live retrieve responses
                                               # for all findings into
                                               # data/foundry_iq_snapshot.json

Requires AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_ADMIN_KEY in the environment
(see .env.example; keep real values out of the repository).

Uses Python stdlib (urllib.request) only, matching mcp_server.py conventions.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

from foundry_iq_grounding import (
    API_VERSION,
    FINDING_INTENTS,
    KNOWLEDGE_BASE_NAME,
    KNOWLEDGE_SOURCE_NAME,
    SNAPSHOT_PATH,
    load_corpus,
    retrieve_grounding,
)

INDEX_NAME = "shadow-omega-security-index"
SEMANTIC_CONFIG_NAME = "sec-semantic-config"

INDEX_DEFINITION = {
    "name": INDEX_NAME,
    "fields": [
        {"name": "id", "type": "Edm.String", "key": True, "filterable": True},
        {"name": "title", "type": "Edm.String", "searchable": True},
        {"name": "terms", "type": "Edm.String", "searchable": True},
        {"name": "content", "type": "Edm.String", "searchable": True},
        {"name": "cwe_id", "type": "Edm.String", "filterable": True, "retrievable": True},
        {"name": "owasp_id", "type": "Edm.String", "filterable": True, "retrievable": True},
        {"name": "source_url", "type": "Edm.String", "retrievable": True},
        {
            "name": "finding_tags",
            "type": "Collection(Edm.String)",
            "filterable": True,
            "retrievable": True,
        },
    ],
    "semantic": {
        "configurations": [
            {
                "name": SEMANTIC_CONFIG_NAME,
                "prioritizedFields": {
                    "titleField": {"fieldName": "title"},
                    "prioritizedContentFields": [{"fieldName": "content"}],
                    "prioritizedKeywordsFields": [{"fieldName": "terms"}],
                },
            }
        ]
    },
}

KNOWLEDGE_SOURCE_DEFINITION = {
    "name": KNOWLEDGE_SOURCE_NAME,
    "kind": "searchIndex",
    "description": "Curated CWE/OWASP security knowledge for Shadow-Omega audit grounding.",
    "encryptionKey": None,
    "searchIndexParameters": {
        "searchIndexName": INDEX_NAME,
        "semanticConfigurationName": SEMANTIC_CONFIG_NAME,
        "sourceDataFields": [
            {"name": "id"},
            {"name": "title"},
            {"name": "cwe_id"},
            {"name": "owasp_id"},
            {"name": "source_url"},
        ],
    },
}

KNOWLEDGE_BASE_DEFINITION = {
    "name": KNOWLEDGE_BASE_NAME,
    "description": "Grounding knowledge base for Shadow-Omega convergence certificates.",
    "knowledgeSources": [{"name": KNOWLEDGE_SOURCE_NAME}],
    "encryptionKey": None,
}


def _credentials() -> tuple[str, str]:
    endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT", "").rstrip("/")
    key = os.environ.get("AZURE_SEARCH_ADMIN_KEY", "")
    if not endpoint or not key:
        sys.exit(
            "AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_ADMIN_KEY must be set "
            "(see .env.example)."
        )
    return endpoint, key


def _send(url: str, payload: dict[str, Any], method: str) -> dict[str, Any]:
    _, key = _credentials()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "api-key": key},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {"status": resp.status}
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", errors="replace")
        sys.exit(f"{method} {url} failed: HTTP {err.code}\n{detail}")


def provision() -> None:
    endpoint, _ = _credentials()

    print(f"[1/4] PUT index {INDEX_NAME}")
    _send(
        f"{endpoint}/indexes/{INDEX_NAME}?api-version={API_VERSION}",
        INDEX_DEFINITION,
        "PUT",
    )

    print("[2/4] mergeOrUpload corpus documents")
    corpus = load_corpus()
    actions = [{"@search.action": "mergeOrUpload", **doc} for doc in corpus]
    result = _send(
        f"{endpoint}/indexes/{INDEX_NAME}/docs/index?api-version={API_VERSION}",
        {"value": actions},
        "POST",
    )
    uploaded = sum(1 for item in result.get("value", []) if item.get("status"))
    print(f"      {uploaded}/{len(corpus)} documents accepted")

    print(f"[3/4] PUT knowledge source {KNOWLEDGE_SOURCE_NAME}")
    _send(
        f"{endpoint}/knowledgesources/{KNOWLEDGE_SOURCE_NAME}?api-version={API_VERSION}",
        KNOWLEDGE_SOURCE_DEFINITION,
        "PUT",
    )

    print(f"[4/4] PUT knowledge base {KNOWLEDGE_BASE_NAME}")
    _send(
        f"{endpoint}/knowledgebases/{KNOWLEDGE_BASE_NAME}?api-version={API_VERSION}",
        KNOWLEDGE_BASE_DEFINITION,
        "PUT",
    )

    print("provisioning complete (all steps idempotent; safe to re-run)")


def snapshot() -> None:
    _credentials()  # fail fast with a clear message before any retrieval
    responses: dict[str, Any] = {}
    for finding in FINDING_INTENTS:
        print(f"retrieve: {finding}")
        responses[finding] = retrieve_grounding(finding)

    payload = {
        "schema": "shadow-omega.foundry-iq-snapshot.v1",
        "knowledge_base": KNOWLEDGE_BASE_NAME,
        "api_version": API_VERSION,
        "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "note": (
            "Recorded live retrieve responses from the Foundry IQ knowledge base. "
            "Used as the bundled_snapshot fallback so the grounding pipeline runs "
            "without Azure credentials."
        ),
        "responses": responses,
    }
    with open(SNAPSHOT_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    print(f"snapshot written to {SNAPSHOT_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provision", action="store_true", help="create index/source/base")
    parser.add_argument("--snapshot", action="store_true", help="record live retrieve responses")
    args = parser.parse_args()

    if not args.provision and not args.snapshot:
        parser.print_help()
        sys.exit(1)
    if args.provision:
        provision()
    if args.snapshot:
        snapshot()


if __name__ == "__main__":
    main()
