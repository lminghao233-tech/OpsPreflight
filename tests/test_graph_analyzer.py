import unittest

from opspreflight.analyzer import Analyzer
from opspreflight.graph import DependencyGraph
from opspreflight.models import AnalysisContext
from tests.helpers import plan


class GraphAnalyzerTests(unittest.TestCase):
    def test_graph_handles_cycles(self):
        graph = DependencyGraph({"a": ["b"], "b": ["a"]})
        affected, _ = graph.blast_radius(["a"])
        self.assertEqual(affected, ("b",))

    def test_tier_one_scores_more(self):
        graph = DependencyGraph({"a": ["checkout"]}, {"checkout": 1})
        _, points = graph.blast_radius(["a"])
        self.assertEqual(points, 15)

    def test_safe_owned_change_passes(self):
        context = AnalysisContext(owners={"resource.test": "team"})
        result = Analyzer().analyze(plan("service", {}, {}), context)
        self.assertEqual(result.verdict, "PASS")

    def test_block_rule_overrides_score(self):
        context = AnalysisContext(owners={"resource.test": "team"})
        result = Analyzer().analyze(plan("bucket", {}, {"encrypted": False}), context)
        self.assertEqual(result.verdict, "BLOCK")

    def test_missing_owner_reviews(self):
        result = Analyzer().analyze(plan("service", {}, {}), AnalysisContext())
        self.assertEqual(result.verdict, "REVIEW")

    def test_analysis_is_idempotent(self):
        context = AnalysisContext(owners={"resource.test": "team"})
        analyzer = Analyzer()
        first = analyzer.analyze(plan("service", {}, {}), context)
        second = analyzer.analyze(plan("service", {}, {}), context)
        self.assertEqual(first.analysis_id, second.analysis_id)

    def test_history_rollback_adds_points(self):
        history = [{"repository": "repo", "resource_type": "service", "outcome": "rollback"}]
        context = AnalysisContext(repository="repo", owners={"resource.test": "team"})
        result = Analyzer(history=history).analyze(plan("service", {}, {}), context)
        self.assertEqual(result.history_points, 15)

    def test_blast_radius_affects_score(self):
        graph = DependencyGraph({"resource.test": ["checkout"]}, {"checkout": 1})
        context = AnalysisContext(owners={"resource.test": "team"})
        result = Analyzer(graph=graph).analyze(plan("service", {}, {}), context)
        self.assertEqual(result.blast_radius_points, 15)


if __name__ == "__main__":
    unittest.main()

