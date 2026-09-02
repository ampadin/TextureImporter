# Texture Importer for Unreal Engine

An Unreal Engine editor plugin that scans a folder of PBR texture sets, detects material
groups automatically, generates a packed ORM (AO/Roughness/Metallic) texture via
Pillow, imports everything with the correct engine-side settings, and optionally
creates a Material Instance per detected material — all driven from a single Editor
Utility Widget.

Designed to automate a repetitive texture import workflow and to demonstrate a clean separation between engine‑agnostic logic and Unreal‑specific integration.

![Gif Example](https://dri.me/VDMbqn4TjzOgGOXBnXrnQd8EWwDYD0)

## Index
1. [Why this exists](#why-this-exists)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Project structure](#project-structure)
6. [Configuration](#configuration)
7. [Usage](#usage)
8. [Architecture](#architecture)
9. [Testing](#testing)
10. [Known limitations](#known-limitations)
11. [License](#license)


## Why this exists

Manually importing a batch of PBR textures into Unreal is repetitive: setting the
right compression and sRGB flags per channel, creating a consistent folder structure,
renaming every file to match a naming convention, and packing AO/Roughness/Metallic
into a single ORM texture by hand — especially when several materials in the same
batch all need the exact same configuration.

This tool automates that pass end to end. It never modifies your original source
textures — they're only read, never written to, which acts as a safety net against
accidentally corrupting source art. It builds the destination folder structure
automatically. And when the individual AO, Roughness, or Metallic maps aren't
available for a material, it packs a usable ORM texture on the fly with Pillow,
falling back to sensible defaults for whichever channel is missing. Generated ORM
textures are written to a `_Generated` subfolder inside the selected source directory.

## Features

- Automatic material grouping from a flat folder of texture files, based on
  configurable naming conventions
- Configurable texture-type detection via alias lists (`texture_rules.json`) —
  supports arbitrary suffixes/prefixes used by different texture sources
- ORM (Ambient Occlusion / Roughness / Metallic) packing via Pillow, with automatic
  fallback to a default ORM texture when one or more channels are missing
- Optional import of AO, Roughness, Metallic, Opacity, and Emissive as individual
  textures, on top of BaseColor / Normal / Height / ORM which are always imported
- Correct per-channel Unreal import settings (sRGB, compression) applied
  automatically based on texture type, including an optional green-channel flip
  for normal maps authored with the OpenGL convention
- Optional Material Instance creation, with automatic detection of the Master
  Material's texture parameters — color-coded in the widget so you can spot and
  fix anything that wasn't matched confidently (see [Usage](#usage))
- Editor Utility Widget front-end: pick a source folder, adjust options, import
- Configuration entirely driven by JSON files — no code changes needed for most
  naming/behavior tweaks
- Available per-run `.txt` log written to `Saved/TextureImporter/Logs/`

## Requirements

- Unreal Engine 5.3+ (developed/tested against the Interchange import pipeline)
- Python Editor Script Plugin enabled (`Edit > Plugins > Python Editor Script Plugin`)
- Pillow is bundled with the plugin under `Resources/ThirdParty/` — no separate
  `pip install` is required. This is intentional: Unreal ships its own embedded
  Python interpreter, separate from your system Python, and it doesn't have
  internet-based `pip` installs enabled by default. Installing a package into it
  normally means locating Unreal's own `python.exe` and running `pip` against it
  manually. Vendoring Pillow directly avoids that step — the plugin works out of
  the box.

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
5. Run the Editor Utility Widget from
   `Plugins/TextureImporter/EUW_TextureImporter`
   (`Right click > Run Editor Utility Widget`). Keep the Editor Utility Widget inside the
   plugin's own Content folder. The Python integration relies on this relative path, and moving the widget will prevent the scripts from being located correctly.

### If something stops responding after a change

This plugin is Python-based: Blueprint nodes are generated from the `.py` files at
editor startup rather than compiled ahead of time like C++. Two different things
can go stale, and they need two different fixes — this applies to you as a user
pulling an update, and even more so if you're editing the plugin's own code:

- **A node looks broken, greyed out, or is missing its pins** — this means a
  function's *signature* changed (a new parameter was added, a return type
  changed). Fix: open the widget's graph, select all nodes (`Ctrl+A`), right-click
  → **Refresh Nodes**.
- **A node runs without errors but the result looks wrong, outdated, or nothing
  happens** — this means the *internal logic* of a `.py` file changed, which
  Refresh Nodes does not pick up. Fix: fully close and reopen the editor. This is
  the single most common thing to try if the plugin ever behaves unexpectedly
  after an update.

## Project structure

```
TextureImporter/
├── Content/
│   ├── Python/
│   │   └── init_unreal.py            # sets up sys.path and registers the Blueprint Function Library
│   └── EUW_TextureImporter.uasset    # the Editor Utility Widget the user runs
├── Resources/
│   ├── ThirdParty/PIL/                # vendored Pillow (includes its own LICENSE)
│   └── T_Default_ORM.PNG              # fallback ORM texture
├── TI_Scripts/
│   ├── Config/
│   │   ├── plugin_settings.json          # default paths and import options
│   │   ├── naming_rules.json             # destination prefix/suffixes
│   │   ├── texture_rules.json            # detection aliases per texture type
│   │   └── material_parameter_rules.json # aliases/prefixes for auto-detecting Master Material parameters
│   ├── Core/                          # engine-agnostic logic (pure Python, no `unreal` based)
│   │   ├── Models/                     # dataclasses: MaterialJob, TextureAsset, ImportOptions...
│   │   └── Python/                      # scanning, grouping, naming, ORM building, pipeline
│   └── Unreal/                        # Unreal-specific integration layer
│       ├── ue_entry.py                 # orchestrates Core + Unreal, entry point (`execute`)
│       ├── importer.py                 # AssetImportTask handling, texture configuration
│       ├── material_instancer.py       # Material Instance creation
│       ├── material_parameters.py      # Master Material parameter auto-detection
│       ├── editor_api.py               # thin, Blueprint-friendly wrapper functions
│       └── ti_blueprint_library.py     # exposes editor_api functions as Blueprint nodes
└── TextureImporter.uplugin
```

## Configuration

All behavior is controlled through four JSON files in `TI_Scripts/Config/`. **These
are starting conventions, not a fixed spec** — every list of aliases or suffixes
below is meant to be extended. If your studio or your own asset library uses a
naming pattern that isn't in here (a different suffix, a different word for
"roughness", a Master Material with parameters named some other way), add it —
nothing in the code needs to change, only these files.

**`plugin_settings.json`** — default paths and import options:

```json
{
    "masterMaterial": "/Game/Shaders/Materials/M_Master_01.M_Master_01",
    "createORM": true,
    "importAO": false,
    "importRoughness": false,
    "importMetallic": false,
    "importOpacity": false,
    "importEmissive": false,
    "flipGreen": false,
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

- `flipGreen` flips the green channel on imported normal maps — enable it if your
  source textures were authored for the OpenGL normal-map convention (common
  outside Unreal) rather than Unreal's native DirectX convention. If your normal
  maps look inverted after import, this is usually why.
- `materialParameters` is the **fallback** mapping used only when a texture
  parameter can't be automatically matched on your Master Material (see
  `material_parameter_rules.json` below and [Usage](#usage)) — it maps a texture
  type to the name of the corresponding parameter.

**`naming_rules.json`** — controls the destination asset name (`T_<Material>_<Suffix>`):

```json
{
    "prefix": "T_",
    "suffixes": { "BaseColor": "A", "Normal": "N", "ORM": "ORM", "Height": "H", ... }
}
```

**`texture_rules.json`** — controls how a **source filename** maps to a texture
type. Each entry is a list of lowercase aliases checked against filename tokens:

```json
{
    "BaseColor": ["basecolor", "albedo", "diffuse", "color", "bc", "a", "d"],
    "Normal": ["normal", "normalmap", "nor", "nrm", "n"],
    ...
}
```

> Single-character aliases (`a`, `n`, `r`, `m`, `h`...) are convenient but can
> collide with each other on ambiguous filenames. If you rely on short suffixes,
> test your naming convention against the detector before trusting it on a large
> library — see [Known limitations](#known-limitations).

**`material_parameter_rules.json`** — controls how a **Master Material's texture
parameter name** is automatically matched to a texture type, independently from
the filename rules above:

```json
{
    "parameterAliases": {
        "BaseColor": ["basecolor", "albedo", "a01", "color", "bc", "diffuse"],
        "Normal": ["normal", "normalmap", "normal_map", "nrm", "n01"],
        ...
    },
    "parameterPrefixes": ["texture", "tex", "t"]
}
```

`parameterPrefixes` are stripped from the start of a parameter name before
matching, so `T_BaseColor`, `Tex_BaseColor`, and `BaseColor` all match the same
`basecolor` alias. If your Master Material uses parameter names that don't match
anything here, either add them to `parameterAliases`, or just type the correct
name directly in the widget — see Usage below.

## Usage

1. Open the Editor Utility Widget
2. Click **Browse** and pick the folder containing your source textures
3. Adjust Texture Destination, Material Destination, and the options (Create
   Material Instance, Create ORM Texture, Overwrite, Flip Green Channel,
   per-channel import toggles for AO/Roughness/Metallic/Opacity/Emissive) — they
   default to the values in `plugin_settings.json`
4. Pick (or type) a **Master Material**. This automatically scans its texture
   parameters and tries to match each one to a texture type, filling in the
   parameter-name fields below. Each field is color-coded to show the result:
   - **Blue** — a confident match was found, or a name you typed yourself matches
     a real parameter on the material
   - **Orange** — multiple possible matches were found on the material and one
     was picked automatically; worth double-checking
   - **Yellow** — no match was found; the field is either empty or showing the
     fallback value from `plugin_settings.json`
   - **Red** — the name typed in this field doesn't exist as a texture parameter
     on the selected Master Material
   Any warnings from this scan (e.g. which parameters were ambiguous) also show
   up in the Status field immediately, before you import. This whole step only
   matters if **Create Material Instance** is enabled — a texture whose parameter
   field is orange, yellow, or red may not get assigned correctly.
5. Click **Import**
6. Read the result in the Status field; a full log is also written to
   `Saved/TextureImporter/Logs/`

## Architecture

The plugin is split into two independent layers:

- **`Core`** contains all the logic — scanning, material grouping, texture-type
  detection, naming, ORM generation — as plain Python with no dependency on the
  `unreal` module. It operates purely on `pathlib.Path` and Pillow.
- **`Unreal`** is a thin integration layer that turns `Core` output into engine
  calls (`AssetImportTask`, `MaterialInstanceConstant`, `MaterialEditingLibrary`,
  etc.) and exposes a small, Blueprint-friendly API (`ti_blueprint_library.py`)
  via `unreal.BlueprintFunctionLibrary`, so the Editor Utility Widget never
  touches Python objects directly — only primitive types (str/bool/int/array) as
  individual function calls.

This separation means the `Core` layer can, in principle, be reused to build an
importer for a different engine or DCC tool by writing a new integration layer
against the same `Core` API. **This has not been implemented or tested** — the only
existing integration is Unreal. Treat the multi-engine angle as a structural choice
made with that goal in mind, not as a proven capability.

## Testing

All functionality has been tested manually, both inside the editor and through
direct execution of the Python modules: the full import flow, ORM generation and
its fallback logic, Master Material parameter auto-detection (including ambiguous
and unmatched cases), Material Instance creation, overwrite behavior, and
error/warning handling across multiple material configurations.

The `Core` layer has no dependency on `unreal`, which makes it suitable for automated testing (e.g., pytest). a test suite is planned for the future.

## Known limitations

- **Synchronous import.** A large batch will block the editor UI for the duration
  of the import, with no progress bar. For big libraries, import in smaller batches.
- **No automated test suite** for the `Core` layer yet (see Testing above).
- **Single-letter texture aliases** can produce false-positive type detection on
  ambiguous filenames (see [Configuration](#configuration)).
- **Folder scan is not recursive** — only files directly inside the selected source
  folder are considered. A recursive mode exists in the codebase but is intentionally disabled.
- **Parameter auto-detection assumes one parameter per texture type.** Master
  Materials with multiple texture sets (e.g. `A_01`/`A_02`/`A_03`...) will only
  have their first matching set auto-detected; additional sets require manual
  setup and aren't assigned by Material Instance creation.
- Tested primarily on Windows / UE 5.7. Not verified on macOS or Linux.

## License

This project is licensed under the [MIT License](LICENSE).

It bundles [Pillow](https://python-pillow.org/) under `Resources/ThirdParty/PIL/`,
licensed under the MIT-CMU License — see the `LICENSE` file included in that folder.
