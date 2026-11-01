# FAQ

**Is `.orepro` a new metadata standard?** No. It is a ZIP extension using RO-Crate
metadata plus a versioned OpenRepro manifest.

**Does PASS mean scientifically verified?** No. It means the implemented structural
and integrity checks found no issues. Scientific validity is always NOT_EVALUATED.

**Does it run experiments?** Importing and validation never execute code. The v0.2
development CLI offers explicit opt-in reproduction on Linux with local Docker.
See [execution](execution.md) for prerequisites and limits.

**Does it require ChatGPT?** No. CLI and Python work locally and offline after installation.
A local MCP client is optional; hosted ChatGPT connectivity is not verified.

**Are checksums signatures?** No. They detect accidental or uncoordinated changes,
but cannot authenticate a package against an attacker who rewrites metadata too.

**Can I use real data?** Yes, if you have the right to preserve/share it. Review privacy,
licensing, provenance and scientific limitations yourself.

**Can I import every RO-Crate?** No. v0.1 uses the restricted profile documented in
[package format](package-format.md).
