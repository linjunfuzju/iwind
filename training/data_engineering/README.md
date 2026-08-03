# Dataset Construction and Benchmark Module

This package builds auditable offshore-wind and marine-engineering datasets using only the Python standard library. It accepts curated JSONL records and emits strict, deterministic corpus and benchmark artifacts.

## Capabilities

- Frozen dataclass schemas with unknown-field rejection.
- Unicode and whitespace normalization.
- Stable content/source-derived document and question identifiers.
- Deterministic token-aware chunking using Unicode word/punctuation boundaries.
- Exact SHA-256 and configurable shingle-Jaccard near deduplication.
- Record-balanced grouped splits that never divide a `document_id`.
- Cross-split group, exact-text, and near-text contamination audits.
- Corpus statistics and manifests containing input/output sizes and SHA-256 hashes.
- Dependency-free exact-match, token-F1, and objective-choice helpers.

The built-in tokenizer is intentionally model-independent and reproducible. If publication statistics must use a specific model tokenizer, calculate those additional counts upstream and record the tokenizer revision in the manifest.

## Corpus Contract

Each output row contains `document_id`, `chunk_id`, `text`, `language`, `domain`, `task`, `source_type`, `source_uri`, `metadata`, `content_sha256`, `token_count`, and `chunk_index`. Supported languages are `en`, `ja`, and `zh`; supported domains are `marine_engineering` and `offshore_wind`.

Fallback document IDs are derived from `source_uri`, or normalized content when no usable URI exists. They never depend on source line order. Chunk IDs are `<document_id>:<zero-padded-index>`.

## Benchmark Contract

Objective records require at least two unique `choices`, an `answer` exactly equal to one choice, and no `reference_answer`. Open-ended records require `reference_answer` and prohibit `choices` and `answer`. Every record requires evidence document IDs and one of `easy`, `medium`, or `hard`.

## Commands

```bash
python -m iwind.data_engineering.build_corpus \
  --input data/raw.jsonl \
  --output-dir data/processed \
  --max-tokens 2048 \
  --overlap-tokens 128 \
  --near-dedup-threshold 0.90 \
  --require-provenance

python -m iwind.data_engineering.build_benchmarks \
  --input data/benchmark_source.jsonl \
  --output-dir data/benchmarks

python -m iwind.data_engineering.contamination_audit \
  --train data/processed/corpus_train.jsonl \
  --validation data/processed/corpus_validation.jsonl \
  --test data/processed/corpus_test.jsonl \
  --output data/processed/contamination.json \
  --fail-on-findings
```

Near-deduplication is an exact pairwise Jaccard implementation intended for curated corpora and defensible audits. For web-scale collections, use an upstream LSH/MinHash system and preserve its decisions in provenance metadata.

## Tests

```bash
python -m unittest discover -s iwind/data_engineering/tests -v
```
