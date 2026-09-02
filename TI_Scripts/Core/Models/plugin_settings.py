from dataclasses import dataclass

@dataclass(slots= True) #slots=True to prevent accidental new attributes and keep the object closed
class PluginSettings:
    master_material : str
    create_material_instance: bool

    create_orm: bool
    import_ao: bool
    import_roughness: bool
    import_metallic: bool
    import_emissive: bool
    import_opacity:bool
    
    flip_green: bool
    overwrite: bool
    save_assets: bool

    supported_extensions: list[str]

    material_parameters: dict[str,str]
    material_destination: str
    texture_destination:str