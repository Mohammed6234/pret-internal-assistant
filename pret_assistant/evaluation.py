import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import AnswerResponse, EvaluationCase
from .service import AssistantService


@dataclass(frozen=True)
class EvaluationResult:
    case: EvaluationCase
    response: AnswerResponse
    passed: bool
    failures: tuple[str, ...] = ()


def load_cases(path: str | Path) -> list[EvaluationCase]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [EvaluationCase.from_mapping(item) for item in payload]


def run_evaluations(
    service: AssistantService,
    cases: Iterable[EvaluationCase],
) -> list[EvaluationResult]:
    results: list[EvaluationResult] = []
    for case in cases:
        response = service.handle(case.user, case.question)
        failures: list[str] = []

        if response.decision is not case.expected_decision:
            failures.append(
                f"expected decision {case.expected_decision.value!r}, "
                f"got {response.decision.value!r}"
            )

        actual_evidence = frozenset(response.evidence_ids)
        if actual_evidence != case.expected_evidence_ids:
            failures.append(
                f"expected evidence {sorted(case.expected_evidence_ids)!r}, "
                f"got {sorted(actual_evidence)!r}"
            )

        results.append(
            EvaluationResult(
                case=case,
                response=response,
                passed=not failures,
                failures=tuple(failures),
            )
        )

    return results
