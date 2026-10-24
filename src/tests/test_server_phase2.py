import importlib
import subprocess
from fastapi.testclient import TestClient
server = importlib.import_module('server.app')
client = TestClient(server.app)


def test_desktop_cors_and_catalog():
    response = client.get('/api/v1/assets', headers={'Origin': 'tauri://localhost'})
    assert response.status_code == 200
    assert response.headers['access-control-allow-origin'] == 'tauri://localhost'
    assert response.json()['total_3d_models'] == 666


def test_missing_compile_marker_fails(monkeypatch):
    monkeypatch.setattr(server.subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout='', stderr=''))
    assert client.post('/api/v1/compile', json={}).status_code == 500


def test_timeout_and_crash_are_not_success(monkeypatch):
    def timeout(*a, **k):
        raise subprocess.TimeoutExpired('blender', 120)
    monkeypatch.setattr(server.subprocess, 'run', timeout)
    assert client.post('/api/v1/compile', json={}).status_code == 504
    def crash(*a, **k):
        raise subprocess.CalledProcessError(-11, 'blender', stderr='Metal startup crash')
    monkeypatch.setattr(server.subprocess, 'run', crash)
    assert client.post('/api/v1/compile', json={}).status_code == 500


def test_agent_clearance_survives_compile():
    result = client.post('/api/v1/agent/prompt', json={'prompt': 'Widen clearance to 45m'}).json()
    assert result['compilation']['min_clearance_m'] == 45


def test_invalid_scene_does_not_escape_or_truncate():
    assert client.post('/api/v1/scenes', json={'scene_name': '../escape', 'ast_data': {}}).status_code == 400
    assert client.post('/api/v1/compile', json={'raw_ast': {}}).status_code == 422
