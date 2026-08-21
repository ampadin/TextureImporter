from dataclasses import dataclass, field

from TI_Scripts.Core.Models.texture_asset import TextureAsset
from TI_Scripts.Core.Models.enums import TextureType

@dataclass

class TextureCollection:
   textures: dict[TextureType, TextureAsset] = field(default_factory=dict)

   def get(self,texture_type: TextureType)-> TextureAsset | None: return self.textures.get(texture_type)
   def set(self,texture_type: TextureType, texture: TextureAsset): self.textures[texture_type] = texture
   def has(self, textures_type: TextureType) -> bool: return textures_type in self.textures

   def clear(self): self.textures.clear()
   def items(self): return self.textures.items()
   def keys(self): return self.textures.keys()
   def values(self): return self.textures.values()
   def __contains__( self, texture_type: TextureType) -> bool: return texture_type in self.textures
   def __iter__(self): return iter(self.textures.values())
