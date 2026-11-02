# FAQ

**Is `.orepro` a new metadata standard?** No. It is a ZIP extension using RO-Crate
metadata plus a versioned OpenRepro manifest.

**Does PASS mean scientifically verified?** No. It means the implemented structural
and integrity checks found no issues. Scientific validity is always NOT_EVALUATED.

**Does it run experiments?** Importing and validation never execute code. Software 1.0.0 offers explicit opt-in reproduction on Linux with local Docker.
See [execution](execution.md) for prerequisites and limits.

**Does it require ChatGPT?** No. CLI and Python work locally and offline after installation.
A local MCP client is optional; hosted ChatGPT connectivity is not verified.

**Are checksums signatures?** No. They detect accidental or uncoordinated changes,
but cannot authenticate a package against an attacker who rewrites metadata too.

**Can I use real data?** Yes, if you have the right to preserve/share it. Review privacy,
licensing, provenance and scientific limitations yourself.

**Can I import every RO-Crate?** No. Native package schema 0.1 uses the restricted profile documented in
[package format](package-format.md).


**Is the product called Capybara or OpenRepro?** Capybara is the repository/product
identity and Repro is the mascot. The installed Python distribution/module/commands
remain `openrepro` for compatibility.

**Do I need PyPI or a token?** No account/token is required for installation from
the verified GitHub wheel or for local package management. Zenodo API automation
uses its own securely configured token. PyPI publication is currently deferred.

**Does `publish` create a public website or DOI?** No. It registers an immutable
revision in a local catalog. Zenodo publication is a separate explicit operation.

**Can I test with my own research?** Yes. Independent tests, usability feedback and
scientific-method reviews are welcome. Follow the [evaluation protocol](pilot-protocol.md)
and [contribution guide](../CONTRIBUTING.md); use synthetic/minimal data in public issues.

**What should I cite?** Use the relevant archived version DOI when it matches the
software/data used, or the project concept DOI for the version family. The manually
archived rc1 record is not evidence that 1.0.0 has the same version DOI. See
[Zenodo and citation](zenodo.md).
