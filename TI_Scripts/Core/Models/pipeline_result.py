from dataclasses import dataclass, field

from TI_Scripts.Core.Models.enums import JobStatus


@dataclass

class PipelineResult:

    status: JobStatus

    message: str = ""

    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    generated_assets: list[str] = field(default_factory=list)

    materials_processed: int = 0
    textures_imported: int = 0
    textures_skipped: int = 0
    materials_instances_created: int = 0
    orm_generated: int = 0

