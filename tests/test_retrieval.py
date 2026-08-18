import unittest

from pret_assistant.models import KnowledgeDocument, UserContext
from pret_assistant.retrieval import InMemoryRetriever


class RetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.user = UserContext(
            user_id="employee-123",
            market="UK",
            store_id="123",
            groups=frozenset({"store-colleague"}),
        )
        self.documents = [
            KnowledgeDocument(
                doc_id="allowed-equipment",
                title="Equipment reporting process",
                content="Report a faulty display fridge through the maintenance process.",
                market="UK",
                allowed_groups=frozenset({"store-colleague"}),
            ),
            KnowledgeDocument(
                doc_id="restricted-equipment",
                title="Manager-only equipment escalation",
                content="Manager-only escalation thresholds for repeated faults.",
                market="UK",
                allowed_groups=frozenset({"store-manager"}),
            ),
        ]
        self.retriever = InMemoryRetriever(self.documents)

    def test_retrieval_returns_matching_allowed_evidence(self) -> None:
        evidence = self.retriever.retrieve(
            "What is the process for a faulty display fridge?",
            self.user,
        )

        self.assertEqual([item.document.doc_id for item in evidence], ["allowed-equipment"])
        self.assertGreater(evidence[0].score, 0)

    def test_retrieval_never_returns_an_unauthorized_document(self) -> None:
        evidence = self.retriever.retrieve(
            "What are the manager-only escalation thresholds for repeated faults?",
            self.user,
        )

        self.assertEqual(evidence, [])

    def test_retrieval_returns_no_evidence_when_terms_do_not_match(self) -> None:
        evidence = self.retriever.retrieve(
            "What is the supplier invoice process?",
            self.user,
        )

        self.assertEqual(evidence, [])


if __name__ == "__main__":
    unittest.main()
