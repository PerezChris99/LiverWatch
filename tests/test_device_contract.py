from datetime import datetime,timezone
import pytest
from app.services.device_contract import DeviceMeasurement,to_observation_payload
def test_device_contract_requires_quality_bounds():
 with pytest.raises(ValueError): DeviceMeasurement("d",1,"ALT",1,"U/L",datetime.now(timezone.utc),2,"ble")
def test_device_payload_is_pending():
 m=DeviceMeasurement("d",1,"ALT",1,"U/L",datetime.now(timezone.utc),.9,"ble")
 assert to_observation_payload(m)["validation_state"]=="pending"
