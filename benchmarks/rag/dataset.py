"""Strict source-anchored labels; old Agent/holdout datasets are never loaded."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from typing_extensions import Annotated

Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class EvidenceLabel(StrictModel):
    id: NonEmpty
    doc_id: NonEmpty
    page: Annotated[int, Field(ge=1)] | None
    section_path: list[NonEmpty] = Field(default_factory=list)
    quote: NonEmpty
    source_sha256: Digest


class FactLabel(StrictModel):
    id: NonEmpty
    accepted_answers: Annotated[list[NonEmpty], Field(min_length=1)]
    evidence_ids: Annotated[list[NonEmpty], Field(min_length=1)]


class Case(StrictModel):
    id: NonEmpty
    split: Literal["dev", "test"]
    family_id: NonEmpty
    category: NonEmpty
    question: NonEmpty
    doc_ids: Annotated[list[NonEmpty], Field(min_length=1)]
    answerable: bool
    reference_answer: str
    required_evidence: list[EvidenceLabel]
    facts: list[FactLabel] = Field(default_factory=list)
    review_status: Literal["pending_human_review", "ai_verified", "approved"] = "pending_human_review"
    session_id: NonEmpty | None = None
    history: list[dict] = Field(default_factory=list)
    retrieval_question: NonEmpty | None = None

    @model_validator(mode="after")
    def consistent_labels(self):
        if len(set(self.doc_ids)) != len(self.doc_ids):
            raise ValueError("doc_ids must be unique")
        evidence_ids = {label.id for label in self.required_evidence}
        if len(evidence_ids) != len(self.required_evidence):
            raise ValueError("Evidence IDs must be unique within a case")
        if any(label.doc_id not in self.doc_ids for label in self.required_evidence):
            raise ValueError("Evidence must belong to the allowed source scope")
        if self.answerable and (not self.required_evidence or not self.reference_answer.strip()):
            raise ValueError("Answerable cases need a reference answer and source evidence")
        if not self.answerable and (self.required_evidence or self.facts):
            raise ValueError("Unanswerable cases cannot contain positive answer/evidence labels")
        if len({fact.id for fact in self.facts}) != len(self.facts):
            raise ValueError("Fact IDs must be unique within a case")
        if any(not set(fact.evidence_ids).issubset(evidence_ids) for fact in self.facts):
            raise ValueError("A fact refers to an unknown evidence ID")
        return self


class Dataset(StrictModel):
    version: NonEmpty
    title: NonEmpty
    corpus_manifest: NonEmpty
    cases: list[Case]
    corpus_manifest_sha256: Digest | None = None
    split_group_policy: Literal["family_session", "document"] = "family_session"

    @model_validator(mode="after")
    def validate_groups(self):
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError("Case IDs must be unique")
        for field in ("family_id", "session_id"):
            groups: dict[str, set[str]] = {}
            for case in self.cases:
                value = getattr(case, field)
                if value is not None:
                    groups.setdefault(value, set()).add(case.split)
            if any(len(splits) > 1 for splits in groups.values()):
                raise ValueError(f"Split leakage: {field} crosses dev/test")
        if self.split_group_policy == "document":
            groups = {}
            for case in self.cases:
                for doc_id in case.doc_ids:
                    groups.setdefault(doc_id, set()).add(case.split)
            if any(len(splits) > 1 for splits in groups.values()):
                raise ValueError("Split leakage: a source document crosses dev/test")
        return self


def load_dataset(path: str | Path, *, split: str = "dev", allow_test: bool = False) -> Dataset:
    """Return only the requested split; test activation always needs an opt-in."""
    if split not in {"dev", "test"}:
        raise ValueError("Only dev/test are supported; no implicit all-split mode")
    if split == "test" and not allow_test:
        raise ValueError("Final test activation requires allow_test=True")
    dataset = Dataset.model_validate_json(Path(path).read_text(encoding="utf-8-sig"))
    chosen = [case for case in dataset.cases if case.split == split]
    if not chosen:
        raise ValueError(f"No cases in requested split: {split}")
    return dataset.model_copy(update={"cases": chosen})


def _normal(value: str) -> str:
    from benchmarks.rag.metrics import normalize_text
    return normalize_text(value)


def verify_sources(dataset: Dataset, dataset_path: str | Path, *, project_root: Path | None = None) -> dict:
    """Verify every permitted document and every exact quote at its real locator.

    Successful verification proves provenance/text containment, not semantic
    sufficiency. The reference review_status is never promoted here.
    """
    from qa_agent.config import PROJECT_ROOT
    from qa_agent.documents import load_documents, verify_document_hash
    from qa_agent.rag.parsers import parse_document
    root = Path(project_root or PROJECT_ROOT).resolve()
    manifest = (Path(dataset_path).resolve().parent / dataset.corpus_manifest).resolve()
    manifest_hash = sha256(manifest.read_bytes()).hexdigest()
    if dataset.corpus_manifest_sha256 is not None and manifest_hash != dataset.corpus_manifest_sha256:
        raise ValueError("Corpus manifest hash changed")
    documents = {doc["doc_id"]: doc for doc in load_documents(manifest, project_root=root)}
    allowed = {doc_id for case in dataset.cases for doc_id in case.doc_ids}
    if not allowed.issubset(documents):
        raise ValueError("Dataset scope contains a document absent from the manifest")
    hashes = {doc_id: verify_document_hash(documents[doc_id]) for doc_id in sorted(allowed)}
    pages: dict[str, list[dict]] = {}
    checks = []
    for case in dataset.cases:
        for label in case.required_evidence:
            if hashes[label.doc_id] != label.source_sha256:
                raise ValueError(f"Evidence source hash changed: {case.id}/{label.id}")
            if label.doc_id not in pages:
                # Native PDFs keep section labels on same-column regions,
                # while the containing page owns its physical page number.
                # Use the same page/region merge as the production chunker.
                records = []
                for record in parse_document(documents[label.doc_id]):
                    if "regions" in record:
                        parent = {key: value for key, value in record.items() if key != "regions"}
                        records.extend({**parent, **region} for region in record["regions"] if region["text"].strip())
                    else:
                        records.append(record)
                pages[label.doc_id] = records
            matches = [record for record in pages[label.doc_id]
                       if record.get("page") == label.page
                       and (not label.section_path or
                            record.get("section_path", [])[:len(label.section_path)] == label.section_path)
                       and _normal(label.quote) in _normal(record.get("text", ""))]
            if not matches:
                raise ValueError(f"Evidence quote/locator not found in source: {case.id}/{label.id}")
            checks.append({"case_id": case.id, "evidence_id": label.id, "doc_id": label.doc_id,
                           "page": label.page, "section_path": label.section_path,
                           "quote_and_locator_verified": True,
                           "semantic_sufficiency": "pending_review"})
    return {"manifest_path": str(manifest.relative_to(root)) if manifest.is_relative_to(root) else str(manifest),
            "manifest_sha256": manifest_hash, "document_sha256": hashes,
            "evidence_checks": checks, "review_status_changed": False}
