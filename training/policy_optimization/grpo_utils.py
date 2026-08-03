"""GRPO validation, callbacks, comparative export, and checkpoint helpers."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from statistics import mean
from typing import Any, Callable, Iterable

from transformers import TrainerCallback
from transformers.trainer_utils import get_last_checkpoint


def validate_grpo_config(config: dict[str, Any], world_size: int | None = None) -> None:
    required = (
        "policy_model_path", "train_file", "validation_file", "output_dir", "num_generations",
        "per_device_train_batch_size", "gradient_accumulation_steps", "temperature", "top_p",
        "max_prompt_length", "max_completion_length",
    )
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"Missing GRPO configuration fields: {missing}")
    if int(config["num_generations"]) < 2:
        raise ValueError("num_generations must be at least 2 for group-relative optimization")
    if float(config["temperature"]) <= 0:
        raise ValueError("temperature must be positive")
    if not 0 < float(config["top_p"]) <= 1:
        raise ValueError("top_p must be in (0, 1]")
    for key in ("max_prompt_length", "max_completion_length", "per_device_train_batch_size", "gradient_accumulation_steps"):
        if int(config[key]) <= 0:
            raise ValueError(f"{key} must be positive")
    size = int(os.environ.get("WORLD_SIZE", "1")) if world_size is None else world_size
    generation_count = int(config["num_generations"])
    global_train_batch = int(config["per_device_train_batch_size"]) * size
    if global_train_batch % generation_count != 0:
        raise ValueError(f"Global train batch size {global_train_batch} must be divisible by num_generations={generation_count}")
    if "per_device_eval_batch_size" in config:
        global_eval_batch = int(config["per_device_eval_batch_size"]) * size
        if global_eval_batch % generation_count != 0:
            raise ValueError(f"Global evaluation batch size {global_eval_batch} must be divisible by num_generations={generation_count}")
    transport = config.get("reward_transport", "local")
    if transport == "local" and not config.get("reward_model_path"):
        raise ValueError("Local reward transport requires reward_model_path")
    if transport == "http" and not config.get("reward_endpoint"):
        raise ValueError("HTTP reward transport requires reward_endpoint")


def resolve_resume_checkpoint(output_dir: str, resume: str) -> str | None:
    if resume == "none":
        return None
    if resume == "auto":
        return get_last_checkpoint(output_dir)
    path = Path(resume)
    if not path.is_dir():
        raise ValueError(f"Resume checkpoint does not exist: {resume}")
    return str(path)


class JsonlMetricsCallback(TrainerCallback):
    def __init__(self, output_dir: str) -> None:
        self.path = Path(output_dir) / "metrics.jsonl"

    def on_log(self, args, state, control, logs=None, **kwargs):
        if not state.is_world_process_zero or not logs:
            return control
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {"step": state.global_step, **logs}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return control


def comparative_evaluation(
    records: Iterable[dict[str, Any]],
    baseline_generate: Callable[[Any], Any],
    policy_generate: Callable[[Any], Any],
    reward_function: Callable[..., list[float]],
) -> dict[str, Any]:
    rows = []
    for record in records:
        prompt = record["prompt"]
        baseline = baseline_generate(prompt)
        policy = policy_generate(prompt)
        scores = reward_function([prompt, prompt], [baseline, policy], sample_id=[record.get("sample_id")] * 2)
        rows.append({**record, "baseline_completion": baseline, "policy_completion": policy, "baseline_reward": scores[0], "policy_reward": scores[1]})
    deltas = [row["policy_reward"] - row["baseline_reward"] for row in rows]
    return {
        "examples": rows,
        "summary": {
            "count": len(rows),
            "baseline_mean_reward": mean(row["baseline_reward"] for row in rows) if rows else 0.0,
            "policy_mean_reward": mean(row["policy_reward"] for row in rows) if rows else 0.0,
            "mean_reward_delta": mean(deltas) if deltas else 0.0,
            "policy_win_rate": sum(delta > 0 for delta in deltas) / len(deltas) if deltas else 0.0,
            "tie_rate": sum(delta == 0 for delta in deltas) / len(deltas) if deltas else 0.0,
        },
    }


def export_evaluation(result: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def export_model_artifact(trainer: Any, processing_class: Any, output_dir: Path, source_checkpoint: str | None) -> None:
    """Export inference files with provenance, without presenting them as a resumable checkpoint."""
    output_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(output_dir))
    if processing_class is not None:
        processing_class.save_pretrained(str(output_dir))
    provenance = {"source_checkpoint": source_checkpoint, "artifact_type": "inference_export"}
    (output_dir / "export_manifest.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def copy_comparative_report(report: Path, export_dir: Path) -> None:
    if not report.is_file():
        raise ValueError(f"Comparative report does not exist: {report}")
    export_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(report, export_dir / report.name)
