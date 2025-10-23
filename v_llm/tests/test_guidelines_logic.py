import importlib.util, pathlib

mod_path = pathlib.Path(__file__).resolve().parents[1] / 'src' / 'guidelines_logic.py'
spec = importlib.util.spec_from_file_location('local_guidelines_logic', str(mod_path))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
analyze_guidelines = getattr(mod, 'analyze_guidelines')


def test_clarify_on_missing_info():
    # if only 'céphalées' without duration or red flags -> ask to clarify
    out = analyze_guidelines("patiente 35 ans, céphalées")
    assert isinstance(out, str)
    assert out.startswith("Pour préciser:"), f"expected clarification, got: {out}"


def test_urgency_on_fever():
    out = analyze_guidelines("Patient 40 ans, céphalées aiguës avec fièvre à 39°C")
    assert out and "URGENCE" in out


def test_irm_on_progressive():
    out = analyze_guidelines("Patient 40 ans, céphalées progressives depuis 2 mois")
    assert out and "IRM" in out


def test_urgency_on_loss_of_consciousness():
    out = analyze_guidelines("Patient 33 ans, céphalées brutales, perte de connaissance")
    assert out and ("URGENCE" in out or "urgence" in out)
