"""Native Jolt regression tests: import real GLB triangles; never mock physics."""
import json
import os
from pathlib import Path
import struct
import subprocess

import pytest

GODOT = Path(os.environ.get('GODOT_BIN', '/Applications/Godot.app/Contents/MacOS/Godot'))
ENGINE = Path(__file__).resolve().parents[1]/'engine'
pytestmark = pytest.mark.skipif(not GODOT.is_file(), reason='Godot binary not installed')


def write_road(path, gap=False, wall=False):
    vertices = []
    def quad(a, b, c, d):
        vertices.extend([a,b,c,a,c,d])
    for start,end in ([(0,400),(420,1100)] if gap else [(0,1100)]):
        quad((-7,0,start),(-7,0,end),(7,0,end),(7,0,start))
    if wall:
        quad((-7,0,200),(-7,5,200),(7,5,200),(7,0,200))
    binary = b''.join(struct.pack('<3f', *p) for p in vertices)
    document = {'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[0]}],
        'nodes':[{'name':'Track_Surface_fixture','mesh':0}],
        'meshes':[{'primitives':[{'attributes':{'POSITION':0},'mode':4}]}],
        'buffers':[{'byteLength':len(binary)}],
        'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':len(binary),'target':34962}],
        'accessors':[{'bufferView':0,'componentType':5126,'count':len(vertices),'type':'VEC3',
            'min':[-7,0,0],'max':[7,5 if wall else 0,1100]}]}
    payload=json.dumps(document).encode()
    payload += b' '*((-len(payload))%4)
    path.write_bytes(struct.pack('<III',0x46546C67,2,12+8+len(payload)+8+len(binary)) + struct.pack('<II',len(payload),0x4E4F534A)+payload+struct.pack('<II',len(binary),0x004E4942)+binary)


@pytest.mark.parametrize('case,expected,reason',[
    ('valid',0,'completed'), ('gap',1,'lost road support'),
    ('wall',1,'blocked'), ('short',1,'too short'),
])
def test_jolt_traversal(tmp_path, case, expected, reason):
    glb=tmp_path/'road.glb'
    write_road(glb, gap=case=='gap', wall=case=='wall')
    manifest=tmp_path/'road.json'
    manifest.write_text(json.dumps({'coordinate_system':'Y_UP_METERS',
        'tracks':[{'points':[[0,0,0],[0,0,900 if case=='short' else 1100]]}],
        'physics_contracts':{'engine':'JOLT_3D','max_physics_tick_ms':4.0}}))
    report=tmp_path/'report.json'
    result=subprocess.run([str(GODOT),'--headless','--fixed-fps','60','--path',str(ENGINE/'physics'),
        '--log-file',str(tmp_path/'godot.log'),'--script',str(ENGINE/'godot_audit_physics.gd'),
        '--',str(glb),str(manifest),'1000',str(report)],capture_output=True,text=True,timeout=20)
    assert report.is_file(), result.stdout+result.stderr
    data=json.loads(report.read_text())
    assert result.returncode==expected, data
    assert reason in data['reason'], data
    if expected==0:
        assert data['route_progress_m']>=1000
        assert data['distance_driven_m']>=1000
        assert data['max_physics_tick_ms']<=4.0
