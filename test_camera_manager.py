"""
Tests for tools.camera_manager (pure spec + parm mapping). Outside Houdini.

    python test_camera_manager.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
PASS="\033[32mOK\033[0m"; FAIL="\033[31mFAIL\033[0m"; errors=[]
def check(label, fn):
    try: fn(); print("  "+label.ljust(50)+" "+PASS)
    except Exception as e: print("  "+label.ljust(50)+" "+FAIL+"  "+str(e)); errors.append((label,e))

print("\n=== imports (no hou) ===")
def _imp():
    from lh_houdini_pipeline.tools.camera_manager import (
        CameraSpec, CameraContext, ResolutionPreset, spec_from_preset,
        create_camera, list_cameras)
    from lh_houdini_pipeline.tools.camera_manager import service
check("camera_manager imports without hou", _imp)

from lh_houdini_pipeline.tools.camera_manager import (
    CameraSpec, CameraContext, ResolutionPreset, spec_from_preset)

print("\n=== presets ===")
def _preset_dims():
    assert ResolutionPreset.HD1080.width==1920 and ResolutionPreset.HD1080.height==1080
    assert abs(ResolutionPreset.HD1080.aspect-0.5625) < 1e-6
check("ResolutionPreset dims/aspect", _preset_dims)

print("\n=== OBJ parm mapping ===")
def _obj_parms():
    spec=spec_from_preset("camA", ResolutionPreset.HD1080, focal_length=35.0, fstop=2.8)
    p=spec.to_parms(CameraContext.OBJ)
    assert p["focal"]==35.0 and p["fstop"]==2.8
    assert p["aperture"]==41.4214
    assert p["resx"]==1920 and p["resy"]==1080
    assert "near" in p and "far" in p and "focus" in p
    # OBJ mapping must NOT use USD parm names
    assert "focalLength" not in p
check("OBJ cam parms (focal/aperture/resx/resy)", _obj_parms)

print("\n=== Stage (USD) parm mapping ===")
def _stage_parms():
    spec=spec_from_preset("camB", ResolutionPreset.HD1080, focal_length=85.0)
    p=spec.to_parms(CameraContext.STAGE)
    assert p["focalLength"]==85.0
    assert p["horizontalAperture"]==41.4214
    assert "clippingRange1" in p and "clippingRange2" in p
    assert "fStop" in p and "focusDistance" in p
    # USD camera carries no resolution
    assert "resx" not in p and "resolution" not in p
check("USD camera parms (focalLength/clippingRange/...)", _stage_parms)

def _vertical_aperture_derived():
    spec=spec_from_preset("camC", ResolutionPreset.HD1080)  # 16:9
    p=spec.to_parms(CameraContext.STAGE)
    # vertical = horizontal * 1080/1920
    expected = 41.4214 * (1080/1920)
    assert abs(p["verticalAperture"]-expected) < 1e-6, p["verticalAperture"]
check("vertical aperture derived from aspect", _vertical_aperture_derived)

def _explicit_vertical():
    spec=CameraSpec(name="x", vertical_aperture=24.0)
    assert spec.effective_vertical_aperture()==24.0
check("explicit vertical aperture honoured", _explicit_vertical)

def _square_default_vertical():
    spec=CameraSpec(name="x")  # no resolution, no vertical
    assert spec.effective_vertical_aperture()==spec.horizontal_aperture
check("no resolution -> vertical == horizontal", _square_default_vertical)
print("\n=== merge planning (pure) ===")
from lh_houdini_pipeline.tools.camera_manager import CameraTiming, plan_merge, TurntableSpec

def _merge_two_animated():
    plan = plan_merge([CameraTiming("A",1,10), CameraTiming("B",5,8)], start_frame=1001)
    segs = {s.name: s for s in plan.segments}
    # A first (start 1): offset 1000, dst 1001..1010
    assert segs["A"].offset==1000 and segs["A"].dst_start==1001 and segs["A"].dst_end==1010, segs["A"]
    # B next: starts at 1011, offset 1011-5=1006, dst 1011..1014
    assert segs["B"].dst_start==1011 and segs["B"].offset==1006 and segs["B"].dst_end==1014, segs["B"]
    assert plan.end_frame==1014, plan.end_frame
check("merge: two animated cams placed end-to-end", _merge_two_animated)

def _merge_static_after_animated():
    plan = plan_merge([CameraTiming("stat"), CameraTiming("anim",1,5)], start_frame=1001)
    segs = {s.name: s for s in plan.segments}
    # animated first (1001..1005), static occupies single frame 1006
    assert segs["anim"].dst_start==1001 and segs["anim"].dst_end==1005
    assert segs["static" if "static" in segs else "stat"].is_static
    assert segs["stat"].dst_start==1006 and segs["stat"].dst_end==1006, segs["stat"]
    assert plan.end_frame==1006
check("merge: static camera placed after animated", _merge_static_after_animated)

def _turntable_angles():
    tt = TurntableSpec(total_frames=120, start_frame=1)
    assert tt.angle_at(0)==0.0
    assert tt.angle_at(60)==180.0
    assert tt.angle_at(120)==360.0
    assert tt.frame_numbers()[0]==1 and tt.frame_numbers()[-1]==120
check("turntable: angle_at sweeps 0..360", _turntable_angles)

def _turntable_orbit_math():
    from lh_houdini_pipeline.tools.camera_manager import turntable_transforms, TurntableSpec
    import math
    tt = TurntableSpec(total_frames=120, start_frame=1, pitch_deg=20.0)
    keys = turntable_transforms(tt, center=(0.0,0.0,0.0), radius=10.0)
    assert len(keys)==120, len(keys)
    k0 = keys[0]
    # frame 0: angle 0 -> at +Z, ry 0, rx -pitch, height = 10*tan(20)
    assert k0.frame==1 and abs(k0.tx-0.0)<1e-6 and abs(k0.tz-10.0)<1e-6, k0
    assert abs(k0.ry-0.0)<1e-6 and abs(k0.rx+20.0)<1e-6
    assert abs(k0.ty - 10.0*math.tan(math.radians(20.0))) < 1e-6
    k30 = keys[30]   # angle 90 -> at +X, ry 90, tz ~ 0
    assert abs(k30.ry-90.0)<1e-6 and abs(k30.tx-10.0)<1e-6 and abs(k30.tz-0.0)<1e-6, k30
check("turntable: orbit transform math (pos/ry/pitch)", _turntable_orbit_math)

print("\n=== camera exporting ===")
def _camera_frame_data():
    from lh_houdini_pipeline.tools.camera_manager import CameraFrameData
    fd = CameraFrameData(
        frame=1001, tx=1.0, ty=2.0, tz=3.0, rx=10.0, ry=20.0, rz=30.0,
        focal=35.0, haperture=24.0, vaperture=18.0, near=0.1, far=1000.0,
        fstop=5.6, focus=5.0
    )
    assert fd.frame == 1001
    assert fd.tx == 1.0
    assert fd.focal == 35.0
check("CameraFrameData structure", _camera_frame_data)

def _nuke_camera_writer():
    import tempfile, os
    from lh_houdini_pipeline.tools.camera_manager import CameraFrameData, write_nuke_camera_script
    fd1 = CameraFrameData(
        frame=1001, tx=0.0, ty=0.0, tz=10.0, rx=0.0, ry=0.0, rz=0.0,
        focal=35.0, haperture=10.0, vaperture=10.0, near=0.1, far=1000.0,
        fstop=5.6, focus=5.0
    )
    fd2 = CameraFrameData(
        frame=1002, tx=1.0, ty=0.0, tz=10.0, rx=0.0, ry=10.0, rz=0.0,
        focal=35.0, haperture=10.0, vaperture=10.0, near=0.1, far=1000.0,
        fstop=5.6, focus=5.0
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        nk_file = os.path.join(tmpdir, "test_camera.nk")
        ok = write_nuke_camera_script("NukeCam", [fd1, fd2], nk_file)
        assert ok
        assert os.path.exists(nk_file)
        
        with open(nk_file, "r") as f:
            content = f.read()
            
        assert "Camera2 {" in content
        assert "translate {{ curve x1001 0.000000 x1002 1.000000 } { curve x1001 0.000000 x1002 0.000000 } { curve x1001 10.000000 x1002 10.000000 }}" in content
        assert "rotate {{ curve x1001 0.000000 x1002 0.000000 } { curve x1001 0.000000 x1002 10.000000 } { curve x1001 0.000000 x1002 0.000000 }}" in content
        assert "focal {{ curve x1001 35.000000 x1002 35.000000 }}" in content
        assert "rot_order XYZ" in content
check("write_nuke_camera_script output", _nuke_camera_writer)

print("\n=== camera variants ===")
def _camera_variants():
    from lh_houdini_pipeline.tools.camera_manager import CameraVariantSpec, VariantSetSpec
    v1 = CameraVariantSpec("wide", 24.0)
    v2 = CameraVariantSpec("front", 50.0, tx=0.0, ty=0.0, tz=10.0)
    vset = VariantSetSpec("lens", (v1, v2))
    assert vset.name == "lens"
    assert len(vset.variants) == 2
    assert vset.variants[0].focal_length == 24.0
    assert vset.variants[1].tz == 10.0
check("CameraVariantSpec & VariantSetSpec structure", _camera_variants)

try:
    import hou
    _HAS_HOU = True
except ImportError:
    _HAS_HOU = False

if _HAS_HOU:
    def _stage_variants():
        import hou
        from lh_houdini_pipeline.tools.camera_manager import service, CameraSpec, CameraContext, CameraVariantSpec
        
        # Clear/Create temp test camera
        spec = CameraSpec(name="test_var_cam", focal_length=50.0)
        cam_path = service.create_camera(spec, context=CameraContext.STAGE, force=True)
        assert cam_path == "/stage/test_var_cam"
        
        # Create variants
        variants = [
            CameraVariantSpec("wide", 24.0),
            CameraVariantSpec("medium", 50.0),
        ]
        ok = service.create_camera_variants(cam_path, "lens", variants)
        assert ok
        
        # Verify node existence
        python_lop = hou.node("/stage/variants_test_var_cam_lens")
        assert python_lop is not None
        
        # Clean up
        hou.node(cam_path).destroy()
        python_lop.destroy()
    check("create stage variants (lens)", _stage_variants)


print("\n=== summary ===")
if errors:
    print("  "+str(len(errors))+" FAILED"); [print("    - "+l+": "+str(e)) for l,e in errors]; sys.exit(1)
print("  All camera_manager assertions passed."); sys.exit(0)

