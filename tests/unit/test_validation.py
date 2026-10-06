from app.services.validation import ValidationStudy,release_gate
def test_validation_release_gate_blocks_early_signal():
 s=ValidationStudy("s1","sweat","reference-lab","adults","clinical_correlation",100)
 assert not release_gate(s)
def test_completed_study_passes_gate():
 s=ValidationStudy("s1","sweat","reference-lab","adults","completed",100)
 assert release_gate(s)
