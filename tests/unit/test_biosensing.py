import pytest
from app.services.biosensing import BiosensingExperiment,classify_signal
def test_experimental_signal_is_not_clinical():
 e=BiosensingExperiment("sweat","creatinine","study-1")
 assert not e.is_clinical and classify_signal(e,.9)["clinical_use_allowed"] is False
def test_biosensing_validates_stage():
 with pytest.raises(ValueError): BiosensingExperiment("sweat","ALT","study-1","diagnostic")
