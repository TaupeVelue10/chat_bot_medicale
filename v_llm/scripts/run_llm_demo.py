#!/usr/bin/env python3
"""Demo script to force a call to the LLM (BioMistral via Ollama).

It injects a fake `src.guidelines_logic` module where `analyze_guidelines` returns
None so the deterministic interception is bypassed, then calls
`rag_biomistral_query` with a dummy RAG collection.

Run this only if you have Ollama / the biomistral model available locally.
"""
import sys
import os
import types

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Inject a fake src.guidelines_logic to prevent deterministic interception
fake = types.ModuleType('src.guidelines_logic')
def analyze_guidelines(q):
    return None
fake.analyze_guidelines = analyze_guidelines
sys.modules['src.guidelines_logic'] = fake

from src.ollama import rag_biomistral_query

class DummyCollection:
    def query(self, query_texts, n_results=3):
        # return a minimal RAG-like structure expected by rag_biomistral_query
        return {'documents': [["doc: guidelines excerpt"]], 'metadatas': [[{'source':'local','motif':'test'}]]}

def main():
    q = "Patient 40 ans, céphalées progressives depuis 2 mois, pas de fièvre"
    col = DummyCollection()
    print(f"Calling rag_biomistral_query with question: {q}\n")
    try:
        out = rag_biomistral_query(q, col)
        print("--- LLM response ---")
        print(out)
    except Exception as e:
        print("Error while calling the LLM (Ollama/BioMistral may not be available):")
        print(e)

if __name__ == '__main__':
    main()
