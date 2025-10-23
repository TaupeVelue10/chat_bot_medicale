Showcase Finetuned BioMistral

Purpose
-------
This script lets you run a local finetuned BioMistral (via Ollama) over a set of
prompts and save the outputs with timings.

Prerequisites
-------------
- Ollama installed and configured locally
- The finetuned model available in Ollama (e.g. 'biomistral-clinical:finetuned')
- Python 3.11 (this repo uses it for dev)

Usage
-----
1) Create an examples file (one prompt per line), e.g. `showcase_prompts.txt`.
2) Run the script:

```bash
python3 scripts/showcase_finetuned.py --model biomistral-clinical:finetuned --input-file showcase_prompts.txt
```

Options
-------
--model : used only for logging purposes inside the script (the script calls the same `rag_biomistral_query` helper)
--input-file : file with prompts (required)
--out-dir : output directory (default: `showcase_outputs`)
--no-rag : send the prompt as-is (bypass RAG context retrieval)

Notes
-----
- If `rag_biomistral_query` fails because Ollama isn't available, the script will record the error in the output file for each prompt.
- For demos, consider using `--no-rag` to focus on the model's behavior without additional context.
