import json
import unittest
from pathlib import Path

from pret_assistant.evaluation import load_cases, run_evaluations
from pret_assistant.models import KnowledgeDocument
from pret_assistant.retrieval import InMemoryRetriever
from pret_assistant.service import AssistantService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        documents_path = PROJECT_ROOT / "data" / "knowledge.json"
        documents_payload = json.loads(documents_path.read_text(encoding="utf-8"))
        documents = [KnowledgeDocument.from_mapping(item) for item in documents_payload]
        self.service = AssistantService(InMemoryRetriever(documents))

    def test_all_evaluation_cases_pass(self) -> None:
        cases = load_cases(PROJECT_ROOT / "evals" / "test_cases.json")

        results = run_evaluations(self.service, cases)

        self.assertTrue(all(result.passed for result in results), results)

    def test_high_risk_question_escalates(self) -> None:
        response = self.service.handle(
            {
                "user_id": "employee-123",
                "market": "UK",
                "store_id": "123",
                "groups": ["store-colleague"],
            },
            "There may be food safety contamination from the faulty fridge.",
        )

        self.assertEqual(response.decision.value, "escalate")
        self.assertTrue(response.requires_human)


if __name__ == "__main__":
    unittest.main()
