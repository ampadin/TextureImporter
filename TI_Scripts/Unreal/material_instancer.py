import unreal

from TI_Scripts.Core.Models.material_job import MaterialJob
from TI_Scripts.Core.Models.enums import TextureType

from TI_Scripts.Core.Python.naming import NamingManager
from TI_Scripts.Core.Python.settings import SettingsManager

class MaterialInstanceBuilder:

    def __init__(self, settings:SettingsManager, naming:NamingManager):
        self.asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        self.settings = settings
        self.naming = naming

    def process(self, job:MaterialJob):
        package_path = job.material_destination or self.settings.material_destination
        if not package_path: 
            job.processing_errors.append("material destination not defined")
            return job
        
        self._ensure_directory(package_path)

        if not job.master_material:
            job.processing_errors.append(f"Master material not defined.")
            return job
        
        master = unreal.load_asset(job.master_material)

        if master is None:
            job.warnings.append(f"Cannot load Master Material '{job.master_material}'. Material Instance creation skipped.")
            return job

        instance_name = self.naming.generate_material_instance_name(job.material_name,job)

        factory = unreal.MaterialInstanceConstantFactoryNew()

        try:
            instance = self.asset_tools.create_asset(
                asset_name=instance_name,
                package_path=package_path,                      # path where the material is saved
                asset_class=unreal.MaterialInstanceConstant,
                factory = factory
            )

            if instance is None:
                job.processing_errors.append("Material Instance creation failed.")
                return job
            
            instance.set_editor_property("parent",master)
            job.material_instance_path = instance.get_path_name()

        except Exception as e:
            job.processing_errors.append(f"Cannot create Material Instance: {e}")
            return job

        self._assign_textures(job, instance)

        if self.settings.save_assets:
            unreal.EditorAssetLibrary.save_loaded_asset(instance)

        return job

    def _ensure_directory(self, directory: str) -> None:
        if directory and not unreal.EditorAssetLibrary.does_directory_exist(directory):
            unreal.EditorAssetLibrary.make_directory(directory)
    
    def _assign_textures( self, job: MaterialJob, instance:unreal.MaterialInstanceConstant):
                
        library = unreal.MaterialEditingLibrary()
        
        for texture_type, texture in job.textures.items():
            parameter = self.settings.material_parameters.get(texture_type)
            if parameter is None:
                continue

            if( not texture.unreal_path):     #Scanned textures that are NOT imported would be: not texture.imported or not texture.unreal_path — this now also includes previously-imported ones
                continue

            asset = unreal.load_asset(texture.unreal_path)

            if asset is None:
                job.warnings.append(f"Cannot load texture '{texture.dest_name}'")
                continue

            try:
                library.set_material_instance_texture_parameter_value(instance, parameter, asset)
            except Exception as e: job.warnings.append(f"Cannot assign texture '{texture.dest_name}' to parameter '{parameter}': {e}")
