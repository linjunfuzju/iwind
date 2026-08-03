"""Continued causal-language-model pretraining for the Iwind domain model."""

from __future__ import annotations

import argparse
from pathlib import Path

from datasets import Dataset, load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
    set_seed,
)
from transformers.trainer_utils import get_last_checkpoint

try:
    from .config import load_config
    from .evaluation import perplexity
    from .packing import pack_token_sequences
except ImportError:  # Support direct execution from this directory.
    from config import load_config
    from evaluation import perplexity
    from packing import pack_token_sequences


def tokenize_corpus(dataset, tokenizer, max_length: int, *, drop_remainder: bool = False):
    """Tokenize records, then globally pack them in deterministic dataset order."""
    tokenized = dataset.map(
        lambda batch: tokenizer(batch["text"], add_special_tokens=False, truncation=False),
        batched=True,
        remove_columns=dataset.column_names,
        desc="Tokenizing corpus",
    )
    separator_id = tokenizer.eos_token_id
    packed = [
        block.to_dict()
        for block in pack_token_sequences(
            tokenized["input_ids"],
            max_length,
            separator_id=separator_id,
            drop_remainder=drop_remainder,
        )
    ]
    if not packed:
        raise ValueError("tokenization produced no training sequences")
    return Dataset.from_list(packed)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--deepspeed", type=str)
    parser.add_argument("--resume", default="none", help="none, auto, or a checkpoint path")
    args = parser.parse_args()
    config = load_config(args.config)
    set_seed(config.seed)

    tokenizer = AutoTokenizer.from_pretrained(config.model_name_or_path, trust_remote_code=True)
    if tokenizer.eos_token_id is None:
        raise ValueError("the tokenizer must define an EOS token for document separation")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    files = {"train": str(config.train_file), "validation": str(config.validation_file)}
    raw = load_dataset("json", data_files=files)
    train_dataset = tokenize_corpus(raw["train"], tokenizer, config.max_length, drop_remainder=config.drop_remainder)
    validation_dataset = tokenize_corpus(raw["validation"], tokenizer, config.max_length, drop_remainder=False)

    model = AutoModelForCausalLM.from_pretrained(
        config.model_name_or_path,
        torch_dtype="auto",
        trust_remote_code=True,
        use_cache=False,
    )
    model.gradient_checkpointing_enable()
    training_args = TrainingArguments(
        output_dir=str(config.output_dir),
        per_device_train_batch_size=config.per_device_train_batch_size,
        per_device_eval_batch_size=config.per_device_eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        num_train_epochs=config.num_train_epochs,
        warmup_ratio=config.warmup_ratio,
        weight_decay=config.weight_decay,
        logging_steps=config.logging_steps,
        eval_strategy="steps",
        eval_steps=config.eval_steps,
        save_strategy="steps",
        save_steps=config.save_steps,
        save_total_limit=config.save_total_limit,
        bf16=config.bf16,
        deepspeed=args.deepspeed,
        report_to=["tensorboard"],
        seed=config.seed,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False),
        processing_class=tokenizer,
    )
    checkpoint = get_last_checkpoint(str(config.output_dir)) if args.resume == "auto" else None if args.resume == "none" else args.resume
    trainer.train(resume_from_checkpoint=checkpoint)
    metrics = trainer.evaluate()
    metrics["perplexity"] = perplexity(float(metrics["eval_loss"]))
    trainer.save_metrics("eval", metrics)
    trainer.save_model()
    tokenizer.save_pretrained(config.output_dir)


if __name__ == "__main__":
    main()
