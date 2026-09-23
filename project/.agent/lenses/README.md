# Perspective lenses

lensは、ユーザーやprimaryが明示しなかった視点を持ち込むためのprovider-neutralなbriefです。roleではありません。read-onlyの`advisor` roleへ一つのlensと対象artifactを渡して使います。delegationが使えない場合は、primaryが同じlensを順に自分へ適用し、独立したreviewを得たとは主張しません。

## Selecting lenses

- 対象artifact（brief、設計、diff、UI、release計画）と、今いちばん不確かなassumptionから選ぶ。
- 各lensについて「このlensでしか見つからないfailureは何か」を一文で書けない場合は使わない。
- catalog全部を毎回回さない。lensの数はglobal defaultにせず、名前の付いたriskから導く。
- 同じlensを複数agentへ重複させない。同じ観点の追加は、別のevidence sourceがある時だけ。
- project固有の視点が必要なら、`domain.md`を複製・編集してlensを追加する。

## Catalog

| lens | 主に見つけるもの |
|---|---|
| [product-strategy](product-strategy.md) | 価値の弱さ、scopeの過不足、より良い問題設定 |
| [end-user](end-user.md) | 初回体験、主要journey、error / empty state、accessibility |
| [operations](operations.md) | deploy、観測、障害復旧、data移行、support負荷 |
| [security-privacy](security-privacy.md) | threat、data取扱い、secret、abuse、compliance |
| [cost-scale](cost-scale.md) | 単価、性能限界、scale時の破綻、lock-in |
| [pre-mortem](pre-mortem.md) | 将来失敗したと仮定した時の原因と早期signal |
| [reframe](reframe.md) | 前提の外にある別解、他分野からの類推、大胆な簡略化 |
| [domain](domain.md) | project固有の業界知識、規制、用語（projectが記入する） |

## Brief to an advisor

```text
lens: .agent/lenses/<name>.md
artifact: <paths or commit SHA>
question: <the decision this review informs>
context: docs/product/brief.md, docs/product/assumptions.md
out of scope: <what not to review>
stop: return findings when the lens questions are answered or evidence is unavailable
```

## Using the result

primaryがfindingごとに`fix-now / scheduled / accepted-risk / out-of-scope`を判断し、`docs/product/assumptions.md`のPerspective findings、roadmap、taskへ振り分けます。advisorの提案をそのまま採用せず、多数決にもしません。ユーザーへ伝えるのは、判断を変えるfindingと、ユーザーにしか答えられない問いだけです。
