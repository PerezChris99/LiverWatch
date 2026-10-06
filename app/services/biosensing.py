"""Experimental non-invasive biosensing registry.

Research signals are explicitly non-clinical until validation evidence exists.
"""
from dataclasses import dataclass
EXPERIMENTAL_MODALITIES={"sweat","interstitial_fluid","skin_interfaced","physiological"}
@dataclass(frozen=True)
class BiosensingExperiment:
    modality:str; analyte:str; study_id:str; validation_stage:str="research"
    def __post_init__(self):
        if self.modality not in EXPERIMENTAL_MODALITIES: raise ValueError("Unsupported biosensing modality")
        if self.validation_stage not in {"research","calibration","reference_comparison","clinical_correlation","prospective_validation","validated"}: raise ValueError("Invalid validation stage")
    @property
    def is_clinical(self): return self.validation_stage=="validated"
def classify_signal(experiment,quality_score):
    if not 0<=quality_score<=1: raise ValueError("quality_score must be between 0 and 1")
    return {"analyte":experiment.analyte,"modality":experiment.modality,"quality_score":quality_score,"clinical_use_allowed":experiment.is_clinical}
