"""Keep API tests isolated from user scenes. --run-blender enables native integration.

Default API tests stub the subprocess boundary; live Blender and Godot checks are
separately reported, never represented as unit-test coverage of those engines.
"""
import importlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest


def pytest_addoption(parser):
    parser.addoption('--run-blender', action='store_true', help='Run API compilation tests against headless Blender')


@pytest.fixture(autouse=True)
def isolated_server(monkeypatch, tmp_path, request):
    if request.module.__name__.split('.')[-1] not in ('test_server', 'test_shader_recipes', 'test_server_phase2'):
        return
    server = importlib.import_module('server.app')
    source = Path(__file__).resolve().parents[1]
    scenes, build = tmp_path/'scenes', tmp_path/'build'
    shutil.copytree(source/'scenes', scenes)
    build.mkdir()
    # Existing artifact is used only for the file-serving test.
    artifact = source/'build/sector_01_cerberus_corridor.glb'
    if artifact.exists():
        shutil.copy2(artifact, build/artifact.name)
    monkeypatch.setattr(server, 'SCENES_DIR', scenes)
    monkeypatch.setattr(server, 'BUILD_DIR', build)
    if request.config.getoption('--run-blender'):
        return
    def fake_compile(cmd, **kwargs):
        output = Path(cmd[-1])
        output.write_bytes(b'glTF' + b'\0'*1200)
        result = {"status": "PASSED", "objects_spawned": 96, "objects_retained": 96,
                  "glb_output_bytes": output.stat().st_size, "corridor_clearance_percent": 100.0}
        stdout = '__MOMENTUM_STUDIO_RESULT_START__' + json.dumps(result) + '__MOMENTUM_STUDIO_RESULT_END__'
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr='')
    monkeypatch.setattr(server.subprocess, 'run', fake_compile)
