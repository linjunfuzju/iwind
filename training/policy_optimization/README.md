# GRPO Policy Optimization

This directory implements Group Relative Policy Optimization from an SFT policy using a transport-neutral domain reward boundary. It preserves prompt metadata, validates configuration against both research invariants and the installed TRL API, records JSONL metrics, supports resumable Trainer checkpoints, and provides comparative evaluation and inference-export helpers.

## Prompt Schema

```json
{
  "sample_id": "grpo-000001",
  "prompt": "Analyze the coupled effect of mooring-line stiffness and extreme wave loading.",
  "language": "en",
  "task": "mooring_analysis",
  "source": "held_out_prompt_bank"
}
```

`grpo_data.py` replaces only `prompt` with the system/user conversation and retains all other columns. These columns are passed by TRL to the named `domain_reward` callable and forwarded as per-example metadata. GRPO prompts are reference-free and must be checked for question-level overlap with training and benchmark sets before publication.

## Reward Protocol

`RewardClient.score(prompts, completions, metadata)` returns one finite float per input. Count mismatches, malformed responses, timeouts after retries, and non-finite scores raise errors; failures are never converted to zero rewards.

Local mode loads one reward model per training process. Placement is explicit:

- `reward_device: "rank"` maps the process to `cuda:$LOCAL_RANK` and validates the visible device range.
- `reward_device: "cuda:4"` pins every process to a specified GPU and is generally appropriate only for a single-process launch.
- `reward_device: "cpu"` is explicit CPU inference.

There is no `device_map="auto"`. For multi-process GRPO, local mode duplicates reward-model memory once per rank. Use HTTP mode when a dedicated reward GPU or separate node should serve all policy ranks.

HTTP request to `/score`:

```json
{"prompts": ["..."], "completions": ["..."], "metadata": [{"sample_id": "..."}]}
```

HTTP response:

```json
{"scores": [1.25]}
```

Start a dedicated server on an explicitly selected GPU:

```bash
IWIND_REWARD_TOKEN=replace-me python reward_server.py \
  --model ../reward_modeling/outputs/reward_model \
  --host 127.0.0.1 \
  --port 8080 \
  --device cuda:4 \
  --max-length 2048
```

Set these training configuration fields for HTTP mode:

```json
{
  "reward_transport": "http",
  "reward_endpoint": "http://127.0.0.1:8080/score",
  "reward_timeout_seconds": 30,
  "reward_retries": 2,
  "reward_auth_token_env": "IWIND_REWARD_TOKEN"
}
```

The standard-library threaded server serializes model inference with a lock, caps batch size, supports `/health`, and optionally requires a bearer token. Put TLS, request-size limits, rate limiting, and network authentication in a production reverse proxy; do not expose the bare server publicly.

## Validation And Training

`validate_grpo_config` checks required fields, positive lengths and sampling temperature, valid top-p, at least two generations, reward transport settings, and divisibility of the global per-step train and evaluation batches by `num_generations`. Gradient accumulation is deliberately excluded from this calculation because TRL constructs generation groups before accumulated optimizer steps. `supported_grpo_arguments` separately rejects configuration keys unavailable in the installed TRL version.

```bash
deepspeed --num_gpus 4 train_grpo.py \
  --config configs/training.json \
  --deepspeed configs/deepspeed_zero2.json \
  --resume auto
```

`--resume auto` resumes only from a native Trainer checkpoint under `output_dir`. An explicit checkpoint path must exist. `JsonlMetricsCallback` writes rank-zero logs to `metrics.jsonl` for independent analysis.

## Evaluation And Export

`grpo_utils.py` provides:

- `comparative_evaluation` to generate baseline and optimized completions for the same records, score both in one reward request, and report mean rewards, mean delta, win rate, and tie rate.
- `export_evaluation` to write a deterministic JSON report with examples and aggregate statistics.
- `export_model_artifact` to save inference files plus `export_manifest.json` provenance. An inference export is deliberately not represented as a resumable checkpoint.
- `resolve_resume_checkpoint` to enforce native checkpoint semantics.

Reward-model comparisons are useful diagnostics but are not independent quality evidence when the same reward model trained the policy. Publication-grade evaluation should additionally include blinded human comparison, safety/error categories, task-stratified confidence intervals, and contamination checks.

## QRM Assumptions

Local reward inference supports strict scalar logits and an explicit `quantile_mean` fallback. The fallback assumes the output columns are commensurate quantile values whose arithmetic mean is a valid scalar ranking score. It does not implement QRM-specific gating, calibration, uncertainty aggregation, or a distributional training loss. Confirm the exact remote-code revision before claiming exact QRM compatibility.

## Verification

Tests mock framework and network boundaries and never download models:

```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```
