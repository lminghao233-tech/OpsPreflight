import unittest

from opspreflight.analyzer import Analyzer
from opspreflight.brief import deterministic_brief
from opspreflight.models import AnalysisContext
from opspreflight.storage import Store
from tests.helpers import plan


class StorageBriefTests(unittest.TestCase):
    def safe_result(self):
        return Analyzer().analyze(
            plan("service", {}, {}), AnalysisContext(owners={"resource.test": "team"})
        )

    def block_result(self):
        return Analyzer().analyze(
            plan("bucket", {}, {"encrypted": False}),
            AnalysisContext(owners={"resource.test": "team"}),
        )

    def test_save_and_get(self):
        store = Store()
        result = self.safe_result()
        store.save_analysis(result)
        self.assertEqual(store.get_analysis(result.analysis_id)["verdict"], "PASS")

    def test_duplicate_save_is_idempotent(self):
        store = Store()
        result = self.safe_result()
        store.save_analysis(result)
        store.save_analysis(result)
        count = store.connection.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
        self.assertEqual(count, 1)

    def test_block_requires_break_glass(self):
        store = Store()
        result = self.block_result()
        store.save_analysis(result)
        with self.assertRaises(PermissionError):
            store.approve(result.analysis_id, "alice", "needed")

    def test_break_glass_is_audited(self):
        store = Store()
        result = self.block_result()
        store.save_analysis(result)
        store.approve(result.analysis_id, "alice", "incident response", break_glass=True)
        self.assertEqual(store.timeline(result.analysis_id)[-1]["event_type"], "approval.break_glass")

    def test_reason_is_required(self):
        store = Store()
        result = self.safe_result()
        store.save_analysis(result)
        with self.assertRaises(ValueError):
            store.approve(result.analysis_id, "alice", "")

    def test_outcome_validation(self):
        store = Store()
        result = self.safe_result()
        store.save_analysis(result)
        with self.assertRaises(ValueError):
            store.record_outcome(result.analysis_id, "alice", "maybe")

    def test_outcome_is_audited(self):
        store = Store()
        result = self.safe_result()
        store.save_analysis(result)
        store.record_outcome(result.analysis_id, "alice", "success")
        self.assertEqual(store.timeline(result.analysis_id)[-1]["event_type"], "deployment.outcome")

    def test_brief_preserves_verdict(self):
        result = self.block_result().to_dict()
        brief = deterministic_brief(result)
        self.assertEqual(brief["verdict"], "BLOCK")
        self.assertEqual(brief["source"], "deterministic-fallback")


if __name__ == "__main__":
    unittest.main()

