# Lens: end user

## Purpose

実際のuserが初めて触れてから目的を達成するまでの体験を、user側の知識と状況で辿る。

## Use when

UI / CLI / APIの設計やdiff、demo前、onboardingやerror handlingを変えた時。

## Questions

- 初回のuserは、説明なしで最初の成功までたどり着けるか。どこで止まるか。
- 主要journeyの各stepで、userは今何が起きていて次に何をすればよいか分かるか。
- 空の状態、読み込み中、失敗、部分的成功、権限不足の時に何が見えるか。
- 取り消し、やり直し、data消失の不安に応えているか。
- keyboard操作、screen reader、色覚、文字サイズ、低速回線、小さい画面で破綻しないか。
- 用語はuserの言葉か、実装の言葉か。
- 実際に動かしたevidence（primaryが`$verify-product-experience`で得たscreenshot、操作log）があるか。無ければcodeからの推測だと明示する。

## Return

journey上の位置、再現手順、userへの影響、severity、最小の改善案を返す。実際に操作・screenshotで確認したものと、codeから推測したものを分ける。

## Avoid

好みだけのvisual指摘、全画面の網羅的checklist、実装costを無視した再設計案。
