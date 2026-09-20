import json
import unittest

from opspreflight.models import AnalysisContext
from opspreflight.parser import parse_plan
from opspreflight.policies import evaluate_all
from tests.helpers import plan


def rule_ids(raw_plan, context=None):
    context = context or AnalysisContext(owners={"resource.test": "team"})
    return {item.rule_id for item in evaluate_all(parse_plan(raw_plan), context)}


class PolicyTests(unittest.TestCase):
    def test_public_management_port(self):
        raw = plan("aws_security_group", {}, {"ingress": [{"from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]}]})
        self.assertIn("NETWORK-001", rule_ids(raw))

    def test_https_public_is_not_management_port(self):
        raw = plan("aws_security_group", {}, {"ingress": [{"from_port": 443, "to_port": 443, "cidr_blocks": ["0.0.0.0/0"]}]})
        self.assertNotIn("NETWORK-001", rule_ids(raw))

    def test_public_database(self):
        self.assertIn("DATA-001", rule_ids(plan("aws_db_instance", {}, {"publicly_accessible": True})))

    def test_encryption_disabled(self):
        self.assertIn("DATA-002", rule_ids(plan("aws_s3_bucket", {}, {"encrypted": False})))

    def test_iam_double_wildcard_dict(self):
        after = {"policy": {"Statement": {"Effect": "Allow", "Action": "*", "Resource": "*"}}}
        self.assertIn("IAM-001", rule_ids(plan("aws_iam_policy", {}, after)))

    def test_iam_double_wildcard_json(self):
        policy = json.dumps({"Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]})
        self.assertIn("IAM-001", rule_ids(plan("aws_iam_policy", {}, {"policy": policy})))

    def test_iam_limited_resource_is_not_double_wildcard(self):
        after = {"policy": {"Statement": {"Effect": "Allow", "Action": "*", "Resource": "arn:one"}}}
        self.assertNotIn("IAM-001", rule_ids(plan("aws_iam_policy", {}, after)))

    def test_production_stateful_replacement(self):
        context = AnalysisContext(environment="production", owners={"resource.test": "team"})
        raw = plan("aws_db_instance", {}, {}, ["delete", "create"])
        self.assertIn("CHANGE-002", rule_ids(raw, context))

    def test_development_replacement_not_blocked(self):
        context = AnalysisContext(environment="development", owners={"resource.test": "team"})
        raw = plan("aws_db_instance", {}, {}, ["delete", "create"])
        self.assertNotIn("CHANGE-002", rule_ids(raw, context))

    def test_backup_retention_reduced(self):
        raw = plan("aws_db_instance", {"backup_retention_period": 14}, {"backup_retention_period": 1})
        self.assertIn("DATA-003", rule_ids(raw))

    def test_backup_retention_increased_is_safe(self):
        raw = plan("aws_db_instance", {"backup_retention_period": 7}, {"backup_retention_period": 14})
        self.assertNotIn("DATA-003", rule_ids(raw))

    def test_production_replica_reduction(self):
        context = AnalysisContext(environment="production", owners={"resource.test": "team"})
        raw = plan("service", {"replicas": 3}, {"replicas": 1})
        self.assertIn("RELIABILITY-001", rule_ids(raw, context))

    def test_missing_owner(self):
        raw = plan("service", {}, {})
        self.assertIn("CONTEXT-001", rule_ids(raw, AnalysisContext()))

    def test_registered_owner(self):
        raw = plan("service", {}, {})
        self.assertNotIn("CONTEXT-001", rule_ids(raw))


if __name__ == "__main__":
    unittest.main()

