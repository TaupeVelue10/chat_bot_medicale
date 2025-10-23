#!/usr/bin/env python3
"""Simple showcase runner for a finetuned model available to Ollama.

Usage: python3 scripts/showcase_finetuned.py --model <model_name> --input-file examples.txt

The script will read example prompts (one per line) and call `rag_biomistral_query`
(or directly call Ollama) to get outputs, timing each call and saving results to a
`showcase_outputs/` directory with timestamp.

This script expects Ollama to be installed and the specified model to be available
(e.g., a finetuned biomistral model accessible as 'biomistral-clinical:finetuned').
"""
import argparse
import os
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.ollama import rag_biomistral_query

class DummyCollection:
    def query(self, query_texts, n_results=3):
        return {'documents': [["doc: guidelines excerpt"]], 'metadatas': [[{'source':'local','motif':'showcase'}]]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=False, default='biomistral-clinical:latest', help='Model name to display (for logging)')
    p.add_argument('--input-file', required=True, help='File with one prompt per line')
    p.add_argument('--out-dir', default='showcase_outputs', help='Directory to save outputs')
    p.add_argument('--no-rag', action='store_true', help='Bypass RAG and send the prompt as-is')
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_path = os.path.join(args.out_dir, f'showcase_{timestamp}.txt')

    with open(args.input_file) as f:
        prompts = [l.strip() for l in f.readlines() if l.strip()]

    with open(out_path, 'w') as out_f:
        for i, prompt in enumerate(prompts, 1):
            q = prompt if args.no_rag else prompt
            col = DummyCollection()
            start = time.time()
            try:
                resp = rag_biomistral_query(q, col)
                duration = time.time() - start
                out_f.write(f'--- Prompt {i} ---\n')
                out_f.write(prompt + '\n')
                out_f.write(f'Duration: {duration:.2f}s\n')
                out_f.write(resp + '\n\n')
                print(f'[{i}/{len(prompts)}] OK ({duration:.2f}s)')
            except Exception as e:
                duration = time.time() - start
                out_f.write(f'--- Prompt {i} (ERROR) ---\n')
                out_f.write(prompt + '\n')
                out_f.write(f'Duration: {duration:.2f}s\n')
                out_f.write('ERROR: ' + str(e) + '\n\n')
                print(f'[{i}/{len(prompts)}] ERROR ({duration:.2f}s): {e}')

    print('\nShowcase saved to', out_path)

if __name__ == '__main__':
    main()
