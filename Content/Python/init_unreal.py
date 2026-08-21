import sys
from pathlib import Path
import unreal

PLUGIN_ROOT = Path(unreal.Paths.project_plugins_dir()) / "TextureImporter"
THIRD_PARTY = PLUGIN_ROOT / "Resources" / "ThirdParty"

for path in (PLUGIN_ROOT, THIRD_PARTY):
    path = str(path)
    if path not in sys.path:
        sys.path.insert(0, path)

from TI_Scripts.Unreal import ti_blueprint_library

unreal.log(f"TextureImporter ready: {PLUGIN_ROOT}")