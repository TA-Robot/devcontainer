# Mira Companion v2 — Mira World

Codex lifecycle hookと`agentctl` managed jobのsanitized eventを、VS Code下部の短いpixel-art世界へ変換するworkspace extensionです。コーディングが主役で、ミラはその進行に合わせて世界の中を動きます。

- read / planning / edit / shell / test / delegationごとに対応するmap拠点へ自動移動
- idle中は資料庫、作戦卓、工房、test gate、dispatch dockの間を時々散歩
- Codex / Claude / Grokのagentctl jobをprovider countとrole別の仲間spriteで表示
- Codex native subagent稼働中も小さな仲間spriteがdockへ出現
- 完了、test、recovery、badgeなどのeventを自動演出
- 長い作業の完了など、自然な区切りにだけ45秒間のone-click popを表示
- clickによるXP差、連打報酬、ハイタッチ、なでる、reaction menu、notification toastはなし
- `workbench.reduceMotion`、window focus、panel visibilityを尊重
- prompt、code、task objective、workspace path、tool arguments、command、tool output、transcriptは読み込みも保存もしない

workspace初回とremote runtime rebuild直後だけbottom panelを開き、同じruntimeでのその後はVS Codeが記憶するpanel状態を尊重します。右下の小さなMira glyphはworldを再度開くtoggleで、主表示ではありません。Activity Barやsidebarは追加しません。

設定は`miraCompanion.autoOpen`、`miraCompanion.motion`、`miraCompanion.statusBar`、`miraCompanion.stateFile`です。

packageはrepository rootから作ります。

```bash
scripts/build-mira-vsix
scripts/test-mira-vsix.sh
```

設計の正本は`docs/mira/architecture.md`、60案と試行記録は`temp/mira-companion-v2/`です。

v0.4.0は`agentctl job run --provider codex|claude|grok`を観測します。Claude / Grok CLIをagentctl外で単独起動したinteractive sessionはまだ対象外です。
