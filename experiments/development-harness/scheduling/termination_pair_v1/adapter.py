"""Reuse the sealed native actor; substitute only the synthetic provider fixture."""
import importlib.util
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent


def run(output, public, **options):
    spec = importlib.util.spec_from_file_location('continuation_native_actor', HERE.parent/'native_recovery_v1/actor.py')
    native = importlib.util.module_from_spec(spec); spec.loader.exec_module(native)
    if options.get('fake'):
        # A fresh module instance and private fixture directory: no old source
        # mutation, shared-global patch, or live execution-path substitution.
        fixture = output.parent/(output.name+'-fixture')
        fixture.mkdir(mode=0o700, exist_ok=False)
        shutil.copyfile(native.LEGACY/'accounting.py', fixture/'accounting.py')
        for name in ('fake_solo.py', 'fake_adaptive.py'):
            profile = options.get('fake_mode')
            probe = (HERE.parent/'deadline_capture_v1/probe.py' if profile in ('deadline', 'invalid', 'missing', 'child')
                     else HERE.parent/'continuation_pair_v1/probe.py')
            source = probe.read_text()
            if profile in ('deadline', 'invalid', 'missing', 'child'):
                # Give the real CLI time to reach the intended interruption
                # point, then keep its first tool pending beyond the 20s probe
                # deadline. Neither the frozen prototype nor live is changed.
                needle = "'yield_time_ms': 10000"
                if source.count(needle) != 1: raise ValueError('unexpected frozen probe source')
                source = source.replace(needle, "'yield_time_ms': 30000")
            (fixture/name).write_text(source)
        for path in fixture.iterdir(): path.chmod(0o444)
        native.LEGACY = fixture
    return native.run(output, public, **options)
