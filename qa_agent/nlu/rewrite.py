"""Apply verifiable, non-overlapping edits to the original question only."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RewritePatch:
    start: int
    end: int
    original: str
    replacement: str
    method: str
    evidence_ref: str

    def as_dict(self) -> dict:
        return asdict(self)


def apply_patches(question: str, patches: list[RewritePatch]) -> str:
    ordered = sorted(patches, key=lambda patch: (patch.start, patch.end))
    previous_end = 0
    for patch in ordered:
        if not (0 <= patch.start < patch.end <= len(question)):
            raise ValueError("改写补丁范围越界或为空。")
        if patch.start < previous_end:
            raise ValueError("改写补丁不能重叠。")
        if question[patch.start:patch.end] != patch.original:
            raise ValueError("改写补丁与原始字符不一致。")
        if not patch.replacement or not patch.evidence_ref:
            raise ValueError("改写补丁必须具有替换文本和已核验依据。")
        previous_end = patch.end
    result = question
    for patch in reversed(ordered):
        result = result[:patch.start] + patch.replacement + result[patch.end:]
    return result
