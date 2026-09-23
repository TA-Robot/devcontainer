# Wave 8 identifiable remeasurement

実施開始日: 2026-08-28

## Objective

旧108 recordsで識別できなかった`problem/evaluator saturation`、`effort effect`、
`fixed strategy or missing artifact`を、新しいtask-artifact retentionとrevision-aware
validity gateの下で再測定する。これはmodel/providerのdefault選定ではなく、exact case
内の判断材料を増やす有限観測である。

## Why these cells

| Case | Series | Repeat | Purpose |
| --- | --- | ---: | --- |
| F06-L r1 | medium / high | 3 | 旧Codex 3/11→11/11差とGrok 5/11 flatが再現するかを見る。threshold仮説なのでまず隣接2設定を反復する |
| F10-S r5 | medium / high | 2 | 公開contract/templateと単一edit-surface criterionへ修正したexact small caseが実際に解けるか、artifact付きで確認する。深いladderを先に消費しない |
| F12-L r3 | Codex medium / high / xhigh / max; Grok medium / high / xhigh | 2 | plural-goldなopen-ended large caseでdepth差を見る。Grok maxは既知のprovider rejectionなので再送しない |

Repeat数はglobal defaultではない。F06は既存signalの再現、F10はinstrumentation/contract
repair確認、F12は高effortを含むdepth観測という異なる問いから決める。2反復は分散推定を
完成させる数ではなく、singletonのまま結論するのを避け、追加反復の必要性を判断する
第一段階である。

## Provider boundary

- Codex `gpt-5.6-sol`: credential window pass。requested effortを記録するが、runtimeで
  applied値を独立確認できない限り`unknown`のまま扱う。
- Grok `grok-4.6`: host CLI 1.0.5と一時private HOME内でrefreshしたcredential copyを
  使用する。元credentialは変更しない。medium/high/xhighのapplied metadataを観測する。
- Claude: CLIはあるが`loggedIn=false`かつcredential freshness不明。generationを開始せず
  unmeasuredに残す。

## Safety and stop conditions

- C0 primary-only、fresh ephemeral session、concurrency 1、automatic retryなし。
- task artifact retentionは`task-artifacts`。最大16 files、各256 KiB、合計1 MiB。
- raw prompt、provider transcript、stderr、private reasoning、credentialはrecord/atlasへ保存しない。
- quality failでも次cellへ進む。Infrastructure failure、deadline、setting rejection、credential
  safety window失敗はそのmanifestの停止理由として保持し、quality populationへ混ぜない。
- Same case revision / fixture identity / applied setting / repeat / infrastructure population /
  measurement headroomを別々に監査する。全passは`ceiling-limited`であってmodel saturationではない。

## Planned manifests

1. `wave8d-c0-grok-f06-threshold.json`: 6 runs
2. `wave8d-c0-grok-f10-r5-contract.json`: 4 runs
3. `wave8d-c0-grok-f12-r3-depth.json`: 6 runs
4. `wave8d-c0-sol-f06-threshold.json`: 6 runs
5. `wave8d-c0-sol-f10-r5-contract.json`: 4 runs
6. `wave8d-c0-sol-f12-r3-depth.json`: 8 runs

全34 planned runsを一つのglobal batchへ暗黙展開せず、目的・timeout・停止判断が異なる6つの
immutable manifestへ分ける。各manifestをprovider-free dry-runしてから明示的にlive実行する。

## Revision-2 floor and stop decision

最初の`wave8-c0-grok-f10-contract.json`はrevision 2のmedium/highを各2回実行した。4回とも
provider/infrastructureは正常終了し、applied effortも確認できたが、scoreはmediumが2/7、
highが1/7で全てquality failだった。terminal wallは58.4–121.9秒だった。

保持artifactの自動・内部監査では、mediumはseeded semantic root causeを特定していた一方、
公開されていないnesting/field shapeとの差で落ちた。highはallowlist外pathを編集し、必要な
`performance.json`を残していなかった。全runがunexpected path 2件を持ちsnapshot partialだった。
したがってrevision 2の4件はterminal operational evidenceとして保持するが、effort-quality
curveからは除外する。残り30 runをそのまま流すのを止め、F10/F12をrevision 3へ修復した。

## Revision-3 live floor and second stop

`wave8b-c0-grok-f10-r3-contract.json`は最初のmedium/high各1件で停止した。両方とも
provider/infrastructure success、applied setting確認済みで、terminal wallは49.9秒と43.4秒。
mediumはpublic 2/2をpassし、保持artifactの構造監査でも5つのsemantic obligationを満たしていた。
しかし両runにuntracked scratch pathが2件あり、hidden evaluatorが各semantic testのsetupで
同じscope違反を再検査したため、medium 2/7、high 1/7という誤解を招くscoreになった。

これはagentのeditable-surface違反という観測と、evaluatorが一つの違反を5重計上する設計不良が
重なったもの。2件はterminal/scope operational evidenceとして保持し、revision 3はeffort-quality
比較をconditional-onlyにする。Revision 4ではpublic validatorがexact editable surfaceを先に
検査し、scratchをagent自身が修正できるようにした。残り2件の起動前にbatchを手動停止した。

## Revision-4 live floor and third stop

`wave8c-c0-grok-f10-r4-contract.json`はmedium 1件だけを記録して停止した。applied medium、
infrastructure success、terminal wall 59.3秒、untracked scratch 2件で、public edit-surface checkは
意図どおりfailした。しかしhidden側の旧setup scope checkが残り、hidden 5/5も同時にfailした。
これはrevision 4実装の不完全さであり、effort evidenceには使わない。Revision 5でhidden scope
checkを除き、protected input integrityとsemantic criteriaを独立させた。次run開始前に停止した。

## Wave-8d completed measurements

最終finite matrixはGrok 16件、Codex Sol 18件、合計34件をautomatic retryなしで完走した。
Codexはrequested effortのみでruntime applied値は未確認、Grokはmedium/high/xhighのapplied値を
確認済みである。以下の中央値は同一case/setting内のraw terminal-wall中央値であり、典型値や
provider rankingではない。

| Case/provider | Setting (n) | terminal wall min / median / max | Score observations | Artifact interpretation |
| --- | --- | --- | --- | --- |
| F10-S r5 / Grok | applied medium (2) | 43.9 / 46.6 / 49.3 s | 6/7, 6/7 | semantic 5/5、scopeだけfail。両方partial、untracked 2件 |
| F10-S r5 / Grok | applied high (2) | 57.8 / 74.9 / 91.9 s | 6/7, 6/7 | 同上。quality headroomなし |
| F10-S r5 / Sol | requested medium (2) | 66.1 / 67.0 / 67.8 s | 7/7, 7/7 | complete 2/2、ceiling |
| F10-S r5 / Sol | requested high (2) | 73.9 / 75.5 / 77.0 s | 7/7, 7/7 | complete 2/2、ceiling |
| F06-L r1 / Grok | applied medium (3) | 27.7 / 32.9 / 34.2 s | 5/11, 3/11, 3/11 | required test artifactは全件0。2件はscratchのみ |
| F06-L r1 / Grok | applied high (3) | 26.3 / 27.2 / 28.6 s | 5/11 × 3 | required artifactは全件missing |
| F06-L r1 / Sol | requested medium (3) | 219.7 / 227.7 / 295.5 s | 10/11, 9/11, 5/11 | complete 3/3、within-cell variance大 |
| F06-L r1 / Sol | requested high (3) | 426.9 / 455.2 / 506.1 s | 9/11, 7/11, 9/11 | complete 3/3、旧11/11を再現せず |
| F12-L r3 / Grok | applied medium (2) | 116.7 / 162.8 / 208.9 s | 0/12 × 2 | cleanだがartifact missing |
| F12-L r3 / Grok | applied high (2) | 176.5 / 186.8 / 197.1 s | 0/12 × 2 | cleanだがartifact missing |
| F12-L r3 / Grok | applied xhigh (2) | 194.7 / 200.0 / 205.4 s | 0/12 × 2 | cleanだがartifact missing |
| F12-L r3 / Sol | requested medium (2) | 157.6 / 160.6 / 163.6 s | 12/12, 11/12 | complete 2/2。2件目はclaim provenance |
| F12-L r3 / Sol | requested high (2) | 259.2 / 267.6 / 276.0 s | 12/12, 11/12 | complete 2/2。2件目はunknown honesty |
| F12-L r3 / Sol | requested xhigh (2) | 293.5 / 298.6 / 303.7 s | 12/12, 11/12 | complete 2/2。2件目はunknown honesty |
| F12-L r3 / Sol | requested max (2) | 431.8 / 438.7 / 445.5 s | 11/12 × 2 | complete 2/2。unknown honestyを2/2で再現 |

## F06 revision-1 identity disposition

Atlas build時に、F06-L revision 1が二つのbundle digestへ分岐していることを検出した。原因は
public `check_test_only.py`生成時の`repr(set(...))`で、Python hash seedにより二つのallowlist
pathの表記順が変わったことだった。意味上は同じsetでもexact fixture identityではないため、
旧4件/Grok 6件とSol 6件をpoolしない。

Revision 2ではsorted set literalへ固定し、異なる二つの`PYTHONHASHSEED` subprocessでworkspace
tree、base SHA、bundle digestが一致するtestを追加した。Current Atlasは一つのidentityしか
同一revisionへ収容しない不変条件を守り、artifact-retained repeatを持つSol 6件をconditional
side evidenceとして採用する。旧4件とGrok 6件はimmutable recordと本書へ保持するがAtlasから
除外する。Revision 2のlive値はまだunmeasuredである。

## What the completed wave identifies

1. F10-SはSolでmedium/highともfull-pass、Grokもsemantic obligationsは全件passしており、
   このscoreはceiling-limited。`mediumで十分`を他問題へ一般化できない。
2. F06-Lの旧Codex medium/high一点差は再現しなかった。さらにrevision-1 fixture identityが
   nondeterministicだったため、旧点との直接比較自体を禁止する。
3. F12-L Solは全settingでcomplete artifactへ到達したが、各cellの2回目やmaxでbounded unknownを
   閉じる失敗が出た。higher requested effortの単調改善は観測されない。
4. F06/F12 Grokのall-failは難問飽和ではない。必要artifactへ到達しないtask-entry floorであり、
   reasoning depthとtool/task completion failureを分離すべきである。
5. 同一cell内の時間・quality varianceがsetting間差と同程度以上の箇所がある。singletonsから
   effort ruleを作らず、projectごとにrepeatとheadroomを設計するという当初方針を支持する。

## Current release closure

Current Atlasにはbase releaseからidentity-conflictingなF06-L revision 1を4件外した104件、
F10 revision floor 7件、Wave-8d Grok F10/F12 10件、Wave-8d Sol F06/F10/F12 18件の
合計139件を収録した。Wave-8d Grok F06 6件は別fixture identityなのでimmutable evidenceには
残すが、同一case revisionへpoolしない。選択と除外の機械可読な正本は
`wave8-release-disposition.json`である。

- Atlas: 139 samples / 113 series / 118 case strata / 370 output entities
- Run-set digest: `sha256:9c600a65732a674735bf17a4149713a1c4fdc4cb865df6ff61b679261046a9b6`
- Atlas / skill snapshot SHA-256: `924bb1a8c3b459c72473934d1a81cc7e54a68cc6adb8b208bc8a0eb86f2a41db`
- Human report SHA-256: `6324c1ffdbfe5127680cc911bfb049e9aec724446e138d1f9ff5736f9aea11ad`
- Validity / skill validity SHA-256: `870d6226d113015e87473860eb7c53224fc6e89aa997dfa0f122a5cb4577f67f`
- Catalog: revision 8 / digest `sha256:d51bca6a32f5396dceae3b928de6d358ee70e7507a882f4cf9843833c44fcc2c`

F06-L revision 2、Claude current matrix、Grok maxは値を補完せず`unmeasured`のまま残す。
Codex Solのeffortは全てrequested/status unknownであり、applied effortの因果効果としては扱わない。
