"""LoRA supervised fine-tuning with assistant-only cross-entropy loss."""

from __future__ import annotations

import argparse
from pathlib import Path

from datasets import load_dataset
from peft import LoraConfig, TaskType, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, EarlyStoppingCallback, Trainer, TrainingArguments, set_seed
from transformers.trainer_utils import get_last_checkpoint

try:
    from .config import load_config
    from .sft_data import AssistantOnlyCollator, SFTRecord, encode_messages
except ImportError:  # Support direct execution from this directory.
    from config import load_config
    from sft_data import AssistantOnlyCollator, SFTRecord, encode_messages


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--deepspeed")
    parser.add_argument("--resume", default="none", help="none, auto, or a checkpoint path")
    args = parser.parse_args()
    config = load_config(args.config)
    set_seed(config.seed)

    tokenizer = AutoTokenizer.from_pretrained(config.model_name_or_path, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        if tokenizer.eos_token_id is None:
            raise ValueError("the tokenizer must define either a pad or EOS token")
        tokenizer.pad_token = tokenizer.eos_token
    raw = load_dataset("json", data_files={"train": str(config.train_file), "validation": str(config.validation_file)})

    def preprocess(record):
        validated = SFTRecord.from_dict(record)
        return encode_messages(list(validated.messages), tokenizer, config.max_length, truncation=config.truncation)

    train_dataset = raw["train"].map(preprocess, remove_columns=raw["train"].column_names, desc="Preparing SFT train data")
    validation_dataset = raw["validation"].map(
        preprocess, remove_columns=raw["validation"].column_names, desc="Preparing SFT validation data"
    )
    model = AutoModelForCausalLM.from_pretrained(
        config.model_name_or_path, torch_dtype="auto", trust_remote_code=True, use_cache=False
    )
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    model = get_peft_model(
        model,
        LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=config.lora_r,
            lora_alpha=config.lora_alpha,
            lora_dropout=config.lora_dropout,
            bias="none",
            target_modules=list(config.target_modules),
        ),
    )
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
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        bf16=config.bf16,
        deepspeed=args.deepspeed,
        report_to=["tensorboard"],
        remove_unused_columns=False,
        seed=config.seed,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        data_collator=AssistantOnlyCollator(tokenizer, pad_to_multiple_of=8),
        processing_class=tokenizer,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=config.early_stopping_patience)],
    )
    checkpoint = get_last_checkpoint(str(config.output_dir)) if args.resume == "auto" else None if args.resume == "none" else args.resume
    trainer.train(resume_from_checkpoint=checkpoint)
    trainer.save_model(config.output_dir)
    tokenizer.save_pretrained(config.output_dir)


if __name__ == "__main__":
    main()
