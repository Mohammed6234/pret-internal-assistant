import unittest

from pret_assistant.answer import build_grounded_answer
from pret_assistant.models import KnowledgeDocument, RetrievedEvidence


class AnswerTests(unittest.TestCase):
    def test_grounded_answer_contains_content_and_source(self) -> None:
        evidence = [
            RetrievedEvidence(
                document=KnowledgeDocument(
                    doc_id="ops-equipment-v1",
                    title="Equipment procedure",
                    content="Raise a maintenance request after making the area safe.",
                ),
                score=0.8,
                matched_terms=("equipment", "request"),
            )
        ]

        response = build_grounded_answer(evidence)

        self.assertIn("Raise a maintenance request", response.answer or "")
        self.assertEqual(response.evidence_ids, ("ops-equipment-v1",))
        self.assertEqual(response.decision.value, "answer")
        self.assertFalse(response.requires_human)

    def test_empty_evidence_produces_refusal(self) -> None:
        response = build_grounded_answer([])

        self.assertEqual(response.decision.value, "refuse")
        self.assertIsNone(response.answer)
        self.assertEqual(response.evidence_ids, ())
        self.assertTrue(response.requires_human)


if __name__ == "__main__":
    unittest.main()
