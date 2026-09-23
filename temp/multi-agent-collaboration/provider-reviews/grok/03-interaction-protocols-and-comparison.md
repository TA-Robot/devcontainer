# 03. Interaction protocols and comparison

Reviewer: independent Grok 4.6  
Date: 2026-08-26  
Status: independent review. Not repository policy.

【結論】orchestratorが選ぶのは12 mode名ではなく、mechanismを最安で出す topology + independence level + stop rule である。予定roundは成功条件ではなくcost capにすぎない。delegation不許可なら同じ枠を一人の逐次作業へ縮退する。

## Topology

運用者向けは6つ。12名はcatalog alias。

| topology | alias | いつ使う |
|---|---|---|
| solo | solo | whyが書けない、分割が制約に負ける |
| parallel | dispatch, fanout, pipeline | shardが切れる、またはstage contractが安定 |
| advice | panel等 | 正解が一意でない。実装前 |
| review | critique, maker-checker, red-team, deliberation | 初案/実装があり誤りコストが高い |
| variants | bake-off系 | 安価に作れ事前rubricで測れる |
| recurring | sentinel, event-triggered | 同じbounded問いが時間/eventで再発。runtime確認後 |

【結論】`pipeline` はmodeではなく逐次job graph。`sentinel` / `event-triggered` はlifecycle/trigger。`deliberation` は独立modeに固定せず、reviewにevidence-delta付き追加roundを許した状態である。一つのphaseで複数mechanismを同時回収しない。必要ならentry/exit付きstageに分ける。現行「3 mode以上積むな」の整数は未検証。禁止理由は過負荷であり、3という数ではない。

使い分けの短縮禁止: dispatchの丸投げとworktree無しwrite、overlap fanout、人数先行のadvice、無期限critique、同じsessionのself-checkを独立と呼ぶこと、許可範囲外red-team、後付けrubricと自動hybrid、常駐sessionと無人merge。

【仮説】ambiguous architectureに毎回 advice→critique→variants を積むと小さい判断まで固定費を払う。Must増が観測されない領域はsoloへ戻す。

## Independence（blindはdefaultではない）

| level | 向くとき |
|---|---|
| isolated-blind | 見積り・選択肢列挙。anchoringが主失敗 |
| partitioned-context | 観点が別の証拠源を見るcoverage |
| shared-context | debugや既知artifactの深度。独立性は主張できない |
| sequential-handoff | pipeline / critique / maker-checker |

【結論】adviceでanchoringが主失敗ならblindを選ぶ。探索コストが主失敗ならpartitioned。すでに共有すべきartifactがあるreviewはblind panelではない。一致性はconfidenceの根拠にしない。比較するのはevidence、assumption、constraint、disconfirming test。primary推奨はadviceのfirst roundに出さず、reviewでは対象として出す。二つを同時にやらない。

## Direct vs primary-mediated

事実: agentctlはconversation graphを持たず持つべきでもない。Grok durable writeはnested subagent無効でjob内peerは使えない。cross-provider対話はnativeに乗らない。interactive Lane Rのsame-provider messagingはprovider UXに残る。

【結論】横断providerとLane Wの比較可能な協働はprimary-mediatedが実装可能な標準。peerは観測と権限を満たすときの最適化。

Trade-off: mediatedはstopと権限が見え、primaryがbottleneck。peerはtokenが安い可能性（未検証）があるが、言い換えloop・nested spawn・permission継承・再現不能が起きやすい。peerを使うならfacilitator、topic、messageまたはwall-clockのcost cap、spawn/write/permission変更禁止、interrupt、成果はclaim ledger。transcriptを次roundやcontrol planeへ複製しない。

渡すもの: shared facts、open claim、disagreement、新しい質問、path/commandへのpointer、残budget。渡さないもの: 全文transcript、private reasoning、「全員一致せよ」。戻りはrecommendation / evidence / assumptions / alternatives / risks / unknowns / confidence / disconfirming test。複数roundはclaim IDと status（open/accepted/rejected/test-needed）。status変化が無い応答は長くても無価値として止める。

## Termination

停止はOR。1) acceptance 2) decisive evidence/test 3) evidence-delta zero 4) binding constraint（human minutes含む） 5) user境界 6) 残利益を調整コストが超える 7) safety/scope 8) recurringの無益（新規drift無し）。予定回数到達は最後の安全網であり成功ではない。synthesisはtopology実況ではなく決定、決定的evidence、disagreement、棄却理由、残risk、stop_reason。agent数とtokenは成果に書かない。

Bias制御: adviceでのanchoring回避、author/providerを品質としない、多数決しない、disconfirming testを先に書く、rubric事後変更でその比較を無効化、rubber-stamp禁止、差が消えたsteelmanは差が無かったので続けない。variantsの途中diff共有は原則禁止。

## 公正で安いvariant比較

共通化: full base SHA、allowed/forbidden paths、acceptanceとfixture、事前rubric（correctness, safety, scope, maintainability, performance, risk, migration, human review）、resource/deadlineの上限、比較ownerはprimary。`job collect` はwinnerを決めない。

独立: job/branch/worktree、探索過程、戦略そのもの（書き味差は独立単位ではない）、必要なときだけのprovider、evaluator。

してはいけない: 案ごとに採点基準を変える、correctness不合格を性能で救済、全案を本番品質まで育てる、hybridを未検証で安全とみなす、Lane I無しでuntrusted isolationを主張する。

安くする: 文書上のadviceで非支配戦略だけ残し、測定でしか解けない残差だけ実装する。correctness gateを先に通す。hybridは新しいintegration task。追加実装のdefaultは0。比較する場合の最小は独立戦略が複数あるときだけであり、「通常2 / 例外3」を固定しない。

critiqueはclaim反証、maker-checkerはMustの再検証、red-teamは許可範囲のexploit evidence。red-teamをホスト資格情報や外側ネットワークへ広げない。privileged containerはsecurity boundaryではない。synthesis/winner/外部副作用はprimary所有。多数決は相関の高い票を水増しする。

unknown: claim ledgerの早期停止、小さなteamでのblinding実効、interactive Grok subagentがLane Rで安く同じMustを出すか。出てもwrite pathへpeerを持ち込まない。

