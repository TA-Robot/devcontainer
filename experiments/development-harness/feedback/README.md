# 公開検証と修正の実行 contract v1

P1の実装。両条件へ同じ公開要求・チェック・選択手順を渡し、自己検証するAと、提出後に
公開検査の結果を自動返却するBを有限の予算で実行する。実モデルでの効果は未測定。
次の実験課題・評価器・予算・実行順の固定はP2で行う。既存の小課題は校正専用。

## 両条件に渡すもの

| 項目 | A: `control` / `self` | B: `improved` / `feedback` |
| --- | --- | --- |
| 要求・公開check・選択表 | 同じphaseまで公開 | 同じphaseまで公開 |
| 自主的な検証・修正 | 予算内で自由 | 予算内で自由 |
| model・effort・CLI・image・起動設定 | 共通manifest・同一性確認 | 同左 |
| 提出後の公開検査 | 自動実行しない | 登録済みの検査を実行 |
| 公開検査失敗後 | session内で自ら検証・修正できる | 残予算と修正回数上限を満たすと、新しいsessionへ公開出力を返す |
| 隠された最終検査 | 両条件の開発終了後 | 同左。結果を開発へ返さない |

Aへも公開検査のsource、argv、所要時間上限、必須選択表を提示する。Aの検証や修正を制限して
差を作らない。Bが自主検証を重複したり、新sessionでcontextを失ったりする費用も介入の一部。
効果の仮説は未実証で、疑似providerの修正成功を実開発での改善量に読み替えない。

## 公開checkの登録と選択

`public_checks.py`がsource SHA-256と固定entrypointを検証する。機械が実行できるargvは
`python3 /public-checks/<id>.py`と登録済みのliteral引数だけ。開発者の応答からcommandを生成しない。
script自体は信頼された課題側のコードで、その安全性をPythonという言語だけで保証しない。

| tier | 公開・選択規則 | 用途 |
| --- | --- | --- |
| `capability` | phase 1で公開し、どちらの開発者より先にも両環境で実行 | 必要な検証が起動できる証拠。model要求なし |
| `focused` | 指定phase以降に公開。事前の選択表で選ぶ | 変更箇所に対応する短い検査 |
| `required` | 指定phase以降、全ての提出時選択表に必須 | 公開した要求の退行・受入検査 |

`phase_check_ids`を全phase分固定し、未公開・不明なIDや必須検査の省略を拒否する。
配布対象の全検査はP2の課題対応表で確定する。既存checkの入口は次のとおり。
これはscope選択の棚卸しであり、次の課題で省略可能な検査を確定した表ではない。

| 変更scope | focused候補 | 必須確認の正本 |
| --- | --- | --- |
| job状態・依存・復旧・収集 | `scripts/test-agentctl-jobs.py`の該当case | `AGENTS.md`のagentctl/job fabric suiteとdoctor |
| 契約・native template | `scripts/test-agent-contracts.py` | contract validatorとtemplate lifecycleの該当suite |
| template導入・更新・復旧 | `scripts/test-manage-agent-project.py` | lifecycle suite。配布変更時は実imageのcontainer suiteも必要 |
| Docker配布・CLI起動 | AI CLI wrapper/syncの該当suite | `AGENTS.md`のdevcontainer suite、buildとimage内確認 |

課題側scriptは固定の検査を呼び、bytecode/cache/reportは一時領域へ出す。検査がsourceを変更したら
成功にしない。外部検査に修正を混ぜない。検査後はGit HEAD・index差分・file bytes/mode・directory・
symlinkの同一性を照合する。Git内部の全metadataの完全性を証明する仕組みではない。

公開用directoryは条件別の専用read-only bind mount `/public-checks`へ接続する。
phaseごとにscriptと`checks.json`を公開し、将来の名前・source・選択表を先に置かない。
外部入力やcontainer imageに隠されたoracleや将来要求を含めないことは、P2の入力監査にも必要。

## 同じ環境で検証できること

開発と自動検査は、明示したCodexのnamed permission profile `harness-public`を使う。
`:workspace`を継承し、`network_access`を共通指定、local bindingを有効化する。
検査は`codex sandbox -P harness-public --include-managed-config`を通し、開発は同じprofileを
`default_permissions`に設定する。通常利用者の既定設定は変更しない。
両方ともdangerous-default wrapperを無効化し、自動検査には認証を必要としない独立したconfig homeを使う。

seal時に同じimage digest、clean source、異なる専用container、起動設定・環境変数・mount属性を照合する。
追加入力はread-only bindだけで、内容のhashも揃える。初期のwritable layerに差分があれば拒否する。
既存のcacheを使うなら固定したread-only入力にする。seal後、起動前にも環境を再照合する。
これはホスト負荷や順序によるcacheの温まり方まで同一にする証明ではない。

両方の能力検査が通るまで開発sessionを起動しない。実Docker校正はネットワークなしの専用containerで、
疑似providerと実Codex sandboxを使用した。sandboxの名前空間作成のためにこの校正containerには
`--privileged`を指定するが、host認証やDocker socketは渡さない。通常devcontainerの権限変更ではない。

## 予算、原提出、失敗

P1の条件全体の時計は、phase公開から最後の検査・停止・回収までのmonotonic elapsed time。
初期capture、起動、開発、公開検査、待機、停止、archive、修正を全て共通の開発予算から引く。
P0各attemptの原時計も保存し、P1の親の時計と混同しない。親の期限をP0へ渡し、起動準備で
使い切ったらproviderを起動しない。cleanupは提出上限後も有限の停止・回収枠で実行し、超過を隠さない。

後続phaseの最小時間・output・sessionを予約してから修正を許可する。outputは観測されたusageの累積で、
厳密なin-turn上限ではない。usage不明、提出なし、残予算不足、修正回数上限では追加sessionを開始しない。
公開出力はstdout/stderr共有のbyte上限で切り、切断の事実を残す。検査のtimeout・停止未確認・source変化は
`unknown`として記録し、その条件の修正と未開始の条件を止める。単なる公開検査不合格とは区別する。
Codex sandboxの起動中断で空の`.agents` / `.codex`が残った場合も、source変化を除外して成功にしない。

修正ごとに新しい`attempt-NNN`を作り、作業中のsourceを引き継ぐ。原提出のstateやarchiveを書き換えない。
各phaseの最後の原archiveを、全開発停止後に固定評価器へ渡す。未提出の成果が合格しても予算内完了にしない。
比較を一度開始したら同じdirectoryで再実行しない。所有者死亡後の無人復旧はP0と同じく未提供。

| field | 計上する範囲 |
| --- | --- |
| conditionの`elapsed_seconds` | 公開・capture・起動・検証・停止・修正を含む全開発区間 |
| `public_check_seconds` | 上記の内数。検査準備・実行・停止・source照合 |
| `initialization_seconds` | seal時の入力確認と両条件の初期capture |
| `capabilities`内の`elapsed_seconds` | 開発前の能力確認。条件の開発予算外で明示 |
| `hidden_evaluation_seconds` | 全開発後のarchive展開と固定評価 |
| 比較全体の`elapsed_seconds` | run入口から集計まで。事前のimage準備やsealは含まない |

同じ品質・予算・取得窓を両方満たす場合だけ、条件全体のelapsed timeで速度比を計算する。
外部評価や配布を含む「利用可能までの速度」、金額、release合格はこの比から推定しない。
P2ではimage準備等の外部費用も含めた実験上限・入力監査・実行順を固定する。

## 入力と使用

`workflow.py seal`はschema 1 / kind `public-feedback-v1`の設定を受け取る。

- `manifest`: P0と同じstudy/model/effort/CLI・phases・admission・時間/output/session/capture上限。
  `schema_version`、`clock`、`condition`は親が設定するため指定しない。
- `conditions`: `id`、`mode`、`workspace`、`release`、`container`の2件。実行はこの登録順。
- `image`: immutable image ID。`task`と必要時の`legacy`は固定評価器を指定する。
- `capability_seconds`、`observer_seconds`: 外部検査の明示上限。
- `public_checks`: schema 1、`scope/rationale/owner/update_when`、`limits_kind: cost_cap`、
  `max_source_bytes/max_output_bytes/max_feedback_rounds`、`retry_min_seconds/retry_min_output_tokens`、
  `network_access`、`checks`、`phase_check_ids`。
- 各check: `id/phase/tier/description/source/sha256/argv/seconds`。全情報はsealへ保存するので開発側に渡さない。

resource上限は当該比較のcost cap、phaseと修正開始の最小予約はplanning prior、source・停止・
同一環境・read-only・欠測保持はhard guard。scopeはsealした比較、更新ownerはprimary/integrator。
task・CLI・image・校正所要時間が変われば次のseal前に見直す。fixtureの数値は運用defaultではない。

```bash
python3 experiments/development-harness/feedback/workflow.py seal \
  --config /private/feedback.json --output /private/new-feedback
python3 experiments/development-harness/feedback/workflow.py run --output /private/new-feedback
```

workspace・公開directory・出力は相互に包含しない。公開directoryは空、containerは停止状態で用意する。
現在の評価器接続は既存の`duplicates-v1/redaction-v2/acceptance-v2`のみ。次の課題を決めたらP2で
対応表と評価器の識別能力を固定する。この校正入口だけをlive比較の開始条件にしない。

## 検証

```bash
TERMINAL_DEVELOPMENT_IMAGE=sha256:検証済みimageのID \
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-development-feedback.py scripts/test-terminal-development.py
```

image未指定時はDocker試験をskipする。新版の検証証跡と旧suiteの回帰結果は`validation.json`。
