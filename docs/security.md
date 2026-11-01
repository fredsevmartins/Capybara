# Security model

[Disclosure policy](../SECURITY.md). Native imports treat ZIP files as untrusted:
portable relative paths, inventory, checksums, count/size/ratio limits, case
collisions, compression, malformed metadata and special-file rejection are checked
before committing a new workspace. Import never executes payloads.

The MCP server exposes only local stdio management inside a configured root. It
has no execution, upload or public HTTP tools. Explicit execution requires a
reviewed recipe and Linux/local Docker, with the policy and limits in
[execution](execution.md). No writable host directories/socket/home are mounted;
output/log storage uses bounded tmpfs and validated tar collection. Docker is a
shared-kernel boundary, not protection equivalent to a separate VM.

Environment resolution uses binary wheels, no source-build scripts, secure registry
transport and exact hash locks. Offline image build retains pip hash checking and
network isolation. Review the immutable base and selected dependencies; neither a
hash nor a tag authenticates a package publisher. No TLS/checksum verification is
disabled during installation or troubleshooting.

Editing uses private sibling backups and restores affected bytes on handled failures.
Retained backups/recovery journals can contain research data. Use trusted local
ownership, a single writer and external backups. Checksums are not signatures;
metadata/provenance is descriptive and unsigned. Power loss, filesystem loss and
malicious concurrent local writers are not covered by transactional guarantees.

Catalogs verify immutable package hashes and expose only search/download routes.
They have no public write API. Anonymous public serving makes data public; use a
separate read-only service account, TLS reverse proxy, access/rate limits and backups
for deployment. Use Zenodo for reviewed public deposits/DOIs. Token values belong
in secure environment settings; they are sent only as headers to the configured
Zenodo host. Redirects/foreign bucket hosts are rejected and journals omit credentials.

HTML reports and catalog pages escape analysis/metadata content and set restrictive
content policies. Logs and outputs remain untrusted research content. No malware
scanning, cryptographic authorship signatures, independent security certification
or scientific validation is claimed. Stable release acceptance is tracked in the
[launch checklist](launch-checklist.md).
