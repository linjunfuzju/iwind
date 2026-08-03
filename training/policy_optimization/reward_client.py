"""Local and HTTP reward clients behind one validated batch protocol."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol, Sequence

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class RewardClient(Protocol):
    def score(self, prompts: Sequence[Any], completions: Sequence[Any], metadata: Sequence[dict[str, Any]] | None = None) -> list[float]: ...


def conversation_content(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(str(item.get("content", "")) for item in value if isinstance(item, dict)).strip()
    raise TypeError(f"Unsupported conversation value: {type(value)!r}")


def validate_scores(scores: Any, expected: int) -> list[float]:
    if not isinstance(scores, list) or len(scores) != expected:
        raise ValueError(f"Reward service returned {len(scores) if isinstance(scores, list) else 'non-list'} scores; expected {expected}")
    normalized = [float(score) for score in scores]
    if not bool(torch.isfinite(torch.tensor(normalized, dtype=torch.float32)).all()):
        raise ValueError("Reward service returned non-finite scores")
    return normalized


def resolve_reward_device(device: str, local_rank: int | None = None) -> torch.device:
    """Resolve placement explicitly; 'rank' maps each process to its LOCAL_RANK GPU."""
    if device == "rank":
        rank = int(os.environ.get("LOCAL_RANK", "0")) if local_rank is None else local_rank
        if not torch.cuda.is_available():
            raise RuntimeError("reward_device='rank' requires CUDA")
        if rank < 0 or rank >= torch.cuda.device_count():
            raise ValueError(f"LOCAL_RANK {rank} is outside visible CUDA devices")
        return torch.device(f"cuda:{rank}")
    resolved = torch.device(device)
    if resolved.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError(f"Requested reward device {device!r}, but CUDA is unavailable")
    return resolved


class LocalRewardClient:
    def __init__(self, model_path: str, max_length: int, device: str = "rank", adapter: str = "scalar_logits") -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
        if self.tokenizer.pad_token_id is None:
            if self.tokenizer.eos_token_id is None:
                raise ValueError("Reward tokenizer has neither pad_token_id nor eos_token_id")
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.device = resolve_reward_device(device)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            torch_dtype="auto",
            trust_remote_code=True,
        ).to(self.device)
        self.model.config.pad_token_id = self.tokenizer.pad_token_id
        self.model.eval()
        self.max_length = max_length
        self.adapter = adapter

    def _scalar_scores(self, outputs: Any) -> torch.Tensor:
        logits = outputs.logits
        if logits.ndim == 1:
            return logits
        if logits.ndim == 2 and logits.shape[-1] == 1:
            return logits[:, 0]
        if self.adapter == "quantile_mean" and logits.ndim == 2 and logits.shape[-1] > 1:
            return logits.float().mean(dim=-1)
        raise ValueError(f"Reward adapter {self.adapter!r} cannot consume logits shape {tuple(logits.shape)}")

    def score(self, prompts, completions, metadata=None) -> list[float]:
        if len(prompts) != len(completions):
            raise ValueError("Reward prompt and completion counts differ")
        if metadata is not None and len(metadata) != len(prompts):
            raise ValueError("Reward metadata count differs from prompt count")
        conversations = []
        for prompt, completion in zip(prompts, completions):
            prompt_messages = prompt if isinstance(prompt, list) else [{"role": "user", "content": conversation_content(prompt)}]
            conversations.append(prompt_messages + [{"role": "assistant", "content": conversation_content(completion)}])
        texts = [self.tokenizer.apply_chat_template(value, tokenize=False, add_generation_prompt=False) for value in conversations]
        batch = self.tokenizer(texts, padding=True, truncation=True, max_length=self.max_length, return_tensors="pt")
        batch = {key: value.to(self.device) for key, value in batch.items()}
        with torch.inference_mode():
            scores = self._scalar_scores(self.model(**batch)).float().cpu().tolist()
        return validate_scores(scores, len(prompts))


@dataclass
class HTTPRewardClient:
    endpoint: str
    timeout_seconds: float = 30.0
    retries: int = 2
    retry_backoff_seconds: float = 0.5
    auth_token: str | None = None

    def score(self, prompts, completions, metadata=None) -> list[float]:
        if len(prompts) != len(completions):
            raise ValueError("Reward prompt and completion counts differ")
        payload = json.dumps({"prompts": prompts, "completions": completions, "metadata": metadata}, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        request = urllib.request.Request(self.endpoint, data=payload, headers=headers, method="POST")
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    body = json.loads(response.read().decode("utf-8"))
                if not isinstance(body, dict) or "scores" not in body:
                    raise ValueError("Reward service response must contain a scores field")
                return validate_scores(body["scores"], len(prompts))
            except (urllib.error.URLError, TimeoutError):
                if attempt == self.retries:
                    raise
                time.sleep(self.retry_backoff_seconds * (2**attempt))
        raise AssertionError("unreachable")


class TRLRewardFunction:
    """Named callable preserving extra dataset columns as request metadata."""

    __name__ = "domain_reward"

    def __init__(self, client: RewardClient) -> None:
        self.client = client

    def __call__(self, prompts, completions, **kwargs) -> list[float]:
        metadata = []
        for index in range(len(prompts)):
            metadata.append({key: values[index] for key, values in kwargs.items() if isinstance(values, (list, tuple)) and len(values) == len(prompts)})
        return self.client.score(prompts, completions, metadata)


def build_reward_function(config: dict[str, Any]) -> TRLRewardFunction:
    transport = config.get("reward_transport", "local")
    if transport == "local":
        client = LocalRewardClient(
            config["reward_model_path"],
            config["reward_max_length"],
            device=config.get("reward_device", "rank"),
            adapter=config.get("reward_adapter", "scalar_logits"),
        )
    elif transport == "http":
        client = HTTPRewardClient(
            endpoint=config["reward_endpoint"],
            timeout_seconds=float(config.get("reward_timeout_seconds", 30)),
            retries=int(config.get("reward_retries", 2)),
            auth_token=os.environ.get(config.get("reward_auth_token_env", "IWIND_REWARD_TOKEN")),
        )
    else:
        raise ValueError(f"Unsupported reward_transport {transport!r}")
    return TRLRewardFunction(client)
