from dataclasses import dataclass, field
from pathlib import Path

from TI_Scripts.Core.Models.texture_collection import TextureCollection
from TI_Scripts.Core.Models.texture_asset import TextureAsset
from TI_Scripts.Core.Models.enums import TextureType
from TI_Scripts.Core.Models.orm_task import ORMTask

@dataclass
class MaterialJob:
    source_folder: Path
    source_files: list[Path]

    material_name: str

    master_material: str
    texture_destination: str = ""
    material_destination: str = ""

    material_instance_path: str = ""
    
    textures: TextureCollection = field(default_factory=TextureCollection)

    orm_task : ORMTask | None = None

    processing_errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generated_files: list[Path] = field(default_factory=list)


    def get(self, texture_type: TextureType) -> TextureAsset | None:
      return self.textures.get(texture_type)
            
    def set(self, texture_type: TextureType, texture: TextureAsset):

           if self.has(texture_type):               # warns when a second file of the same texture type overwrites the first
               current = self.get(texture_type)
               self.warnings.append(
                   f"Duplicate detected for {texture_type.name}: "
                   f"'{current.og_name}' replaced by '{texture.og_name}'"
               )
           self.textures.set(texture_type, texture)

    def has (self, texture_type: TextureType) -> bool:
        return self.textures.has(texture_type)

    def reset(self):
        self.textures.clear()
        self.orm_task = None
        self.material_instance_path = ""
        self.processing_errors.clear()
        self.warnings.clear()
        self.generated_files.clear()
        #self.master_material = ""