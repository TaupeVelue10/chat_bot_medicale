import subprocess
import sys
import os
import textwrap

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PY = sys.executable


def run_cli_with_input(input_text: str, timeout: int = 10) -> str:
    proc = subprocess.run([PY, '-u', 'src/main.py'], input=input_text, capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=timeout)
    return proc.stdout


def test_e2e_clarify_then_urgency():
    # Scenario: initial minimal info triggers clarification, then answering with loss of consciousness triggers URGENCE
    input_sequence = textwrap.dedent("""
    patiente 33 ans, céphalées
    brutale, 2 semaines, perte de connaissance
    quit
    """)
    out = run_cli_with_input(input_sequence)
    assert "Pour préciser" in out
    assert ("URGENCE" in out or "urgence" in out)


def test_e2e_progressive_irm():
    # Scenario: explicit progressive duration should directly return IRM sans clarif
    input_sequence = textwrap.dedent("""
    Patient 40 ans, céphalées progressives depuis 2 mois, pas de fièvre
    quit
    """)
    out = run_cli_with_input(input_sequence)
    assert "IRM" in out or "IRM cérébrale" in out or "Recommandation" in out
