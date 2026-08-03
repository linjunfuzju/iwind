"""Validate, stage, and atomically export a GPTQ model using optional runtimes."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

try:
    from .artifacts import atomic_write_json, build_manifest, read_jsonl
except ImportError:
    from artifacts import atomic_write_json, build_manifest, read_jsonl


def resolve_path(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (base / path).resolve()


def validate_contract(config: dict[str, Any], base: Path) -> dict[str, Any]:
    source = resolve_path(config["source_model"], base)
    calibration = resolve_path(config["calibration_file"], base)
    output = resolve_path(config["output_dir"], base)
    if not source.is_dir():
        raise ValueError(f"source model directory does not exist: {source}")
    if not calibration.is_file():
        raise ValueError(f"calibration file does not exist: {calibration}")
    if output == source or source in output.parents or output in source.parents:
        raise ValueError("source and output must be separate, non-nested directories")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"output directory is not empty: {output}")
    if config.get("bits") not in {2, 3, 4, 8}:
        raise ValueError("bits must be one of 2, 3, 4, or 8")
    if int(config.get("group_size", 0)) == 0 or int(config["group_size"]) < -1:
        raise ValueError("group_size must be -1 or a positive integer")
    if not 0 <= float(config.get("damp_percent", -1)) <= 1:
        raise ValueError("damp_percent must be in [0, 1]")
    records = read_jsonl(calibration)
    texts = [record.get("text") for record in records]
    if not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError("calibration records require non-empty text")
    return {"source": source, "calibration": calibration, "output": output, "texts": texts}


def quantize(config: dict[str, Any], base: Path) -> Path:
    contract = validate_contract(config, base)
    try:
        from gptqmodel import GPTQModel, QuantizeConfig
        from transformers import AutoTokenizer
    except ImportError as error:
        raise RuntimeError("quantization requires the pinned optional GPTQ runtime dependencies") from error
    output: Path = contract["output"]
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.stage-", dir=output.parent))
    try:
        quantization = QuantizeConfig(
            bits=config["bits"], group_size=config["group_size"], damp_percent=config["damp_percent"],
            desc_act=config["desc_act"], static_groups=config["static_groups"], sym=config["sym"],
            true_sequential=config["true_sequential"],
        )
        tokenizer = AutoTokenizer.from_pretrained(contract["source"], trust_remote_code=config.get("trust_remote_code", False))
        model = GPTQModel.from_pretrained(
            contract["source"], quantize_config=quantization, device_map=config.get("device_map", "auto"),
            trust_remote_code=config.get("trust_remote_code", False),
        )
        model.quantize(contract["texts"])
        model.save_quantized(stage)
        tokenizer.save_pretrained(stage)
        required = config.get("required_export_files", ["config.json"])
        missing = [name for name in required if not (stage / name).is_file()]
        if missing:
            raise RuntimeError(f"staged export is missing required files: {missing}")
        files = [path for path in stage.rglob("*") if path.is_file()]
        manifest = build_manifest("gptq_export", files, {
            "source_model": str(contract["source"]), "calibration_file": str(contract["calibration"]),
            "bits": config["bits"], "group_size": config["group_size"], "trust_remote_code": config.get("trust_remote_code", False),
        })
        for artifact in manifest["artifacts"]:
            artifact["path"] = str(Path(artifact["path"]).relative_to(stage))
        atomic_write_json(stage / "export_manifest.json", manifest)
        if output.exists():
            output.rmdir()
        os.replace(stage, output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    path = args.config.resolve()
    config = json.loads(path.read_text(encoding="utf-8"))
    contract = validate_contract(config, path.parent)
    if args.validate_only:
        print(json.dumps({key: str(value) if isinstance(value, Path) else len(value) for key, value in contract.items()}, indent=2))
        return
    print(quantize(config, path.parent))


if __name__ == "__main__":
    main()
