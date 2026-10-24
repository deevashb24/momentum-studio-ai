import json
from pathlib import Path

import pytest
from engine.asset_snapper import AssetCatalog, TrackPath, intersects_corridor, sample_spline, to_blender


def straight():
    return {"type": "POLY", "points": [{"co": [0, 0, 0]}, {"co": [0, 0, 100]}]}


def test_bezier_handles_and_endpoints():
    spline = {"type": "BEZIER", "points": [
        {"co": [0, 0, 0], "handle_right": [20, 0, 0]},
        {"co": [0, 0, 40], "handle_left": [20, 0, 40]}]}
    samples = sample_spline(spline)
    assert samples[0] == (0, 0, 0)
    assert samples[-1] == (0, 0, 40)
    assert max(p[0] for p in samples) > 14
    assert TrackPath(spline).length > 40


def test_arc_length_and_frame():
    path = TrackPath(straight())
    assert path.length == 100
    point, tangent, right = path.at(53)
    assert point == pytest.approx((0, 0, 53))
    assert tangent == (0, 0, 1)
    assert right == (1, 0, 0)
    assert to_blender((2, 3, 4)) == (2, -4, 3)


def test_bounds_catch_edge_when_center_is_outside():
    path = TrackPath(straight())
    assert intersects_corridor(((31, 0, 40), (60, 90, 50)), [(path, 32)])
    assert not intersects_corridor(((33, 0, 40), (60, 90, 50)), [(path, 32)])
    assert intersects_corridor(((-1, -1, 49), (1, 1, 51)), [(path, 32)])


def test_closed_and_degenerate_tracks():
    spline = straight()
    spline['closed'] = True
    assert sample_spline(spline)[-1] == (0, 0, 0)
    with pytest.raises(ValueError):
        sample_spline({"points": [{"co": [0, 0, 0]}, {"co": [0, 0, 0]}]})
    with pytest.raises(ValueError):
        sample_spline({**straight(), "type": "NURBS"})


def test_catalog_prefers_glb_and_rejects_escape(tmp_path):
    assets = tmp_path/'assets'
    assets.mkdir()
    for ext in ('fbx', 'glb'):
        (assets/f'model.{ext}').touch()
    catalog_file = assets/'asset_catalog.json'
    entries = [{"name": "model", "format": ext.upper(), "relative_path": f"assets/model.{ext}"} for ext in ('fbx','glb')]
    catalog_file.write_text(json.dumps({"categories": {"roads": entries}}))
    assert AssetCatalog(tmp_path).resolve('roads', 'model').suffix == '.glb'
    (assets/'model.glb').unlink()
    assert AssetCatalog(tmp_path).resolve('roads', 'model').suffix == '.fbx'
    entries[0]['relative_path'] = '../outside.fbx'
    catalog_file.write_text(json.dumps({"categories": {"roads": entries}}))
    with pytest.raises(ValueError):
        AssetCatalog(tmp_path).resolve('roads', 'model')


def test_real_catalog_resolves_requested_models():
    catalog = AssetCatalog(Path(__file__).resolve().parents[2])
    for category, name in [('roads', 'light-square-double'), ('roads', 'road-driveway-double'), ('industrial_megatowers', 'detail-tank')]:
        assert catalog.resolve(category, name).is_file()
