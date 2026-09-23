# 2026-09-23: モデル更新に合わせたCLIと利用入口の更新

対象は通常配布・CLI互換性・今後の要求設定。封印済み実験のactor、image、model catalog、得点は変更しない。
検証はCLI metadata、疑似provider、非agentのcontainer testで行った。実モデルの生成・比較は実行していない。

## 配布とホスト

| CLI | 旧stable | 新stable | この作業後のホスト |
| --- | --- | --- | --- |
| Codex | 0.153.0 | 0.156.0 | 0.156.0（0.153.4から更新） |
| Claude Code | 2.1.220 | 2.1.280 | 2.1.280 |
| Grok Build | 1.0.3 | 1.0.41 | 1.0.41 |

Codex/Claudeのversionはnpm registry、Grokは公式stable endpointから取得して固定した。
Grokの公式Linux x86_64 artifactのSHA-256は
`9ce03ed23e16ea01072b4496263d6213a27899e1e3e107f008d36edf82e70407`。
image buildでも同じhashを照合した。Node、Gemini、Featureのversionは今回の対象外。
新しいproduction依存はない。

edge起動はホストのCLIを同期するため、imageだけ更新しても古いホスト版へ戻ることがある。
今回ホストのCodexも更新した。Claudeは要件を満たし、Grokも1.0.41と認証済みを確認した。
稼働中containerの再作成はしていない。新imageの利用には通常のRebuild Containerが必要。
既存のstable image tagは上書きせず、次の検証用tagを作成した。

| image | ID |
| --- | --- |
| `devcontainer-model-refresh:20260923` | `sha256:cc855f9ad8968bf81f59d7e765e12760b9ef63c0f6d3efa264ef95f5d2fb47e2` |
| `devcontainer-model-refresh-frozen:20260923` | `sha256:e09fa5893855dc4b7ea8142b9e0468913808b8861b4712256715a8c2c08acb7e` |

## モデルの利用方針

| 用途 | 指定 | 確認と限界 |
| --- | --- | --- |
| Codexの日常・複雑なコード開発 | `gpt-6-sol` | 更新後の`codex debug models`で掲載とeffort/multi-agent metadataを確認。生成成功は未検証 |
| 難題のstrong solo候補 | `gpt-6-astra` | Solへ自動置換しない。新CLIでの実験能力・費用回収は新protocolごとに検証 |
| Claude | `claude-opus-5-5` | Claude Code 2.1.280以上が公式要件。`opus`はprovider/CLIによるaliasで、固定実験には完全IDを使う |
| Grok | `grok-4.7` | 認証後の`grok --no-auto-update models`で既定として掲載。生成成功とは別 |
| Grokの高速variant | `grok-4.7-build-fast` | 同一覧に掲載。価格・speed条件が変わるので実験では通常版と区別 |

通常のnative agent templateはモデル継承を維持する。全roleへ新モデルを直書きしない。
旧`codex-second-agent`の既定値だけは`gpt-5.5`から`gpt-6-sol`へ更新した。
`CODEX_SA_MODEL`の上書きと既存session互換は維持する。旧モデルでsessionを継続したい場合は明示指定する。
Claudeの旧wrapperは`opus`を維持し、READMEでaliasと固定IDの違いを説明した。

```bash
codex --model gpt-6-sol
claude --model claude-opus-5-5
grok --model grok-4.7 --reasoning-effort high
```

これらは利用例であり、一括したlive実験の開始コマンドではない。
通常コマンドのapproval/sandboxと、明示したtrusted入口の区別は維持する。

## effortと測定

Grok 4.7の文書化されたeffortは`low / medium / high / xhigh`。
durationの計画・batch読込み・直接実行で同じmodel別guardを使い、`max`は認証や起動の前に拒否する。
Grok 4.6等の過去の`max`試行は、当時の要求・受理/拒否・観測としてそのまま読める。
provider全体の古い実験ladderを新モデルへ無条件に適用しない。

Codex CLIの`ultra`は単独のreasoning量だけではなく、自動delegationを伴う設定。
APIのeffort一覧とCLIを混ぜず、solo条件ではtool公開とmodel metadataの両方を確認する。
今回観測したCodex CLI catalogのcontext_windowは272000だった。APIのmodel pageの上限を
CLIの実効値として上書きしない。要求値・掲載値・適用値は区別して残す。

新モデルに対応する測定がなければ`unmeasured`。全caseの再実行は今回行わない。

## 検証

- durationのfocused 35試験、関連回帰172試験が通過。4.7のlow受理、maxの早期拒否、旧max試行の読込みを確認。
- agent contract validator、配布skill validatorが通過。
- devcontainer lock、並列build隔離、stable/edge同期、safe/trusted wrapper、指定shell構文checkが通過。
- second-agentの両backend回帰と実CLI flag contractが通過。
- plain imageのbuild、Mira hook/永続観測、project導入・更新・中断復旧・rollbackが通過。
- plain imageでagentctl独立checkの42試験が通過。
- official Dev Container CLIのfrozen build、配布確認、独立check42試験、DinD起動とdoctorが通過。

ログは今回の環境の`/tmp/devcontainer-model-refresh-*.log`。これは一時logで、過去の固定実験記録の代わりではない。
新CLIによる実モデルの長時間協働・全usage完全性は未検証。旧actorはCLI 0.153.0/Astra/highを要求しており、
新しい比較へ接続する場合は別版で能力・終了・回収を検証する。

撤去/rollbackは、この更新のDockerfile pin・既定値・guardを戻して前のimageを使う。
ホストCodexのrollbackが必要なら`npm install -g @openai/codex@0.153.4`。
過去の実験imageと原記録は保持している。

## 公式資料（2026-09-23確認）

- [Codexでのモデル選択](https://learn.chatgpt.com/docs/models)
- [GPT-6 Sol API仕様](https://developers.openai.com/api/docs/models/gpt-6-sol)
- [Claude Code model設定と最低CLI版](https://code.claude.com/docs/en/model-config)
- [Grok 4.7・effort・Fastの範囲](https://docs.x.ai/developers/grok-4-7)
- [Grok Build CLI](https://docs.x.ai/build/cli/reference)
