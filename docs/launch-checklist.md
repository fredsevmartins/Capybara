# Stable 1.0 release scope and external evaluation

Version 1.0.0 concludes the software delivery requested by the owner for a
**trusted local workflow**: organize and validate packages, explicitly reproduce
reviewed analysis in a local Linux Docker daemon, compare outputs, generate
reports, and exchange immutable revisions through catalogs or explicit deposits.
The Python package and commands remain `openrepro`; the repository is Capybara.

Earlier candidates proposed broader final-product gates requiring outside
researcher, usability and security evaluations. Those evaluations have **not**
been completed. The owner requested completion and GitHub publication; 1.0 narrows
the release claim to the implemented local software contract. It does not assert
that those external gates were passed or that research validity was certified.

| Capability | Engineering acceptance | External evidence still absent |
| --- | --- | --- |
| Environments | Exact hashes, registered wheels/lock, offline image builds | Representative independent user studies |
| Execution | Explicit reviewed execution, quotas, isolation, cleanup and recovery tests | Independent security review for the deployment threat model |
| Comparisons | Iris measurements, independently implemented references, units and justified tolerances | Researchers validating new methods and datasets |
| Workflow | CLI, Python API, MCP management tools, recipes, reports and documentation | Independent researcher usability feedback |
| Sharing | Immutable revisions, search, citations, read-only catalog, resumable Zenodo client | Exact identity of the manually uploaded rc1 archive against its tag |
| Distribution | Full OS/Python matrix, real Docker, clean wheel installation, checked release artifacts | Independent installation on a researcher's own machine |

## Supported boundaries

Package management supports Python 3.11–3.13 on Linux, macOS and Windows. Running
analysis and building environments require Linux and a trusted local Docker daemon.
Review imported code and execution recipes before granting explicit execution.
Docker isolation is defense in depth, not a certified boundary for hostile code.
The catalog is read-only HTTP for trusted networks; it is not an authenticated
multi-tenant public service. MCP exposes management, not execution.
Scientific validity remains `NOT_EVALUATED` regardless of matching results.
Use the [pilot protocol](pilot-protocol.md) for external evaluation before making
broader scientific, usability, security or institutional deployment claims.

## Publication acceptance

Before tagging: lint, documentation/schema checks, the complete local suite with
real Docker, distribution metadata/inventory checks and an installed-wheel
end-to-end acceptance must pass. GitHub publication additionally requires the
remote nine-combination OS/Python matrix and Docker verification. Download the
public artifacts, compare SHA-256 with the CI record and install the downloaded
wheel in a clean environment. Record actual results in [verification](verification.md).
Never substitute a tag push for evidence of a successful Release.

## Zenodo and PyPI

The user manually published OpenRepro 1.0.0rc1:
[version DOI](https://doi.org/10.5281/zenodo.23869679) and
[project/concept DOI](https://doi.org/10.5281/zenodo.23869678).
The screenshot shows `OpenRepro-main.zip`; exact archive/tag correspondence remains
unverified because direct Zenodo access is blocked in this environment. Preserve
that archive. Neither rc2 nor 1.0.0 is claimed to be deposited under the rc1 version
DOI. GitHub–Zenodo integration may archive the stable release automatically; a new
version DOI must be observed before documenting it as published.

PyPI was explicitly deferred by the owner. GitHub delivers the wheel, source and
checksums without a PyPI account. The optional trusted-publisher workflow remains
disabled unless explicitly selected in a future manual dispatch. No token belongs
in chat or source control; API automation can use securely configured credentials
when needed, and is not required for this GitHub delivery.
