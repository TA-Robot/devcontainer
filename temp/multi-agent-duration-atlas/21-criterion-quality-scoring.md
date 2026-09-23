# Criterion-level quality scoring

実装日: 2026-08-27

Status: binary quality gateを維持したまま、model/provider選定に使えるcriterion-level scoreをfixture、isolated evaluator、run diagnostics、raw reporterへ追加。

## Why

`quality_pass=false`だけでは、全要件を外したrunと、境界条件を一つだけ外したrunを区別できません。時間とbinary successだけを並べると、速いがほぼ不正解なmodelと、惜しいmodelを同じfailureへ潰します。

一方、単一の百分率を人間的な品質へ読み替えるのも危険です。今回はversioned fixture contractに列挙した**全必須criterionの機械判定率**としてだけ扱います。

## S case v2 rubric

`F04-S-PY-001`は次の5 checkへ分けました。

| Scope | Check ID | 判定対象 |
| --- | --- | --- |
| public | `workspace-1` | agent-visible unit test bundle |
| hidden | `hidden-separator-normalization` | separator runとunsupported文字 |
| hidden | `hidden-ascii-filtering` | ASCII-only contract |
| hidden | `hidden-empty-result` | normalized empty resultのreject |
| hidden | `hidden-length-bound` | 32文字上限 |

binary `online_acceptance=pass`は従来どおり5/5だけです。選定材料として、次を追加で残します。

- passed / total
- ratio
- public passed / total
- hidden passed / total
- failed check IDs
- resolution (`criterion`または`aggregate-check`)

全criterionはrequiredで、重みは等価です。これはutility scoreやmodel総合点ではありません。

## Existing three runs

以前のartifactは意図どおり破棄済みなので、hidden bundleの内部を再採点できません。既存runは次の粗い表示になります。

```text
r02 terra low   1/2 (50.0%) aggregate  failed=f04-s-python-hidden-v1
r03 terra high  1/2 (50.0%) aggregate  failed=f04-s-python-hidden-v1
r04 sol low     1/2 (50.0%) aggregate  failed=f04-s-python-hidden-v1
```

この50%は「仕様の半分を満たした」という意味ではありません。public bundle 1件がpass、複数criterionを内包したhidden bundle 1件がfail、という**aggregate check resolution**です。hidden内部で何項目通ったかはunknownです。

## New run behavior

新fixtureはhidden test methodを個別container invocationで実行します。public check processにはhidden evaluatorをmountせず、hidden check時だけread-only mountします。各checkはnetwork none、read-only rootfs/workspace、credentialなしです。

新runのreport例:

```text
SCORE                  FAILED CRITERIA
4/5 (80.0%) hidden=3/4 hidden-empty-result
```

これならbinary failを維持しつつ、「empty境界だけ落とした」ことをcontent-freeに比較できます。raw prompt、回答、patch、test stdout/stderrは保存しません。

## Calibration

実Dockerでv2 S fixtureを検証しました。

| Artifact | Score | Failed criteria |
| --- | ---: | --- |
| seeded initial | 0/5、hidden 0/4 | 全5 check |
| private known-good | 5/5、hidden 4/4 | なし |

M/L fixtureもhidden test method単位のtargetをcatalogへ持ち、同じscore contractを使います。

## Selection use

model/provider比較では最低限、次を隣接表示します。

- terminal/user-result time
- binary quality pass/fail
- criterion scoreとresolution
- failed criterion IDs
- requested model/effortとidentity/application confidence
- CLI/image/sandbox surface

異なるrubric revision、`aggregate-check`と`criterion`、S/M/L、別caseのratioを一つの平均へpoolしません。criterion scoreが高いことは選定材料ですが、project固有のrisk weightingを自動決定しません。
