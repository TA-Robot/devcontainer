# Lens: cost and scale

## Purpose

利用が増えた時、またはpaid dependencyを使い続けた時に、性能と費用がどこで破綻するかを問う。

## Use when

data model、外部API / LLM / cloud resourceの利用、同期処理、cacheやqueueの設計、価格や利用上限に関わる判断。

## Questions

- 1 user / 1 request / 1 jobあたりのcostは何で決まるか。測ったか、推定か。
- 最初に限界に達するresourceは何か（CPU、memory、DB、rate limit、予算）。
- 10倍の利用で線形に増えるもの、超線形に増えるものは何か。
- 高価な処理を減らすcache、batch、非同期化の余地はあるか。
- 特定vendorへのlock-inは許容できるか。移行する場合のcostは。
- costの異常を早く検知できるか。

## Return

cost / 性能のdriver、測定値または推定の根拠、破綻点、今必要な対策と後で良い対策を返す。推定値にはroleとして`hypothesis`を付ける。

## Avoid

実需のない早すぎる最適化、測定なしの断定。
