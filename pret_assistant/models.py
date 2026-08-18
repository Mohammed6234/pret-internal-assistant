from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


def _string_set(value: Any) -> frozenset[str]:
    if value is None:
        return frozenset()
    if isinstance(value, str):
        return frozenset({value})
    if isinstance(value, (list, tuple, set, frozenset)):
        return frozenset(str(item) for item in value)
    raise TypeError(f"Expected a string or collection of strings, got {type(value)!r}")


class Decision(str, Enum):
    ANSWER = "answer"
    REFUSE = "refuse"
    ESCALATE = "escalate"


@dataclass(frozen=True)
class UserContext:
    user_id: str
    market: str
    groups: frozenset[str] = field(default_factory=frozenset)
    store_id: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "UserContext":
        return cls(
            user_id=str(payload["user_id"]),
            market=str(payload["market"]),
            groups=_string_set(payload.get("groups")),
            store_id=(None if payload.get("store_id") is None else str(payload["store_id"])),
        )


@dataclass(frozen=True)
class KnowledgeDocument:
    doc_id: str
    title: str
    content: str
    market: str | None = None
    allowed_groups: frozenset[str] = field(default_factory=frozenset)
    allowed_store_ids: frozenset[str] = field(default_factory=frozenset)
    sensitivity: str = "internal"
    version: str = "1.0"

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "KnowledgeDocument":
        return cls(
            doc_id=str(payload["doc_id"]),
            title=str(payload["title"]),
            content=str(payload["content"]),
            market=(None if payload.get("market") is None else str(payload["market"])),
            allowed_groups=_string_set(payload.get("allowed_groups")),
            allowed_store_ids=_string_set(payload.get("allowed_store_ids")),
            sensitivity=str(payload.get("sensitivity", "internal")),
            version=str(payload.get("version", "1.0")),
        )


@dataclass(frozen=True)
class RetrievedEvidence:
    document: KnowledgeDocument
    score: float
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class AnswerResponse:
    decision: Decision
    answer: str | None = None
    evidence_ids: tuple[str, ...] = ()
    reason: str | None = None
    requires_human: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "answer": self.answer,
            "evidence_ids": list(self.evidence_ids),
            "reason": self.reason,
            "requires_human": self.requires_human,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class EvaluationCase:
    name: str
    question: str
    user: UserContext
    expected_decision: Decision
    expected_evidence_ids: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "EvaluationCase":
        return cls(
            name=str(payload["name"]),
            question=str(payload["question"]),
            user=UserContext.from_mapping(payload["user"]),
            expected_decision=Decision(str(payload["expected_decision"])),
            expected_evidence_ids=_string_set(payload.get("expected_evidence_ids")),
        )
