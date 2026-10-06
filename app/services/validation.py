"""Clinical validation evidence primitives."""
from dataclasses import dataclass
@dataclass(frozen=True)
class ValidationStudy:
    study_id:str; modality:str; reference_standard:str; population:str; stage:str
    sample_size:int=0
    def __post_init__(self):
        if self.sample_size<0: raise ValueError("sample_size cannot be negative")
        if self.stage not in {"protocol","calibration","reference_comparison","clinical_correlation","prospective_validation","completed"}: raise ValueError("invalid validation stage")
@dataclass(frozen=True)
class ValidationMetric:
    name:str; value:float; unit:str; cohort:str
def release_gate(study:ValidationStudy,required_stage="prospective_validation")->bool:
    order=["protocol","calibration","reference_comparison","clinical_correlation","prospective_validation","completed"]
    return order.index(study.stage)>=order.index(required_stage)
