# Capybara documentation

**Capybara 1.0.0** provides OpenRepro, a toolkit for portable scientific experiment
packages. Repository/product: Capybara. Python package/module/CLI: `openrepro`.
Use it to organize protocols, data, code and provenance; check integrity; explicitly
reproduce reviewed analysis; and exchange immutable packages. Result agreement does
not establish scientific validity. See the [supported scope](launch-checklist.md).

## Start here

| Goal | Guide |
| --- | --- |
| Read in Portuguese | [Guia em português](guide-pt-br.md) |
| Install a public release | [Installation](installation.md) |
| Complete a first workflow without Docker | [Quick start](quickstart.md) |
| Understand PASS, WARN and FAIL | [Scientific integrity](scientific-integrity.md) |
| Find a command or option | [CLI overview](cli-reference.md) and [complete options](cli-options.md) |
| Use Python | [API guide](python-api.md) and [signatures and returns](api-reference.md) |
| Resolve a failure | [Troubleshooting](troubleshooting.md) and [FAQ](faq.md) |

## User workflows

- [Edit metadata and files; recover edits](editing.md).
- [Plan and run reviewed analysis](execution.md); [resolve/build environments](environments.md).
- [Understand reproducibility and tolerances](reproducibility.md).
- [Exchange, discover and cite packages](exchange.md); [back up and restore](operations.md).
- [Deposit with Zenodo and obtain a DOI](zenodo.md).
- [Convert local RO-Crates](interoperability.md); [integrate a local MCP client](mcp-integration.md).
- [Synthetic examples](examples.md) and [attributed real Iris example](../examples/iris/README.md).

## Reference and design

- [Package format 0.1](package-format.md), [JSON schemas](schemas/README.md),
  [version compatibility](compatibility.md) and [architecture](architecture.md).
- [Threat model](security.md), [vulnerability reporting](../SECURITY.md),
  [mascot and brand assets](branding.md), [repository rename](repository-rename.md).
- Workflows: [lifecycle](workflows/experiment-lifecycle.md), [export](workflows/package-export.md),
  [import](workflows/package-import.md), [validation](workflows/validation.md),
  [MCP](workflows/mcp-interaction.md).

## Contribution, evidence and releases

- [Contributing and local checks](../CONTRIBUTING.md), [code of conduct](../CODE_OF_CONDUCT.md).
- [GitHub releases](github-releases.md), [changelog](../CHANGELOG.md),
  [release scope](launch-checklist.md), [actual verification evidence](verification.md).
- [Independent evaluation protocol](pilot-protocol.md).
- [Optional PyPI publication](pypi-publication.md): deferred, not required for installation.

Software 1.0.0, native package schema 0.1, recipe schema 0.2 and environment schema 1
are separate versions. Native RO-Crate validation covers the generated profile,
not arbitrary JSON-LD graphs. Published release archives remain immutable; corrections
to these guides are available on the repository's `main` branch.
