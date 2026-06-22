"""
Tests for tools.hda (HDA creation, python module, event scripts, dynamic parms).

    python test_hda.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
PASS = "\033[32mOK\033[0m"
FAIL = "\033[31mFAIL\033[0m"
SKIP = "\033[33mSKIP\033[0m"
errors = []

def check(label, fn):
    try:
        fn()
        print("  " + label.ljust(50) + " " + PASS)
    except Exception as e:
        print("  " + label.ljust(50) + " " + FAIL + "  " + str(e))
        errors.append((label, e))

def skip(label, reason):
    print("  " + label.ljust(50) + " " + SKIP + "  " + reason)

print("\n=== HDA Imports (no hou) ===")
def _imp():
    from lh_houdini_pipeline.houdini import hda
check("import hda module without hou", _imp)

try:
    import hou
    _HAS_HOU = True
except ImportError:
    _HAS_HOU = False

if _HAS_HOU:
    print("\n=== Live HDA Packaging Tests (inside Houdini) ===")
    def _test_hda_packaging():
        import tempfile
        from lh_houdini_pipeline.houdini import hda
        
        # 1. Create a subnet node in /obj
        obj = hou.node("/obj")
        subnet = obj.createNode("subnet", "temp_subnet_for_test")
        
        # 2. Convert to HDA
        hda_path = os.path.join(tempfile.gettempdir(), "test_pipeline_hda.hda").replace("\\", "/")
        definition = hda.create_hda_from_subnet(
            subnet_node=subnet,
            hda_path=hda_path,
            asset_name="test_pipeline_hda",
            asset_label="Test Pipeline HDA"
        )
        assert definition is not None, "Failed to create HDA definition"
        
        # 3. Create dynamic ParmTemplateGroup
        ptg = hou.ParmTemplateGroup()
        ptg.append(hou.ButtonParmTemplate("my_button", "Click Me"))
        ptg.append(hou.FloatParmTemplate("my_float", "My Float", 1))
        ok_ptg = hda.set_hda_parm_template_group(definition, ptg)
        assert ok_ptg, "Failed to set ParmTemplateGroup"
        
        # 4. Set Python HDA Module
        phm_code = (
            "def initialize_node(node):\n"
            "    node.parm('my_float').set(42.0)\n"
        )
        ok_phm = hda.set_hda_python_module(definition, phm_code)
        assert ok_phm, "Failed to set Python Module"
        
        # 5. Set OnCreated event handler
        on_created_code = (
            "node = kwargs['node']\n"
            "node.hdaModule().initialize_node(node)\n"
        )
        ok_event = hda.set_hda_event_script(definition, "OnCreated", on_created_code)
        assert ok_event, "Failed to set OnCreated event handler"
        
        # 6. Save and reload HDA
        ok_save = hda.save_and_reload_hda(definition)
        assert ok_save, "Failed to save and reload HDA"
        
        # 7. Clean up original subnet node (which was converted to the HDA type)
        hou.node("/obj/temp_subnet_for_test").destroy()
        
        # 8. Instantiate HDA to verify
        node = obj.createNode("test_pipeline_hda", "my_pipeline_hda_inst")
        assert node is not None, "Failed to instantiate HDA"
        
        # 9. Verify dynamic parameters exist
        assert node.parm("my_button") is not None, "Dynamic button parameter not found"
        assert node.parm("my_float") is not None, "Dynamic float parameter not found"
        
        # 10. Verify OnCreated triggered and PythonModule code was executed (value set to 42.0)
        val = node.parm("my_float").eval()
        assert val == 42.0, f"OnCreated callback did not execute correctly, value is: {val}"
        
        # 11. Clean up HDA node and file
        node.destroy()
        hou.hda.uninstallFile(hda_path)
        if os.path.exists(hda_path):
            os.remove(hda_path)
            
    check("complete HDA packaging pipeline", _test_hda_packaging)
else:
    skip("complete HDA packaging pipeline", "hou not available")

print("\n=== Summary ===")
if errors:
    print("  " + str(len(errors)) + " FAILED")
    for label, e in errors:
        print("    - " + label + ": " + str(e))
    sys.exit(1)
print("  All HDA assertions passed.")
sys.exit(0)
