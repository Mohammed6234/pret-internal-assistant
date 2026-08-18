from typing import Protocol, Sequence

from .models import AnswerResponse, Decision, RetrievedEvidence


class AnswerGenerator(Protocol):
    def generate(self, question: str, evidence: Sequence[RetrievedEvidence]) -> str:
        ...

class DeterministicAnswerGenerator:
    def generate(self, question: str, evidence: Sequence[RetrievedEvidence]) -> str:
        del question
        evidence_lines = [
            f"- {item.document.content.strip()}"
            for item in evidence
            if item.document.content.strip()
        ]
        return "Based on approved guidance:\n" + "\n".join(evidence_lines)


def build_grounded_answer(
    evidence: Sequence[RetrievedEvidence],
    *,
    question: str = "",
    generator: AnswerGenerator | None = None,
) -> AnswerResponse:
    if not evidence:
        return AnswerResponse(
            decision=Decision.REFUSE,
            reason="I could not find approved guidance for that question.",
            requires_human=True,
        )

    answer_generator = generator or DeterministicAnswerGenerator()
    answer = answer_generator.generate(question, evidence)
    return AnswerResponse(
        decision=Decision.ANSWER,
        answer=answer,
        evidence_ids=tuple(item.document.doc_id for item in evidence),
        metadata={"grounding": "approved-evidence-only"},
    )


def build_refusal(reason: str, *, requires_human: bool = False) -> AnswerResponse:
    return AnswerResponse(
        decision=Decision.REFUSE,
        reason=reason,
        requires_human=requires_human,
    )


def build_escalation(reason: str) -> AnswerResponse:
    return AnswerResponse(
        decision=Decision.ESCALATE,
        reason=reason,
        requires_human=True,
    )
