# Synthesis consultation pilot v1

2026-09-06。初回の有限な探索比較。対象はF12-L-MDJSON-001 revision 3の証拠統合。
旧atlas観測へ追加せず、このprotocol・source・imageで新しいrunを作る。

## 問いと介入

事故・隔離・移行を別contextで点検した事前助言が、最終成果の数値・参照・明示制約の整合を改善するか。
対照Aはsolo maker、Bはadvisorの提出を停止・保全してからfresh makerへ渡す直列の事前助言。
期待する作用は観点の補充と見落としの検出。途中の相談やnative peer-to-peer操作は対象にしない。
両makerは同じ公開source、課題、検証手段、権限を持ち、自由に自己検証できる。
advisorにはmakerの結果・hidden oracle・模範解答を見せない。最終化と採否はmakerが所有する。

## 固定する比較条件

| 項目 | 初回live値・意味 |
| --- | --- |
| case / rubric | F12-L revision 3、現行公開3＋hidden9項目。全12項目とsource contractを要求 |
| provider | Codex CLI 0.153.0、要求model gpt-6-astra、要求effort high。applied/resolvedは確認できた範囲だけ記録 |
| image | sha256:c7f904a12d7e7c63a2c7e46bc6654c8304b497a2836ecb08fb5bea0118f679ea |
| participant / repeat | Aのmaker、Bのadvisorとmaker。各条件1episodeの探索で、repeatによる一般効果確認ではない |
| condition cap | 各900秒、output合計18,000。Bはadvisor＋maker＋受渡しで共有 |
| advisor cap / maker reserve | advisor最大180秒・開始最低30秒。makerへ最低300秒・1,000 outputを予約。soloはcondition全体を使える |
| observation | stop10秒、capture30秒、取得窓10秒、snapshot16 MiB、advice16 KiB |
| order | `synthesis-consultation-pilot-v1`のSHA256先頭byteの偶奇で事前割付。configへ実順序を保存 |
| validation / cleanup | model-free probeは各30秒、外部評価の実行は各最大90秒（作成・削除は各30秒）、所有containerの削除は各30秒 |

数値はこのpilotのcost cap、最低予約はplanning prior、有限なparticipant構造と独立評価はhard guard。
根拠は小さなrepository内の構造化成果、既存Cycle 005の開発・検証量、相談後のmaker作業を残す必要性。
scopeはこの1組、ownerはprimary/integrator。正常probeの不成立、task/CLI/image変更なら新protocolで見直す。
モデルの結果を見て上限を延ばしたり、良いrunへ差し替えたりしない。
output上限は観測されたturn終了単位であり、in-turnの厳密な総token・料金上限ではない。
全input/cache/output、欠測、準備、開発、受渡し、停止・回収、外部採点の費用を分ける。

## 採否基準

1. 全員の停止、同じ公開source、環境同等性、必要な検証能力、完全なoutput usageを満たさなければ効果判断を保留。
2. 固定12項目の成績と失敗IDを両条件とも報告する。source違反、未完了、予算超過、欠測も除外しない。
3. Bだけが全項目へ到達し、予算内なら、この範囲での相談候補として残す。1組から一般既定にはしない。
4. 両側全項目なら、Bがcondition実時間で10%以上短く、input/outputのどちらもAの110%以下の場合だけ、
   速度・消費の改善候補として次の確認へ進む。これはこの探索のhypothesis/採用priorで、統計的有意差の基準ではない。
5. 品質が下がる、あるいは同品質で時間・消費の改善条件を満たさない場合、この「常に事前助言」方式を既定化しない。
   他課題・途中相談・他のroleの価値まで否定しない。
6. free textの実効性、事故防止、rollbackの機能、一般的創造性は未測定。監査済みの12点をそれらの証拠にしない。

仮説が外れたら、未測定の改善率を配布せず、不要な事前助言を避ける条件や次の検証点をガイドへ戻す。
良い差があっても、確認課題・repeat・精度・費用を別途事前固定するまで推奨へ昇格させない。

## 実行境界

通常のdevcontainer設定は変更しない。過去に検証した専用containerとnamed workspace profileを使用。
provider通信とtask commandのnetwork設定を分け、task commandのnetworkは無効にする。
全participantのenvironment fingerprintを比較し、全員のmodel-free sandbox probe後にのみ開発を始める。
全体の予定実行・評価時間を覆う認証の有効期間を確認し、private copyを終了後に削除する。
外部評価には認証をmountしない。modelの再試行、fallback、評価得点の人/LLM上書きは行わない。

既存terminalが生成する汎用promptには課題と衝突するhandoff要件があるため、
新しいrelayが入力hashを確認し、課題固有promptへ置換して両hashを保存する。旧runnerは変更しない。
公開チェックとの整合を含め、relay・actor停止・採点を疑似providerと実imageで確認してからliveへ進む。

Codexの非対話実行、JSONL、ephemeral、明示sandboxの仕様は
[公式OpenAI documentation](https://learn.chatgpt.com/docs/non-interactive-mode)を参照。
現CLIのnamed profile表面は実imageのprobeを根拠とし、文書だけから対応を仮定しない。
