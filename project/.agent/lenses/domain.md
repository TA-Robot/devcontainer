# Lens: domain

このlensはprojectが記入します。業界知識、規制、専門用語、慣習など、一般的なengineeringの視点では見落としやすい領域を書きます。複数の領域があれば、このfileを複製して名前を変えます。

## Purpose

`<<domain>>`の専門家の立場から、product判断が現場の現実と合っているかを問う。

## Use when

`<<domain-specific triggers: regulatory feature, domain data model, workflow change>>`

## Questions

- `<<domain-specific question>>`
- 現場のuserは、この用語・手順・数値をどう理解し、どう使っているか。
- 業界の規制、標準、慣習で、この設計が違反・逸脱しているものはあるか。
- 専門家なら最初に疑う前提は何か。

## Return

domain上の根拠（規制、標準、一次資料、userの発言）、product判断への影響、推奨、確認すべき問いを返す。確認できない事項は`unknown`とする。

## Avoid

根拠のない業界慣習の断定。一次資料がない場合は問いとして返す。
