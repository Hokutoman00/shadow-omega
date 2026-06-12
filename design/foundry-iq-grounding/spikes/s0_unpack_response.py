"""S0 spike (G3): GA retrieve 応答の二重 JSON 展開。公式 docs の応答例で資格情報なしで挙動確認。"""
import json

# agentic-retrieval-how-to-retrieve の GA 応答例を縮約（response[0].content[0].text は JSON 文字列）
raw = {
    "response": [{"content": [{"type": "text", "text": json.dumps([
        {"ref_id": "0", "title": "CWE-362", "terms": "race condition", "content": "balance check..."}
    ])}]}],
    "references": [{"type": "searchIndex", "id": "0", "activitySource": 2,
                    "docKey": "cwe-362-race-condition", "sourceData": None}],
    "activity": [{"type": "searchIndex", "id": 2, "knowledgeSourceName": "shadow-omega-security-ks",
                  "count": 1, "elapsedMs": 412}],
}

chunks = json.loads(raw["response"][0]["content"][0]["text"])
ref_by_id = {r["id"]: r for r in raw["references"]}
assert chunks[0]["ref_id"] in ref_by_id, "citation 整合 (I2) が崩れている"
print("docKey =", ref_by_id[chunks[0]["ref_id"]]["docKey"])
print("activity =", [a for a in raw["activity"] if a["type"] == "searchIndex"][0]["elapsedMs"], "ms")
