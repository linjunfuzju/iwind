# Supervised Fine-Tuning

This package aligns the domain-pretrained model with multilingual engineering instructions using LoRA and assistant-only causal-language-model loss.

## Strict Input Contract

Each JSONL row contains `sample_id`, `messages`, `language`, `task`, and optional `metadata`. Unknown fields are rejected. Messages contain exactly `role` and `content`, use non-empty content, and follow this ordering:

- An optional single `system` message appears first.
- A `user` message starts each exchange.
- Every `assistant` message follows a user message.
- The final message is an assistant response.

Supported languages are `en`, `ja`, and `zh`.

## Masking and Truncation

The tokenizer chat template is applied after every appended turn. The implementation verifies that serialization is prefix-stable, then labels only tokens introduced by assistant turns. User, system, and padding labels are `-100`.

`assistant_tail` truncation, the default, selects a window ending at the final supervised token so long prompts cannot silently remove all loss-bearing tokens. `right` preserves legacy right truncation and raises an error if it removes all assistant supervision. Dynamic padding can be rounded to a multiple of eight by the collator.

## Configuration

Configuration loading is strict. Data and output paths are resolved relative to the JSON file. LoRA target modules are configurable because projection names are architecture-dependent.

## Commands

```bash
deepspeed --num_gpus 4 iwind/instruction_tuning/train_sft.py \
  --config iwind/instruction_tuning/configs/training.json \
  --deepspeed iwind/instruction_tuning/configs/deepspeed_zero2.json \
  --resume auto

python iwind/instruction_tuning/merge_adapter.py \
  --base-model /shared/models/DeepSeek-R1-0528-Qwen3-8B \
  --adapter iwind/instruction_tuning/outputs/sft \
  --output iwind/instruction_tuning/outputs/sft_merged
```

External-model assumptions are that the chat template is append-prefix-stable, the configured LoRA module names exist, the model supports gradient checkpointing/input gradients, and the saved adapter directory contains tokenizer files for merging.

Pure-Python validation and masking tests do not load a model:

```bash
python -m unittest discover -s iwind/instruction_tuning/tests -v
```
