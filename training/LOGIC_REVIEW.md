# Static Logic Review

This review records the principal corrections applied while extracting and completing the original notebook logic as Python modules. Model training and GPU inference remain external runtime activities; pure data, schema, statistical, packing, protocol, and retrieval logic is covered by local unit tests.

## Dataset Construction

- Unified `Article`, `article`, `content`, and `text` into one explicit `text` field.
- Added stable document and chunk identifiers, provenance, content hashes, and group-level splits.
- Replaced misleading filename-based sample counts with manifest counts.
- Added exact and near-duplicate detection with explicit rejection reasons.
- Added grouped splitting, contamination checks, corpus statistics, and hash-addressed manifests.
- Added strict multilingual benchmark validation for both objective and open-ended questions.

## Domain Pretraining

- Isolated continued causal pretraining from instruction tuning.
- Added validated config-relative paths and automatic latest-checkpoint discovery.
- Replaced map-batch-local grouping with deterministic global packing and explicit EOS boundaries.
- Derived perplexity from validation loss rather than generation output.
- Kept DeepSpeed launcher arguments outside the training script configuration.

## Supervised Fine-Tuning

- Replaced manual prompt concatenation with the tokenizer's native chat template.
- Removed `DataCollatorForLanguageModeling` from SFT because it can overwrite prepared labels.
- Masked all system, user, and padding tokens with `-100`.
- Allowed every assistant turn to contribute to loss and added supervision-preserving truncation.
- Removed unsupported metadata fields from model forward inputs.
- Separated LoRA adapter training from standalone merged-model export.

## Reward Model

- Implemented deterministic question-group splitting before preference-pair expansion.
- Added executable five-level rubric validation, deterministic pair IDs, manifests, and quality-gap statistics.
- Documented that prompt-controlled synthetic quality levels are not equivalent to expert labels.
- Unified reward training and inference formatting through the tokenizer chat template.
- Added explicit scalar-logit and quantile-mean adapter boundaries instead of silently selecting an output.
- Included possible QRM gating and quantile head names in trainable-parameter selection.
- Avoided unsafe global `torch.load` monkey patches.

## GRPO

- Passed all configured GRPO fields through a version-aware constructor check.
- Added the previously ignored maximum prompt length.
- Removed the false claim that a callback performed early stopping when it only saved a model.
- Replaced one-forward-pass-per-completion reward scoring with batch scoring.
- Added explicit per-rank local placement and a versioned HTTP reward-service boundary.
- Made reward failures explicit rather than converting them into zero rewards.
- Preserved native Trainer checkpoints for resume and kept exported models conceptually separate.
- Did not claim an entropy coefficient that is not explicitly implemented by the selected TRL API.

## Evaluation and Quantization

- Separated objective accuracy from expert-rated open-ended dimensions.
- Added deterministic quantization comparison helpers separately from stochastic evaluation protocols.
- Added calibration deduplication, deterministic sampling, exact allocation, mandatory shortfall handling, and exact/near leakage exclusion.
- Rejected empty calibration data and unsafe source/output path relationships.
- Removed character-based response slicing; generation clients consume structured API responses.
- Added benchmark and expert-rating schemas, Wilson/bootstrap intervals, and paired SFT-versus-GRPO comparison.
- Added atomic artifact manifests, stable citation contracts, lexical/dense/structured retrieval adapters, rank fusion, context budgeting, and RAG metrics.

## Remaining Research Requirements

- Verify the exact `QRM-Llama3.1-8B-v2` custom output API and revision before training.
- Freeze and publish real dataset manifests, annotation guidelines, adjudication records, and split hashes.
- Validate dependency and CUDA compatibility on the target cluster.
- Bind the provided lexical, dense callback, structured, and reranking interfaces to the production Iwind indexes.
- Run blinded expert evaluation, inter-rater agreement, ablations, and the implemented SFT-versus-GRPO statistical comparison on frozen artifacts.
- Record all model revisions, prompt templates, hardware, random seeds, excluded samples, and release hashes in the paper artifacts.
