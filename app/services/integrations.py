"""External integration ports.

Core domain code depends on these small contracts rather than vendor SDKs.
"""
from dataclasses import dataclass
from typing import Protocol,Optional
@dataclass(frozen=True)
class DeliveryResult:
 accepted:bool; external_id:Optional[str]=None; detail:str=""
class SmsPort(Protocol):
 def send(self,to:str,message:str)->DeliveryResult: ...
class EmailPort(Protocol):
 def send(self,to:str,subject:str,body:str)->DeliveryResult: ...
class LaboratoryPort(Protocol):
 def submit(self,patient_code:str,tests:list[str])->DeliveryResult: ...
class DevicePort(Protocol):
 def ingest(self,payload:dict)->DeliveryResult: ...
