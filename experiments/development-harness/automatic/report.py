#!/usr/bin/env python3
"""Render already-computed decisions; no grading overrides or manual score fields."""
import argparse
import json
from pathlib import Path


def render(result):
    labels = {True: '合格', False: '不合格', None: '未確認'}
    names = {'long-integer': '巨大整数を含むログの秘密情報除去',
             'surrogate-utf8': '伏せ字後のUTF-8出力',
             'gc-active-verification': '検証中の作業領域のGC除外',
             'publication-signal': '中断時の誤った成功確定の防止',
             'git-stat-refresh': '内容を変えないGit更新の許容'}
    title = '小規模修正' if result['scale'] == 'small' else '複数段階の開発'
    lines = [f'# 自動比較: {title}', '',
             '既存成果を新版テストで再評価した校正記録。新しいモデル比較ではない。'
             if result['mode'] == 'retrospective' else '事前固定のテストと予算に基づく自動比較。', '',
             '| 条件 | 固定した品質条件 | 開発時間 | 観測output tokens | 予算内提出 |',
             '| --- | --- | --- | --- | --- |']
    for key, name in [('control', '対照'), ('improved', '改良')]:
        value = result['conditions'][key]
        duration = f'{value["development_seconds"] / 60:.2f}分'
        if value.get('development_seconds_kind') == 'conservative_reservation':
            duration += '（予約分を計上、実測欠測）'
        elif value.get('development_seconds_kind') == 'observed_with_shutdown':
            duration += '（停止処理込み）'
        usage = (f'{value["output_tokens"]:,}' if value.get('usage_complete', True)
                 else f'使用量不明（完了sessionの確定分: {value["output_tokens"]:,}）')
        lines.append(f'| {name} | {labels[value["final_quality_accepted"]]} | '
                     f'{duration} | {usage} | '
                     f'{"はい" if value["submitted_within_observed_budget"] else "いいえ"} |')
    lines += ['', '速度比: ' + (f'{result["speed_ratio"]:.3f}（対照時間÷改良時間）。'
              if result['speed_ratio'] is not None else '算出しない。両条件の品質・予算条件が揃っていない。'), '',
              '人による採点・合否の上書きなし。配布を含む全面的な品質保証とは区別する。', '']
    if result.get('automatic_execution_completed') is False:
        lines += ['開発の一括実行は中断。停止確認後、保存済み成果の採点を完了した記録。', '']
    for key, name in [('control', '対照'), ('improved', '改良')]:
        recovered = result['conditions'][key].get('recovered_artifact')
        if recovered:
            lines.append(f'{name}の中断後に保全した成果: {labels[recovered["quality"]["accepted"]]}。'
                         '提出済み・予算内完了とは扱わず、正確な終了時刻も推定しない。')
        terminal = result['conditions'][key]['terminal']
        if not terminal:
            lines.append(f'{name}: 提出物の観測なし。')
            continue
        quality = terminal['quality']
        failed = [names.get(c['name'], c['name']) for c in quality['checks'] if c['status'] == 'failed']
        unknown = [names.get(c['name'], c['name']) for c in quality['checks'] if c['status'] == 'unknown']
        if failed:
            lines.append(f'{name}の不合格項目: ' + '、'.join(failed) + '。')
        if unknown or quality['measurement'] == 'unknown':
            lines.append(f'{name}の未確認項目: ' + ('、'.join(unknown) if unknown else quality.get('reason', '観測不足')) + '。')
    lines += ['', f'同時間の品質観測: {len(result["common_time_quality"])}時点。'
              '詳細・個別テスト結果・観測時間は比較結果のJSONに保存。']
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparison', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(render(json.loads(args.comparison.read_text())))
