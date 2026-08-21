from dataclasses import dataclass
from pathlib import Path
from TI_Scripts.Core.Models.enums import TextureType
from typing import Optional

@dataclass
class TextureAsset:
    og_name: str
    og_path: Path
    texture_type: TextureType
    dest_name: str = ""
    
    dest_path: Optional[Path] = None
    unreal_path: str = ""
    
    imported: bool = False
    generated: bool = False
    skipped: bool = False
