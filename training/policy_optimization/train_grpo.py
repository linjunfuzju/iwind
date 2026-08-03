"""Group Relative Policy Optimization for the Iwind SFT model."""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path

from datasets import load_dataset
from transformers import set_seed
from trl import GRPOConfig, GRPOTrainer

try:
    from .grpo_data import prepare_dataset
    from .grpo_utils import JsonlMetricsCallback, resolve_resume_checkpoint, validate_grpo_config
    from .reward_client import build_reward_function
except ImportError:  # Support direct execution from this directory.
    from grpo_data import prepare_dataset
    from grpo_utils import JsonlMetricsCallback, resolve_resume_checkpoint, validate_grpo_config
    from reward_client import build_reward_function


def supported_grpo_arguments(values: dict) -> dict:
    parameters = inspect.signature(GRPOConfig.__init__).parameters
    unsupported = sorted(key for key in values if key not in parameters)
    if unsupported:
        raise ValueError(f"Installed TRL does not support configured GRPO arguments: {unsupported}")
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--deepspeed")
    parser.add_argument("--resume", default="none")
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    validate_grpo_config(config)
    set_seed(config["seed"])

    raw = load_dataset("json", data_files={"train": config["train_file"], "validation": config["validation_file"]})
    train_dataset = prepare_dataset(raw["train"], config["system_prompt"])
    validation_dataset = prepare_dataset(raw["validation"], config["system_prompt"])
    reward = build_reward_function(config)

    values = {
        "output_dir": config["output_dir"],
        "per_device_train_batch_size": config["per_device_train_batch_size"],
        "per_device_eval_batch_size": config["per_device_eval_batch_size"],
        "gradient_accumulation_steps": config["gradient_accumulation_steps"],
        "learning_rate": config["learning_rate"],
        "num_train_epochs": config["num_train_epochs"],
        "logging_steps": config["logging_steps"],
        "eval_strategy": "steps",
        "eval_steps": config["eval_steps"],
        "save_strategy": "steps",
        "save_steps": config["save_steps"],
        "save_total_limit": config["save_total_limit"],
        "num_generations": config["num_generations"],
        "temperature": config["temperature"],
        "top_p": config["top_p"],
        "epsilon": config["epsilon"],
        "beta": config["beta"],
        "max_prompt_length": config["max_prompt_length"],
        "max_completion_length": config["max_completion_length"],
        "warmup_steps": config["warmup_steps"],
        "max_grad_norm": config["max_grad_norm"],
        "bf16": config["bf16"],
        "deepspeed": args.deepspeed,
        "report_to": ["tensorboard"],
        "remove_unused_columns": False,
        "seed": config["seed"],
    }
    trainer = GRPOTrainer(
        model=config["policy_model_path"],
        reward_funcs=[reward],
        args=GRPOConfig(**supported_grpo_arguments(values)),
        train_dataset=train_dataset,
        eval_dataset=validation_dataset,
        callbacks=[JsonlMetricsCallback(config["output_dir"])],
    )
    checkpoint = resolve_resume_checkpoint(config["output_dir"], args.resume)
    trainer.train(resume_from_checkpoint=checkpoint)
    trainer.save_model(config["output_dir"])


if __name__ == "__main__":
    main()
