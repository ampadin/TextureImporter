from dataclasses import dataclass


@dataclass(slots=True)
class ImportOptions:
    master_material: str
    create_material_instance: bool = True

    create_orm: bool = True

    import_ao: bool = False
    import_roughness: bool = False
    import_metallic: bool = False
    
    overwrite: bool = False