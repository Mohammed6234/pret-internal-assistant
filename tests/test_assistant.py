import logging
import unittest
from pathlib import Path

from assistant import Document, answer_question, load_documents
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_RUN_CONTEXT_LOGGER = "streamlit.runtime.scriptrunner_utils.script_run_context"


class MissingScriptRunContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not (
            record.name == SCRIPT_RUN_CONTEXT_LOGGER
            and "missing ScriptRunContext!" in record.getMessage()
        )


class AssistantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = load_documents(ROOT / "data" / "knowledge.json")

    def test_store_colleague_receives_permitted_answer_and_source(self) -> None:
        result = answer_question(
            "How do I report a faulty display fridge?",
            "Store colleague",
            self.documents,
        )

        self.assertEqual(result.status, "answer")
        self.assertIn("maintenance request", result.message)
        self.assertEqual(result.document_id, "OPS-001")
        self.assertEqual(result.document_url, "https://pret.example/documents/OPS-001")
        self.assertIsNone(result.case)

    def test_store_manager_can_read_a_general_document(self) -> None:
        result = answer_question(
            "How do I report that I cannot attend a shift?",
            "Store manager",
            self.documents,
        )

        self.assertEqual(result.status, "answer")
        self.assertEqual(result.document_id, "HR-001")

    def test_colleague_is_denied_manager_only_guidance_without_source_leakage(self) -> None:
        result = answer_question(
            "What are the escalation thresholds for repeated equipment faults?",
            "Store colleague",
            self.documents,
        )

        self.assertEqual(result.status, "access_denied")
        self.assertEqual(
            result.message,
            "Sorry, you do not have the correct access level. Ask your manager to make this request.",
        )
        self.assertIsNone(result.document_id)
        self.assertIsNone(result.document_url)
        self.assertNotIn("repeat-fault threshold", result.message)

    def test_manager_receives_manager_only_guidance(self) -> None:
        result = answer_question(
            "What are the escalation thresholds for repeated equipment faults?",
            "Store manager",
            self.documents,
        )

        self.assertEqual(result.status, "answer")
        self.assertEqual(result.document_id, "OPS-002")
        self.assertIn("manager escalation route", result.message)

    def test_unsupported_question_prepares_complete_agent_case(self) -> None:
        result = answer_question(
            "What is the approved supplier invoice process?",
            "Store colleague",
            self.documents,
        )

        self.assertEqual(result.status, "unavailable")
        self.assertEqual(
            result.message,
            "I don't have this information available. Would you like to talk to an agent?",
        )
        self.assertIsNotNone(result.case)
        self.assertEqual(result.case.question, "What is the approved supplier invoice process?")
        self.assertEqual(result.case.role, "Store colleague")
        self.assertEqual(result.case.search_outcome, "No approved document matched")
        self.assertEqual(result.case.documents_checked, 4)
        self.assertEqual(result.case.reason, "Approved information unavailable")
        self.assertRegex(result.case.reference, r"^CASE-[0-9A-F]{8}$")

    def test_empty_question_requests_input_without_agent_case(self) -> None:
        result = answer_question("  ", "Store colleague", self.documents)

        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.message, "Please enter a question.")
        self.assertIsNone(result.case)

    def test_unknown_role_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown role"):
            answer_question("How do I report a faulty fridge?", "Administrator", self.documents)

    def test_equal_matches_are_resolved_by_document_id(self) -> None:
        tied = [
            Document("ZZZ", "Fridge help", "Second", "https://pret.example/ZZZ", ("fridge",), ("Store colleague",)),
            Document("AAA", "Fridge help", "First", "https://pret.example/AAA", ("fridge",), ("Store colleague",)),
        ]

        result = answer_question("fridge", "Store colleague", tied)

        self.assertEqual(result.document_id, "AAA")

    def test_permitted_match_is_selected_when_restricted_match_sorts_first(self) -> None:
        tied = [
            Document("AAA", "Fridge help", "Restricted", "https://pret.example/AAA", ("fridge",), ("Store manager",)),
            Document("ZZZ", "Fridge help", "Permitted", "https://pret.example/ZZZ", ("fridge",), ("Store colleague",)),
        ]

        result = answer_question("fridge", "Store colleague", tied)

        self.assertEqual(result.status, "answer")
        self.assertEqual(result.document_id, "ZZZ")
        self.assertEqual(result.message, "Permitted")


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script_run_context_logger = logging.getLogger(SCRIPT_RUN_CONTEXT_LOGGER)
        cls.missing_context_filter = MissingScriptRunContextFilter()
        cls.script_run_context_logger.addFilter(cls.missing_context_filter)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.script_run_context_logger.removeFilter(cls.missing_context_filter)

    def test_role_change_changes_manager_question_outcome(self) -> None:
        app = AppTest.from_file(ROOT / "app.py").run()

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.button), 5)
        self.assertEqual(len(app.chat_input), 1)
        app.button(key="suggestion-2").click().run()
        self.assertIn("correct access level", app.warning[0].value)

        app.selectbox(key="role").select("Store manager").run()
        self.assertIn("manager escalation route", app.success[0].value)

    def test_unsupported_question_reveals_case_only_after_confirmation(self) -> None:
        app = AppTest.from_file(ROOT / "app.py").run()
        app.button(key="suggestion-5").click().run()

        self.assertIn("talk to an agent", app.info[0].value.casefold())
        self.assertEqual(len(app.json), 0)
        app.button(key="talk-to-agent").click().run()
        self.assertEqual(len(app.json), 1)
        self.assertIn("CASE-", str(app.json[0].value))


if __name__ == "__main__":
    unittest.main()
