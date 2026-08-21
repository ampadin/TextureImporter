from pathlib import Path

from TI_Scripts.Core.Models.import_options import ImportOptions
from TI_Scripts.Core.Models.enums import JobStatus

from TI_Scripts.Unreal.ue_entry import execute, get_default_import_options, write_last_import_log as write_last_import_log_impl

# ------------------------------------------------------------------
# Defaults: se cargan una sola vez por sesión de editor y se cachean.
# ------------------------------------------------------------------
_defaults_cache: dict | None = None

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

def get_default_create_orm() -> bool:
    return _get_defaults()["create_orm"]

def get_default_import_ao() -> bool:
    return _get_defaults()["import_ao"]

def get_default_import_roughness() -> bool:
    return _get_defaults()["import_roughness"]

def get_default_import_metallic() -> bool:
    return _get_defaults()["import_metallic"]

def get_default_overwrite() -> bool:
    return _get_defaults()["overwrite"]

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
    overwrite: bool,
) -> bool:
    """
    Runs the import with the values given by the EUW. 
    Returns only the overall success; the rest of the result data is queried afterward with get_last_import_status_text().
    """

    global _last_result_summary

    options = ImportOptions(
        master_material=master_material,
        create_material_instance=create_material_instance,
        create_orm=create_orm,
        import_ao=import_ao,
        import_roughness=import_roughness,
        import_metallic=import_metallic,
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
