from TI_Scripts.Core.Python.settings import SettingsManager
from TI_Scripts.Core.Models.texture_asset import TextureAsset
from TI_Scripts.Core.Models.enums import TextureType
from TI_Scripts.Core.Models.material_job import MaterialJob
import re

class NamingManager:
#--------- Constructor ---------------
    def __init__(self, settings: SettingsManager):
        self.settings = settings

#----------- Functions --------------
    def generate_texture_name( self, material_name:str, texture: TextureAsset, job: MaterialJob) -> None:   # -> Instead of overwriting, it changes the texture's name only at destination
    
        prefix = self.settings.prefix
        suffix = self.settings.get_suffix(texture.texture_type)
        
        if not material_name:
            job.processing_errors.append("Material name is empty")
            return
        if not prefix:
            job.processing_errors.append("No prefix defined in naming_rules.json")
            return
        if not suffix:
            job.processing_errors.append(f"No suffix defined for {texture.texture_type}")
            return

        material_name = self.sanitize_name(material_name,job)
        texture.dest_name = (f"{prefix}{material_name}_{suffix}")
        

    def sanitize_name(self, name:str, job:MaterialJob)->str:
        if not name:
            job.processing_errors.append("Empty name in sanitize name")
            return ""
        
        name = name.strip()
        name = re.sub(r"[ \-\.]+", "_", name)       #replace separators with _
        name = re.sub(r"[^A-Za-z0-9_]", "", name)   # strip invalid characters (also removes accents); use r"[^\w]" instead if you need unicode-aware matching
        name = re.sub(r"_+","_",name)               #avoids double _(__)
        name = name.strip("_")                      # remove the _ at the beginning and end
        return name

    #material and folder naming
    def generate_material_instance_name(self, material_name:str, job:MaterialJob)->str:
        return (f"MI_{self.sanitize_name(material_name, job)}")
    
    def generate_folder_name(self, folder:str, job:MaterialJob)->str:
        return self.sanitize_name(folder, job)