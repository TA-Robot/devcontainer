# 05. Repository capabilities and roadmap

Reviewer: independent Grok 4.6  
Date: 2026-08-26  
Status: independent review. Not repository policy.

【結論】先に用意すべきなのは新しいrunnerでも12 modeのschemaでもなく、(1) 未検証整数を高権限面から外すこと、(2) mechanism-firstの短いplan、(3) transcript無しの観測、(4) 既存job fabric上の比較手順である。schedulerは手動sentinelが価値を出してからでよい。

## 所有

| 層 | 持つ | 持たない |
|---|---|---|
| このrepo | lane/role/task-result/worktree/collect、事故低減、短いcollaboration plan、content-free観測、将来のfinite trigger | debate意味、winner、transcript、private reasoning、token正規化、isolationの偽主張 |
| provider-native | interactive subagent UX、same-provider messaging、model/reasoning、native permission、provider usage表示 | 横断durable workflow、merge/push、schedule自己変更 |
| primary/human | 選択、synthesis、integration、schedule enable、昇格 | auto merge |
| Mira | sanitized lifecycle表示 | steering、approval、scheduler authority、本文 |

task/result schema v1にcollaboration fieldを混ぜない。別contractすらC2で使われたfield以外は作らない。Grok `--max-turns 64` / memory無効 / nested disableはwriteのownership guardであり、playbookのround上限に転用しない。interactive Lane Rまで同じ制約を主張しない。

## 基盤が用意するもの

今すぐ（docs only）: `AGENTS.md` / template / persona / playbook / collaboration-modelから「通常2/最大3 round」「通常2 variants」「3 agent典型」「blind普遍default」を外す。残すのはmechanism-first、single-writer、scheduler未実装、accidental-writeとsecurityの区別。12名はalias表として残してよい。rollbackはgit revert。plan templateへmechanism、binding constraint、independence level、human review minutes、stop_reasonを足し、数値枠はrationale無しでは埋め済みにしない。advice resultとclaim ledgerとvariant checklistはMarkdown例でよい。winner自動判定は書かない。

C2: 1 run 1行のcontent-free log（topology、N_extra実績、rounds_opened、independence、lane、provider id、elapsed、human minutes、採否、mechanism_fired、decisive yes/no、rework、stop_reason）。本文/path/promptなし。job correctnessに接続しない。捨てれば消える。

あると良いが必須ではない: 起動前cost card（N_extra、human minutes、capacity、worktree数の概算）、既存create/run/validate/collectを並べるvariant手順。新しいorchestratorは書かない。

Scheduler（E6通過後）: disabled-by-default store、next-run preview、manual dry-run、read-only sentinel一件でのdedupe/overlap/budget/backoff/failure+usefulness circuit、fault injection。その後opt-in candidate commit。auto integrationなし。Miraはcontent-free表示のみ。hard guardを満たさないschedulerは追加しない。削除手順: disable、未完cancel、runtimeを外しjob fabricは残す。

【仮説】安いcost simulatorは60 pattern追加より意思決定に効くことがある。E1が「日常はsolo」を示したらsimulatorより数値除去の方が効く。

Nativeへ残す: 対話UX、peer messaging、model選択、approval UI、provider usage、interactive resume（clean retryとは別）。基盤が重ねてよいのはcapability probe、broker commit、scope再計算、content-free envelope。

## 過剰・欠落・誤分類

過剰: 60候補の運用必須化、12 modeのC0昇格、未検証整数の高権限コピー、blind普遍default、「1 phase 3 mode」の整数、routing 8段の決定木化、example YAML数値のarchitecture化、高コストcomposition例の標準化。

欠落: human minutesをroutingに入れる、binding constraint、independence選択、evidence-deltaを固定roundより前に置く、N_extraをindependent unitから導く、solo baseline、usefulness/attention、数値のinvalidation、Lane I無しでのuntrusted禁止、Grok durable pathでpeerが使えない事実。

誤分類: pipelineをmode、sentinel/eventをinteraction topology、deliberationをround数本質の別mode、capacity defaultを推奨N、max-turnsをround政策、worktreeをisolation、speedとthroughputの揺れ。acceptedに値するのは直交軸（lane/role/mode/lifecycle/authority）だけである。

残すべき核: 直交軸、solo明示、why_multi_agent、single-writer、transcript非保存、scheduler未実装を仮定しない、finite job、auto mergeしない。削る核: 未検証整数、12 mode必須化、blind普遍default。

採らない提案: collaboration graphをagentctlへ入れる、auto merge、Lane I完成前のuntrusted定期実行。rollbackが重い。

## Roadmap

現行C0が文書先行しすぎた。修正順:

- R0 数値とblind普遍defaultを高権限面から除去。docs only。
- R1 plan templateにmechanism/constraint/human minutes。
- R2 nativeのままE1–E5とcontent-free log。このrepoのbounded taskに閉じ、サンプルアプリは作らない。
- R3 埋まったfieldだけoptional規約。v1 schemaは触らない。
- R4 E6が正ならread-only scheduler pilot + fault injection。
- R5 opt-in candidate。auto integrationなし。

失敗時: R0はrevert、R2はsolo-firstのまま、R4は手動に戻しC5を始めない。riskは具体例不足、標本の過剰一般化、観測helperの本文吸い、legacy session世界の復活、Companionのauthority化。

最小pilot: 小さい修正のsolo対照1行、同規模の独立reviewer一人（追加roundなし）、真に曖昧なときだけ観点の違うadvice、各runでhuman minutesとmechanism_firedとstop_reason。定期は人が手動read。含めない: 人数目標、固定round消化、3 provider同時、auto merge、Lane I主張、transcript収集、brokerでのnested再有効化。合格はMustまたはreworkで勝ちhuman minutes込み非負。不合格なら縮小しschedulerへ進まない。

5文書で棄却する全球固定: deliberation通常2/最大3を品質政策にすること、variants通常2をdefaultにすること、3 agent典型、panel blind普遍default、1 phase 3 modeの整数、YAMLの900秒/circuit 3/backoff/1日1回を全球値にすること。安全側として残してよいが品質値ではないもの: overlap forbid、同一schedule concurrent 1、disabled-by-default、定期のattempts starting 1、catch-up最新一件、isolated capacity 0、Grok writeのnested disable。

【結論】強みはlaneとjobとsingle-writerにある。collaboration層で今壊しているのは、測る前に儀式の整数を凍結したことである。直すのはruntime追加より、権威ある文書の降格と、人間のreview込みの小さな実験である。tooling量とagent数を成果にしない。

