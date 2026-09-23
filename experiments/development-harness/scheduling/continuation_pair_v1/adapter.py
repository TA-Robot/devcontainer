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
            shutil.copyfile(HERE/'probe.py', fixture/name)
        for path in fixture.iterdir(): path.chmod(0o444)
        native.LEGACY = fixture
    return native.run(output, public, **options)
