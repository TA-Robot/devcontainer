"""Reuse frozen quality arithmetic; keep clock quality and output admission apart."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def promising(comparison):
    overall = comparison['overall']['difference']
    return (overall['on_time_value'] >= 0 and overall['critical_on_time'] >= 0
            and (overall['on_time_value'] > 0 or overall['critical_on_time'] > 0)
            and all(row['difference']['critical_on_time'] >= 0 for row in comparison['bands'].values()))


def summarize(result, inputs):
    if result['quality_status'] != 'measured': raise ValueError('complete cohort required')
    spec = importlib.util.spec_from_file_location('cohort_frozen_arithmetic', ROOT/'scripts/report-dynamic-solo-profile.py')
    arithmetic = importlib.util.module_from_spec(spec); spec.loader.exec_module(arithmetic)
    comparisons = {}
    for candidate, baseline in (('adaptive', 'solo'), ('adaptive', 'initial'), ('solo', 'initial')):
        values = arithmetic.summarize({
            'submission': result['assessments'][candidate]['evaluation'],
            'reference': result['assessments'][baseline]['evaluation']})
        overall = {}
        for axis in ('submission', 'reference'):
            summed = {key: sum(row[axis][key] for row in values['bands'].values())
                      for key in (*arithmetic.SUMS, 'critical_on_time', 'critical_total')}
            summed['on_time_fraction'] = summed['on_time_value']/summed['offered_value'] if summed['offered_value'] else None
            summed['critical_fraction'] = summed['critical_on_time']/summed['critical_total'] if summed['critical_total'] else None
            overall[axis] = summed
        overall['difference'] = {key: overall['submission'][key]-overall['reference'][key]
                                 for key in (*arithmetic.SUMS, 'critical_on_time')}
        for row in values['cases'].values():
            for axis in ('submission', 'reference'):
                row[axis] = {k: v for k, v in row[axis].items() if k not in ('trace', 'completion_times')}
        for rows in (values['cells'].values(), values['bands'].values(), values['cases'].values(), [overall]):
            for row in rows:
                row[candidate] = row.pop('submission'); row[baseline] = row.pop('reference')
        values['overall'] = overall
        values['triage_promising'] = promising(values)
        comparisons[candidate+'_vs_'+baseline] = values
    return {'kind': 'continuation-pair-quality-v1', 'status': 'measured', 'input_seal': inputs,
            'pair_triage_promising': all(comparisons[key]['triage_promising']
                                        for key in ('adaptive_vs_solo', 'adaptive_vs_initial')),
            'scope': 'continuation quality from a common initial source; one developer per condition and a fixed non-agent baseline',
            'output_budget_admission': result['output_budget_admission'], 'billing_completeness': 'unknown',
            'stable_collaboration_effect_established': False, 'confirmation_used': False,
            'outer_preparation_and_human_review_cost': 'unmeasured', 'comparisons': comparisons}
