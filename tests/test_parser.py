import unittest

from opspreflight.parser import REDACTED, parse_plan, redact


class ParserTests(unittest.TestCase):
    def test_rejects_non_object(self):
        with self.assertRaises(ValueError):
            parse_plan([])

    def test_requires_resource_changes(self):
        with self.assertRaises(ValueError):
            parse_plan({})

    def test_parses_basic_change(self):
        result = parse_plan({"resource_changes": [{"address": "x", "type": "t", "change": {"actions": ["create"], "after": {"x": 1}}}]})
        self.assertEqual(result[0].actions, ("create",))

    def test_redacts_sensitive_field_name(self):
        self.assertEqual(redact({"password": "secret"})["password"], REDACTED)

    def test_redacts_terraform_sensitive_mask(self):
        self.assertEqual(redact({"custom": "secret"}, {"custom": True})["custom"], REDACTED)

    def test_redaction_does_not_mutate_source(self):
        source = {"password": "secret"}
        redact(source)
        self.assertEqual(source["password"], "secret")

    def test_redacts_nested_list(self):
        result = redact([{"token": "x"}])
        self.assertEqual(result[0]["token"], REDACTED)


if __name__ == "__main__":
    unittest.main()

