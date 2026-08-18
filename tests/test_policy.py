import unittest

from pret_assistant.models import KnowledgeDocument, UserContext
from pret_assistant.policy import is_document_allowed


class PolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store_colleague = UserContext(
            user_id="employee-123",
            market="UK",
            store_id="123",
            groups=frozenset({"store-colleague"}),
        )

    def test_allows_document_for_matching_group_and_market(self) -> None:
        document = KnowledgeDocument(
            doc_id="ops-equipment-uk-v1",
            title="UK equipment procedure",
            content="Raise an approved maintenance request.",
            market="UK",
            allowed_groups=frozenset({"store-colleague"}),
        )

        self.assertTrue(is_document_allowed(self.store_colleague, document))

    def test_denies_document_for_another_group(self) -> None:
        document = KnowledgeDocument(
            doc_id="ops-manager-only-v1",
            title="Manager escalation procedure",
            content="Manager-only guidance.",
            market="UK",
            allowed_groups=frozenset({"store-manager"}),
        )

        self.assertFalse(is_document_allowed(self.store_colleague, document))

    def test_denies_document_for_another_market(self) -> None:
        document = KnowledgeDocument(
            doc_id="ops-equipment-fr-v1",
            title="France equipment procedure",
            content="Use the France process.",
            market="FR",
            allowed_groups=frozenset({"store-colleague"}),
        )

        self.assertFalse(is_document_allowed(self.store_colleague, document))

    def test_denies_document_for_another_store_when_store_scope_is_present(self) -> None:
        document = KnowledgeDocument(
            doc_id="store-456-local-v1",
            title="Store 456 local process",
            content="Store-specific guidance.",
            market="UK",
            allowed_groups=frozenset({"store-colleague"}),
            allowed_store_ids=frozenset({"456"}),
        )

        self.assertFalse(is_document_allowed(self.store_colleague, document))


if __name__ == "__main__":
    unittest.main()
