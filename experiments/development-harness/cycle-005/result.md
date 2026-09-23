# Cycle 005の結果と採用

**A/Bの実開発、固定評価、追加レビュー、実装の統合・実image確認まで完了。**
この1組では自動feedbackによる高速化は確認できず、追加修正も発動しなかった。
成果の採用は同期処理の正しさ・互換性に基づく。元の測定・13項目の得点は変更しない。

## 固定条件の結果

| 条件 | 固定評価 | 開発・検査・停止回収の全経過 | 観測output | 追加修正 |
| --- | --- | ---: | ---: | ---: |
| A: 自己検証 | 13/13、予算・取得窓内 | 587.194秒（9分47秒） | 14,555 | 0 |
| B: 自動feedback | 13/13、予算・取得窓内 | 780.894秒（13分01秒） | 21,343 | 0 |

両側とも最初のsessionで提出。Bの提出後の公開検査も合格し、修正sessionは不要だった。
Bの時間はAより193.700秒、約33.0%長い。自動公開検査の6.724秒はBの内数であり、無料にしていない。
この差の全てを検査自動化の費用や因果効果とは扱わない。初期prompt・情報が同じ1組でも、
開発経路・実行順・providerの揺れがある。特に今回はfeedback修正が発動していない。

順序は事前seedでA→B。初期sourceは`db4621846718ff517f5bcd1adc455531809ae04c`から
実験・校正コードを除き、両側へ同一のGit treeを配った。要求model/effortは`gpt-6-astra/high`、
Codexは`0.153.0`。providerが明示していない適用値はunknown。
両環境の能力確認は開発前に合格し、固定評価は両開発が終了してから実施した。
詳細・source/archive hash・原結果のhashは[result.json](result.json)。差し替えrunや採点上書きはない。

## 追加レビューと実装の選択

両案ともroot所有の`/opt`配下にあるdevuser所有prefixを更新できた。
prefix全体の交換ではなく、準備した世代への`bin`切替を使うため、親directoryのwrite権限は不要。

同じ追加probeを両成果へ適用すると、次の差が出た。

| 公開要求に関係する利用ケース | A | B |
| --- | --- | --- |
| 更新しないCLIがprefix外への相対symlink | 同期は成功を返すが、そのCLIが実行不能 | 元のCLIを実行可能なまま保持 |
| 既存package directoryが外部directoryへのsymlink | 同期を拒否 | 外部のbytesを変えずに更新 |

原観測は[supplementary-review.json](supplementary-review.json)。固定13項目の外で識別した
互換性の差なので、13/13を遡って変更しない。一方、全公開要求を満たす成果同士の速度比較とは
扱わない。Bの成果の優れた点を、自動feedbackの因果効果とも断定しない。

Bはcleanなインストール先で取得し、既存のsymlinkを保守的に再配置してから、
要求された実行ファイルを永続配置先で再検証する。prefixのdirectory inodeをlockするため、
別名pathの呼出しも同じ更新所有権を使い、`/tmp`のlock file保守を必要としない。
この互換性と実装上の根拠からBのruntime・回帰テストを選んだ。

## 統合と実際の利用

同期のshell入口はchannel・manifestの既存方針を維持し、新しいPython標準libraryのhelperへ
準備・実行ファイル検証・lock・atomic publicationを任せる。新しい依存、権限拡張、常駐serviceはない。
採用したruntimeとtransaction testのbytesはBの元の提出物と一致する。主たる実装の後処理修正はない。
実装・回帰テストの統合commitは`508efd6`。
説明には、公開後のcaller喪失と、外部volumeを使う場合の世代保持について補足した。

- 開始前: 新課題8・feedback19・terminal27・旧ハーネス42の計96テストが実Docker込みで合格。
- 統合後: 同期policy、transaction10件、safe/trusted wrapper、校正とadapter8件が合格。
- 実image: checkoutを起動時と同じ`/workspace`へread-only mountし、networkなしで同期policy・transaction10件・wrapperを確認。
- 稼働中のdevcontainer: installer/downloaderを使えない設定で実際のpost-start入口を実行し、
  Codex 0.153.0、Claude 2.1.220、Gemini 0.17.1、Grok 1.0.13の一致を確認。追加取得なし。

検証証跡は[integration.json](integration.json)。比較終了後の検査・統合作業を開発時間へ戻さない。
校正が将来の製品修正に依存しないよう、未修正scriptを`baseline-sync.sh`へ固定した。
開発者へ渡したsourceや、今回の固定評価を後から変更したものではない。

古い世代は実行中CLIのため自動削除しないので、更新には追加容量が必要。
既定prefixはcontainer再作成で回収される。外部volumeへ移したprefixには同じ回収を約束しない。
今回の結果だけで自動feedbackを通常運用の既定へ昇格させず、新方式の大規模効果も未測定として残す。
比較用containerは停止確認後に削除し、比較のために作った認証fileのコピーも削除した。
原source・archive・測定証跡はprivate stateへ保持し、普段使いのdevcontainerとhost認証は保持した。
