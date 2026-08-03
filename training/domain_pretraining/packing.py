"""Deterministic, global causal-LM token packing without framework dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence


@dataclass(frozen=True, slots=True)
class PackedSequence:
    input_ids: tuple[int, ...]
    attention_mask: tuple[int, ...]
    labels: tuple[int, ...]
    source_indices: tuple[int, ...]

    def to_dict(self) -> dict[str, list[int]]:
        return {
            "input_ids": list(self.input_ids),
            "attention_mask": list(self.attention_mask),
            "labels": list(self.labels),
        }


def pack_token_sequences(
    sequences: Iterable[Sequence[int]],
    block_size: int,
    *,
    separator_id: int | None = None,
    drop_remainder: bool = False,
) -> Iterator[PackedSequence]:
    """Pack in input order across all records, never losing batch-local remainders."""
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    buffer: list[int] = []
    owners: list[int] = []
    for source_index, sequence in enumerate(sequences):
        tokens = list(sequence)
        if any(not isinstance(token, int) or token < 0 for token in tokens):
            raise ValueError(f"sequence {source_index} contains an invalid token id")
        if not tokens:
            continue
        if buffer and separator_id is not None:
            buffer.append(separator_id)
            owners.append(source_index)
        buffer.extend(tokens)
        owners.extend([source_index] * len(tokens))
        while len(buffer) >= block_size:
            block = tuple(buffer[:block_size])
            source_indices = tuple(dict.fromkeys(owners[:block_size]))
            yield PackedSequence(block, (1,) * block_size, block, source_indices)
            del buffer[:block_size]
            del owners[:block_size]
    if buffer and not drop_remainder:
        block = tuple(buffer)
        yield PackedSequence(block, (1,) * len(block), block, tuple(dict.fromkeys(owners)))


def packing_statistics(packed: Iterable[PackedSequence], block_size: int) -> dict[str, float | int]:
    blocks = list(packed)
    tokens = sum(len(block.input_ids) for block in blocks)
    capacity = len(blocks) * block_size
    return {
        "sequences": len(blocks),
        "tokens": tokens,
        "capacity": capacity,
        "utilization": tokens / capacity if capacity else 0.0,
    }
