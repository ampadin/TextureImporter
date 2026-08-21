README
# Texture Importer for Unreal Engine
An Unreal Engine editor plugin that scans a folder of PBR textures, detects material
groups automatically, generates a packed ORM (AO/Roughness/Metallic) texture via
Pillow, imports everything with the correct engine-side settings, and optionally
creates a Material Instance per detected material — all driven from a single Editor
Utility Widget.

Built as a portfolio piece to demonstrate a clean separation between engine-agnostic
logic and engine-specific integration code.

## Why this exists
Manually importing a batch of PBR textures into Unreal is repetitive: setting the 
right compression and sRGB flags per channel, creating a consistent folder structure,
renaming every file to match a naming convention, and packing AO/Roughness/Metallic
into a single ORM texture by hand — especially when several materials in the same batch
all need the exact same configuration.

This tool automates that pass end to end. It never modifies your original source textures;
they're only read, never written to, which acts as a safety net against accidentally 
corrupting source art. 
It builds the destination folder structure automatically. And when the individual AO,
Roughness, or Metallic maps aren't available for a material, it packs a usable ORM texture
on the fly with Pillow, falling back to sensible defaults for whichever channel is missing.
Generated ORM textures are written to a _Generated subfolder inside the selected source directory.

## Features
- Automatic material grouping from a flat folder of texture files, based on
  configurable naming conventions
- Configurable texture-type detection via alias lists (`texture_rules.json`) —
  supports arbitrary suffixes/prefixes used by different texture sources
- ORM (Ambient Occlusion / Roughness / Metallic) packing via Pillow, with automatic
  fallback to a default ORM texture when one or more channels are missing
- Correct per-channel Unreal import settings (sRGB, compression) applied automatically
  based on texture type
- Optional Material Instance creation with automatic texture-parameter assignment
- Editor Utility Widget front-end: pick a source folder, adjust options, import
- Configuration entirely driven by JSON files — no code changes needed for most
  naming/behavior tweaks
- Per-run `.txt` log written to `Saved/TextureImporter/Logs/`

## Requirements
- Unreal Engine 5.3+
- Python Editor Script Plugin enabled (`Edit > Plugins > Python Editor Script Plugin`)
- Pillow is bundled with the plugin under `Resources/ThirdParty/`,   no separate `pip install`
  is required. This is intentional: Unreal ships its own embedded Python interpreter,
  separate from your system Python, and it doesn't have internet-based pip installs enabled by default.
  Installing a package into it normally means locating Unreal's own python.exe and
  running pip against it manually.
  Vendoring Pillow directly avoids that step — the plugin works out of the box.

## Installation

1. Copy the `TextureImporter` folder into your project's `Plugins/` directory
2. Enable the plugin from `Edit > Plugins > Project > TextureImporter`, and enable
   the Python Editor Script Plugin if it isn't already
3. Restart the editor
4. If the "TextureImporter" category doesn't show up when searching for nodes in
   Blueprint, or the Editor Utility Widget's buttons don't respond, the plugin's
   `init_unreal.py` likely didn't auto-register. Fix it once, per project:
   - `Edit > Project Settings > Plugins > Python Editor Script Plugin > Startup Scripts`
   - Add `<YourProject>/Plugins/TextureImporter/Content/Python/init_unreal.py`
   - Restart the editor
5. Run the Editor Utility Widget from Plugins/TextureImporter Content/EUW_TextureImporter.
   Keep the widget asset inside the plugin's own Content folder.

## Project structure
```
TextureImporter/
├── Content/
│   └── Python/
│       └── init_unreal.py     # sets up sys.path and registers the Blueprint Function Library
│       └── EUW_TextureImporter.uasset  # Widget for the user -> Corregir
├── Resources/
│   ├── ThirdParty/PIL/           # vendored Pillow
│   └── T_Default_ORM.PNG         # fallback ORM texture
├── TI_Scripts/
│   ├── Config/
│   │   ├── plugin_settings.json  # default paths, options, extensions
│   │   ├── naming_rules.json     # destination prefix/suffixes
│   │   └── texture_rules.json    # detection aliases per texture type
│   ├── Core/                     # engine-agnostic logic (pure Python, not `unreal` based)
│   │   ├── Models/                # dataclasses: MaterialJob, TextureAsset, ImportOptions...
│   │   └── Python/                 # scanning, grouping, naming, ORM building, pipeline
│   └── Unreal/                   # Unreal-specific integration layer
│       ├── ue_entry.py            # orchestrates Core + Unreal, entry point (`execute`)
│       ├── importer.py            # AssetImportTask handling, texture configuration
│       ├── material_instancer.py  # Material Instance creation
│       ├── editor_api.py          # thin, Blueprint-friendly wrapper functions
│       └── ti_blueprint_library.py # exposes editor_api functions as Blueprint nodes
└── TextureImporter.uplugin
```
## Configuration
All behavior is controlled through the three JSON files in `TI_Scripts/Config/`.

**`plugin_settings.json`** 		# default paths and import options:
```
{
    "masterMaterial": "/Game/Shaders/Materials/M_Master_01.M_Master_01",
    "createORM": true,
    "importAO": false,
    "importRoughness": false,
    "importMetallic": false,
    "overwrite": false,
    "saveAssets": true,
    "supportedExtensions": [".png", ".tga", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".exr"],
    "materialParameters": {
        "BASECOLOR": "A_01",
        "NORMAL": "N_01",
        "ORM": "ORM_01",
        "HEIGHT": "H_01"
    },
    "createMaterialInstance": true,
    "textureDestination": "/Game/Shaders/Textures",
    "materialDestination": "/Game/Shaders/Materials"
}
```
-> `materialParameters` maps a texture type to the name of the corresponding texture
    parameter on your Master Material — only types listed here get assigned when a
    Material Instance is created.

**`naming_rules.json`**    #controls the destination asset name (`T_<Material>_<Suffix>`):
```
{
    "prefix": "T_",
    "suffixes": { "BaseColor": "A", "Normal": "N", "ORM": "ORM", "Height": "H", ... }
}
```

**`texture_rules.json`**   #controls how a filename maps to a texture type.		    
```
{
    "BaseColor": ["basecolor", "albedo", "diffuse", "color", "bc", "a", "d"],
    "Normal": ["normal", "normalmap", "nor", "nrm", "n"],
    ...
}
```
-> Single-character aliases (`a`, `n`, `r`, `m`, `h`...) are convenient but can
   collide with each other on ambiguous filenames. If you rely on short suffixes,
   test your naming convention against the detector before trusting it on a large
   library — see [Known limitations](#known-limitations).


## Usage
1. Open the Editor Utility Widget
2. Click **Browse** and pick the folder containing your source textures
3. Adjust Texture Destination, Material Destination, Master Material, and the
   options (Create Material Instance, Create ORM Texture, Overwrite, per-channel
   import toggles) — they default to the values in `plugin_settings.json`
4. Click **Import**
5. Read the result in the Status field; a full log is also written to
   `Saved/TextureImporter/Logs/`

## Architecture
The plugin is split into two independent layers:

- **`Core`** contains all the logic — scanning, material grouping, texture-type
  detection, naming, ORM generation — as plain Python with no dependency on the
  `unreal` module. It operates purely on `pathlib.Path` and Pillow.
- **`Unreal`** is a thin integration layer that turns `Core` output into engine
  calls (`AssetImportTask`, `MaterialInstanceConstant`, etc.) and exposes a small,
  Blueprint-friendly API (`ti_blueprint_library.py`) via
  `unreal.BlueprintFunctionLibrary`, so the Editor Utility Widget never touches
  Python objects directly — only primitive types (str/bool/int/array) as individual
  function calls.

This separation means the `Core` layer can, in principle, be reused to build an
importer for a different engine or DCC tool by writing a new integration layer
against the same `Core` API. **This has not been implemented or tested** — the only
existing integration is Unreal. Treat the multi-engine angle as a structural choice
made with that goal in mind, not as a proven capability.

##Testing
All functionality has been tested manually both inside Unreal and through direct execution
of the Python modules.
The full import flow, ORM generation and fallback logic, Material Instance creation,
overwrite behavior, and error/warning handling have been validated across multiple
material configurations.

The `Core` layer fully independent from `unreal`, making it suitable for automated testing.

## Known limitations
- **Synchronous import.** A large batch will block the editor UI for the duration
  of the import, with no progress bar. For big libraries, import in smaller batches.
- **Single-letter texture aliases** can produce false-positive type detection on
  ambiguous filenames (see [Configuration]).
- **Folder scan is not recursive** — only files directly inside the selected source
  folder are considered.
- Tested primarily on Windows / UE 5.7. Not verified on macOS or Linux.

## License
This project is licensed under the [MIT License](LICENSE).   

It bundles [Pillow](https://python-pillow.org/) under `Resources/ThirdParty/PIL/`,
licensed under the [HPND License](https://github.com/python-pillow/Pillow/blob/main/LICENSE).
