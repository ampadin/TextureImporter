from pathlib import Path

from Resources.ThirdParty.PIL import Image

from TI_Scripts.Core.Models.material_job import MaterialJob
from TI_Scripts.Core.Models.orm_task import ORMTask
from TI_Scripts.Core.Models.enums import TextureType
from TI_Scripts.Core.Models.texture_asset import TextureAsset
from TI_Scripts.Core.Models.import_options import ImportOptions

from TI_Scripts.Core.Python.settings import SettingsManager
from TI_Scripts.Core.Python.naming import NamingManager


class ORMBuilder:
   #--------CONSTRUCTOR -----------------
    def __init__(self, naming:NamingManager, settings: SettingsManager):
        self.naming = naming
        self.settings = settings

        #load or create the default ORM
        self.resource_folder = (Path(__file__).parents[3] / "Resources") 
        self.default_texture_path = (self.resource_folder / "T_Default_ORM.PNG")

        if self.default_texture_path.exists(): 
            with Image.open(self.default_texture_path) as img: 
                self.default_orm = img.convert("RGB")
            self.default_orm_warning = None
            self.default_orm_warning_reported = False           #so it only happens once
        else: 
            self.default_orm_warning = "Default ORM not found. Creating fallback texture"
            self.default_orm = Image.new("RGB", (512, 512), (255, 128, 0))  # AO=255, Rough=128, Metal=0 , created when the resource file doesn't exist
            self.default_orm_warning_reported = False

        self._default_orm_disk_path: Path| None = None

    #--------PUBLIC ---------------

    def process(self, job:MaterialJob, options:ImportOptions) -> MaterialJob:

        if self.default_orm_warning and not self.default_orm_warning_reported:
            job.warnings.append(self.default_orm_warning)
            self.default_orm_warning_reported = True

        if job.has(TextureType.ORM):
            return job                          # ORM texture already exists, skip generation
        if not options.create_orm:
            return job                          #ORM generation disabled by options
        
        # If these textures exist they're used to build the ORM, regardless of whether they're also imported individually
        ao = job.get(TextureType.AO)
        roughness = job.get(TextureType.ROUGHNESS)
        metallic = job.get(TextureType.METALLIC)

        task = ORMTask(ao=ao, roughness=roughness,metallic=metallic)
        job.orm_task = task

        #No channel textures found -> use the default ORM
        if not self._should_generate(task):
              job.warnings.append(f"No AO, roughness or Metallic textures found for '{job.material_name}'. Using default ORM.")
              source_path = self._resolve_default_orm_source(job)
              if source_path is None:
                  return job
              
              texture = self._create_texture(source_path,TextureType.ORM, generated= not self.default_texture_path.exists()) 
              self.naming.generate_texture_name(job.material_name,texture,job)
              task.generated_texture = texture
              job.set(TextureType.ORM,texture)
              return job

    #  generating ORM because at least one channel is present, the rest fall back to the default ORM
        texture = self._generate_texture(job,task)

        if texture is None:
            return job  

        task.generated_texture = texture 
        job.set(TextureType.ORM, texture)

        return job

    #---------------PRIVATE ---------------
    def _should_generate(self,task:ORMTask)->bool:
        result = any((task.ao, task.roughness, task.metallic))           # generate a new ORM if any channel is present
        return result

    def _resolve_default_orm_source(self, job:MaterialJob)-> Path|None:
        """Returns a valid disk path for the default ORM.  Uses T_Default_ORM.PNG directly if it exists as a resource;
           otherwise saves self.default_orm (generated in memory) to _Generated the first time and reuses that file on later calls within the same session."""
        if self.default_texture_path.exists():
            return self.default_texture_path

        if self._default_orm_disk_path and self._default_orm_disk_path.exists():
            return self._default_orm_disk_path

        output_folder = Path(job.source_folder) / "_Generated"
        output_folder.mkdir(parents=True, exist_ok=True)
        output_file = output_folder / "T_Default_ORM.png"

        try:
            self.default_orm.save(output_file)
        except Exception as e:
            job.processing_errors.append(f"Cannot save fallback default ORM: {e}")
            return None

        self._default_orm_disk_path = output_file
        job.generated_files.append(output_file)
        return output_file
 
    def _generate_texture(self, job:MaterialJob, task:ORMTask) -> TextureAsset | None:
        reference_size = self._get_reference_size(task)

        #******roughness****
        rough = self._load_channel(task.roughness,"G", job, reference_size)
        #****AO****
        ao = self._load_channel(task.ao,"R", job, reference_size)
         #****Metallic****
        metallic = self._load_channel(task.metallic,"B", job, reference_size)

        
        #****ORM****
        try:
            orm= Image.merge("RGB",(ao, rough,metallic))
        except Exception as e:
            job.processing_errors.append( f"Cannot build ORM texture: {e}" )
            return None
        
        output_folder = Path(job.source_folder) / "_Generated"          
        output_folder.mkdir( parents=True,exist_ok=True)

        output_file = (output_folder / f"{job.material_name}_ORM.png")
        try:
            orm.save(output_file)
        except Exception as e:
            job.processing_errors.append(f"Cannot save generated ORM: {e}")
            return None            

        texture = self._create_texture(output_file, TextureType.ORM, generated=True)
        self.naming.generate_texture_name(job.material_name,texture,job)       

        job.generated_files.append(output_file)

        return texture

 
    def _load_channel(self,texture: TextureAsset| None, default_channel: str, job:MaterialJob, target_size: tuple[int, int])->Image.Image: 

        if texture is None:                                             #fall back to the default ORM's channel if missing
            job.warnings.append(f"Missing {default_channel} channel texture. Using default ORM fallback.") 
            channel = self.default_orm.getchannel(default_channel)
            return self._resize_if_needed(channel, target_size)
        try:
            with Image.open(texture.og_path) as img:
                original_size= img.size
                channel = img.convert("L")                              #open and convert to grayscale
                if original_size != target_size:
                    job.warnings.append(f"Resized '{texture.og_name}' from {original_size[0]}x{original_size[1]} to {target_size[0]}x{target_size[1]} for ORM generation.")
            return self._resize_if_needed(channel, target_size)
        
        except Exception as e:
            job.processing_errors.append(f"Cannot open texture '{texture.og_name}': {e}")
            channel = self.default_orm.getchannel(default_channel)
            return self._resize_if_needed(channel, target_size)


    def _resize_if_needed(self, image:Image.Image, target_size: tuple [int,int]) -> Image.Image:
        if image.size == target_size:
            return image
        try:
            return image.resize(target_size, Image.Resampling.LANCZOS)
        except AttributeError:                                              #Error in case of compatibility issues with older versions of PILLOW
            return image.resize(target_size, Image.LANCZOS)


    def _get_reference_size(self, task: ORMTask) -> tuple[int,int]:
        """ Returns the size of the first available texture, in priority order AO -> Roughness -> Metallic.
            Falls back to the default ORM's size if none are available. """
        
        for texture in (task.ao, task.roughness, task.metallic):
            if texture is None:
                continue
            try:
                with Image.open(texture.og_path) as img:
                    return img.size
            except Exception:
                continue
        return self.default_orm.size


    def _create_texture(self, file:Path, texture_type:TextureType, generated:bool)->TextureAsset:
        return TextureAsset(og_name = file.name, og_path=file,texture_type=texture_type,generated=generated)