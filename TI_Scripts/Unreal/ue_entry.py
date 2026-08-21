
from pathlib import Path

import unreal

import datetime

from TI_Scripts.Core.Models.enums import JobStatus
from TI_Scripts.Core.Models.import_options import ImportOptions
from TI_Scripts.Core.Models.pipeline_result import PipelineResult

from TI_Scripts.Core.Python.pipeline import run_pipeline
from TI_Scripts.Core.Python.settings import SettingsManager
from TI_Scripts.Core.Python.texture_detector import TextureDetector
from TI_Scripts.Core.Python.naming import NamingManager
from TI_Scripts.Core.Python.scanner import Scanner
from TI_Scripts.Core.Python.ORMBuilder import ORMBuilder
from TI_Scripts.Core.Python.material_grouper import MaterialGrouper

from TI_Scripts.Unreal.importer import Importer
from TI_Scripts.Unreal.material_instancer import MaterialInstanceBuilder

PLUGIN_ROOT = Path(__file__).resolve().parents[2]

def execute(source_folder:Path |str,texture_root:str, material_root:str, options: ImportOptions | None=None): 
    """Punto de entrada principal el sistema. Ejecuta el proceso de importacion.
        Los valores de configuración se cargan desde SettingsManager/plugin_settings.json.
        Afectan a cada ejecución de forma exclusiva sin modficar los valores default."""

    settings = SettingsManager(PLUGIN_ROOT)
    if options is None:
        options = settings.create_default_import_options()

    #SON default options        
    naming = NamingManager(settings)
    detector = TextureDetector(settings)
    scanner = Scanner(detector, naming, settings)
    orm_builder = ORMBuilder(naming, settings)
    importer = Importer(settings)
    grouper = MaterialGrouper(settings)
    material_builder = MaterialInstanceBuilder(settings,naming)

    #Create jobs
    jobs = grouper.create_jobs(source_folder=Path(source_folder), master_material=options.master_material,) 

    results = []

    for job in jobs:     
        texture_base = texture_root or settings.texture_destination 
        job.texture_destination = f"{texture_base.rstrip('/')}/{job.material_name}" if texture_base else "" 

        job.material_destination =str(material_root) 

        _ensure_unreal_directory(job.texture_destination)
        _ensure_unreal_directory(job.material_destination)

        result = run_pipeline(job=job, scanner=scanner, orm_builder=orm_builder, settings=settings, options=options)  #Scanner + ORM
    
        if result.status == JobStatus.ERROR:
            results.append(result)
            continue

        importer.process(job,options)                           #Importer
        if job.processing_errors:
            result.errors.extend(job.processing_errors)
            result.warnings.extend(job.warnings)
            result.status = JobStatus.ERROR
            results.append(result)
            continue

        if options.create_material_instance:                    #Create MI
            material_builder.process(job)
            if job.processing_errors:
                result.errors.extend(job.processing_errors)
                result.warnings.extend(job.warnings)
                result.status = JobStatus.ERROR
                results.append(result)
                continue

        result.materials_processed = 1
        result.textures_imported = sum(1 for t in job.textures if t.imported)
        result.textures_skipped = sum(1 for t in job.textures if t.skipped)
        result.materials_instances_created = 1 if job.material_instance_path else 0
        result.orm_generated = 1 if job.orm_task and job.orm_task.generated_texture else 0

        result.warnings.extend(job.warnings)
        result.errors.extend(job.processing_errors)
        result.generated_assets.extend(str(path) for path in job.generated_files)

        if job.material_instance_path:
            result.generated_assets.append(job.material_instance_path)

        if result.errors:
            result.status = JobStatus.ERROR
        elif result.warnings:
            result.status = JobStatus.WARNING
        else:
            result.status = JobStatus.SUCCESS
        
        results.append(result) 

    if not results and settings.validation_warnings: results.append(PipelineResult(status=JobStatus.WARNING, warnings=list(settings.validation_warnings)))
        
    return results

def get_default_import_options() -> dict:              ## Returns the default values the EUW needs. Source: plugin_settings.json + SettingsManager
    settings = SettingsManager(PLUGIN_ROOT)
    options = settings.create_default_import_options()

    return {
        "master_material":options.master_material,
        "texture_destination":settings.texture_destination,
        "material_destination":settings.material_destination,

        "create_material_instance": options.create_material_instance,
        "create_orm": options.create_orm,
        "import_ao": options.import_ao,
        "import_roughness": options.import_roughness,
        "import_metallic": options.import_metallic,
        "overwrite":options.overwrite,
    }

def get_log_directory() ->str: return str(Path(unreal.Paths.project_saved_dir())/"TexturesImporter"/"Logs")

def write_last_import_log(status_text: str) -> str:
    """
    Saves `status_text` in a .txt file with a timestamp in the Saved/TextureImporter/Logs folder.
    Returns the path to the generated file, or "" if it fails.
    """
    log_dir = Path(get_log_directory())
    try:
        log_dir.mkdir(parents=True,exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir/f"import_{timestamp}.txt"
        log_file.write_text(status_text,encoding="utf-8")
        return str(log_file)
    except Exception as e:
        unreal.log_error(f"Cannot write import log: {e}")
        return ""

def _ensure_unreal_directory(path:str) -> None:
    if path and not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)
