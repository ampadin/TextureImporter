from TI_Scripts.Core.Models.pipeline_result import PipelineResult
from TI_Scripts.Core.Models.enums import JobStatus
from TI_Scripts.Core.Models.material_job import MaterialJob
from TI_Scripts.Core.Models.import_options import ImportOptions

from TI_Scripts.Core.Python.scanner import Scanner
from TI_Scripts.Core.Python.ORMBuilder import ORMBuilder
from TI_Scripts.Core.Python.settings import SettingsManager


def run_pipeline(job:MaterialJob, scanner: Scanner, orm_builder:ORMBuilder, settings: SettingsManager, options: ImportOptions) ->PipelineResult: 
    result = PipelineResult(status=JobStatus.RUNNING)

    try:
        #1.scan textures
        scanner.scan(job, job.source_files)
        if job.processing_errors:       
            result.status = JobStatus.ERROR                  # stop pipeline if scanning produced errors
            return  _finalize_result(result,job,settings)
        
        #2. generate orm if needed
        orm_builder.process(job, options)
        if job.processing_errors:     
            result.status = JobStatus.ERROR                  #stop pipeline if ORMBuilder produced errors
            return  _finalize_result(result,job,settings)

    except Exception as e:
        job.processing_errors.append(f"Pipeline error: {e}")

    return  _finalize_result(result,job,settings)



def _finalize_result(result: PipelineResult, job: MaterialJob, settings: SettingsManager,) -> PipelineResult:
    result.warnings.extend(settings.validation_warnings)
    result.warnings.extend(job.warnings)
    result.errors.extend(job.processing_errors)

    result.generated_assets.extend(str(path) for path in job.generated_files) 

    if result.errors:
        result.status = JobStatus.ERROR
    elif result.warnings:
        result.status = JobStatus.WARNING
    else:
        result.status = JobStatus.SUCCESS
    return result