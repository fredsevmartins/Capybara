# Security policy

The supported stable software line is **1.0.x**. Use the latest verified stable
GitHub Release and consult its release notes. Pre-release candidates are retained
for historical comparison; package schema `0.1` is separate from software version
`1.0.0`. No independent security certification is claimed.

Do not disclose exploitable vulnerabilities or sensitive datasets in public issues.
Use the repository's GitHub **Report a vulnerability** flow if enabled. If unavailable,
contact the owner through a private contact method listed on their GitHub profile;
if no private channel is available, open a minimal issue requesting one without
exploit details. No response-time guarantee or bug bounty is offered.

Include affected version, sanitized reproduction steps, expected impact and a minimal
synthetic archive. Never include credentials or real private research data.

OpenRepro validates package structure and integrity, not authenticity, scientific
correctness or malware safety. See [threat model](docs/security.md).
