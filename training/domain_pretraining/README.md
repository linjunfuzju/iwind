# Domain Pretraining

This package performs continued causal-language-model pretraining on the normalized Iwind corpus. Its configuration, packing, and evaluation helpers are pure Python; model execution requires the packages listed in `requirements.txt`.

## Data and Packing Contract

Input files are JSONL records with non-empty `text`. Training and validation data must have disjoint `document_id` groups and should pass `iwind.data_engineering.contamination_audit` before training.

Documents are tokenized without automatically inserted special tokens, separated by the tokenizer EOS ID, and globally packed in deterministic dataset order. Packing spans the complete split instead of dropping a remainder at each mapping batch. The final partial block is retained by default; set `drop_remainder` to `true` only when fixed-length-only batches are required.

## Configuration

`config.load_config` rejects unknown/missing keys and invalid ranges. `train_file`, `validation_file`, and `output_dir` are resolved relative to the JSON configuration file, not the shell working directory. Input files are checked before model loading.

Important assumptions:

- The tokenizer defines an EOS token suitable as a document boundary.
- `trust_remote_code=True` is intentional for the selected model and must be security-reviewed.
- Validation perplexity is `exp(eval_loss)` with safe overflow handling.
- The Hugging Face model supports gradient checkpointing.

## Command

```bash
deepspeed --num_gpus 4 iwind/domain_pretraining/train.py \
  --config iwind/domain_pretraining/configs/training.json \
  --deepspeed iwind/domain_pretraining/configs/deepspeed_zero2.json \
  --resume auto
```

The model and data paths in the shipped configuration are placeholders. No training is required to run the utility tests:

```bash
python -m unittest discover -s iwind/domain_pretraining/tests -v
```
