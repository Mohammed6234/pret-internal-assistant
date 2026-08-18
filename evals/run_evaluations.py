import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pret_assistant.evaluation import load_cases, run_evaluations
from pret_assistant.models import KnowledgeDocument
from pret_assistant.retrieval import InMemoryRetriever
from pret_assistant.service import AssistantService


def main() -> int:
    documents_payload = json.loads(
        (PROJECT_ROOT / "data" / "knowledge.json").read_text(encoding="utf-8")
    )
    documents = [KnowledgeDocument.from_mapping(item) for item in documents_payload]
    service = AssistantService(InMemoryRetriever(documents))
    cases = load_cases(PROJECT_ROOT / "evals" / "test_cases.json")
    results = run_evaluations(service, cases)

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.case.name}")
        if result.failures:
            for failure in result.failures:
                print(f"       {failure}")

    passed = sum(result.passed for result in results)
    print(f"\n{passed}/{len(results)} evaluation cases passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
