from src.ollama import rag_biomistral_query
from src.indexage import create_index


class DummyCollection:
    def query(self, query_texts, n_results=3):
        return {'documents': [['doc1','doc2','doc3']], 'metadatas': [[{'source':'s','motif':'m'},{'source':'s','motif':'m'},{'source':'s','motif':'m'}]]}


def test_rag_returns_questions_for_missing_info():
    c = DummyCollection()
    out = rag_biomistral_query('patiente 34 ans céphalées', c)
    assert isinstance(out, str)
    assert out.lower().startswith('pour préciser')
