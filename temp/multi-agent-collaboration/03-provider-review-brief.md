# Independent provider review brief

Date: 2026-08-26

## Assignment

このrepositoryは、Codex / Claude / Grokのnative agentと`agentctl` execution fabricを使い、devcontainer上で高速かつ安定したmulti-agent developmentを実現しようとしています。

現状はread / write / isolated lane、role、job単位worktree、structured result、single-writer integrationを持ちます。さらに、parallel dispatchだけでなく、独立した意見収集、agent間の反復対話、複数案の同時実装と比較、maker-checker、red-team、定期・event駆動agentを含むcollaboration modelを検討しています。

ただし、現在の文書には次のpremature assumptionがあります。

- deliberationを「通常2 round、最大3 round」とする。
- variant implementationを「通常2案」とする。
- 説明例で「3 agentへ聞く」を典型として扱う。
- blind first round等を、project contextによらないdefaultとして扱う箇所がある。

これらはまだ実証されていません。projectの目的、期間、利用可能な人間のreview時間、provider / model、task coupling、失敗コスト、評価可能性、quota / credit、tooling maturityにより適切な人数、round、interaction topology、automation levelは変わる可能性があります。

既存案を擁護するのではなく、**ゼロベースで反証・再設計**してください。

## Questions

1. Multi-agent collaborationは、どんな因果mechanismによってsolo agentより価値を生むか。価値が生まれない条件は何か。
2. task / projectごとに、agent数、provider構成、round数、interaction topology、duration、budgetをどう選び、どう学習・変更すべきか。
3. orchestratorは、dispatch、independent advice、dialogue、parallel variants、adversarial review、recurring agents等をどう使い分けるべきか。
4. agent同士の直接対話とprimary-mediated dialogueには、どんなtrade-offがあるか。固定round以外にどんなtermination ruleが必要か。
5. parallel implementationを公正かつ安価に比較するために、何を共通化し、何を独立させるべきか。
6. recurring / scheduled / event-driven agentを、runaway usage、duplicate work、stale context、alert fatigue、unauthorized writeからどう守るか。
7. このrepositoryが事前に用意すべきtool / contract / template / telemetry / simulatorは何か。逆に、provider-native layerへ残すべきものは何か。
8. 実装前に何をexperimentし、どんなmetric / evidenceで有効性を判断すべきか。
9. projectごとの試行錯誤を可能にしつつ、危険な自由度だけをhard guardにするにはどうするか。
10. 現在の`docs/agents/collaboration-model.md`、`project/docs/agents/collaboration-playbook.md`、`temp/multi-agent-collaboration/`のどこが過剰、欠落、誤分類か。

## Required output

指定されたprovider専用directoryへ、次の5文書をMarkdownで作成してください。

1. `01-principles-and-value-mechanisms.md`
   - multi-agentが価値を生むmechanism
   - soloが勝つ条件
   - assumptionsとanti-patterns
2. `02-adaptive-selection-and-experimentation.md`
   - project / taskごとのadaptive selection
   - agent数、round数、duration、budgetを固定しない方法
   - experiment design、metrics、learning loop
3. `03-interaction-protocols-and-comparison.md`
   - dispatch、advice、dialogue、debate、variants、maker-checker等のtopology
   - termination、synthesis、comparison、bias control
4. `04-recurring-agents-and-governance.md`
   - scheduled / event-driven / long-horizon patterns
   - quota、overlap、dedupe、backoff、circuit、permission、audit
5. `05-repository-capabilities-and-roadmap.md`
   - このrepositoryが事前に提供すべき具体的tooling
   - native providerへ残すもの
   - staged roadmap、dependency、risk、rollback、最小pilot

各文書で次を守ってください。

- 結論と仮説を区別する。
- 固定値を提案する場合、根拠、適用範囲、測定による更新方法を示す。
- agent数を品質の代理指標にしない。
- token / credit / quotaだけでなく、人間のreviewとintegration costも扱う。
- provider transcriptやprivate reasoningの保存を前提にしない。
- security boundaryとaccidental-write boundaryを区別する。
- open-ended autonomous improvementやauto merge / pushを安易に推奨しない。
- 現行architectureと異なる提案も許可するが、migrationと削除可能性を示す。
- 重要な反対意見、unknown、失敗条件を隠さない。
- 互いのprovider review outputは読まず、独立に作業する。

## Repository context to inspect

- `AGENTS.md`
- `AGENTS_TEMPLATE.md`
- `docs/architecture.md`
- `docs/adr/0001-native-first-multi-agent-execution.md`
- `docs/agents/collaboration-model.md`
- `docs/agents/implementation-status.md`
- `docs/agentctl.md`
- `docs/mira/persona.md`
- `project/AGENTS.md`
- `project/.agent/`
- `project/docs/agents/collaboration-playbook.md`
- `project/docs/agents/runbook.md`
- `temp/multi-agent-collaboration/01-pattern-catalog.md`
- `temp/multi-agent-collaboration/02-operating-model.md`

## Scope and stop

- 指定された5文書以外を変更しない。
- source code、schema、existing docs、Git stateを変更しない。
- nested agentをspawnしない。
- 5文書が揃い、相互参照と主張が整合したら終了する。
- 認証、tool、情報不足で完遂できない場合は、作成済み文書を保持し、最後の応答でblockerを明示する。
