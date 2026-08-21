import re

from TI_Scripts.Core.Python.settings import SettingsManager
from TI_Scripts.Core.Models.enums import TextureType

class TextureDetector:
    def __init__(self,settings:SettingsManager):
        self.settings = settings
        
    def detect(self, filename: str) ->TextureType:
        
        tokens:list[str] = re.split(r"[_\-\.\s]+", filename.lower())        # avoids false-positive suffix detection inside ordinary words, e.g. BOAT -> OA

        compact = re.sub(r"[^a-z0-9]", "", filename.lower())                #strips everything that isn't a letter or digit
        for texture_type in TextureType:
            if texture_type == TextureType.UNKNOWN:
                continue

            aliases:list[str] = self.settings.get_aliases(texture_type)
            for alias in aliases:
                if alias in tokens:
                    return texture_type
                
                if len(alias)>1 and compact.endswith(alias):                #avoids false positives
                    return texture_type

        return TextureType.UNKNOWN
