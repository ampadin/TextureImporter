from pathlib import Path

from TI_Scripts.Core.Models.material_job import MaterialJob
from TI_Scripts.Core.Models.texture_asset import TextureAsset
from TI_Scripts.Core.Models.enums import TextureType

from TI_Scripts.Core.Python.settings import SettingsManager
from TI_Scripts.Core.Python.texture_detector import TextureDetector
from TI_Scripts.Core.Python.naming import NamingManager


class Scanner:
    # ------ CONSTRUCTOR & FUNCTIONS ---   
    def __init__(self, detector:TextureDetector, naming:NamingManager, settings :SettingsManager):
        self.detector = detector
        self.naming = naming
        self.settings = settings

    def scan(self, job: MaterialJob,files :list[Path]):       
        """
            generated_folder = job.source_folder / "_Generated"              # Add files from _Generated -> NOT enabled
            if generated_folder.exists():
                for file in generated_folder.iterdir():
                    if file.is_file():
                        files.append(file)  
        """
    
        for file in files:                       #Iterates over each file
            if not file.is_file():               #skip folders
                continue
            if file.suffix.lower() not in self.settings.supported_extensions:            #checks file extensions
                continue

            #detect texture type
            try:
                texture_type = self.detector.detect(file.stem)
            except Exception as e:
                job.processing_errors.append(f"Detector error in '{file.name}': {e}")
                continue

            if texture_type == TextureType.UNKNOWN:
                job.warnings.append(f"Unknown texture type: {file.name}")
                continue

            """if job.has(texture_type):             #Prevent overwriting a texture of the same type -> NOT enabled
                continue"""

            # Create and name the texture
            texture = self._create_texture(file, texture_type)
            self.naming.generate_texture_name(job.material_name, texture,job)
            job.set(texture.texture_type,texture)

        return job
    
    def _create_texture(self, file:Path, texture_type: TextureType)->TextureAsset:
        return TextureAsset(og_name = file.name, og_path =  file, texture_type = texture_type)