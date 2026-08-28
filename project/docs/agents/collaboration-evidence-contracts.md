# Collaboration evidence contracts

## Purpose

projectごとに異なるmulti-agent設計を後から検証できるよう、実行前の判断と実行後の観測を分離します。人間へのform入力、固定agent数、固定往復数、automatic routingは要求しません。

```text
primary decision packet
  -> selected candidateのbounded projectionをtaskへ添付
  -> agentctlがIDをopaque化してMira episodeへ相関
  -> read-only aggregate report
  -> primaryがoutcome packetとplanning priorを更新
```

## Contracts

- `.agent/schemas/collaboration-decision.schema.json`: 実行前。soloを含む候補、task fingerprint、期待mechanism、binding constraint、prediction、stop condition、limitの役割、不確実性を保持する。
- `.agent/schemas/task.schema.json#collaboration`: 選択済み候補のcontent-free projection。任意fieldなので既存taskはそのまま有効。
- `.agent/schemas/collaboration-outcome.schema.json`: 実行後。time、topology、quality / coordination proxy、coverage、停止理由、仮説のlearning deltaを保持する。
- `$MIRA_COMPANION_EPISODE_DIR/collaboration-episodes.json`: hookが自動生成するbounded observation。decision / outcome packetの代替ではない。

examplesは`.agent/examples/collaboration-*.example.json`にあります。

## Decision workflow

1. 現在のtask fingerprintとbinding constraintを書く。
2. solo alternativeを必ず比較可能な候補として残す。他の候補数はexpected mechanismと識別可能な差から導く。
3. 各候補へrelation、lifecycle、participant basis、independence policy、prediction evidence、stop conditionを付ける。
4. 一つを選び、primaryがdecision packetを保存する。保存場所とretentionはproject policyで決め、secretやprivate reasoningを入れない。
5. packet fileの実byte列をSHA-256で固定する。

```bash
python3 scripts/validate-agent-contracts.py \
  --schema project/.agent/schemas/collaboration-decision.schema.json \
  --instance path/to/decision.json
sha256sum path/to/decision.json
```

6. 選択したjobのtaskへ次だけを添付する。

```json
{
  "collaboration": {
    "plan_id": "project-local-plan-id",
    "candidate_id": "selected-candidate-id",
    "decision_digest": "sha256:<64 lowercase hex>",
    "relation": "consult",
    "lifecycle": "bounded-exchange",
    "expected_mechanisms": ["coverage", "error-decorrelation"],
    "binding_constraint": "evaluator",
    "annotation_source": "primary-plan"
  }
}
```

task projectionはallowlist済みcategoryだけです。詳細なrationale、objective、prompt、path、agentの発言は入れません。project固有の細分類が必要ならpacket側へ保持し、projectionでは`project-specific`を使います。

## Automatic correlation

`agentctl`はstored taskを再読込し、schema-bounded projectionだけをMira bridgeへ送ります。

- plan IDはplan単位のopaque keyへhashする。
- candidate IDはplanとの組でopaque keyへhashする。
- decision digestはimmutable packetとの結び付けとして保持する。
- relation、lifecycle、mechanism、constraintはallowlist外ならannotation全体を拒否する。
- task objective、path、result本文、raw job / attempt IDはepisodeへ送らない。
- bridge failureはjob correctness pathへ影響しない。

projectionがないdirect provider turnや旧taskは、semanticsを`unknown`、correlationを`available: false`として記録します。topologyからrelationを推測しません。

## Read-only review

通常はSkillを使います。

```bash
python3 .codex/skills/review-collaboration-evidence/scripts/report_evidence.py \
  --format markdown --max-groups 20 --max-output-bytes 32768
```

wrapperは現在のworkspace keyをprocess内で計算してfilterします。`--all-workspaces`は明示的な横断auditだけに使います。基盤CLIを直接使う場合は次です。

```bash
report-agent-collaboration-evidence \
  --format json --max-episodes 512 --max-groups 100
```

reportはepisode bodyやopaque IDを出さず、exact semantic groupごとの件数、observed durationのmin / median / max、terminal outcome、worker / review / rework proxy、coverageだけを返します。上限はcontext / storage safety capであり、推奨sample数ではありません。

## Outcome and learning

primaryはartifactとacceptance checksを確認してからoutcome packetを作ります。自動観測できない値は`null`または`unknown`にし、terminal successからqualityを補完しません。

- `mechanism_result`: 期待mechanismがsupported / contradicted / inconclusive / unmeasuredのどれか。
- `prediction_result`: 実行前predictionを観測で判定できたか。
- `routing_prior`: このprojectの次回仮説をstrengthen / weaken / unchanged / insufficient-evidenceのどれにするか。

一観測や異質なgroupからglobal defaultを作りません。task fingerprint、fixture、execution surface、oracle、risk、coverageが揃わない比較はdescriptive evidenceとして残します。

## Deliberate boundary

現在提供するのはdecision semantics、safe correlation、bounded reportです。次はまだ行いません。

- provider / model / effort / relationの自動ranking
- recommendationや自動dispatch
- recurring schedulerやquota消費
- transcript、private reasoning、task contentの収集
- merge、push、PR、releaseとの自動接続

これらはproject-local evidenceで必要性、evaluator、cost、permission、kill pathが確認された後に別milestoneとして判断します。
