# Reward Modeling

This directory implements an auditable pairwise reward-model pipeline for offshore wind and marine engineering. It validates five-level rubric annotations, performs question-group-safe splitting, expands all cross-level preferences, records manifests and descriptive statistics, trains through an explicit reward-output adapter, and evaluates pairwise ranking behavior.

## Executable Rubric

`rubric.py` defines the only accepted ordinal levels:

Portable Draft 2020-12 schemas are provided in `schemas/question_group.schema.json` and `schemas/preference_pair.schema.json`. `rubric.py` additionally enforces cross-record and ordering constraints that JSON Schema alone cannot express, including unique response IDs, unique question IDs, and the presence of at least two distinct levels.

| Level | Name | Operational definition |
|---|---|---|
| 1 | Unacceptable | Material technical errors, unsafe advice, poor relevance, or incoherent reasoning |
| 2 | Limited | Mostly relevant but shallow, incomplete, or materially imprecise |
| 3 | Competent | Correct core answer and acceptable logic with incomplete engineering coverage |
| 4 | Strong | Accurate, rigorous, clear, and multi-perspective engineering analysis |
| 5 | Expert | Comprehensive, evidence-aware, uncertainty-aware, and operationally useful analysis |

Input is JSONL with one complete question group per line:

```json
{
  "question_id": "question-000001",
  "question": "Assess the governing load combinations for this support structure.",
  "language": "en",
  "task": "structural_load_assessment",
  "source": "expert_panel_2026_01",
  "responses": [
    {"response_id": "r1", "text": "...", "level": 1, "annotator_id": "expert-03", "rationale": "..."},
    {"response_id": "r3", "text": "...", "level": 3, "annotator_id": "expert-07", "rationale": "..."},
    {"response_id": "r5", "text": "...", "level": 5, "annotator_id": "expert-03", "rationale": "..."}
  ]
}
```

Validation rejects missing fields, invalid levels, duplicate response IDs, duplicate question IDs, fewer than two responses, and groups with no cross-level ordering. Rubric labels remain metadata unless their provenance supports the claims made in a publication; synthetic labels must not be described as expert adjudication.

## Preparation

```bash
python prepare_preferences.py \
  --input data/question_groups.jsonl \
  --output-dir data \
  --seed 42 \
  --train-fraction 0.8 \
  --validation-fraction 0.1
```

The split is a stable SHA-256 assignment of `seed:question_id`. A question and every pair derived from it can occur in only one partition. Pair expansion emits every response combination with unequal levels exactly once, always placing the higher level in `chosen`; same-level ties are omitted. Original question metadata and response annotation metadata are retained.

`manifest.json` records schema version, source and output SHA-256 checksums, split parameters, question IDs, response/pair counts, level counts, quality-gap counts, tasks, and languages. Exact split proportions are expected only asymptotically because groups are indivisible.

## Reward Boundary

`reward_adapter.py` prevents model-specific output assumptions from leaking into training and evaluation:

- `scalar_logits` accepts only `[batch]` or `[batch, 1]` logits.
- `quantile_mean` explicitly averages a configured two-dimensional quantile field.

The default is `scalar_logits`. `quantile_mean` is an integration fallback, not an implementation of a particular QRM paper's distributional training objective. Before using a custom QRM revision, inspect its remote code, output field, quantile semantics, and documented loss. If the revision requires quantile targets, gating, uncertainty weighting, or another distributional objective, implement that exact objective rather than claiming exact QRM reproduction.

## Training

`PairwiseRewardTrainer` uses Bradley-Terry loss, emits prediction tensors shaped `[batch, 2]`, and emits labels containing preferred index and quality gap. This makes Hugging Face evaluation deterministic and supports overall and per-gap ranking metrics. The tokenizer padding ID is copied to `model.config.pad_token_id`; audit metadata is retained by preprocessing and collation but never forwarded to the model.

```bash
deepspeed --num_gpus 4 train_reward_model.py \
  --config configs/training.json \
  --deepspeed configs/deepspeed_zero2.json \
  --resume auto
```

Evaluate an exported model without training:

```bash
python evaluate_preferences.py \
  --model outputs/reward_model \
  --data data/test/preference_dataset.jsonl \
  --output outputs/reward_model/test_metrics.json \
  --reward-adapter scalar_logits
```

## Verification

The tests use small tensors, temporary files, and mocks only. They do not load external datasets or models.

```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```
