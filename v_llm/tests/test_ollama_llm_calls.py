import types
import sys

from src import ollama


class DummyCollection:
    def query(self, query_texts, n_results=3):
        return {'documents': [["doc1"]], 'metadatas': [[{'source': 'guidelines', 'motif': 'test'}]]}


def test_rag_uses_llm_and_returns_recommendation(monkeypatch):
    # Ensure analyze_guidelines does not force clarification
    fake_guidelines = types.SimpleNamespace(analyze_guidelines=lambda q: None)
    monkeypatch.setitem(sys.modules, 'src.guidelines_logic', fake_guidelines)

    # Fake ollama module: provide a generate method returning a dict with 'response'
    fake_ollama = types.SimpleNamespace()

    def fake_generate(model, prompt, temperature=None):
        return {'response': 'Recommandation: IRM cérébrale — justification factice'}

    fake_ollama.generate = fake_generate

    monkeypatch.setattr(ollama, '_import_installed_ollama', lambda: fake_ollama)

    col = DummyCollection()
    out = ollama.rag_biomistral_query("Patient 40 ans, céphalées progressives depuis 2 mois", col)
    assert isinstance(out, str)
    assert out.startswith('Recommandation:')


def test_rag_returns_pour_preciser_if_guidelines_requests_it(monkeypatch):
    # If local guidelines request clarification, rag_biomistral_query should return it directly
    fake_guidelines = types.SimpleNamespace(analyze_guidelines=lambda q: "Pour préciser: q1 | q2 | q3")
    monkeypatch.setitem(sys.modules, 'src.guidelines_logic', fake_guidelines)

    # _import_installed_ollama should not be called, but provide a fake anyway
    fake_ollama = types.SimpleNamespace(generate=lambda *a, **k: {'response': 'IGNORED'})
    monkeypatch.setattr(ollama, '_import_installed_ollama', lambda: fake_ollama)

    col = DummyCollection()
    out = ollama.rag_biomistral_query("patiente 33 ans, céphalées", col)
    assert isinstance(out, str)
    assert out.startswith('Pour préciser:')
