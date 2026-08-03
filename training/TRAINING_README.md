# Iwind Domain Model Training Pipeline

This directory contains the reconstructed, model-oriented source code for the Iwind offshore wind and marine engineering language-model pipeline. The original notebooks were removed after their useful logic was reviewed, corrected, and converted into auditable Python modules.

## Research Pipeline

| Module | Purpose | Primary Model or Artifact |
|---|---|---|
| `data_engineering` | Corpus normalization, filtering, deduplication, splitting, and multilingual benchmark construction | Training and benchmark datasets |
| `domain_pretraining` | Continued autoregressive domain pretraining | `DeepSeek-R1-0528-Qwen3-8B` |
| `instruction_tuning` | Instruction alignment with LoRA and assistant-only loss | Domain SFT model |
| `reward_modeling` | Pairwise preference learning with five-level quality metadata | `QRM-Llama3.1-8B-v2` |
| `policy_optimization` | Group Relative Policy Optimization using the reward model | GRPO policy model |
| `evaluation_and_integration` | Full-cycle evaluation, GPTQ export, and three-path RAG integration contracts | Final Iwind inference model |

## Design Principles

- All extracted source code, comments, configuration keys, and documentation are in English.
- Every JSONL format has an explicit schema and stable identifiers.
- Training, validation, test, calibration, and benchmark partitions must be isolated before model training.
- Native tokenizer chat templates are used instead of manually concatenated special tokens.
- SFT loss is applied only to assistant tokens and never to padding tokens.
- Reward data is split by question group before preference-pair expansion to prevent leakage.
- Reward-service failures are errors, not valid zero-valued rewards.
- Checkpoints and publishable model releases are treated as different artifacts.
- Evaluation separates deterministic model fidelity from stochastic generation robustness.
- The final answer generator must distinguish retrieved evidence, engineering assumptions, and unsupported claims.

## Expected Execution Order

```text
data_engineering
  -> domain_pretraining
  -> instruction_tuning
  -> reward_modeling
  -> policy_optimization
  -> evaluation_and_integration
```

Each module has its own `README.md`, `requirements.txt`, configuration files, Python entry points, and local unit tests for core logic. Paths in example configurations are placeholders and must be changed to match the target cluster.

## Implementation Coverage

- `data_engineering`: strict records, stable identifiers, deterministic chunking, exact and near deduplication, grouped splitting, contamination audit, statistics, and artifact manifests.
- `domain_pretraining`: validated configuration, deterministic global token packing, explicit EOS boundaries, retained-token accounting, training, checkpoint resume, and perplexity helpers.
- `instruction_tuning`: strict conversation validation, assistant-only labels, supervision-preserving truncation, LoRA training, evaluation helpers, and adapter merge safeguards.
- `reward_modeling`: executable five-level rubric, grouped preference preparation, deterministic pair expansion, scalar and quantile adapter boundaries, pairwise Trainer evaluation, and stratified metrics.
- `policy_optimization`: validated GRPO geometry, local and HTTP reward clients, explicit per-rank placement, reward server, rank-zero metrics callback, checkpoint handling, and comparative evaluation helpers.
- `evaluation_and_integration`: benchmark schemas, expert ratings, confidence intervals, paired SFT/GRPO comparison, calibration leakage checks, atomic GPTQ staging, performance aggregation, retrieval adapters, rank fusion, context budgeting, citation validation, and RAG metrics.

## Validation

Run all static checks and local logic tests from the repository root:

```bash
python iwind/validate_pipeline.py
```

The validator parses all Python and JSON files, checks that documentation and requirements are present, and runs the six module test suites. Data, packing, statistics, artifact, and RAG tests use the standard library. Reward and policy tests use the installed Torch and NumPy packages with mocked models. The validator does not download checkpoints or start training.

## Static Review Scope

The reconstructed code was checked statically for module boundaries, Python syntax, JSON configuration validity, data-field consistency, checkpoint semantics, and cross-stage path contracts. No packages were installed and no model training, inference, quantization, or distributed process was started.

## Source Reconstruction

The original notebooks were removed after their training logic was reviewed and reconstructed into the modules above. The extracted implementation corrects known notebook-level inconsistencies rather than reproducing them verbatim.
