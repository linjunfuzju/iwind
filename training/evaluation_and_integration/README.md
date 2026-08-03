# Evaluation, Export, and Iwind Integration

This package provides dependency-free evaluation and RAG primitives plus explicit optional-runtime boundaries for inference and GPTQ export. Core modules require Python 3.10 or newer; importing them does not load a model or require packages from `requirements.txt`.

## Evaluation

`schemas.py` validates benchmark, prediction, and auditable expert-rating records. Objective scoring applies Unicode, case, whitespace, boolean, and finite-number normalization while retaining punctuation and units. Reports include Wilson intervals for accuracy and seeded bootstrap intervals for expert dimensions. SFT-versus-GRPO reports use question-aligned paired deltas, wins, losses, and ties; positive deltas always mean GRPO improved over SFT.

Benchmark JSONL fields:

```json
{"question_id":"q1","question_type":"objective","prompt":"...","answer":"A","acceptable_answers":["Alpha"],"split":"test"}
```

Prediction JSONL fields:

```json
{"question_id":"q1","answer":"A","model_id":"sft-v1","run_id":"seed-0"}
{"question_id":"q2","answer":"...","model_id":"sft-v1","run_id":"seed-0","expert_ratings":[{"rater_id":"expert-01","protocol_version":"iwind-rating-v1","blind":true,"scores":{"relevance":4,"professionalism":5,"completeness":4,"consistency":4},"rationale":"..."}]}
```

Commands:

```bash
python -m iwind.evaluation_and_integration.evaluate_benchmarks --benchmark benchmark.jsonl --predictions predictions.jsonl --output report.json
python -m iwind.evaluation_and_integration.evaluate_benchmarks --benchmark benchmark.jsonl --sft-predictions sft.jsonl --grpo-predictions grpo.jsonl --output comparison.json
```

## Calibration And Export

All relative config paths are resolved relative to the config file, not the caller's working directory. Calibration performs normalized exact deduplication and configurable token-Jaccard leakage checks against benchmark/evaluation JSON, JSONL, raw text entries, or SHA-256 lists. Leakage checks also run during quota redistribution. By default, a sample shortfall is fatal.

Calibration and manifests are written with temp-file, fsync, and atomic replace semantics. Manifests include SHA-256 and byte size. Quantization performs a runtime-free contract validation before lazily importing GPTQ dependencies. Export writes to a sibling staging directory, checks required files, emits `export_manifest.json`, and atomically renames the complete stage into place. Source and output directories must be separate and non-nested; existing non-empty output is rejected. `trust_remote_code` defaults to false.

```bash
python -m iwind.evaluation_and_integration.build_calibration --config iwind/evaluation_and_integration/configs/calibration.json
python -m iwind.evaluation_and_integration.quantize_gptq --config iwind/evaluation_and_integration/configs/quantization.json --validate-only
# Remove --validate-only only in the provisioned external model runtime.
```

`quantization_compare.py` compares ID-aligned deterministic baseline and quantized outputs using normalized exact match and token multiset F1. `performance.py` aggregates generated-token-normalized throughput, latency mean/median/p95, and peak memory. Fidelity runs must use identical prompts, chat templates, stopping rules, greedy decoding, and tokenizer revisions. Stochastic robustness is a separate seeded experiment.

## RAG Integration

`rag_types.py` defines queries, documents, path-specific hits, fused evidence, bounded contexts, and citation validation. `retrievers.py` provides a lexical BM25-style retriever, a dense callback adapter that does not own an embedding model, and metadata-filtered structured retrieval. `retrieval_fusion.py` uses weighted reciprocal-rank fusion, deterministic tie breaking, deduplication, and a callback reranker. `context_and_citations.py` budgets evidence and validates `[S1]` citations. `rag_metrics.py` reports retrieval recall/precision/hit/MRR and citation validity/precision/recall.

```bash
python -m iwind.evaluation_and_integration.rag_pipeline --query "Assess the likely cable fault mechanism" --documents documents.jsonl
```

The lexical/structured demonstration is local and deterministic. Dense retrieval and reranking are application-supplied callbacks. `GenerationClient` lazily imports the optional OpenAI client and validates returned citations.

## Verification

```bash
python -m unittest discover -s iwind/evaluation_and_integration/tests -v
python -m compileall -q iwind/evaluation_and_integration
```

Static checks do not establish model quality. A publication must additionally report immutable dataset/model revisions, benchmark construction and leakage audit, exclusion counts, expert recruitment and blinding, inter-rater analysis, hardware, runtime versions, prompts/templates, random seeds, uncertainty intervals, and all failed or omitted samples.
