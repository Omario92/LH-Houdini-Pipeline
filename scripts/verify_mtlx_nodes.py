"""
Verify the Houdini MaterialX node-type assumptions used by
``lh_houdini_pipeline.materialx.builder`` against the local Houdini build.

Run with hython (no UI needed)::

    "C:/Program Files/Side Effects Software/Houdini 21.0.631/bin/hython.exe" ^
        "E:/OneDrive/Documents/Claude/Projects/LH Houdini Pipeline/scripts/verify_mtlx_nodes.py"

or paste into the Houdini Python Shell.

It checks, without modifying anything you keep:
    * hou version
    * the mtlx* / subnet / subnetconnector node types exist in a Vop network
    * standard_surface exposes the input names builder.py wires to
    * mtlximage exposes file / signature / colorspace parms
    * mtlx* output is named "out"
A temporary matnet is created under /obj and destroyed at the end.
"""

from __future__ import annotations

import hou

OK = "[ OK ]"
NO = "[MISS]"

EXPECTED_INPUTS = [
    "base_color", "metalness", "specular_roughness", "normal",
    "emission_color", "opacity",
]
NODE_TYPES = [
    "subnet", "mtlxstandard_surface", "mtlximage",
    "mtlxnormalmap", "mtlxdisplacement", "subnetconnector",
]
IMAGE_PARMS = ["file", "signature", "filecolorspace", "colorspace"]


def main() -> None:
    print("Houdini version:", hou.applicationVersionString())

    # A matnet hosts the same Vop node types used in /stage materiallibrary.
    matnet = hou.node("/obj").createNode("matnet", "lh_verify_tmp")
    try:
        print("\n-- node types available in matnet --")
        available = {}
        for nt in NODE_TYPES:
            try:
                n = matnet.createNode(nt)
                available[nt] = n
                print(" ", OK, nt)
            except Exception as exc:  # noqa: BLE001
                print(" ", NO, nt, "->", exc)

        surf = available.get("mtlxstandard_surface")
        if surf is not None:
            names = set(surf.inputNames())
            print("\n-- mtlxstandard_surface inputs builder.py uses --")
            for inp in EXPECTED_INPUTS:
                print(" ", OK if inp in names else NO, inp)
            print("  total inputs:", len(names))

        img = available.get("mtlximage")
        if img is not None:
            print("\n-- mtlximage parms --")
            for pm in IMAGE_PARMS:
                print(" ", OK if img.parm(pm) is not None else NO, pm)
            print("  output names:", img.outputNames())

        nmap = available.get("mtlxnormalmap")
        if nmap is not None:
            print("\n-- mtlxnormalmap --")
            print("  input names :", nmap.inputNames())
            print("  output names:", nmap.outputNames())

        disp = available.get("mtlxdisplacement")
        if disp is not None:
            print("\n-- mtlxdisplacement --")
            print("  input names :", disp.inputNames())

        conn = available.get("subnetconnector")
        if conn is not None:
            print("\n-- subnetconnector parms (connectorkind/parmname/parmtype) --")
            for pm in ["connectorkind", "parmname", "parmlabel", "parmtype"]:
                print(" ", OK if conn.parm(pm) is not None else NO, pm)
    finally:
        matnet.destroy()
        print("\nTemporary matnet removed. Verification done.")


if __name__ == "__main__":
    main()
