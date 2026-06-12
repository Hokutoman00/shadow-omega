# Grounded Audit Knowledge Layer — design.md

Shadow-Ω の収束証明書（convergence certificate）に、Foundry IQ（Azure AI Search agentic retrieval / knowledge base）由来の引用付きセキュリティ知識を組み込むピースの設計書。
深度化プロトコル（`protocols/deep-ideation-protocol.md`）原則1〜7 準拠。

- 要件の根拠: Agents League Creative Apps Core Requirement #2「Microsoft IQ Integration (Required)」。Shadow-Ω は現状 Foundry の **モデル推論** のみ利用しており、**知識検索層（Foundry IQ）** は未統合（虚偽 claim 禁止 = C1）
- 制約: 追加投資ゼロ円（chairman 指示）。締切 6/14 11:59 PM PT
- スコープ判断の所在: 削る判断は chairman のみ（介入10 / 心得1）

---

## 0. ゼロ円成立の根拠（確認済み事実）

| # | 事実 | 出所 |
|---|------|------|
| Z1 | Azure AI Search **Free tier で knowledge base 3 個 / knowledge source 3 個 / KB あたり source 3 個** まで作成可 | search-limits-quotas-capacity（ms.date 2026-06-02 版の agentic retrieval 上限表） |
| Z2 | 公式文書が「最小コスト・PoC には **Azure AI Search の free tier と agentic retrieval の無料トークン枠**」を明示推奨 | what-is-foundry-iq |
| Z3 | **GA 2026-04-01 API は minimal・抽出型 retrieval のみ**で、LLM（query planning / answer synthesis）は **非 web ソースでは unsupported** → Azure OpenAI のデプロイ・課金が構造的に不要 | agentic-retrieval-how-to-create-knowledge-base / how-to-retrieve |
| Z4 | minimal effort は「query 文字列がそのまま retrieval engine に渡る（keyword / hybrid search）」= LLM ゼロ | how-to-retrieve「Use minimal reasoning effort」節 |
| Z5 | 各 knowledge base は標準で **MCP サーバー**（tool 名 `knowledge_base_retrieve`）を公開する | how-to-retrieve「Call the MCP endpoint」節 |

**chairman action（唯一の外部依存）**: Azure 無料アカウント作成（カード登録のみ・請求ゼロ）。これが済むまで live スパイク（leaf S1）は実行不能だが、コーパス・スキーマ・実装・テスト・fallback は全て先行可能。

**未検証リスク R1**: Free tier 上での semantic configuration 作成可否（GA の knowledge source は `semanticConfigurationName` 必須）。Z1/Z2 から成立見込みだが、スパイク S1 で実機確認する。不成立時の代替経路は §6 に記載。

---

## 1. 3段階構造（原則1: 均等深化）

```
前段階: 知識空間の生成
  curated security corpus (JSON)
    → Azure AI Search index (semantic config 付き)
    → search-index knowledge source
    → knowledge base（LLM なし・GA API）

中段階: 監査所見と知識空間の非対称接続
  certificate の finding（4値）
    → 静的 intent テーブル（LLM なしの query 決定）
    → POST /knowledgebases/{kb}/retrieve (intents 形式)
    → ref_id ↔ references[].docKey ↔ ローカル corpus の三点突合
    → citation オブジェクト列

後段階: 圧縮と適用
  citation 列 → certificate の knowledge_grounding 節
             → evidence_sources への新 entry 型
             → recommended_patch_strategy への grounded_in 付与
             → MCP tool として Copilot へ露出
             → 審査員向け: KB 自身の MCP endpoint も公開
```

### 前段階 WWHW
- **What（対象の再定義）**: 「セキュリティ知識」を、Shadow-Ω の finding 4 値（`non_atomic_value_transfer` / `invalid_amount_transfer` / `direct_authority_mutation` / `no_convergence`）に向けて正規化した **finding-addressable corpus**（各文書が `finding_tags` を持つ）として再定義する
- **How**: `data/security_knowledge_corpus.json`（下記スキーマ）→ REST 4 連 PUT/POST（leaf P2〜P5）で Azure 側オブジェクトに射影
- **Who**: provisioning スクリプト `foundry_iq_provision.py` を実行する開発者（1回限り・idempotent）
- **Why**: GA API の minimal retrieval は web ソース不可（LLM 必須のため）。自前 index 経由が唯一のゼロ円経路（Z3）

### 中段階 WWHW
- **What**: 「引用」を、`ref_id`（retrieve 応答内の参照 ID）・`docKey`（index 上の文書キー）・ローカル corpus エントリの **三点が突合済みの citation オブジェクト** として再定義する
- **How**: finding → 固定 intent 文字列（leaf G1 の静的テーブル）→ retrieve REST 呼び出し（G2）→ 応答の二重 JSON の展開（G3）→ docKey でローカル corpus を逆引きし CWE/OWASP ID を復元（G4）
- **Who**: `convergence_certificate.build_convergence_certificate()` と MCP tool `ground_finding` の呼び出し元（Copilot / 審査員）
- **Why**: 収束証明書の所見が「Shadow-Ω の合成宇宙の多数決」だけでなく、**CWE/OWASP という外部知識体系への引用**で接地される → hallucination 削減という Foundry IQ の本来目的に一致

### 後段階 WWHW
- **What**: 「証明書」を、自己完結の監査結果から **provenance ラベル付き（`foundry_iq_live` / `bundled_snapshot`）の grounded 文書** へ再定義する
- **How**: leaf E1〜E3（certificate 拡張）+ E4（MCP tool）+ E5（README / 提出文面）
- **Who**: ①GitHub Copilot（MCP tool 経由で grounded certificate を受領）②審査員（README 手順で KB の MCP endpoint を Copilot に直結可能）③資格情報なしで repo を動かす審査員（fallback snapshot で全機能動作）
- **Why**: 審査基準 Accuracy 20% / Reliability&Safety 20% に直撃。live と snapshot を明示ラベルで区別することで C1（欺かない）を構造的に保証

---

## 2. 前段階の leaf（P 系列）

### P1: corpus 定義 — `data/security_knowledge_corpus.json`
新規ファイル。`json.load()` で読める配列。文書スキーマ（fixture は §5）:

```json
{
  "id": "cwe-362-race-condition",
  "title": "CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization",
  "terms": "race condition, TOCTOU, non-atomic update, check-then-act",
  "content": "本文 300-800 字。balance check と decrement が別命令に分かれた transfer の悪用経路と、mutex / compare-and-swap による直列化の根拠を記述。",
  "cwe_id": "CWE-362",
  "owasp_id": "A04:2021",
  "source_url": "https://cwe.mitre.org/data/definitions/362.html",
  "finding_tags": ["non_atomic_value_transfer"]
}
```

収録 12 文書（finding カバレッジは不変量 I1）:

| finding | 文書 id（CWE/OWASP） |
|---|---|
| non_atomic_value_transfer | cwe-362-race-condition / cwe-667-improper-locking / patch-mutex-cas（直列化パッチ根拠） |
| invalid_amount_transfer | cwe-20-input-validation / cwe-682-incorrect-calculation / cwe-1284-quantity-validation / patch-amount-guard |
| direct_authority_mutation | cwe-269-privilege-management / cwe-284-access-control / owasp-a01-broken-access-control / patch-guarded-authority-api |
| no_convergence | secure-design-residual-risk（OWASP A04 設計レビュー・残存リスクの扱い） |

文書本文は CWE/OWASP 公式定義の要約 + Shadow-Ω finding への対応関係を自前執筆（コピペではなく要約 = ライセンス安全。`source_url` で原典を引用）。合計 < 50 KB（Free tier 50 MB の 0.1%）。

### P2: index 作成 — `urllib.request.Request(url, method="PUT")`
`PUT {AZURE_SEARCH_ENDPOINT}/indexes/shadow-omega-security-index?api-version=2026-04-01`、ヘッダ `api-key` + `Content-Type: application/json`。body:

```json
{
  "name": "shadow-omega-security-index",
  "fields": [
    {"name": "id", "type": "Edm.String", "key": true, "filterable": true},
    {"name": "title", "type": "Edm.String", "searchable": true},
    {"name": "terms", "type": "Edm.String", "searchable": true},
    {"name": "content", "type": "Edm.String", "searchable": true},
    {"name": "cwe_id", "type": "Edm.String", "filterable": true, "retrievable": true},
    {"name": "owasp_id", "type": "Edm.String", "filterable": true, "retrievable": true},
    {"name": "source_url", "type": "Edm.String", "retrievable": true},
    {"name": "finding_tags", "type": "Collection(Edm.String)", "filterable": true, "retrievable": true}
  ],
  "semantic": {
    "configurations": [{
      "name": "sec-semantic-config",
      "prioritizedFields": {
        "titleField": {"fieldName": "title"},
        "prioritizedContentFields": [{"fieldName": "content"}],
        "prioritizedKeywordsFields": [{"fieldName": "terms"}]
      }
    }]
  }
}
```

### P3: 文書投入 — `POST .../docs/index`
`POST {endpoint}/indexes/shadow-omega-security-index/docs/index?api-version=2026-04-01`。body は `{"value": [{"@search.action": "mergeOrUpload", ...corpus 文書}, ...]}`。`json.dumps(payload).encode("utf-8")` を `urllib.request.urlopen()` に渡す（タイムアウト 15s）。

### P4: knowledge source 作成
`PUT {endpoint}/knowledgesources/shadow-omega-security-ks?api-version=2026-04-01`:

```json
{
  "name": "shadow-omega-security-ks",
  "kind": "searchIndex",
  "description": "Curated CWE/OWASP security knowledge for Shadow-Omega audit grounding.",
  "encryptionKey": null,
  "searchIndexParameters": {
    "searchIndexName": "shadow-omega-security-index",
    "semanticConfigurationName": "sec-semantic-config",
    "sourceDataFields": [
      {"name": "id"}, {"name": "title"}, {"name": "cwe_id"},
      {"name": "owasp_id"}, {"name": "source_url"}
    ]
  }
}
```

（GA 2026-04-01 では `semanticConfigurationName` 必須 — how-to-search-index の preview 節の注記より逆算。確認済み）

### P5: knowledge base 作成
`PUT {endpoint}/knowledgebases/shadow-omega-kb?api-version=2026-04-01`:

```json
{
  "name": "shadow-omega-kb",
  "description": "Grounding knowledge base for Shadow-Omega convergence certificates.",
  "knowledgeSources": [{"name": "shadow-omega-security-ks"}],
  "encryptionKey": null
}
```

`models` フィールドなし = LLM なし（Z3）。

### P6: provisioning CLI — `foundry_iq_provision.py`
`argparse.ArgumentParser()` で 2 サブコマンド:
- `--provision`: P2→P3→P4→P5 を順に実行（全て PUT/mergeOrUpload なので再実行安全）
- `--snapshot`: 4 finding 全てについて G2 の retrieve を実行し、生応答を `data/foundry_iq_snapshot.json` に `json.dump(obj, fh, indent=2)` で保存（fallback 用の正本。録画日時を `captured_at` に付記）

接続情報は `os.environ.get("AZURE_SEARCH_ENDPOINT")` / `os.environ.get("AZURE_SEARCH_ADMIN_KEY")`。`.env.example` に 2 変数を追記（値は空。実値は `~/.credentials/` 管理でコミット禁止）。

---

## 3. 中段階の leaf（G 系列）— 新規モジュール `foundry_iq_grounding.py`

### G1: intent テーブル（LLM なしの query 決定）
モジュール定数 `FINDING_INTENTS: dict[str, str]`。`dict.__getitem__` のみで分岐なし:

```python
FINDING_INTENTS = {
    "non_atomic_value_transfer": "race condition non-atomic balance update check-then-act mitigation mutex compare-and-swap",
    "invalid_amount_transfer": "improper input validation negative amount quantity bounds guard",
    "direct_authority_mutation": "broken access control privilege escalation direct role mutation guarded API",
    "no_convergence": "secure design review residual risk defense in depth",
}
```

### G2: retrieve 呼び出し — `retrieve_grounding(finding: str) -> dict`
`POST {endpoint}/knowledgebases/shadow-omega-kb/retrieve?api-version=2026-04-01`、ヘッダ `api-key`。body（確認済みの GA 形式）:

```json
{
  "intents": [{"type": "semantic", "search": "<FINDING_INTENTS[finding]>"}],
  "knowledgeSourceParams": [
    {"knowledgeSourceName": "shadow-omega-security-ks", "kind": "searchIndex"}
  ]
}
```

`urllib.request.urlopen(req, timeout=10)` → `json.loads(resp.read().decode("utf-8"))`。`mcp_server.py` の `_http_post()` と同じ urllib 規約（追加依存ゼロ）。

### G3: 応答の二重 JSON 展開 — `unpack_response(raw: dict) -> list[dict]`
確認済みの応答構造: `raw["response"][0]["content"][0]["text"]` は **JSON 文字列**（`[{"ref_id": "0", "title": ..., "terms": ..., "content": ...}]`）。`json.loads()` で 2 段目を展開。`raw["references"]`（`{type, id, activitySource, docKey, sourceData}`）と `raw["activity"]`（`searchIndex` / `agenticReasoning` entry）も同時に返す。`KeyError` / `json.JSONDecodeError` は G6 の fallback へ送る。

### G4: 三点突合 — `build_citations(chunks, references, corpus_by_id) -> list[dict]`
- `corpus_by_id` = P1 の corpus を `{doc["id"]: doc for doc in corpus}` で索引化
- 各 chunk の `ref_id` と `references[].id` を `str.__eq__` で突合 → `docKey` を得る
- `docKey` で `corpus_by_id` を逆引き → `cwe_id` / `owasp_id` / `source_url` を復元
- citation オブジェクト（fixture は §5）に組み上げ。`excerpt` は `chunk["content"][:280]`
- `provenance` 値は G4 自身では決めず、引数 `provenance: str` として受け取る（G5 が `"foundry_iq_live"`、G6 が `"bundled_snapshot"` を渡す。grader 副次シグナル反映）

### G5: 公開 API — `ground_finding(finding: str) -> dict`
G1→G2→G3→G4 を直列に呼び、`{"provenance": "foundry_iq_live", "knowledge_base": "shadow-omega-kb", "api_version": "2026-04-01", "citations": [...], "retrieval_activity": {...}}` を返す。`retrieval_activity` には activity 配列から `knowledgeSourceName` / `count` / `elapsedMs` を転記（操作の透明性 = 審査の Reliability 軸）。

### G6: fallback — `load_snapshot_grounding(finding: str) -> dict`
発動条件は 3 つのみ（明示列挙・silent fallback 禁止の構造化）:
1. `AZURE_SEARCH_ENDPOINT` / `AZURE_SEARCH_ADMIN_KEY` が未設定
2. `urllib.error.URLError` / `TimeoutError`
3. G3 の展開失敗

`data/foundry_iq_snapshot.json`（P6 `--snapshot` の録画。録画前の暫定版は同スキーマの手書き版で、`"captured_at": null` により録画前と判別可能）を `json.load()` し、G3→G4 と同じ経路で citation 化。`provenance` は `"bundled_snapshot"` に固定。**ラベルなしで live を装うことはコード経路上不可能**（provenance は G5/G6 の各入口で固定代入され、後から書き換える経路がない）。

---

## 4. 後段階の leaf（E 系列）

### E1: certificate 拡張 — `convergence_certificate.py`
`build_convergence_certificate()` の返り値 dict に新キー `knowledge_grounding`（= G5/G6 の返り値そのまま）。schema 文字列を `shadow-omega.convergence-certificate.v2` に更新し、README の certificate 仕様表にも v2 差分を追記。

### E2: evidence_sources への新 entry
既存の typed entry（`source_static_features` / `deterministic_simulation_trace` / `live_backend_parity`）に追加:

```json
{
  "type": "foundry_iq_knowledge_grounding",
  "provenance": "foundry_iq_live",
  "knowledge_base": "shadow-omega-kb",
  "citation_count": 3,
  "cwe_ids": ["CWE-362", "CWE-667"]
}
```

### E3: patch 戦略の接地
`recommended_patch_strategy`（既存: 文字列）を `{"strategy": <既存文字列>, "grounded_in": [<ref_id>...]}` に拡張。`grounded_in` は citations のうち `id` が `patch-` 始まりの文書の ref_id を `str.startswith("patch-")` で選別。後方互換: 旧 v1 消費側（demo fixture）は §7 の受入テストで更新。

### E4: MCP tool 追加 — `mcp_server.py`
FastMCP デコレータで 2 tool 追加（既存 6 tool と同一規約・docstring 付き）:
- `ground_finding(finding: str) -> str`: G5（失敗時 G6）の結果を `json.dumps(result, indent=2)` で返す
- `get_knowledge_provenance() -> str`: 現在の経路（live / snapshot）・KB 名・env 設定状況（**鍵の値は返さない**。設定有無の bool のみ）を返す

既存 `generate_convergence_certificate` / `run_closed_loop_demo` は E1 経由で自動的に grounding を含む。

### E5: 審査員向け公開 — README + 提出 description
- README に「Foundry IQ Integration」節: アーキテクチャ図差分・ゼロ円構成（Z1〜Z5 の引用）・`foundry_iq_provision.py` 手順・provenance の意味
- **KB 自身の MCP endpoint** を記載: `https://<service>.search.windows.net/knowledgebases/shadow-omega-kb/mcp?api-version=2026-04-01`（ヘッダ `api-key`、tool 名 `knowledge_base_retrieve`）→「Shadow-Ω MCP サーバー + Foundry IQ MCP サーバーの二重 MCP 構成」として Creative Apps 要件①（Copilot/MCP）と②（IQ）を同一アーキテクチャで充足
- **description 本文の正本**: 新規ファイル `platform-upload/description-v3.txt`。生成元 = `C:\tmp\t1-innovation-studio-submission.md` ②節コードフェンス内の v2 全文（現在掲載中の 2,952 字版と同一・確認済み）の末尾に「FOUNDRY IQ INTEGRATION」段落（KB 構成・引用付き grounding・provenance 二値・ゼロ円構成）を追記した全文置換テキスト。repo にコミットする
- **更新スクリプト**: `c:/tmp/aleague-desc-v3.mjs` を新規作成。runfile の実体は Playwright MCP の `browser_run_code_unsafe`（ファイル内容 = `page` オブジェクトを操作する JS。`tmp-gmail-agentsleague.mjs` 52〜56 行で確認済み）なので、v3 全文は template literal としてスクリプト内に埋め込む。内容: `await page.goto("https://innovationstudio.microsoft.com/hackathons/Agents-League-Hackathon/project/124260")` → 編集画面の description 欄を `await page.locator(<description textarea セレクタ>).fill(DESCRIPTION_V3)` → Save ボタンを `await page.getByRole("button", {name: "Save"}).click()`。実行 = `node .claude/scripts/tmp-gmail-agentsleague.mjs runfile c:/tmp/aleague-desc-v3.mjs`
- **検証**: 実行後に `snap` サブコマンド（`browser_snapshot`）で「FOUNDRY IQ INTEGRATION」文字列の掲載残存を確認（L11 / RC-2）

---

## 5. 層境界 fixture（原則4: 型 + 実例 1 件）

**前→中境界**（corpus 文書 → index 投入後に retrieve が返す chunk）:

```json
{"ref_id": "0", "title": "CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization", "terms": "race condition, TOCTOU, non-atomic update, check-then-act", "content": "balance の読取と減算が別命令に分かれた transfer は..."}
```

**中→後境界**（citation オブジェクト）:

```json
{
  "ref_id": "0",
  "doc_key": "cwe-362-race-condition",
  "title": "CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization",
  "cwe_id": "CWE-362",
  "owasp_id": "A04:2021",
  "source_url": "https://cwe.mitre.org/data/definitions/362.html",
  "excerpt": "balance の読取と減算が別命令に分かれた transfer は...",
  "provenance": "foundry_iq_live"
}
```

**後段階出力**（certificate v2 の knowledge_grounding 節）:

```json
{
  "provenance": "foundry_iq_live",
  "knowledge_base": "shadow-omega-kb",
  "api_version": "2026-04-01",
  "citations": [{"ref_id": "0", "doc_key": "cwe-362-race-condition", "cwe_id": "CWE-362", "...": "..."}],
  "retrieval_activity": {"knowledgeSourceName": "shadow-omega-security-ks", "count": 3, "elapsedMs": 412}
}
```

---

## 6. 不変量（原則3）

- **I1: finding カバレッジ**: `{4 finding 値}` = `FINDING_INTENTS` のキー集合 = corpus の `finding_tags` 出現値の和集合 = snapshot のキー集合。受入テストで `set.__eq__` により 4 点一致を確認（COUNT DISTINCT 型）
- **I2: citation 整合**: certificate に載る全 `ref_id` ⊆ retrieve 応答 `references[].id` 集合、かつ全 `doc_key` ⊆ corpus の `id` 集合。`set.issubset()` で確認
- **I3: provenance 二値性**: `knowledge_grounding.provenance ∈ {"foundry_iq_live", "bundled_snapshot"}` 以外の値が存在しない（C1 の機械化）

**R1 不成立時（Free tier で semantic configuration 拒否）の代替経路**: I1〜I3 を保ったまま、P2 から `semantic` 節を外し knowledge source を preview API `2026-05-01-preview`（`semanticConfigurationName` 任意）で作成する。preview 利用は README に明記。コスト構造は不変（ゼロ円のまま）。

---

## 7. 受入テスト — `test_foundry_iq_grounding.py`

`unittest` + `unittest.mock.patch("urllib.request.urlopen")`（既存 repo のテスト規約に準拠、pytest 依存なし）:

1. **live 経路**: §5 の生応答 fixture をモックに与え、`ground_finding("non_atomic_value_transfer")` の citations が I2 を満たす
2. **fallback 経路**: `mock.patch.dict(os.environ, {}, clear=True)` で env を空にし、provenance が `"bundled_snapshot"` になる（silent fallback でないことの否定的 assert: live を示す値が混入しない）
3. **I1**: corpus / FINDING_INTENTS / snapshot の 3 集合一致
4. **certificate v2**: `build_convergence_certificate(リスクfixtureコード)` の返り値に `knowledge_grounding` と `foundry_iq_knowledge_grounding` evidence entry が存在し、`demo/fixtures/convergence-certificate.expected.json` を v2 へ更新して全体一致
5. **G3 異常系**: 二重 JSON が壊れた応答で G6 へ移ること

---

## 8. Definition of Deep チェックリスト（原則7・証拠リンク欄）

- [x] 全 leaf が原則5合格（初出 API スパイク済み・live 分は S1 残） → 証拠: `design/foundry-iq-grounding/spikes/`
  - [x] S0（資格情報不要）: `spikes/s0_unpack_response.py` 実行済み（2026-06-12）。出力: `docKey = cwe-362-race-condition` / `activity = 412 ms` — 二重 JSON 展開と ref_id↔references 突合が docs 記載の応答形で成立
  - [ ] S1（**chairman の Azure 無料アカウント作成後**）: Free tier 実機で P2〜P5 + G2 を一巡し、R1（semantic configuration 可否）の白黒を付ける
- [x] 全層境界に fixture → §5 に 3 件記載済み
- [x] depth-lint ヒット 0 件 → 証拠（2026-06-12 実行、E5/G4 改訂後の再実行）:
  ```
  depth-lint: ヒット 0 件 — 合格（魔法の言葉なし）
  ```
- [x] blind grader 全 leaf 2 点 → 証拠: 下記採点表（独立エージェント・leaf 一覧と rubric のみ入力。初回 E5=1点 → 書き直し → 再採点 2 点）
- [x] 不変量宣言 → §6 に I1〜I3 記載済み

### blind grader 採点表（2026-06-12・設計非参加エージェント）

| # | leaf | 点 | grader 推定 API（抜粋） |
|---|------|---|------|
| 1 | P1 corpus JSON | 2 | 手書き JSON 配列（8 キー dict ×12） |
| 2 | P2 index 作成 | 2 | `urllib.request.Request(url, data=..., method="PUT")` |
| 3 | P3 文書投入 | 2 | `urllib.request.urlopen(req, timeout=15)` + mergeOrUpload |
| 4 | P4 knowledge source | 2 | P2 と同型 PUT、searchIndexParameters まで一意 |
| 5 | P5 knowledge base | 2 | P2 と同型 PUT、body 完全指定 |
| 6 | P6 CLI | 2 | `argparse` store_true ×2 / `os.environ.get()` / `json.dump()` |
| 7 | G1 intent テーブル | 2 | モジュールレベル dict リテラル（4 キー固定） |
| 8 | G2 retrieve | 2 | `urllib.request.urlopen(req, timeout=10)` + `json.loads()` |
| 9 | G3 二重 JSON 展開 | 2 | 添字アクセス + `json.loads()`、例外素通し |
| 10 | G4 三点突合 | 2 | dict 内包 + `chunk["content"][:280]` |
| 11 | G5 ground_finding | 2 | G1〜G4 直列 + `type=="searchIndex"` filter |
| 12 | G6 fallback | 2 | `json.load()` + `except (URLError, TimeoutError)` |
| 13 | E1 certificate v2 | 2 | dict 1 キー追加 + schema 文字列置換 |
| 14 | E2 evidence entry | 2 | `list.append()` + set 内包 |
| 15 | E3 patch 接地 | 2 | list 内包 + `str.startswith("patch-")` |
| 16 | E4 MCP tool ×2 | 2 | `@mcp.tool()` + `json.dumps(result, indent=2)` |
| 17 | E5 README + description | 2（書き直し後） | runfile → `browser_run_code_unsafe` / `page.fill()` / `browser_snapshot` |
| 18 | T1 受入テスト | 2 | `unittest.mock.patch("urllib.request.urlopen")` / `patch.dict(os.environ)` |

副次シグナル反映済み: G4 の provenance を引数渡しに明記（grader 注記）。E5 初回 1 点の理由（複製元スクリプト・本文出所が不定）は、runfile 実体 = `browser_run_code_unsafe` の実コード確認と正本 `C:\tmp\t1-innovation-studio-submission.md` ②節の特定で解消。

---

## 9. 変更ファイル一覧

| ファイル | 種別 |
|---|---|
| `t1-shadow-omega-core/data/security_knowledge_corpus.json` | 新規（P1） |
| `t1-shadow-omega-core/data/foundry_iq_snapshot.json` | 新規（P6/G6） |
| `t1-shadow-omega-core/foundry_iq_provision.py` | 新規（P2〜P6） |
| `t1-shadow-omega-core/foundry_iq_grounding.py` | 新規（G1〜G6） |
| `t1-shadow-omega-core/convergence_certificate.py` | 変更（E1〜E3、schema v2） |
| `t1-shadow-omega-core/mcp_server.py` | 変更（E4） |
| `t1-shadow-omega-core/test_foundry_iq_grounding.py` | 新規（§7） |
| `t1-shadow-omega-core/.env.example` | 変更（2 変数追記・値なし） |
| `README.md` / `t1-shadow-omega-core/README.md` | 変更（E5） |
| `demo/fixtures/convergence-certificate.expected.json` | 変更（v2） |
