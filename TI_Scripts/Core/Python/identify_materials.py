from pathlib import Path
import re

from TI_Scripts.Core.Python.settings import SettingsManager


# Groups files by material name
class MaterialIdentifier:

# ---------- Constructor & PUBLIC ------------   
    def __init__(self, settings: SettingsManager):
        self.settings = settings
        self._prefix = settings.prefix.lower()
        self._known_aliases = settings.get_all_aliases()

    def identify(self, files: list[Path]) -> dict[str, list[Path]]:
        groups: dict[str, list[Path]] = {}

        for file in files:
            material = self._extract_material_name(file.stem)
            if not material: continue
            groups.setdefault(material,[]).append(file)
        return groups
    
# ----------------- PRIVATE -----------------
    def _extract_material_name(self, filename:str) -> str:
        name = filename
        name = self._remove_prefix(name)
        name = self._remove_texture_alias(name)
        name = re.sub(r"_+","_",name)
        return name.strip("_")
        
    def _remove_prefix(self, name:str) -> str:
        if name.lower().startswith(self._prefix):
            return name[len(self._prefix):]

        return name
    
    def _remove_texture_alias(self, name:str) -> str:
        tokens = re.split(r"[_\-\.\s]+",name)
        for i in range(len(tokens)):
            candidate = "_".join(tokens[i:]).lower()
            
            if candidate in self._known_aliases:
                tokens = tokens[:i]
                break
        return  "_".join(tokens)
