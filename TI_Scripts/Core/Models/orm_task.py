from dataclasses import dataclass
from TI_Scripts.Core.Models.texture_asset import TextureAsset

@dataclass
class ORMTask:
    ao: TextureAsset | None
    roughness: TextureAsset | None
    metallic: TextureAsset | None
    generated_texture : TextureAsset | None = None