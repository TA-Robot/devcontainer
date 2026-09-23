"""Retain frozen quality arithmetic and expose observed capture timing separately."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def summarize(result, inputs):
    spec = importlib.util.spec_from_file_location('termination_quality_arithmetic',
                                                 HERE.parent/'continuation_pair_v1/report.py')
    reporter = importlib.util.module_from_spec(spec); spec.loader.exec_module(reporter)
    report = reporter.summarize(result, inputs)
    report.update(kind='termination-pair-quality-v1',
                  scope='common-source continuation artifacts after observed termination; one pair, not exact-cutoff quality',
                  original_episode_admission=result['original_episode_admission'],
                  captures={name: row['classification'] for name, row in result['captures'].items()})
    return report
