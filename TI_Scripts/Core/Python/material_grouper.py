from pathlib import Path

from TI_Scripts.Core.Models.material_job   import MaterialJob

from TI_Scripts.Core.Python.identify_materials import MaterialIdentifier
from TI_Scripts.Core.Python.settings import SettingsManager

class MaterialGrouper:
    # ------ CONSTRUCTOR & PUBLIC----------
    def __init__(self, settings:SettingsManager):
        self.settings = settings
        self.identifier = MaterialIdentifier(settings)

    def create_jobs(self, source_folder:Path | str, master_material:str) -> list[MaterialJob]:
        source_folder = Path(source_folder)

        if not source_folder.exists():
            self.settings.validation_warnings.append(f"Directory Not Found: {source_folder}")
            return[]

        if not source_folder.is_dir():
             self.settings.validation_warnings.append(f"Source path is not a directory: {source_folder}")
             return []
        
        unsupported_files = [file for file in source_folder.iterdir() if file.is_file() and file.suffix.lower() not in self.settings.supported_extensions]
        for file in unsupported_files: self.settings.validation_warnings.append(f"Ignored unsupported file: '{file.name}'")

        files = sorted([ file for file in source_folder.iterdir() if file.is_file() and file.suffix.lower() in self.settings.supported_extensions], key =lambda path: path.name.lower())

        groups = self.identifier.identify(files)
        jobs: list[MaterialJob] = []

        for material_name, material_files in groups.items():
            if not material_files or not material_name: continue

            texture_destination = (
                str(Path(self.settings.texture_destination)/ material_name)
                if self.settings.texture_destination
                else ""
            )

            job = MaterialJob(
                source_folder= source_folder,
                source_files= material_files,
                material_name= material_name,
                master_material= master_material,
                texture_destination= texture_destination, 
                material_destination= self.settings.material_destination,
                )

            jobs.append(job)

        return jobs