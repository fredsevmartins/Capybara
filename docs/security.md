# Security model

See [disclosure policy](../SECURITY.md). Imports treat ZIP files as untrusted input:
entry paths are validated before extraction; duplicate names, case collisions, symlinks,
special files, encryption and unsupported compression are rejected. Staging directories
are cleaned on failure. Size/count/ratio limits constrain resource use. All payloads
must be inventoried and pass SHA-256 verification before import is committed.

Imported scripts remain inert. A valid checksum is not permission to execute them.
The server exposes local stdio only and confines all tool paths to one configured
workspace. Source symlinks are rejected. No TLS or artifact verification is disabled.

Limitations: no signatures, malware scanning, authentication service, immutable audit
trail, protection against malicious local concurrent writers or sandboxed execution.
Use trusted local directory ownership, one writer per experiment and external backups.
Metadata can contain sensitive material; inspect contents before sharing a package.
ZIP limits are fixed module constants in v0.1, not per-client configuration options.
