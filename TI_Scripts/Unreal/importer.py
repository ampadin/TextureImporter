import unreal

from TI_Scripts.Core.Models.material_job import MaterialJob
from TI_Scripts.Core.Models.texture_asset import TextureAsset
from TI_Scripts.Core.Models.enums import (TextureType, TEXTURE_SETTINGS,CompressionType)
from TI_Scripts.Core.Models.import_options import ImportOptions

from TI_Scripts.Core.Python.settings import SettingsManager

#  Mapa CORE -> UNREAL
UNREAL_COMPRESSION_MAP = {
    CompressionType.DEFAULT : unreal.TextureCompressionSettings.TC_DEFAULT,
    CompressionType.NORMAL: unreal.TextureCompressionSettings.TC_NORMALMAP,
    CompressionType.MASK: unreal.TextureCompressionSettings.TC_MASKS,
    CompressionType.DISPLACEMENT: unreal.TextureCompressionSettings.TC_DISPLACEMENTMAP,
    CompressionType.GRAYSCALE : unreal.TextureCompressionSettings.TC_GRAYSCALE,
}
def _get_unreal_texture_settings(texture_type):
        data = TEXTURE_SETTINGS[texture_type]
        return {
            "srgb": data["srgb"],
            "compression" : UNREAL_COMPRESSION_MAP[data["compression"]]
        }

# ----- Constructor & public functions------------
class Importer:
    def __init__(self, settings: SettingsManager):
        self.asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        self.settings = settings


    def process(self, job: MaterialJob,options:ImportOptions)->MaterialJob:
            textures = self.get_importable_textures(job,options)             #only the texture types allowed for this run    
            for texture in textures: 
                self._import_texture(job, texture, options)
            return job

    def get_importable_textures(self, job:MaterialJob, options: ImportOptions) -> list[TextureAsset]: 
        allowed_types = {                                                   #base texture types that should always be considered

            TextureType.BASECOLOR,
            TextureType.NORMAL,
            TextureType.HEIGHT,
            TextureType.ORM,
        } 
        if options.import_ao: allowed_types.add(TextureType.AO)
        if options.import_roughness: allowed_types.add(TextureType.ROUGHNESS)
        if options.import_metallic: allowed_types.add(TextureType.METALLIC)

        # More options can be added here

        return [texture for texture in job.textures if texture.texture_type in allowed_types]


    
# --------- private functions --------
    def _ensure_directory(self, directory: str) -> None:
        if directory and not unreal.EditorAssetLibrary.does_directory_exist(directory):
            unreal.EditorAssetLibrary.make_directory(directory)


    def _import_texture(self, job:MaterialJob, texture:TextureAsset, options : ImportOptions):
        destinaton_path = job.texture_destination or self.settings.texture_destination
        if not destinaton_path:
            job.processing_errors.append("texture destination not defined")
            return
        self._ensure_directory(destinaton_path)

        if not texture.dest_name:                            # check that a destination name exists
            job.processing_errors.append(f"Texture '{texture.og_name}' has no destination name.")
            return

        asset_path = f"{destinaton_path.rstrip('/')}/{texture.dest_name}"

        if not options.overwrite and unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            job.warnings.append(f"Skipped '{texture.dest_name}': already exists and overwrite is disabled.")
            texture.unreal_path = asset_path
            texture.imported = False
            texture.skipped = True
            return 
        
        task = self._build_import_task(destinaton_path, job, texture, options)
        try:
            self.asset_tools.import_asset_tasks([task])         #Read all the task commands and perform the import
        except Exception as e:
            job.processing_errors.append(f"Cannot import '{texture.og_name}': {e}")
            return

        # Unreal neither throws an exception nor imports anything
        if not task.imported_object_paths:
            job.processing_errors.append(f"Failed to import '{texture.og_name}'")
            return

        texture.unreal_path = task.imported_object_paths[0]
        asset: unreal.Texture = unreal.load_asset(texture.unreal_path)   # asset is the texture already loaded in Unreal

        if asset is None:
            job.processing_errors.append(f"Cannot load imported asset '{texture.unreal_path}'")
            return
        
        texture.imported = True
        self._configure_texture(job, texture, asset)                    # configure the texture as required


    def _build_import_task(self, destination_path: str, job: MaterialJob,texture: TextureAsset, options: ImportOptions) -> unreal.AssetImportTask:
        task = unreal.AssetImportTask()   
        task.filename = str(texture.og_path)                            #source file to import
        task.destination_path = destination_path                        #Unreal destination path
        task.destination_name = texture.dest_name                       # destination asset name

        task.replace_existing = options.overwrite                       # replaces the asset if it already exists
        task.automated = True                                           
        task.save = self.settings.save_assets                           

        return task


    def _configure_texture(self, job: MaterialJob, texture: TextureAsset, asset: unreal.Texture):
        config = TEXTURE_SETTINGS.get(texture.texture_type)

        if config is None:
            job.warnings.append(f"No import settings for {texture.texture_type.name}")
            return
        try:                     #Core ->UNREAL
            unreal_settings = _get_unreal_texture_settings(texture.texture_type)

            asset.set_editor_property("srgb", unreal_settings["srgb"])                                #Configurar srgb
            asset.set_editor_property("compression_settings", unreal_settings["compression"])         #Configurar compresion

            if texture.texture_type == TextureType.NORMAL and self.settings.flip_green:     #Configurar flip green en normales segun configuracion
                asset.set_editor_property("flip_green_channel",True)

            if self.settings.save_assets:
                unreal.EditorAssetLibrary.save_loaded_asset(asset)              #auto-saves the texture if configured to do so

        except Exception as e:
            job.processing_errors.append(f"Cannot configure '{texture.dest_name}': {e}")