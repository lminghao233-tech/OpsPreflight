# Security policy

This is a portfolio MVP and should not be placed directly in a production
release path. Please report suspected vulnerabilities privately to the author
rather than opening an issue containing secrets or Terraform plan data.

Never attach real `tfplan`, `tfplan.json`, credentials or identifiable
infrastructure details to a public issue. Reproduce with the synthetic plan
format in `examples/`.

Terraform names, tags and descriptions are treated as untrusted input. Reports
for prompt injection, secret-redaction bypass, citation forgery, verdict
mutation or Break-glass bypass are in scope. The optional model integration must
receive only the redacted evidence packet and must never be used as the release
authority.

