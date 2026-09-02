from pathlib import Path

from TI_Scripts.Core.Models.import_options import ImportOptions
from TI_Scripts.Core.Models.enums import JobStatus, TextureType

from TI_Scripts.Unreal.ue_entry import execute, get_default_import_options, get_material_parameter_names, write_last_import_log as write_last_import_log_impl, get_current_master_material_parameter_names

_defaults_cache: dict | None = None

_detected_parameters: dict[str, str] = {}       #Parametros de material detectados en el master Material actual. Se recalculan solo cuand ocambia el MAster MAterial en el EUW.
_detected_matched: dict[str, bool] = {}
_detected_ambiguous: dict[str, bool] = {}
_available_parameter_names: set[str] = set()
_detected_warnings: list[str] = []

def scan_master_material_parameters(master_material: str)->bool:
    """Call this whenever the Master Material selection changes in the EUW.
    Reads its texture parameters and caches them for the get_detected_*_parameter() getters below."""
    global _detected_parameters, _detected_matched, _detected_ambiguous, _available_parameter_names, _detected_warnings
    result = get_material_parameter_names(master_material)
    _detected_parameters = result["parameters"]
    _detected_matched = result["matched"]
    _detected_ambiguous = result["ambiguous"]
    _available_parameter_names = set(get_current_master_material_parameter_names(master_material))
    _detected_warnings = result["warnings"]
    return result["success"]

def is_parameter_name_valid(parameter_name: str) -> bool:
    #True if parameter_name exists as a texture parameter on the currently  scanned Master Material — for manually-typed inputs.
    return parameter_name in _available_parameter_names

def get_last_scan_warnings() ->list[str]:
    return _detected_warnings

def get_detected_parameter(texture_type:str)->str:
    #texture_type: one of BASECOLOR, NORMAL, ORM, HEIGHT, AO, ROUGHNESS, METALLIC, OPACITY, EMISSIVE
    return _detected_parameters.get(texture_type.upper(),"")

def is_parameter_matched(texture_type:str)->bool:
    #True only if the parameter for this texture type was auto-detected on the current Master Material, not a JSON fallback
    return _detected_matched.get(texture_type.upper(),False)

def is_parameter_ambiguous(texture_type:str)->bool:
     #True if this texture type had multiple real candidates and only one was kept — worth a manual check even though it's 'matched'.
    return _detected_ambiguous.get(texture_type.upper(), False)


def _get_defaults() -> dict:
    global _defaults_cache

    if _defaults_cache is None:
        _defaults_cache = get_default_import_options()
    return _defaults_cache

def get_default_master_material() -> str:
    return _get_defaults()["master_material"]

def get_default_texture_destination() -> str:
    return _get_defaults()["texture_destination"]

def get_default_material_destination() -> str:
    return _get_defaults()["material_destination"]

def get_default_create_material_instance() -> bool:
    return _get_defaults()["create_material_instance"]

def get_default_material_parameters() -> dict[str,str]:     #valors default json
    return _get_defaults().get("material_parameters", {}) 

def get_default_create_orm() -> bool:
    return _get_defaults()["create_orm"]

def get_default_import_ao() -> bool:
    return _get_defaults()["import_ao"]

def get_default_import_roughness() -> bool:
    return _get_defaults()["import_roughness"]

def get_default_import_metallic() -> bool:
    return _get_defaults()["import_metallic"]

def get_default_import_emissive() -> bool:
    return _get_defaults()["import_emissive"]

def get_default_import_opacity() -> bool:
    return _get_defaults()["import_opacity"]

def get_default_overwrite() -> bool:
    return _get_defaults()["overwrite"]

def get_default_flip_green()->bool:
    return _get_defaults()["flip_green"]

# ------------------------------------------------------------------
# Ejecución + resultado del último import, en funciones individuales
# ------------------------------------------------------------------
_last_result_summary: dict = {
    "success": False,
    "materials_processed": 0,
    "textures_imported": 0,
    "textures_skipped":0,
    "materials_instances_created": 0,
    "orm_generated": 0,
    "errors": [],
    "warnings": [],
}

def run_import(
    source_folder: str,
    texture_root: str,
    material_root: str,
    master_material: str,
    create_material_instance: bool,
    create_orm: bool,
    import_ao: bool,
    import_roughness: bool,
    import_metallic: bool,
    import_emissive: bool,
    import_opacity: bool,
    flip_green: bool,
    overwrite:  bool,
    basecolor_parameter: str = "",
    normal_parameter: str = "",
    orm_parameter: str = "",
    height_parameter: str = "",
    ao_parameter: str = "",
    roughness_parameter: str = "",
    metallic_parameter: str = "",
    emissive_parameter: str = "",
    opacity_parameter: str = "",
) -> bool:
    """
    Runs the import with the values given by the EUW. 
    Returns only the overall success; the rest of the result data is queried afterward with get_last_import_status_text().
    """
    global _last_result_summary

    material_parameters = {}
    if basecolor_parameter: material_parameters["BASECOLOR"] = basecolor_parameter
    if normal_parameter: material_parameters["NORMAL"] = normal_parameter
    if orm_parameter: material_parameters["ORM"] = orm_parameter
    if height_parameter: material_parameters["HEIGHT"] = height_parameter
    if ao_parameter: material_parameters["AO"] = ao_parameter
    if roughness_parameter: material_parameters["ROUGHNESS"] = roughness_parameter
    if metallic_parameter: material_parameters["METALLIC"] = metallic_parameter
    if opacity_parameter: material_parameters["OPACITY"] = opacity_parameter
    if emissive_parameter: material_parameters["EMISSIVE"] = emissive_parameter

    typed_material_parameters = {}
    for key, value in material_parameters.items():
        try:
            texture_type = TextureType[key]
        except KeyError:
            continue
        typed_material_parameters[texture_type] = value

    options = ImportOptions(
        master_material=master_material,
        create_material_instance=create_material_instance,
        material_parameters= typed_material_parameters or None,
        create_orm=create_orm,
        import_ao=import_ao,
        import_roughness=import_roughness,
        import_metallic=import_metallic,
        import_opacity=import_opacity,
        import_emissive=import_emissive,
        flip_green=flip_green,
        overwrite=overwrite,
    )

    results = execute(
        source_folder=Path(source_folder),
        texture_root=texture_root,
        material_root=material_root,
        options=options,
    )

    _last_result_summary = {
        "success": bool(results) and not any(r.status == JobStatus.ERROR for r in results),
        "materials_processed": sum(r.materials_processed for r in results),
        "textures_imported": sum(r.textures_imported for r in results),
        "textures_skipped": sum(r.textures_skipped for r in results),
        "materials_instances_created": sum(r.materials_instances_created for r in results),
        "orm_generated": sum(r.orm_generated for r in results),
        "errors": list(dict.fromkeys(e for r in results for e in r.errors)),
        "warnings": list(dict.fromkeys(w for r in results for w in r.warnings)),
    }
    return _last_result_summary["success"]

def get_last_import_status_text()->str:
    s =_last_result_summary
    lines = []

    if s["success"]:
        lines.append(
            f"SUCCESS: {s['materials_processed']} different materials detected, "
            f"{s['textures_imported']} textures imported, "
            f"{s['textures_skipped']} textures skipped, "
            f"{s['materials_instances_created']} material instances created, " 
            f"{s['orm_generated']} ORM generated"
    ) 
    else:
        lines.append(f"FAILED: {s['materials_processed']} materials processed")

    if s["warnings"]:
        lines.append("")
        lines.append(f"WARNINGS ({len(s['warnings'])}):")
        lines.extend(f"- {w}" for w in s["warnings"])

    if s["errors"]:
        lines.append("")
        lines.append(f"ERRORS ({len(s['errors'])}):")
        lines.extend(f"- {e}" for e in s["errors"])

    return "\n".join(lines)

def write_last_log() -> str:
    return write_last_import_log_impl(get_last_import_status_text())
