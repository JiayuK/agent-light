# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Agent Light.app with bundled hook CLIs."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None
root = Path(SPEC).resolve().parent.parent
assets = [(str(root / "agent_light" / "assets"), "agent_light/assets")]

pyobjc_hidden = [
    "AppKit",
    "Foundation",
    "Quartz",
    "Cocoa",
    "objc",
    "PyObjCTools",
    "PyObjCTools.AppHelper",
    "psutil",
    "PIL",
    "PIL.Image",
]
hiddenimports = pyobjc_hidden + collect_submodules("agent_light")

common = dict(
    pathex=[str(root)],
    binaries=[],
    datas=assets,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a_main = Analysis([str(root / "packaging" / "entry_main.py")], **common)
a_relay = Analysis([str(root / "packaging" / "entry_relay.py")], **common)
a_hooks = Analysis([str(root / "packaging" / "entry_hooks.py")], **common)

MERGE(
    (a_main, "main", "Agent Light"),
    (a_relay, "relay", "agent-light-relay"),
    (a_hooks, "hooks", "agent-light-hooks"),
)

pyz_main = PYZ(a_main.pure, a_main.zipped_data, cipher=block_cipher)
exe_main = EXE(
    pyz_main,
    a_main.scripts,
    [],
    exclude_binaries=True,
    name="Agent Light",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)

pyz_relay = PYZ(a_relay.pure, a_relay.zipped_data, cipher=block_cipher)
exe_relay = EXE(
    pyz_relay,
    a_relay.scripts,
    [],
    exclude_binaries=True,
    name="agent-light-relay",
    debug=False,
    strip=False,
    upx=False,
    console=True,
)

pyz_hooks = PYZ(a_hooks.pure, a_hooks.zipped_data, cipher=block_cipher)
exe_hooks = EXE(
    pyz_hooks,
    a_hooks.scripts,
    [],
    exclude_binaries=True,
    name="agent-light-hooks",
    debug=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe_main,
    a_main.binaries,
    a_main.zipfiles,
    a_main.datas,
    exe_relay,
    a_relay.binaries,
    a_relay.zipfiles,
    a_relay.datas,
    exe_hooks,
    a_hooks.binaries,
    a_hooks.zipfiles,
    a_hooks.datas,
    strip=False,
    upx=False,
    name="Agent Light",
)

app = BUNDLE(
    coll,
    name="Agent Light.app",
    icon=None,
    bundle_identifier="com.agent.light",
    info_plist={
        "CFBundleName": "Agent Light",
        "CFBundleDisplayName": "Agent Light",
        "CFBundleShortVersionString": "1.1.1",
        "CFBundleVersion": "1.1.1",
        "LSMinimumSystemVersion": "12.0",
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
    },
)
