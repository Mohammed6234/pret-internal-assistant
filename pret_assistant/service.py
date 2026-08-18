from typing import Any, Mapping

from .answer import (
    AnswerGenerator,
    build_escalation,
    build_grounded_answer,
    build_refusal,
)
from .guardrails import GuardrailAction, assess_question
from .models import AnswerResponse, UserContext
from .retrieval import Retriever


class AssistantService:
    def __init__(
        self,
        retriever: Retriever,
        *,
        answer_generator: AnswerGenerator | None = None,
        top_k: int = 3,
    ) -> None:
        self._retriever = retriever
        self._answer_generator = answer_generator
        self._top_k = top_k

    def handle(
        self,
        user: UserContext | Mapping[str, Any],
        question: str,
    ) -> AnswerResponse:
        user_context = (
            user if isinstance(user, UserContext) else UserContext.from_mapping(user)
        )
        question = str(question or "")

        guardrail_result = assess_question(question)
        if guardrail_result.action is GuardrailAction.REFUSE:
            return build_refusal(guardrail_result.reason or "The request was refused.")
        if guardrail_result.action is GuardrailAction.ESCALATE:
            return build_escalation(
                guardrail_result.reason or "The request requires human support."
            )

        evidence = self._retriever.retrieve(
            question,
            user_context,
            top_k=self._top_k,
        )
        if not evidence:
            return build_refusal(
                "I could not find approved guidance for that question; please contact the relevant support team.",
                requires_human=True,
            )

        return build_grounded_answer(
            evidence,
            question=question,
            generator=self._answer_generator,
        )
