"""Vendor-neutral device ingestion contract."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
SUPPORTED_PROTOCOLS={"ble","https","batch"}
VALIDATION_STATES={"pending","validated","rejected","corrected"}
@dataclass(frozen=True)
class DeviceMeasurement:
    device_id:str; subject_id:int; code:str; value:float; unit:Optional[str]; measured_at:datetime; quality_score:Optional[float]; protocol:str
    def __post_init__(self):
        if self.protocol not in SUPPORTED_PROTOCOLS: raise ValueError("Unsupported device protocol")
        if not self.device_id or not self.code: raise ValueError("device_id and code are required")
        if self.quality_score is not None and not 0<=self.quality_score<=1: raise ValueError("quality_score must be between 0 and 1")
        if self.measured_at.tzinfo is None: raise ValueError("measured_at must be timezone-aware")
def to_observation_payload(m:DeviceMeasurement):
    return {"source_type":"device","source_id":m.device_id,"patient_id":m.subject_id,"code":m.code,"value":m.value,"unit":m.unit,"observed_at":m.measured_at.isoformat(),"quality_score":m.quality_score,"validation_state":"pending"}
