# Lens: operations

## Purpose

release後に、このsystemを動かし続ける人の立場から、壊れ方と直し方を問う。

## Use when

deploy方法、永続data、外部依存、background job、設定を追加・変更した時。

## Questions

- どうdeployし、どうrollbackするか。rollbackでdataは壊れないか。
- 壊れたことに誰がどう気付くか。log、metric、alertは原因まで辿れるか。
- 外部依存が遅い・落ちる・仕様を変えた時にどう振る舞うか。
- data migration、backup、restoreは手順として存在し、試されているか。
- 設定やsecretの変更に再deployが必要か。誤設定はどう検出されるか。
- userからの問い合わせに答えるための情報は取れるか。

## Return

failure scenario、検出手段の有無、復旧手順の有無、推奨する最小の対策を返す。今のmilestoneで必要なものと後へ送れるものを分ける。

## Avoid

projectの規模に見合わない本番運用基盤の要求、根拠のないSLA設定。
