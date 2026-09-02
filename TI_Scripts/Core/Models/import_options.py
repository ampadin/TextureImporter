from dataclasses import dataclass


@dataclass(slots=True)
class ImportOptions:
    master_material: str
    create_material_instance: bool = True
    material_parameters: dict[str,str] | None = None

    create_orm: bool = True

    import_ao: bool = False
    import_roughness: bool = False
    import_metallic: bool = False
    import_emissive: bool = True
    import_opacity: bool = True

    flip_green: bool = False
    
    overwrite: bool = False