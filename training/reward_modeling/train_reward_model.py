"""Pairwise reward-model training with explicit scalar-output validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch
import torch.nn.functional as F
from datasets import load_dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, EarlyStoppingCallback, Trainer, TrainingArguments, set_seed
from transformers.trainer_utils import get_last_checkpoint

try:
    from .reward_adapter import build_reward_adapter
    from .reward_data import PairwiseRewardCollator, format_pair
    from .reward_metrics import pairwise_reward_metrics
except ImportError:  # Support direct execution from this directory.
    from reward_adapter import build_reward_adapter
    from reward_data import PairwiseRewardCollator, format_pair
    from reward_metrics import pairwise_reward_metrics


def configure_trainable_parameters(model, last_n_layers: int, head_patterns: list[str]) -> None:
    layer_count = getattr(model.config, "num_hidden_layers", None)
    layer_patterns = [] if layer_count is None else [f".{index}." for index in range(max(0, layer_count - last_n_layers), layer_count)]
    for name, parameter in model.named_parameters():
        parameter.requires_grad = any(pattern in name for pattern in layer_patterns + head_patterns)
    if not any(parameter.requires_grad for parameter in model.parameters()):
        raise ValueError("No trainable reward-model parameters were selected")


class PairwiseRewardTrainer(Trainer):
    def __init__(self, *args, reward_adapter, **kwargs):
        super().__init__(*args, **kwargs)
        self.reward_adapter = reward_adapter

    def _pair_scores(self, model, inputs):
        chosen = model(input_ids=inputs["chosen_input_ids"], attention_mask=inputs["chosen_attention_mask"])
        rejected = model(input_ids=inputs["rejected_input_ids"], attention_mask=inputs["rejected_attention_mask"])
        return self.reward_adapter(chosen), self.reward_adapter(rejected)

    def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
        chosen_rewards, rejected_rewards = self._pair_scores(model, inputs)
        loss = -F.logsigmoid(chosen_rewards - rejected_rewards).mean()
        outputs = torch.stack((chosen_rewards, rejected_rewards), dim=-1)
        return (loss, outputs) if return_outputs else loss

    def prediction_step(self, model, inputs, prediction_loss_only, ignore_keys=None):
        inputs = self._prepare_inputs(inputs)
        with torch.no_grad():
            with self.compute_loss_context_manager():
                loss, scores = self.compute_loss(model, inputs, return_outputs=True)
        if prediction_loss_only:
            return loss.detach(), None, None
        gaps = inputs["quality_gap"]
        labels = torch.stack((torch.zeros_like(gaps), gaps), dim=-1)
        return loss.detach(), scores.detach(), labels.detach()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--deepspeed")
    parser.add_argument("--resume", default="none")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    set_seed(config["seed"])

    tokenizer = AutoTokenizer.from_pretrained(config["model_name_or_path"], trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        if tokenizer.eos_token_id is None:
            raise ValueError("Reward tokenizer has neither pad_token_id nor eos_token_id")
        tokenizer.pad_token = tokenizer.eos_token
    raw = load_dataset("json", data_files={"train": config["train_file"], "validation": config["validation_file"]})
    preprocess = lambda record: format_pair(record, tokenizer, config["max_length"])
    train_dataset = raw["train"].map(preprocess, remove_columns=raw["train"].column_names)
    validation_dataset = raw["validation"].map(preprocess, remove_columns=raw["validation"].column_names)

    model = AutoModelForSequenceClassification.from_pretrained(
        config["model_name_or_path"],
        num_labels=1,
        torch_dtype="auto",
        trust_remote_code=True,
        use_cache=False,
    )
    model.config.pad_token_id = tokenizer.pad_token_id
    configure_trainable_parameters(model, config["trainable_last_n_layers"], config["trainable_head_patterns"])
    training_args = TrainingArguments(
        output_dir=config["output_dir"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        per_device_eval_batch_size=config["per_device_eval_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        num_train_epochs=config["num_train_epochs"],
        warmup_ratio=config["warmup_ratio"],
        weight_decay=config["weight_decay"],
        logging_steps=config["logging_steps"],
        eval_strategy="steps",
        eval_steps=config["eval_steps"],
        save_strategy="steps",
        save_steps=config["save_steps"],
        save_total_limit=config["save_total_limit"],
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        bf16=config["bf16"],
        deepspeed=args.deepspeed,
        report_to=["tensorboard"],
        remove_unused_columns=False,
        seed=config["seed"],
    )
    trainer = PairwiseRewardTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        data_collator=PairwiseRewardCollator(tokenizer),
        processing_class=tokenizer,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=config["early_stopping_patience"])],
        compute_metrics=pairwise_reward_metrics,
        reward_adapter=build_reward_adapter(config),
    )
    checkpoint = get_last_checkpoint(config["output_dir"]) if args.resume == "auto" else None if args.resume == "none" else args.resume
    trainer.train(resume_from_checkpoint=checkpoint)
    trainer.save_model(config["output_dir"])
    tokenizer.save_pretrained(config["output_dir"])


if __name__ == "__main__":
    main()
