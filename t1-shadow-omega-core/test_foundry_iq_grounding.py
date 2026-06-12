"""
Acceptance tests for the Foundry IQ grounding layer (design §6 invariants I1-I3
and §7 test plan). Run with:  python -m unittest test_foundry_iq_grounding -v

No Azure credentials required: the live path is exercised through a mocked
urllib.request.urlopen, and the fallback path replays the bundled snapshot.
"""

from __future__ import annotations

import io
import json
import os
import unittest
import urllib.error
from unittest import mock

import foundry_iq_grounding as g
from convergence_certificate import build_convergence_certificate

RISKY_TRANSFER_JS = """
async function transfer(accountStore, userId, targetId, amount) {
  const user = await accountStore.get(userId);
  const target = await accountStore.get(targetId);
  if (user.balance >= amount) {
    user.balance -= amount;
    target.balance += amount;
  }
  return { ok: true };
}
"""

_ENV_KEYS = ("AZURE_SEARCH_ENDPOINT", "AZURE_SEARCH_ADMIN_KEY")


def _without_credentials():
    """Context: both Azure env vars absent."""
    cleaned = {k: v for k, v in os.environ.items() if k not in _ENV_KEYS}
    return mock.patch.dict(os.environ, cleaned, clear=True)


def _with_fake_credentials():
    return mock.patch.dict(
        os.environ,
        {
            "AZURE_SEARCH_ENDPOINT": "https://fake-service.search.windows.net",
            "AZURE_SEARCH_ADMIN_KEY": "fake-admin-key-not-a-secret",
        },
    )


def _fake_retrieve_response() -> dict:
    """GA-shaped retrieve response built from real corpus doc keys."""
    chunks = [
        {
            "ref_id": "0",
            "title": "CWE-362",
            "terms": "race condition",
            "content": "Check-then-act on shared balance state without a lock.",
        }
    ]
    return {
        "response": [
            {"content": [{"type": "text", "text": json.dumps(chunks)}]}
        ],
        "references": [
            {
                "type": "searchIndex",
                "id": "0",
                "activitySource": 2,
                "docKey": "cwe-362-race-condition",
                "sourceData": None,
            }
        ],
        "activity": [
            {
                "type": "searchIndex",
                "id": 2,
                "knowledgeSourceName": g.KNOWLEDGE_SOURCE_NAME,
                "count": 1,
                "elapsedMs": 99,
            }
        ],
    }


def _urlopen_returning(payload: dict):
    body = io.BytesIO(json.dumps(payload).encode("utf-8"))
    cm = mock.MagicMock()
    cm.__enter__.return_value = body
    cm.__exit__.return_value = False
    return mock.MagicMock(return_value=cm)


class TestCorpusCoverage(unittest.TestCase):
    """I1: every finding the certificate can emit has corpus documents."""

    def test_finding_coverage_is_exactly_the_intent_table(self):
        tagged = set()
        for doc in g.load_corpus():
            tagged.update(doc["finding_tags"])
        self.assertEqual(tagged, set(g.FINDING_INTENTS))

    def test_corpus_documents_have_required_fields(self):
        required = {"id", "title", "terms", "content", "cwe_id", "owasp_id",
                    "source_url", "finding_tags"}
        corpus = g.load_corpus()
        self.assertGreaterEqual(len(corpus), 12)
        for doc in corpus:
            self.assertTrue(required.issubset(doc), f"missing fields in {doc.get('id')}")


class TestSnapshotFallback(unittest.TestCase):
    """G6 + I2 + I3 on the credential-less path judges actually run."""

    def test_fallback_used_without_credentials_and_no_network_call(self):
        with _without_credentials(), mock.patch.object(
            g.urllib.request, "urlopen"
        ) as fake_urlopen:
            result = g.ground_finding("non_atomic_value_transfer")
        fake_urlopen.assert_not_called()  # negative assert: no silent live attempt
        self.assertEqual(result["provenance"], "bundled_snapshot")
        self.assertGreater(len(result["citations"]), 0)

    def test_all_findings_resolve_with_citations_from_snapshot(self):
        corpus_ids = set(g.corpus_by_id())
        with _without_credentials():
            for finding in g.FINDING_INTENTS:
                result = g.ground_finding(finding)
                self.assertEqual(result["finding"], finding)
                cited = {c["doc_key"] for c in result["citations"]}
                self.assertGreater(len(cited), 0, finding)
                self.assertTrue(cited.issubset(corpus_ids), finding)  # I2

    def test_provenance_is_two_valued(self):
        # I3: every citation carries one of exactly two provenance labels.
        with _without_credentials():
            for finding in g.FINDING_INTENTS:
                result = g.ground_finding(finding)
                labels = {result["provenance"]}
                labels.update(c["provenance"] for c in result["citations"])
                self.assertEqual(labels, {"bundled_snapshot"})

    def test_network_failure_falls_back_not_crashes(self):
        with _with_fake_credentials(), mock.patch.object(
            g.urllib.request,
            "urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            result = g.ground_finding("invalid_amount_transfer")
        self.assertEqual(result["provenance"], "bundled_snapshot")

    def test_unknown_finding_is_an_error_not_a_lookup(self):
        result = g.ground_finding("nonexistent_finding")
        self.assertIn("error", result)
        self.assertEqual(result["known_findings"], sorted(g.FINDING_INTENTS))


class TestLivePath(unittest.TestCase):
    """G2-G4 through a mocked GA retrieve response."""

    def test_live_path_unpacks_and_three_point_matches(self):
        with _with_fake_credentials(), mock.patch.object(
            g.urllib.request, "urlopen", _urlopen_returning(_fake_retrieve_response())
        ):
            result = g.ground_finding("non_atomic_value_transfer")
        self.assertEqual(result["provenance"], "foundry_iq_live")
        self.assertEqual(len(result["citations"]), 1)
        citation = result["citations"][0]
        self.assertEqual(citation["doc_key"], "cwe-362-race-condition")
        self.assertEqual(citation["cwe_id"], "CWE-362")
        self.assertEqual(citation["provenance"], "foundry_iq_live")
        self.assertEqual(result["retrieval_activity"]["elapsedMs"], 99)

    def test_unmatched_ref_ids_are_dropped_not_fabricated(self):
        payload = _fake_retrieve_response()
        payload["references"][0]["docKey"] = "not-in-corpus"
        with _with_fake_credentials(), mock.patch.object(
            g.urllib.request, "urlopen", _urlopen_returning(payload)
        ):
            result = g.ground_finding("non_atomic_value_transfer")
        # I2: a citation may never point outside the corpus.
        self.assertEqual(result["citations"], [])

    def test_malformed_response_falls_back(self):
        with _with_fake_credentials(), mock.patch.object(
            g.urllib.request, "urlopen", _urlopen_returning({"unexpected": True})
        ):
            result = g.ground_finding("direct_authority_mutation")
        self.assertEqual(result["provenance"], "bundled_snapshot")


class TestCertificateV2(unittest.TestCase):
    """E1-E3: the certificate carries grounding and a grounded patch strategy."""

    def test_certificate_embeds_knowledge_grounding(self):
        with _without_credentials():
            cert = build_convergence_certificate(RISKY_TRANSFER_JS)
        self.assertEqual(cert["schema"], "shadow-omega.convergence-certificate.v2")
        grounding = cert["knowledge_grounding"]
        self.assertEqual(grounding["finding"], cert["finding"])  # I1 linkage
        self.assertEqual(grounding["provenance"], "bundled_snapshot")
        self.assertGreater(len(grounding["citations"]), 0)

    def test_evidence_sources_include_foundry_iq(self):
        with _without_credentials():
            cert = build_convergence_certificate(RISKY_TRANSFER_JS)
        types = {entry["type"] for entry in cert["evidence_sources"]}
        self.assertIn("foundry_iq_knowledge_grounding", types)
        entry = next(
            e for e in cert["evidence_sources"]
            if e["type"] == "foundry_iq_knowledge_grounding"
        )
        self.assertEqual(entry["citation_count"], len(cert["knowledge_grounding"]["citations"]))

    def test_patch_strategy_is_grounded_when_converged(self):
        with _without_credentials():
            cert = build_convergence_certificate(RISKY_TRANSFER_JS)
        strategy = cert["recommended_patch_strategy"]
        self.assertIsInstance(strategy, dict)
        self.assertIn("strategy", strategy)
        if cert["status"] == "converged":
            self.assertGreater(len(strategy["grounded_in"]), 0)
            for doc_key in strategy["grounded_in"]:
                self.assertTrue(doc_key.startswith("patch-"))


class TestProvenanceStatus(unittest.TestCase):
    def test_status_reports_presence_only_never_values(self):
        with _with_fake_credentials():
            status = g.provenance_status()
        rendered = json.dumps(status)
        self.assertNotIn("fake-admin-key-not-a-secret", rendered)
        self.assertNotIn("fake-service.search.windows.net", rendered)
        self.assertIs(status["azure_search_endpoint_configured"], True)
        self.assertIs(status["azure_search_admin_key_configured"], True)
        self.assertEqual(status["active_path"], "foundry_iq_live")

    def test_status_without_credentials_points_to_snapshot(self):
        with _without_credentials():
            status = g.provenance_status()
        self.assertEqual(status["active_path"], "bundled_snapshot")
        self.assertIs(status["azure_search_endpoint_configured"], False)


if __name__ == "__main__":
    unittest.main()
