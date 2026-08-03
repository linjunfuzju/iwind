"""Merge a trained LoRA adapter into a standalone causal language model."""

from __future__ import annotations

import argparse
from pathlib import Path

from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.base_model.exists():
        raise ValueError(f"base model path does not exist: {args.base_model}")
    if not args.adapter.is_dir():
        raise ValueError(f"adapter directory does not exist: {args.adapter}")
    if args.output.resolve() in {args.base_model.resolve(), args.adapter.resolve()}:
        raise ValueError("output must differ from base-model and adapter paths")
    base = AutoModelForCausalLM.from_pretrained(str(args.base_model), torch_dtype="auto", trust_remote_code=True)
    merged = PeftModel.from_pretrained(base, str(args.adapter)).merge_and_unload()
    args.output.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(args.output, safe_serialization=True)
    tokenizer_source = args.adapter if (args.adapter / "tokenizer_config.json").exists() else args.base_model
    AutoTokenizer.from_pretrained(str(tokenizer_source), trust_remote_code=True).save_pretrained(args.output)


if __name__ == "__main__":
    main()
